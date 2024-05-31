import time

import streamlit as st
from openai import OpenAI
from nsq_actions import NsqAction
from enum_actions import EnumGenAction
from ai_actions import Action
from api_define_actions import APIGenAction

client = OpenAI()

actions = [NsqAction(), EnumGenAction(), APIGenAction()]


def get_assistant(file):
    if file is None:
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
        vector_store_id=vector_store.id, files=[file]
    )
    _assistant = client.beta.assistants.update(
        assistant_id=_assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    )
    st.session_state['assistant'] = _assistant
    return _assistant


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
    st.rerun()


if __name__ == '__main__':
    st.title('技术方案生成代码')
    action = NsqAction()
    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        assistant = get_assistant(uploaded_file)
        get_thread(assistant.id)

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
                    for prompt in action.get_prompt():
                        expander.write(prompt)
                    fit_action = True
            if not fit_action:
                st.markdown(message["content"])

    assistant = get_assistant(uploaded_file)
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
            input_area = st.container()
            for action in actions:
                st.button(action.get_action_name(), on_click=send_quick_prompt, args=(action, thread, assistant))
