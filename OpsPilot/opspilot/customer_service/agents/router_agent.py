"""
工单路由Agent

职责：根据分类结果决定工单路由策略
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


# 路由规则配置
ROUTING_RULES = {
    "order_issue": {
        "primary_department": "订单组",
        "fallback_department": "客服组",
        "estimated_resolution_time": "2小时",
        "escalation_threshold": 4,  # 超过4小时未处理则升级
    },
    "logistics_issue": {
        "primary_department": "物流组",
        "fallback_department": "客服组",
        "estimated_resolution_time": "1小时",
        "escalation_threshold": 2,
    },
    "refund_request": {
        "primary_department": "退款组",
        "fallback_department": "财务组",
        "estimated_resolution_time": "4小时",
        "escalation_threshold": 8,
    },
    "product_inquiry": {
        "primary_department": "客服组",
        "fallback_department": None,
        "estimated_resolution_time": "30分钟",
        "escalation_threshold": 2,
    },
    "complaint": {
        "primary_department": "投诉组",
        "fallback_department": "主管组",
        "estimated_resolution_time": "1小时",
        "escalation_threshold": 2,
    },
    "other": {
        "primary_department": "客服组",
        "fallback_department": None,
        "estimated_resolution_time": "2小时",
        "escalation_threshold": 4,
    },
}


class TicketRouterAgent(BaseAgent):
    """
    工单路由Agent
    
    决定工单分配策略
    """

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        config = AgentConfig(
            name="TicketRouterAgent",
            role=AgentRole.PLANNING,
            description="工单路由Agent，决定工单分配策略",
            temperature=0.2,
        )
        super().__init__(config, llm_client)

    async def _execute(self, context: AgentContext) -> AgentOutput:
        """执行路由决策"""
        # 获取分类结果
        classification = context.metadata.get("classification", {})
        
        if not classification:
            return AgentOutput(
                success=False,
                error="缺少工单分类信息"
            )
        
        ticket_type = classification.get("ticket_type", "other")
        priority = classification.get("priority", "normal")
        suggested_department = classification.get("suggested_department", "客服组")
        
        # 获取路由规则
        routing_rule = ROUTING_RULES.get(ticket_type, ROUTING_RULES["other"])
        
        # 构建路由决策
        routing = self._make_routing_decision(
            ticket_type=ticket_type,
            priority=priority,
            suggested_department=suggested_department,
            routing_rule=routing_rule,
        )
        
        return AgentOutput(
            success=True,
            result=routing,
            reasoning=f"工单路由到 {routing['assigned_department']}, 预计 {routing['estimated_resolution_time']} 解决"
        )

    def _make_routing_decision(
        self,
        ticket_type: str,
        priority: str,
        suggested_department: str,
        routing_rule: Dict[str, Any],
    ) -> Dict[str, Any]:
        """制定路由决策"""
        # 确定分配部门
        if priority == "high":
            # 高优先级工单优先使用建议部门
            assigned_department = suggested_department
        else:
            # 普通和低优先级使用主部门
            assigned_department = routing_rule["primary_department"]
        
        # 调整预计解决时间
        base_time = routing_rule["estimated_resolution_time"]
        if priority == "high":
            estimated_resolution_time = "立即处理"
        elif priority == "low":
            estimated_resolution_time = base_time
        else:
            estimated_resolution_time = base_time
        
        return {
            "assigned_department": assigned_department,
            "fallback_department": routing_rule.get("fallback_department"),
            "estimated_resolution_time": estimated_resolution_time,
            "escalation_threshold_hours": routing_rule["escalation_threshold"],
            "routing_rule_applied": routing_rule,
            "routed_at": datetime.now().isoformat(),
            "priority_adjusted": priority == "high",
        }

    def get_system_prompt(self, context: AgentContext) -> str:
        """获取系统提示"""
        return """你是一个专业的工单路由助手。
你的任务是根据工单类型、优先级等信息，决定工单应该分配给哪个部门处理。
你需要考虑：
1. 工单类型与部门的匹配度
2. 优先级的紧急程度
3. 备选部门（用于主部门繁忙时）
4. 升级阈值

确保工单能够被高效、准确地处理。"""


class MockTicketRouterAgent(TicketRouterAgent):
    """
    Mock工单路由Agent - 使用规则路由
    """

    async def _execute(self, context: AgentContext) -> AgentOutput:
        """执行路由决策（规则路由）"""
        classification = context.metadata.get("classification", {})
        
        if not classification:
            return AgentOutput(
                success=False,
                error="缺少工单分类信息"
            )
        
        ticket_type = classification.get("ticket_type", "other")
        priority = classification.get("priority", "normal")
        suggested_department = classification.get("suggested_department", "客服组")
        
        # 使用规则路由
        routing_rule = ROUTING_RULES.get(ticket_type, ROUTING_RULES["other"])
        
        # 简单路由决策
        assigned_department = suggested_department if priority == "high" else routing_rule["primary_department"]
        
        result = {
            "assigned_department": assigned_department,
            "fallback_department": routing_rule.get("fallback_department"),
            "estimated_resolution_time": "立即处理" if priority == "high" else routing_rule["estimated_resolution_time"],
            "escalation_threshold_hours": routing_rule["escalation_threshold"],
            "routed_at": datetime.now().isoformat(),
        }
        
        return AgentOutput(
            success=True,
            result=result,
            reasoning=f"工单路由到 {assigned_department}"
        )
