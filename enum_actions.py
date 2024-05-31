import json

import streamlit as st
from ai_actions import Action


class EnumGenAction(Action):

    def get_action_name(self):
        return "枚举类生成"

    def get_prompt(self):
        return ["""找出技术方案中提到的可枚举字段和他的枚举值""",
                """
        基于上面的枚举说明 生成对应的java枚举类,枚举类的类名以Enum结尾，枚举类需要包含根据value找到对应枚举的方法，
        方法入参应该是封装类型而不是基础类型，比如应该使用Integer而不是int,如果找不到对应的枚举,返回null即可,不用抛异常。
        请按下面格式返回
        「enum-info-start」开头
        json数组，数组中的元素包含 desc(枚举的描述),code(枚举代码)
        「enum-info-end」结尾
        返回结果示例
        「enum-info-start」
        [
          {
            "desc": "枚举描述",
            "code": "...",
          }
        ]
        「enum-info-end」
        """]

    def support(self, text: str):
        return "「enum-info-start」" in text

    def parse(self, text: str):
        json_text = text.split("「enum-info-start」")[1].split("「enum-info-end」")[0].replace("```json", "").replace(
            "```", "")
        return json_text

    def actions(self, text: str, index: int, expander: st.expander):
        json_str = self.parse(text).strip()
        try:
            enums = json.loads(json_str)
        except Exception as e:
            enums = eval(json_str)
        tabs = expander.tabs([enum["desc"] for enum in enums])
        for i, tab in enumerate(tabs):
            tab.code(enums[i]["code"])