import json

import streamlit as st
from ai_actions import Action
import streamlit_antd_components as sac



class APIGenAction(Action):

    def get_action_name(self):
        return "API接口生成"

    demo_request_class = repr("""
    @Data
    public class LeadsNoticeConfigQueryRequest implements Serializable {
        private static final long serialVersionUID = -7399380056776393130L;
        /**
        * 总部id
        */
        private Long rootKdtId;
        /**
        * 导购ID
        */
        private Long guideId;
    }        
    """)

    demo_response_class = repr("""
    @Data
    public class LeadsNoticeConfigQueryResponse implements Serializable {
        private static final long serialVersionUID = -5324093008982761172L;
        /**
         * 是否接收销售线索通知
         * 0：接受
         * 1：不接受
         */
        private Integer pushSwitch;
        /**
         * 通知开始时间
         */
        private String startTime;
        /**
         * 通知结束时间
         */
        private String endTime;
    }""")
    print(demo_request_class)

    def get_prompt(self):
        return [
            """
               方案中新增的前端接口有哪些，请整理成列表 
            """,
            """
            将上面这些接口根据其接口描述生成java接口方法
            请按下面格式返回        
            「api-info-start」开头
            json数组，数组中的元素包含 desc(接口方法的描述),method_code(接口方法定义的代码),
            request_class_code(接口方法请求入参类的代码),response_class_code(接口方法返回类的代码)
            代码块是放在json中，一定要做好转义
            「api-info-end」结尾
            返回结果示例
            「api-info-start」
            [
              {
                "desc": "接口方法描述",
                "method_code": "PlainResult<LeadsNoticeConfigQueryResponse> getLeadsNoticeConfig(LeadsNoticeConfigQueryRequest request);",
                "request_class_code": " """ + self.demo_request_class + """ ",
            "response_class_code": " """ + self.demo_response_class + """ ",
          }
        ]
        「api-info-end」
        """]

    def support(self, text: str):

        return "「api-info-start」" in text

    def parse(self, text: str):
        json_text = text.split("「api-info-start」")[1].split("「api-info-end」")[0].replace("```json", "").replace(
            "```", "")
        return json_text

    def actions(self, text: str, index: int, expander: st.expander):
        json_str = self.parse(text).strip()
        try:
            enums = json.loads(json_str)
        except Exception as e:
            enums = eval(json_str)
        print(enums)
        tabs = expander.tabs([enum["desc"] for enum in enums])
        for i, tab in enumerate(tabs):
            tab.code(enums[i]["method_code"])
            tab.code(enums[i]["request_class_code"].replace("'", "").replace("\\n", "\n"))
            tab.code(enums[i]["response_class_code"].replace("'", "").replace("\\n", "\n"))
