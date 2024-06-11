import json

import streamlit as st
from ai_actions import Action


class GuideNsqConsumerGenAction(Action):

    def get_action_name(self):
        return "导购NSQ消费端生成"

    demo_request_class = repr("""
import lombok.Data;

@Data
public class GuideMomentLikeEvent implements Serializable {
    private static final long serialVersionUID = 4178635147040714982L;
     /**
     * 店铺ID
     */
    private Long rootKdtId;

    /**
     * 外部联系人id
     */
    String wecomExternalUserId;

    /**
     * 员工id
     */
    Long staffId;

    /**
     * 流失时间
     */
    Long churnTime;
}    
    """)

    demo_response_class = repr("""
import com.youzan.guide.biz.moment.domain.dto.event.GuideMomentLikeEvent;
import org.springframework.stereotype.Component;

import com.alibaba.fastjson.JSON;
import com.youzan.api.nsq.NsqListener;
import com.youzan.guide.eye.monitor.annotation.NsqConsumerMonitor;
import com.youzan.nsq.client.entity.NSQMessage;

import lombok.extern.slf4j.Slf4j;

/**
 * 点赞动态事件监听
 *
 * @author liuxinfeng
 * @since 2024年05月31日
 */
@Component
@Slf4j
public class GuideMomentLikeEventListener {
    @NsqListener(topic = "wecom_user_customer_rel", channel = "uniflow_customer_rel_churn")
    public void doHandle(NSQMessage message) {
        GuideMomentLikeEvent event = JSON.parseObject(message.getReadableContent(), GuideMomentLikeEvent.class);
    }
}
    """)

    def get_prompt(self):
        return [
            """
            技术方案中提到了哪些NSQ消息消费的topic、channel、event,请整理成列表 
            """,
            """
            将上面这些topic、channel、event按照规则填入Java类中，其中请求参数按照event内容生成
            - 请求参数规则
            所有的request_class中应该包含rootKdtId属性，代表店铺ID，Long类型;    
             
            请按下面格式返回        
            「guide-consumer-info-start」开头
            json数组，数组中的元素包含 desc(),
            request_class_code,response_class_code
            代码块是放在json中，一定要做好转义
            「guide-consumer-info-end」结尾
            返回结果示例
            「guide-consumer-info-start」
            [
              {
                "desc": "consumer的描述",
                "request_class_code": " """ + self.demo_request_class + """ ",
                "response_class_code": " """ + self.demo_response_class + """ ",
               }
            ]
             「guide-consumer-info-end」
        """]

    def support(self, text: str):

        return "「guide-consumer-info-start」" in text

    def parse(self, text: str):
        json_text = text.split("「guide-consumer-info-start」")[1].split("「guide-consumer-info-end」")[0].replace("```json", "").replace(
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
                tab.code(enums[i]["request_class_code"].replace("'", "").replace("\\n", "\n"))
            if enums[i]["response_class_code"]:
                tab.code(enums[i]["response_class_code"].replace("'", "").replace("\\n", "\n"))
