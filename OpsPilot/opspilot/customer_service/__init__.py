"""
智能客服工单路由模块

提供多Agent协作处理客服工单的能力
"""
from opspilot.customer_service.agents import (
    TicketClassifierAgent,
    TicketRouterAgent,
    TicketSolverAgent,
    TicketReviewerAgent,
)
from opspilot.customer_service.agents.escalate_agent import (
    EscalateAgent,
    MockEscalateAgent,
)
from opspilot.customer_service.agents.followup_agent import (
    FollowUpAgent,
    MockFollowUpAgent,
)
from opspilot.customer_service.ticket_router import (
    TicketRouter,
    MockTicketRouter,
    TicketStatus,
)
from opspilot.customer_service.knowledge_base import (
    KnowledgeBase,
    get_knowledge_base,
)
from opspilot.customer_service.work_queue import (
    TicketQueue,
    get_ticket_queue,
    QueueType,
)
from opspilot.customer_service.lifecycle_manager import (
    LifecycleManager,
    get_lifecycle_manager,
    TicketStatus as LifecycleTicketStatus,
)
from opspilot.customer_service.agent_assignment import (
    AgentAssignment,
    get_agent_assignment,
    AgentSkill,
)
from opspilot.customer_service.ticket_analytics import (
    TicketAnalytics,
    get_ticket_analytics,
)
from opspilot.customer_service.api import customer_service_api

__all__ = [
    # Agents
    "TicketClassifierAgent",
    "TicketRouterAgent",
    "TicketSolverAgent",
    "TicketReviewerAgent",
    "FollowUpAgent",
    "MockFollowUpAgent",
    "EscalateAgent",
    "MockEscalateAgent",
    # Router
    "TicketRouter",
    "MockTicketRouter",
    "TicketStatus",
    # Knowledge Base
    "KnowledgeBase",
    "get_knowledge_base",
    # Work Queue
    "TicketQueue",
    "get_ticket_queue",
    "QueueType",
    # Lifecycle
    "LifecycleManager",
    "get_lifecycle_manager",
    "LifecycleTicketStatus",
    # Agent Assignment
    "AgentAssignment",
    "get_agent_assignment",
    "AgentSkill",
    # Analytics
    "TicketAnalytics",
    "get_ticket_analytics",
    # API
    "customer_service_api",
]