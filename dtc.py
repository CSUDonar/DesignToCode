import json
import time

import streamlit as st
from openai import OpenAI
from nsq_actions import NsqAction
from enum_actions import EnumGenAction
from ai_actions import Action
from api_define_actions import APIGenAction
import streamlit.components.v1 as components
from js_component import js_code
import lark_oapi as lark
from lark_oapi.api.wiki.v2 import *
from lark_oapi.api.drive.v1 import *
from lark_oapi.api.auth.v3 import *
import os

client = OpenAI()

actions = [NsqAction(), EnumGenAction(), APIGenAction()]

app_id = os.getenv("lark_app_id")
app_secret = os.getenv("lark_app_secret")
lark_client = lark.Client.builder().app_id(app_id).app_secret(app_secret).build()


@st.cache_resource(ttl='1h')
def get_wiki_file(url: str):
    url = url.split("wiki/")[1]
    # 构造请求对象
    request: InternalTenantAccessTokenRequest = InternalTenantAccessTokenRequest.builder() \
        .request_body(InternalTenantAccessTokenRequestBody.builder()
                      .app_id(app_id)
                      .app_secret(app_secret)
                      .build()) \
        .build()

    # 发起请求
    response: InternalTenantAccessTokenResponse = lark_client.auth.v3.tenant_access_token.internal(request)
    if not response.success():
        raise Exception(response.msg)
    access_token = json.loads(response.raw.content)['tenant_access_token']
    # 构造请求对象
    request: GetNodeSpaceRequest = GetNodeSpaceRequest.builder() \
        .token(url) \
        .build()

    # 发起请求
    option = lark.RequestOption.builder().tenant_access_token(access_token).build()
    response: GetNodeSpaceResponse = lark_client.wiki.v2.space.get_node(request, option)
    if not response.success():
        raise Exception(response.msg)
    obj_token = response.data.node.obj_token
    obj_type = response.data.node.obj_type
    print(obj_token, obj_type)

    request: CreateExportTaskRequest = CreateExportTaskRequest.builder() \
        .request_body(ExportTask.builder()
                      .file_extension("pdf")
                      .token(obj_token)
                      .type(obj_type)
                      .build()) \
        .build()

    # 发起请求
    option = lark.RequestOption.builder().tenant_access_token(access_token).build()
    response: CreateExportTaskResponse = lark_client.drive.v1.export_task.create(request, option)
    if not response.success():
        raise Exception(response.code, response.msg)
    print(response.code, response.msg)
    ticket = response.data.ticket
    while True:
        # 构造请求对象
        request: GetExportTaskRequest = GetExportTaskRequest.builder() \
            .ticket(ticket) \
            .token(obj_token) \
            .build()

        # 发起请求
        option = lark.RequestOption.builder().tenant_access_token(access_token).build()
        response: GetExportTaskResponse = lark_client.drive.v1.export_task.get(request, option)
        # 处理失败返回
        if not response.success():
            raise Exception(response.msg)
        if response.data.result.job_status == 1 or response.data.result.job_status == 2:
            time.sleep(1)
            continue
        if response.data.result.job_status == 0:
            file_token = response.data.result.file_token
            # 构造请求对象
            request: DownloadExportTaskRequest = DownloadExportTaskRequest.builder() \
                .file_token(file_token) \
                .build()

            # 发起请求
            option = lark.RequestOption.builder().tenant_access_token(
                access_token).build()
            response: DownloadExportTaskResponse = lark_client.drive.v1.export_task.download(request, option)

            # 处理失败返回
            if not response.success():
                break
            # 处理业务结果
            f = open(f"/tmp/{response.file_name}", "wb")
            f.write(response.file.read())
            f.close()
            return f"/tmp/{response.file_name}"
        raise Exception(response.data.result.job_error_msg)


@st.cache_resource(ttl='1h')
def get_assistant(_file_path):
    if _file_path is None:
        return None
    if 'assistant' in st.session_state:
        return st.session_state['assistant']
    # 创建助手
    _assistant = client.beta.assistants.create(
        name="技术方案分析",
        description="""
        解析后端的技术方案,并按照用户的要求转换成对应的代码，你需要使用中文回答
        """,
        model="gpt-4o",
        tools=[{"type": "file_search"}]
    )
    vector_store = client.beta.vector_stores.create(name="技术方案" + str(time.time()))
    client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=[open(_file_path, "rb")]
    )
    _assistant = client.beta.assistants.update(
        assistant_id=_assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    )
    st.session_state['assistant'] = _assistant
    return _assistant


