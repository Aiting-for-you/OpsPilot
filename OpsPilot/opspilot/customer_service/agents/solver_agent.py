"""
工单解决Agent

职责：生成工单解决方案
"""
from typing import Optional, Dict, Any, List
from datetime import datetime

from opspilot.agents.base import (
    BaseAgent,
    AgentConfig,
    AgentRole,
    AgentContext,
    AgentOutput,
    BaseLLMClient,
)


# 解决方案模板
SOLUTION_TEMPLATES = {
    "order_issue": {
        "template": "订单问题解决方案：{action}。已{status}。",
        "actions": ["查询订单状态", "联系仓库", "修改订单信息", "取消订单"],
    },
    "logistics_issue": {
        "template": "物流问题解决方案：{action}。预计{estimated_time}到达。",
        "actions": ["查询物流轨迹", "联系快递公司", "安排重新配送", "提供物流补偿"],
    },
    "refund_request": {
        "template": "退款申请处理：{action}。退款金额¥{amount}，预计{refund_time}到账。",
        "actions": ["审核退款条件", "提交退款申请", "联系财务处理", "通知客户退款进度"],
    },
    "product_inquiry": {
        "template": "产品咨询回复：{answer}",
        "actions": ["查询产品信息", "提供产品对比", "解答使用疑问", "推荐相关产品"],
    },
    "complaint": {
        "template": "投诉处理：{action}。补偿方案：{compensation}。",
        "actions": ["记录投诉内容", "调查投诉原因", "制定补偿方案", "回访客户确认"],
    },
    "other": {
        "template": "问题处理：{action}",
        "actions": ["了解问题详情", "协调相关部门", "跟进处理进度"],
    },
}


class TicketSolverAgent(BaseAgent):
    """
    工单解决Agent
    
    生成解决方案并执行
    """

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        config = AgentConfig(
            name="TicketSolverAgent",
            role=AgentRole.EXECUTION,
            description="工单解决Agent，生成解决方案",
            temperature=0.5,
        )
        super().__init__(config, llm_client)

    async def _execute(self, context: AgentContext) -> AgentOutput:
        """执行工单解决"""
        # 获取上下文信息
        ticket_content = context.user_input
        classification = context.metadata.get("classification", {})
        routing = context.metadata.get("routing", {})
        
        if not classification:
            return AgentOutput(
                success=False,
                error="缺少工单分类信息"
            )
        
        ticket_type = classification.get("ticket_type", "other")
        
        # 构建解决提示
        prompt = self._build_solve_prompt(
            ticket_content=ticket_content,
            ticket_type=ticket_type,
            classification=classification,
            routing=routing,
        )
        
        # 调用LLM
        response = await self.llm.generate_json(prompt)
        
        # 解析响应
        solution = self._parse_response(response, ticket_type)
        
        return AgentOutput(
            success=True,
            result=solution,
            reasoning=f"生成解决方案: {solution.get('summary', '')}"
        )

    def _build_solve_prompt(
        self,
        ticket_content: str,
        ticket_type: str,
        classification: Dict[str, Any],
        routing: Dict[str, Any],
    ) -> str:
        """构建解决提示"""
        template = SOLUTION_TEMPLATES.get(ticket_type, SOLUTION_TEMPLATES["other"])
        
        return f"""请为以下客服工单生成解决方案。

工单内容：{ticket_content}

工单分类：{ticket_type}
优先级：{classification.get('priority', 'normal')}
建议处理部门：{routing.get('assigned_department', '客服组')}

可用操作：{', '.join(template['actions'])}

请以JSON格式返回解决方案：
{{
    "action_taken": "执行的操作",
    "resolution": "解决方案描述",
    "estimated_completion": "预计完成时间",
    "requires_followup": true/false,
    "followup_actions": ["后续行动"],
    "customer_notification": "客户通知内容",
    "summary": "处理摘要"
}}

仅返回JSON，不要有其他内容。"""

    def _parse_response(self, response: Dict[str, Any], ticket_type: str) -> Dict[str, Any]:
        """解析响应"""
        return {
            "action_taken": response.get("action_taken", ""),
            "resolution": response.get("resolution", ""),
            "estimated_completion": response.get("estimated_completion", "即时"),
            "requires_followup": response.get("requires_followup", False),
            "followup_actions": response.get("followup_actions", []),
            "customer_notification": response.get("customer_notification", ""),
            "summary": response.get("summary", ""),
            "solved_at": datetime.now().isoformat(),
            "ticket_type": ticket_type,
        }

    def get_system_prompt(self, context: AgentContext) -> str:
        """获取系统提示"""
        return """你是一个专业的客服工单解决助手。
你的任务是根据工单内容生成解决方案。
你需要：
1. 分析工单问题
2. 制定解决方案
3. 确定是否需要后续跟进
4. 生成客户通知内容

确保解决方案清晰、可行、客户友好。"""


class MockTicketSolverAgent(TicketSolverAgent):
    """
    Mock工单解决Agent - 使用模板生成
    """

    async def _execute(self, context: AgentContext) -> AgentOutput:
        """执行工单解决（模板生成）"""
        classification = context.metadata.get("classification", {})
        routing = context.metadata.get("routing", {})
        
        ticket_type = classification.get("ticket_type", "other")
        template = SOLUTION_TEMPLATES.get(ticket_type, SOLUTION_TEMPLATES["other"])
        
        # 使用第一个操作作为解决方案
        action = template["actions"][0]
        
        # 生成简单解决方案
        resolution = template["template"].format(
            action=action,
            status="处理完成",
            estimated_time="1-2天",
            amount=100,
            refund_time="3-5个工作日",
            answer="已为您查询到相关信息",
            compensation="优惠券50元",
        )
        
        result = {
            "action_taken": action,
            "resolution": resolution,
            "estimated_completion": "即时",
            "requires_followup": ticket_type in ["refund_request", "complaint"],
            "followup_actions": ["发送客户通知", "更新工单状态"] if ticket_type in ["refund_request", "complaint"] else [],
            "customer_notification": f"您的工单已处理。{resolution}",
            "summary": f"已执行: {action}",
            "solved_at": datetime.now().isoformat(),
            "ticket_type": ticket_type,
        }
        
        return AgentOutput(
            success=True,
            result=result,
            reasoning=f"使用模板生成解决方案: {action}"
        )
