import json

import streamlit as st
from ai_actions import Action


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

    def get_prompt(self):
        return [
            """
               方案中'接口设计'章节中新增的前端接口有哪些，请整理成列表 
            """,
            """
            将上面这些接口根据其接口描述生成java接口方法
            接口方法定义的代码方法的返回类型遵循下面规则
            - 返回参数规则
            正常情况下是PlainResult<T> T 代表真正要返回的数据类型
            如果接口返回的是一个列表则返回的是ListResult<T> T 代表列表中的元素类型
            如果接口返回的是一个分页数据则返回的是PaginatorResult<T> T 代表分页的列表中的元素类型
            下面是这几个基础响应类的代码
            public class PlainResult<T> {
                private T data;
                private boolean success;
                private int code;
                private String message;
            }
            
            public class ListResult<T> {
                private List<T> data;
                private int count;
                private boolean success;
                private int code;
                private String message;
            }
            
            public class PaginatorResult<T> {
                private ListWithPaginatorVO<T> data;
                private boolean success;
                private int code;
                private String message;
            }
            
            public class ListWithPaginatorVO<T> implements Serializable {
                private Paginator paginator;
                private List<T> items;
            }
            上面的范型T代表的是response_class
            如果返回的是基础类型则不用生成response_class
            
            - 请求参数规则
            所有的request_class中应该包含rootKdtId属性，代表总部ID，Long类型;
            
            你需要为每个方法生成注释，类中的字段也需要生成注释
            
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
        tabs = expander.tabs([enum["desc"] for enum in enums])
        for i, tab in enumerate(tabs):
            if enums[i]["request_class_code"]:
                tab.code(enums[i]["method_code"])
            if enums[i]["request_class_code"]:
                tab.code(enums[i]["request_class_code"].replace("'", "").replace("\\n", "\n"))
            if enums[i]["response_class_code"]:
                tab.code(enums[i]["response_class_code"].replace("'", "").replace("\\n", "\n"))