@st.cache_resource(ttl='1h')
def get_thread(assistant_id):
    if assistant_id is None:
        return None
    if 'thread' in st.session_state and 'run' in st.session_state:
        return st.session_state['thread'], st.session_state['run']
    _thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": """
                下面我要开始提问了
                """
            }
        ]
    )
    _run = client.beta.threads.runs.create_and_poll(
        thread_id=_thread.id, assistant_id=assistant_id
    )
    st.session_state['thread'] = _thread
    st.session_state['run'] = _run
    return _thread, _run


def send_quick_prompt(_action: Action, _thread, _assistant):
    st.session_state.messages.append({"role": "user", "content": _action.get_action_name()})
    prompts = _action.get_prompt()
    for p in prompts:
        client.beta.threads.messages.create(thread_id=_thread.id, role="user", content=p)
        _run = client.beta.threads.runs.create_and_poll(
            thread_id=_thread.id, assistant_id=_assistant.id
        )
        print(run.usage)
    msgs = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=_run.id))
    msg_content = msgs[0].content[0].text
    anno = msg_content.annotations
    for i, a in enumerate(anno):
        msg_content.value = msg_content.value.replace(a.text, "")
    st.session_state.messages.append({"role": "sys", "content": msg_content.value})


if __name__ == '__main__':
    st.title('Design To Code')
    assistant = None
    if "assistant" not in st.session_state:
        st.divider()
        st.markdown("**技术方案文档先要做好权限配置**")
        st.write("1. **文档所有者、知识库管理员 或 其他协作者** 为资源 添加文档应用。")
        st.write("2. 通过云文档 Web 页面右上方 **「...」->「...更多」-> 「添加文档应用」** 入口添加。")
        st.image("img.png")
        st.write("3. 复制链接地址到下面输入框回车等待文档解析完成")
        st.divider()
        docUrl = st.text_input("请输入技术方案链接", key="docUrl")
        if docUrl:
            file_path = get_wiki_file(docUrl.strip())
            if file_path is not None:
                assistant = get_assistant(file_path)
                st.session_state.file_name = file_path
    else:
        assistant = st.session_state.assistant

    if "file_name" in st.session_state:
        name = st.session_state.file_name.replace("/tmp/", "")
        st.write("技术方案:")
        with open(st.session_state.file_name, "rb") as file:
            btn = st.download_button(
                label=name,
                data=file,
                file_name=name,
                mime="application/pdf"
            )
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for index, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            fit_action = False
            for action in actions:
                if action.support(message["content"]):
                    expander = st.expander("详情", expanded=True)
                    action.actions(message["content"], index, expander)
                    fit_action = True
                if action.get_action_name() == message["content"]:
                    expander = st.expander(action.get_action_name(), expanded=False)
                    for i, prompt in enumerate(action.get_prompt()):
                        expander.markdown(f"**提示词 {i + 1}**")
                        expander.text(prompt)
                    fit_action = True
            if not fit_action:
                st.markdown(message["content"])

    if assistant is not None:
        thread, run = get_thread(assistant.id)
        if thread is not None and run is not None:
            question = st.chat_input("请输入")
            if question:
                st.session_state.messages.append({"role": "user", "content": question})
                with st.chat_message("user"):
                    st.markdown(question)

                client.beta.threads.messages.create(thread_id=thread.id, role="user", content=question)
                run = client.beta.threads.runs.create_and_poll(
                    thread_id=thread.id, assistant_id=assistant.id
                )
                print(run.usage)
                messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
                message_content = messages[0].content[0].text
                annotations = message_content.annotations
                for index, annotation in enumerate(annotations):
                    message_content.value = message_content.value.replace(annotation.text, "")
                st.session_state.messages.append({"role": "sys", "content": message_content.value})
                with st.chat_message("sys"):
                    st.markdown(message_content.value)
            with st.container():
                for action in actions:
                    st.button(action.get_action_name(), on_click=send_quick_prompt,
                              args=(action, thread, assistant))
    components.html(js_code)
