from io import StringIO

import pandas as pd
import streamlit as st

from ai_actions import Action


class NsqAction(Action):

    def get_action_name(self):
        return "NSQ资源申请"

    def get_prompt(self):
        return ["""
        技术方案中提到了哪些NSQ消息消费的topic和channel，请按下面格式返回
        「nsq-info-start」开头
        json数组，数组中的元素包含app,topic,channel三个属性
        「nsq-info-end」结尾
        
        返回结果示例
        「nsq-info-start」
        [
          {
            "app": "导购关怀",
            "topic": "guide_customer_care_event",
            "channel": "guide_promotion_channel"
          }
        ]
        「nsq-info-end」
        """]

    def support(self, text: str):
        return "「nsq-info-start」" in text

    def parse(self, text: str):
        markdown_table = text.split("「nsq-info-start」")[1].split("「nsq-info-end」")[0].replace("```json", "").replace(
            "```", "")
        return markdown_table

    def actions(self, text: str, index: int, expander: st.expander):
        if 'dataframe' + str(index) in st.session_state:
            data = st.session_state['dataframe' + str(index)]
        else:
            json_str = self.parse(text).strip()
            # 使用pandas读取表格
            data = pd.read_json(StringIO(json_str))
            st.session_state['dataframe' + str(index)] = data

        data['topicApplyLink'] = "http://localhost:54321/topic/apply/" + data['app'] + "/" + data['topic']
        data['channelApplyLink'] = "http://localhost:54321/topic/apply/" + data['app'] + "/" + data['topic'] + "/" + \
                                   data['channel']
        data_edit = expander.data_editor(
            data,
            column_config={
                "app": st.column_config.TextColumn(
                    "App",
                    max_chars=50

                ),
                "topic": st.column_config.TextColumn(
                    "Topic",
                    max_chars=50
                ),
                "channel": st.column_config.TextColumn(
                    "Channel",
                    max_chars=50
                ),
                "topicApplyLink": st.column_config.LinkColumn(
                    "操作",
                    display_text="点击申请topic"
                ),
                "channelApplyLink": st.column_config.LinkColumn(
                    "操作",
                    display_text="点击申请channel"
                )
            },
            hide_index=True,
            key=index
        )
        if not data_edit.equals(st.session_state['dataframe' + str(index)]):
            st.session_state['dataframe' + str(index)] = data_edit
            st.rerun()
