import json

import streamlit as st
from ai_actions import Action


class WecomNsqConsumerGenAction(Action):

    def get_action_name(self):
        return "企助NSQ消费端生成"

    demo_request_class = repr("""
import lombok.*;
import lombok.experimental.FieldDefaults;
import java.io.Serializable;
   @Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@FieldDefaults(level = AccessLevel.PRIVATE)
public class RelChurnEvent implements Serializable {
    private static final long serialVersionUID = 4178635147040714982L;
    /**
     * 企助店铺ID
     */
    Long yzKdtId;

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
import com.alibaba.fastjson.JSON;
import com.youzan.nsq.client.exception.RetryBusinessException;
import com.youzan.scrm.component.nsq.consumer.annotations.NsqConsumerConfig;
import com.youzan.scrm.component.nsq.consumer.callback.AbstractPullCallback;
import com.youzan.scrm.component.nsq.consumer.pipe.entity.BaseInput;
import com.youzan.wecom.operation.biz.uniflow.listener.model.RelChurnEvent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

/**
 * @author panchengzhi
 * @date 2021/6/7
 */
@Slf4j
@Component
@NsqConsumerConfig(
        lookupAddress = "${sqs.lookup.address}",
        topic = "wecom_user_customer_rel",
        channel = "uniflow_customer_rel_churn",
        msgTimeoutInMilliseconds = 300000,
        rdy = 20,
        maxRetries = 5,
        enableApolloConfig = true,
        autoFinish = false
)
public class UniflowCustomerRelChurnJob extends AbstractPullCallback {

    @Override
    public void doProcess(BaseInput baseInput) throws RetryBusinessException {

        final RelChurnEvent event = JSON.parseObject(baseInput.getMsg(), RelChurnEvent.class);

    }
}
    """)

    def get_prompt(self):
        return [
            """
            技术方案中提到了哪些NSQ消息消费的topic、channel、event,请整理成列表 
            """,
            """
            将上面这些topic、channel、event按照整理成的列表填入Java类中，其中请求参数按照event内容生成
            - 请求参数规则
            所有的request_class中应该包含yzKdtId属性，代表企助店铺ID，Long类型;    
            你需要为每个方法生成注释，类中的字段也需要生成注释
             
            请按下面格式返回        
            「wecom-consumer-info-start」开头
            json数组，数组中的元素包含 desc(),
            request_class_code,response_class_code
            代码块是放在json中，一定要做好转义
            「wecom-consumer-info-end」结尾
            返回结果示例
            「wecom-consumer-info-start」
            [
              {
                "desc": "consumer的描述",
                "request_class_code": " """ + self.demo_request_class + """ ",
                "response_class_code": " """ + self.demo_response_class + """ ",
               }
            ]
             「wecom-consumer-info-end」
        """]

    def support(self, text: str):

        return "「wecom-consumer-info-start」" in text

    def parse(self, text: str):
        json_text = text.split("「wecom-consumer-info-start」")[1].split("「wecom-consumer-info-end」")[0].replace("```json", "").replace(
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
