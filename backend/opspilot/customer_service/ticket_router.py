"""
工单路由器

职责：整合分类、路由、优先级引擎，统一协调工单分发
"""
from typing import Optional, Dict, Any, List
from enum import Enum

from opspilot.customer_service.agents.classifier_agent import (
    TicketClassifierAgent,
    MockTicketClassifierAgent,
    TicketType,
    TicketPriority,
)
from opspilot.customer_service.agents.router_agent import (
    TicketRouterAgent,
    MockTicketRouterAgent,
)


class TicketStatus(str, Enum):
    """工单状态"""
    OPEN = "open"                     # 新建待处理
    IN_PROGRESS = "in_progress"       # 处理中
    PENDING = "pending"              # 等待中
    RESOLVED = "resolved"            # 已解决
    CLOSED = "closed"                 # 已关闭
    REOPENED = "reopened"             # 已重新打开
    ESCALATED = "escalated"           # 已升级


class TicketRouter:
    """
    工单路由器
    
    整合分类、路由、优先级引擎，提供统一的工单分发入口
    """
    
    def __init__(
        self,
        classifier: Optional[TicketClassifierAgent] = None,
        router: Optional[TicketRouterAgent] = None,
    ):
        # 使用Mock版本作为默认
        self.classifier = classifier or MockTicketClassifierAgent()
        self.router = router or MockTicketRouterAgent()
        
        # 优先级配置
        self.priority_rules = {
            TicketPriority.HIGH: {
                "sla_response_minutes": 15,
                "sla_resolve_hours": 4,
                "queue": "urgent",
            },
            "high": {
                "sla_response_minutes": 15,
                "sla_resolve_hours": 4,
                "queue": "urgent",
            },
            TicketPriority.NORMAL: {
                "sla_response_minutes": 60,
                "sla_resolve_hours": 24,
                "queue": "normal",
            },
            "normal": {
                "sla_response_minutes": 60,
                "sla_resolve_hours": 24,
                "queue": "normal",
            },
            TicketPriority.LOW: {
                "sla_response_minutes": 240,
                "sla_resolve_hours": 72,
                "queue": "low",
            },
            "low": {
                "sla_response_minutes": 240,
                "sla_resolve_hours": 72,
                "queue": "low",
            },
        }

    async def route_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        路由工单（主入口）
        
        流程：分类 -> 路由 -> 优先级 -> 返回结果
        """
        ticket_id = ticket_data.get("ticket_id", "")
        content = ticket_data.get("content", "")
        
        # 1. 分类
        classification = await self._classify_ticket(ticket_id, content)
        
        # 2. 路由
        routing = await self._route_ticket(ticket_id, classification)
        
        # 3. 计算优先级和SLA
        priority_info = self._calculate_priority(classification, ticket_data)
        
        # 4. 整合结果
        result = {
            "ticket_id": ticket_id,
            "status": TicketStatus.OPEN.value,
            "classification": classification,
            "routing": routing,
            "priority": priority_info,
            "sla": self._calculate_sla(priority_info),
            "workflow": self._determine_workflow(classification, routing),
        }
        
        return result

    async def _classify_ticket(
        self,
        ticket_id: str,
        content: str,
    ) -> Dict[str, Any]:
        """分类工单"""
        from opspilot.agents.base import AgentContext
        
        context = AgentContext(
            user_input=content,
            metadata={"ticket_id": ticket_id},
        )
        
        output = await self.classifier.execute(context)
        
        if output.success:
            return output.result
        else:
            # 分类失败，使用默认分类
            return {
                "ticket_type": TicketType.OTHER.value,
                "priority": TicketPriority.NORMAL.value,
                "confidence": 0.0,
                "keywords": [],
                "summary": content[:100],
                "suggested_department": "客服组",
            }

    async def _route_ticket(
        self,
        ticket_id: str,
        classification: Dict[str, Any],
    ) -> Dict[str, Any]:
        """路由工单"""
        from opspilot.agents.base import AgentContext
        
        context = AgentContext(
            user_input=ticket_id,
            metadata={
                "ticket_id": ticket_id,
                "classification": classification,
            },
        )
        
        output = await self.router.execute(context)
        
        if output.success:
            return output.result
        else:
            # 路由失败，使用默认路由
            return {
                "assigned_department": classification.get("suggested_department", "客服组"),
                "assigned_agent": None,
                "routing_rule": "default",
                "estimated_resolution_time": "24小时",
            }

    def _calculate_priority(
        self,
        classification: Dict[str, Any],
        ticket_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """计算优先级"""
        priority = classification.get("priority", "normal")
        
        # 检查是否有VIP客户
        is_vip = ticket_data.get("customer_tier") == "vip"
        
        # 调整优先级
        final_priority = priority
        if is_vip and priority == "normal":
            final_priority = "high"
        
        # 获取优先级配置
        priority_config = self.priority_rules.get(
            final_priority,
            self.priority_rules["normal"]
        )
        
        return {
            "priority": final_priority,
            "is_vip": is_vip,
            "queue": priority_config["queue"],
            "auto_escalate": is_vip or priority == "high",
        }

    def _calculate_sla(self, priority_info: Dict[str, Any]) -> Dict[str, Any]:
        """计算SLA"""
        priority = priority_info.get("priority", "normal")
        config = self.priority_rules.get(priority, self.priority_rules["normal"])
        
        from datetime import datetime, timedelta
        
        now = datetime.now()
        
        return {
            "response_deadline": (now + timedelta(minutes=config["sla_response_minutes"])).isoformat(),
            "resolution_deadline": (now + timedelta(hours=config["sla_resolve_hours"])).isoformat(),
            "response_sla_minutes": config["sla_response_minutes"],
            "resolution_sla_hours": config["sla_resolve_hours"],
        }

    def _determine_workflow(
        self,
        classification: Dict[str, Any],
        routing: Dict[str, Any],
    ) -> List[str]:
        """确定工作流"""
        ticket_type = classification.get("ticket_type", "other")
        
        # 基础工作流
        workflow = ["classify", "route", "solve", "verify", "follow_up"]
        
        # 根据类型调整工作流
        if ticket_type == "complaint":
            workflow.insert(4, "escalate")
        elif ticket_type == "refund_request":
            workflow.insert(3, "verify_payment")
        elif ticket_type == "technical_issue":
            workflow.append("escalate")
        
        return workflow

    def get_statistics(self) -> Dict[str, Any]:
        """获取路由器统计"""
        return {
            "total_routed": 0,
            "by_type": {},
            "by_priority": {},
            "by_department": {},
            "avg_resolution_time_hours": 0,
        }


class MockTicketRouter(TicketRouter):
    """
    Mock工单路由器 - 使用规则简化处理
    """
    
    async def route_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """简化路由"""
        ticket_id = ticket_data.get("ticket_id", "")
        content = ticket_data.get("content", "").lower()
        
        # 简单规则分类
        ticket_type = "other"
        department = "客服组"
        
        if any(kw in content for kw in ["订单", "下单"]):
            ticket_type = "order_issue"
            department = "订单组"
        elif any(kw in content for kw in ["物流", "快递"]):
            ticket_type = "logistics_issue"
            department = "物流组"
        elif any(kw in content for kw in ["退款"]):
            ticket_type = "refund_request"
            department = "退款组"
        elif any(kw in content for kw in ["投诉"]):
            ticket_type = "complaint"
            department = "投诉组"
        
        # 简单优先级
        priority = "normal"
        if any(kw in content for kw in ["紧急", "加急"]):
            priority = "high"
        
        return {
            "ticket_id": ticket_id,
            "status": TicketStatus.OPEN.value,
            "classification": {
                "ticket_type": ticket_type,
                "priority": priority,
                "confidence": 0.9,
                "summary": content[:50],
                "suggested_department": department,
            },
            "routing": {
                "assigned_department": department,
                "assigned_agent": None,
                "routing_rule": "keyword_matching",
            },
            "priority": {
                "priority": priority,
                "is_vip": False,
                "queue": "normal" if priority == "normal" else "urgent",
                "auto_escalate": priority == "high",
            },
            "sla": self._get_mock_sla(priority),
            "workflow": ["classify", "route", "solve", "verify", "follow_up"],
        }
    
    def _get_mock_sla(self, priority: str) -> Dict[str, Any]:
        """Mock SLA计算"""
        from datetime import datetime, timedelta
        
        config = self.priority_rules.get(priority, self.priority_rules["normal"])
        now = datetime.now()
        
        return {
            "response_deadline": (now + timedelta(minutes=config["sla_response_minutes"])).isoformat(),
            "resolution_deadline": (now + timedelta(hours=config["sla_resolve_hours"])).isoformat(),
            "response_sla_minutes": config["sla_response_minutes"],
            "resolution_sla_hours": config["sla_resolve_hours"],
        }
