"""
工单分类Agent - 扩展IntentAgent

职责：识别工单类型、优先级、紧急程度
"""
from typing import Optional, Dict, Any
from enum import Enum

from opspilot.agents.base import (
    BaseAgent,
    AgentConfig,
    AgentRole,
    AgentContext,
    AgentOutput,
    BaseLLMClient,
)


class TicketType(str, Enum):
    """工单类型"""
    ORDER_ISSUE = "order_issue"           # 订单问题
    LOGISTICS_ISSUE = "logistics_issue"   # 物流问题
    REFUND_REQUEST = "refund_request"     # 退款申请
    PRODUCT_INQUIRY = "product_inquiry"   # 产品咨询
    COMPLAINT = "complaint"               # 投诉
    OTHER = "other"                       # 其他


class TicketPriority(str, Enum):
    """工单优先级"""
    HIGH = "high"       # 高优先级（VIP客户、紧急问题）
    NORMAL = "normal"   # 正常
    LOW = "low"         # 低优先级


class TicketClassifierAgent(BaseAgent):
    """
    工单分类Agent
    
    继承BaseAgent，复用意图识别逻辑
    """

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        config = AgentConfig(
            name="TicketClassifierAgent",
            role=AgentRole.INTENT,
            description="工单分类Agent，识别工单类型和优先级",
            temperature=0.3,
        )
        super().__init__(config, llm_client)

    async def _execute(self, context: AgentContext) -> AgentOutput:
        """执行工单分类"""
        ticket_content = context.user_input
        
        if not ticket_content:
            return AgentOutput(
                success=False,
                error="工单内容为空"
            )

        # 构建分类提示
        prompt = self._build_classify_prompt(ticket_content)
        
        # 调用LLM
        response = await self.llm.generate_json(prompt)
        
        # 解析响应
        classification = self._parse_response(response)
        
        return AgentOutput(
            success=True,
            result=classification,
            reasoning=f"工单分类: {classification.get('ticket_type', 'unknown')}, 优先级: {classification.get('priority', 'normal')}"
        )

    def _build_classify_prompt(self, ticket_content: str) -> str:
        """构建分类提示"""
        return f"""请分析以下客服工单，识别工单类型和优先级。

工单内容：{ticket_content}

请以JSON格式返回：
{{
    "ticket_type": "工单类型（order_issue/logistics_issue/refund_request/product_inquiry/complaint/other）",
    "priority": "优先级（high/normal/low）",
    "confidence": 0.0-1.0的置信度,
    "keywords": ["关键词列表"],
    "summary": "工单摘要",
    "suggested_department": "建议处理部门（订单组/物流组/退款组/客服组/投诉组）"
}}

仅返回JSON，不要有其他内容。"""

    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析响应"""
        # 验证工单类型
        try:
            TicketType(response.get("ticket_type", "other"))
        except ValueError:
            response["ticket_type"] = TicketType.OTHER.value
            
        # 验证优先级
        try:
            TicketPriority(response.get("priority", "normal"))
        except ValueError:
            response["priority"] = TicketPriority.NORMAL.value
            
        return {
            "ticket_type": response.get("ticket_type", "other"),
            "priority": response.get("priority", "normal"),
            "confidence": response.get("confidence", 0.8),
            "keywords": response.get("keywords", []),
            "summary": response.get("summary", ""),
            "suggested_department": response.get("suggested_department", "客服组"),
        }

    def get_system_prompt(self, context: AgentContext) -> str:
        """获取系统提示"""
        return """你是一个专业的客服工单分类助手。
你的任务是分析客户提交的工单内容，识别：
1. 工单类型：订单问题、物流问题、退款申请、产品咨询、投诉等
2. 优先级：根据问题严重程度和客户等级判断
3. 建议处理部门

请保持客观、准确，确保工单能够被正确路由到合适的处理团队。"""


class MockTicketClassifierAgent(TicketClassifierAgent):
    """
    Mock工单分类Agent - 使用规则匹配
    """

    async def _execute(self, context: AgentContext) -> AgentOutput:
        """执行工单分类（规则匹配）"""
        content = context.user_input.lower()
        
        # 规则匹配工单类型
        ticket_type = TicketType.OTHER
        suggested_department = "客服组"
        
        if any(kw in content for kw in ["订单", "下单", "订单号"]):
            ticket_type = TicketType.ORDER_ISSUE
            suggested_department = "订单组"
        elif any(kw in content for kw in ["物流", "快递", "配送", "发货"]):
            ticket_type = TicketType.LOGISTICS_ISSUE
            suggested_department = "物流组"
        elif any(kw in content for kw in ["退款", "退货", "退钱"]):
            ticket_type = TicketType.REFUND_REQUEST
            suggested_department = "退款组"
        elif any(kw in content for kw in ["投诉", "不满", "差评"]):
            ticket_type = TicketType.COMPLAINT
            suggested_department = "投诉组"
        elif any(kw in content for kw in ["咨询", "问一下", "了解"]):
            ticket_type = TicketType.PRODUCT_INQUIRY
            suggested_department = "客服组"
        
        # 判断优先级
        priority = TicketPriority.NORMAL
        if any(kw in content for kw in ["紧急", "加急", "vip", "马上", "立刻"]):
            priority = TicketPriority.HIGH
        elif any(kw in content for kw in ["不急", "方便时"]):
            priority = TicketPriority.LOW
            
        result = {
            "ticket_type": ticket_type.value,
            "priority": priority.value,
            "confidence": 0.9,
            "keywords": [kw for kw in ["订单", "物流", "退款", "投诉", "咨询"] if kw in content],
            "summary": f"工单类型: {ticket_type.value}",
            "suggested_department": suggested_department,
        }
        
        return AgentOutput(
            success=True,
            result=result,
            reasoning=f"通过关键词匹配识别工单类型: {ticket_type.value}"
        )
