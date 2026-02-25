"""
客服工单路由系统API
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
import asyncio

from opspilot.customer_service.agents import (
    MockTicketClassifierAgent,
    MockTicketRouterAgent,
    MockTicketSolverAgent,
    MockTicketReviewerAgent,
)
from opspilot.customer_service.agents.escalate_agent import MockEscalateAgent
from opspilot.customer_service.agents.followup_agent import MockFollowUpAgent
from opspilot.customer_service.ticket_router import MockTicketRouter
from opspilot.customer_service.knowledge_base import get_knowledge_base
from opspilot.customer_service.work_queue import get_ticket_queue
from opspilot.customer_service.lifecycle_manager import get_lifecycle_manager
from opspilot.customer_service.agent_assignment import get_agent_assignment
from opspilot.customer_service.ticket_analytics import get_ticket_analytics
from opspilot.customer_service.tools.ticket_manager import (
    TicketManagerTool,
    MOCK_TICKETS,
)


# ==================== 数据模型 ====================

class TicketCreateRequest(BaseModel):
    """创建工单请求"""
    customer_id: str = Field(..., description="客户ID")
    content: str = Field(..., description="工单内容")
    priority: Optional[str] = Field("normal", description="优先级")


class TicketCreateResponse(BaseModel):
    """创建工单响应"""
    success: bool
    ticket_id: str
    message: str


class TicketProcessRequest(BaseModel):
    """处理工单请求"""
    ticket_id: str = Field(..., description="工单ID")


class TicketProcessResponse(BaseModel):
    """处理工单响应"""
    success: bool
    ticket_id: str
    status: str
    classification: Dict[str, Any]
    routing: Dict[str, Any]
    solution: Dict[str, Any]
    review: Dict[str, Any]
    processing_time_ms: float
    message: str


class TicketListResponse(BaseModel):
    """工单列表响应"""
    success: bool
    tickets: List[Dict[str, Any]]
    total: int


class AgentStatusResponse(BaseModel):
    """Agent状态响应"""
    agents: Dict[str, Dict[str, Any]]


# ==================== 队列状态模型 ====================

class QueueStatusResponse(BaseModel):
    """队列状态响应"""
    queues: List[Dict[str, Any]]
    total_tickets: int
    sla_violations: int


# ==================== 知识库查询模型 ====================

class KnowledgeQueryRequest(BaseModel):
    """知识库查询请求"""
    query: str = Field(..., description="查询内容")
    category: Optional[str] = Field(None, description="分类筛选")
    limit: Optional[int] = Field(5, description="返回数量")


class KnowledgeQueryResponse(BaseModel):
    """知识库查询响应"""
    success: bool
    query: str
    results: List[Dict[str, Any]]
    total_found: int


# ==================== 统计分析模型 ====================

class TicketAnalyticsResponse(BaseModel):
    """工单统计分析响应"""
    statistics: Dict[str, Any]
    trends: List[Dict[str, Any]]
    agent_performance: List[Dict[str, Any]]
    top_categories: List[Dict[str, Any]]
    sla_report: Dict[str, Any]


# ==================== 智能分配模型 ====================

class AgentListResponse(BaseModel):
    """Agent列表响应"""
    success: bool
    agents: List[Dict[str, Any]]


class AssignmentRequest(BaseModel):
    """分配工单请求"""
    ticket_id: str = Field(..., description="工单ID")
    agent_id: Optional[str] = Field(None, description="指定Agent ID")


class AssignmentResponse(BaseModel):
    """分配工单响应"""
    ticket_id: str
    assigned_agent: str
    assignment_reason: str
    estimated_time: int


# ==================== 升级模型 ====================

class EscalationRequest(BaseModel):
    """升级工单请求"""
    ticket_id: str = Field(..., description="工单ID")
    reason: str = Field(..., description="升级原因")
    escalate_to_expert: Optional[bool] = Field(False, description="是否升级给专家")


class EscalationResponse(BaseModel):
    """升级工单响应"""
    success: bool
    escalation: Dict[str, Any]
    message: str


# ==================== 跟进模型 ====================

class FollowUpRequest(BaseModel):
    """跟进工单请求"""
    ticket_id: str = Field(..., description="工单ID")
    follow_up_type: str = Field(..., description="跟进类型")


class FollowUpResponse(BaseModel):
    """跟进工单响应"""
    success: bool
    follow_up: Dict[str, Any]
    message: str


# ==================== 生命周期模型 ====================

class TicketLifecycleResponse(BaseModel):
    """工单生命周期响应"""
    ticket_id: str
    current_status: str
    status_history: List[Dict[str, Any]]
    response_deadline: Optional[str]
    resolution_deadline: Optional[str]
    is_sla_breached: bool
    time_in_current_status: int


# ==================== API服务 ====================

class CustomerServiceAPI:
    """客服工单API服务"""
    
    def __init__(self):
        self.classifier = MockTicketClassifierAgent()
        self.router = MockTicketRouterAgent()
        self.solver = MockTicketSolverAgent()
        self.reviewer = MockTicketReviewerAgent()
        self.escalate_agent = MockEscalateAgent()
        self.followup_agent = MockFollowUpAgent()
        self.ticket_manager = TicketManagerTool()
        self.ticket_router = MockTicketRouter()
    
    async def create_ticket(self, request: TicketCreateRequest) -> TicketCreateResponse:
        """创建工单"""
        from opspilot.tools.base import ToolContext
        
        context = ToolContext()
        result = await self.ticket_manager._call_tool(
            "create_ticket",
            {
                "customer_id": request.customer_id,
                "content": request.content,
                "priority": request.priority,
            },
            context
        )
        
        return TicketCreateResponse(
            success=result.success,
            ticket_id=result.data.get("ticket_id", "") if result.success else "",
            message=result.message,
        )
    
    async def process_ticket(self, request: TicketProcessRequest) -> TicketProcessResponse:
        """处理工单（完整流程）"""
        start_time = datetime.now()
        
        # 获取工单
        ticket = MOCK_TICKETS.get(request.ticket_id)
        if not ticket:
            return TicketProcessResponse(
                success=False,
                ticket_id=request.ticket_id,
                status="not_found",
                classification={},
                routing={},
                solution={},
                review={},
                processing_time_ms=0,
                message="工单不存在",
            )
        
        # 创建Agent上下文
        from opspilot.agents.base import AgentContext
        from opspilot.core.state_machine import State
        
        context = AgentContext(
            task_id=request.ticket_id,
            state=State.INTENT,
            user_input=ticket.content,
            metadata={"ticket_id": request.ticket_id},
        )
        
        # Step 1: 分类
        classify_result = await self.classifier.execute(context)
        classification = classify_result.result or {}
        context.metadata["classification"] = classification
        
        # Step 2: 路由
        routing_result = await self.router.execute(context)
        routing = routing_result.result or {}
        context.metadata["routing"] = routing
        
        # Step 3: 解决
        solve_result = await self.solver.execute(context)
        solution = solve_result.result or {}
        context.metadata["solution"] = solution
        
        # Step 4: 审核
        review_result = await self.reviewer.execute(context)
        review = review_result.result or {}
        
        # 更新工单
        ticket.classification = classification
        ticket.routing = routing
        ticket.solution = solution
        ticket.review = review
        ticket.status = "resolved" if review.get("passed", False) else "reviewing"
        ticket.updated_at = datetime.now().isoformat()
        
        # 计算处理时间
        processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return TicketProcessResponse(
            success=True,
            ticket_id=request.ticket_id,
            status=ticket.status,
            classification=classification,
            routing=routing,
            solution=solution,
            review=review,
            processing_time_ms=processing_time_ms,
            message="工单处理完成",
        )
    
    async def get_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """获取工单详情"""
        ticket = MOCK_TICKETS.get(ticket_id)
        if ticket:
            return {"success": True, "ticket": ticket.to_dict()}
        return {"success": False, "error": "工单不存在"}
    
    async def list_tickets(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 20
    ) -> TicketListResponse:
        """查询工单列表"""
        from opspilot.tools.base import ToolContext
        
        context = ToolContext()
        result = await self.ticket_manager._call_tool(
            "list_tickets",
            {"status": status, "priority": priority, "limit": limit},
            context
        )
        
        return TicketListResponse(
            success=result.success,
            tickets=result.data.get("tickets", []) if result.success else [],
            total=result.data.get("total", 0) if result.success else 0,
        )
    
    async def get_agent_status(self) -> AgentStatusResponse:
        """获取Agent状态"""
        return AgentStatusResponse(
            agents={
                "classifier": {
                    "status": "ready",
                    "description": "工单分类Agent",
                    "tickets_processed": len([t for t in MOCK_TICKETS.values() if t.classification]),
                },
                "router": {
                    "status": "ready",
                    "description": "工单路由Agent",
                    "tickets_routed": len([t for t in MOCK_TICKETS.values() if t.routing]),
                },
                "solver": {
                    "status": "ready",
                    "description": "工单解决Agent",
                    "tickets_solved": len([t for t in MOCK_TICKETS.values() if t.solution]),
                },
                "reviewer": {
                    "status": "ready",
                    "description": "工单审核Agent",
                    "tickets_reviewed": len([t for t in MOCK_TICKETS.values() if t.review]),
                },
            }
        )
    
    async def get_queue_status(self) -> QueueStatusResponse:
        """获取队列状态"""
        queue = get_ticket_queue()
        queue_info = queue.get_queue_info()
        
        # 统计SLA违规
        sla_violations = queue.get_sla_violations()
        
        return QueueStatusResponse(
            queues=queue_info,
            total_tickets=sum(q["ticket_count"] for q in queue_info),
            sla_violations=sla_violations,
        )
    
    async def get_ticket_lifecycle(self, ticket_id: str) -> TicketLifecycleResponse:
        """获取工单生命周期"""
        lifecycle_manager = get_lifecycle_manager()
        lifecycle = lifecycle_manager.get_ticket_lifecycle(ticket_id)
        
        if lifecycle:
            return TicketLifecycleResponse(
                ticket_id=lifecycle.ticket_id,
                current_status=lifecycle.current_status.value if hasattr(lifecycle.current_status, 'value') else str(lifecycle.current_status),
                status_history=[
                    {"status": h.status.value if hasattr(h.status, 'value') else str(h.status), "timestamp": h.timestamp, "note": h.note}
                    for h in lifecycle.status_history
                ],
                response_deadline=lifecycle.response_deadline.isoformat() if lifecycle.response_deadline else None,
                resolution_deadline=lifecycle.resolution_deadline.isoformat() if lifecycle.resolution_deadline else None,
                is_sla_breached=lifecycle.is_sla_breached,
                time_in_current_status=lifecycle.time_in_current_status,
            )
        
        # 如果没有生命周期信息，返回基本信息
        ticket = MOCK_TICKETS.get(ticket_id)
        if ticket:
            return TicketLifecycleResponse(
                ticket_id=ticket_id,
                current_status=ticket.status,
                status_history=[],
                response_deadline=None,
                resolution_deadline=None,
                is_sla_breached=False,
                time_in_current_status=0,
            )
        
        return TicketLifecycleResponse(
            ticket_id=ticket_id,
            current_status="unknown",
            status_history=[],
            response_deadline=None,
            resolution_deadline=None,
            is_sla_breached=False,
            time_in_current_status=0,
        )
    
    async def query_knowledge(self, request: KnowledgeQueryRequest) -> KnowledgeQueryResponse:
        """查询知识库"""
        knowledge_base = get_knowledge_base()
        results = knowledge_base.search(request.query, request.category, request.limit)
        
        return KnowledgeQueryResponse(
            success=True,
            query=request.query,
            results=[
                {
                    "id": r["id"],
                    "title": r["title"],
                    "content": r["content"],
                    "category": r["category"],
                    "tags": r["tags"],
                    "relevance_score": r["relevance_score"],
                }
                for r in results
            ],
            total_found=len(results),
        )
    
    async def get_analytics(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> TicketAnalyticsResponse:
        """获取工单统计分析"""
        analytics = get_ticket_analytics()
        stats = analytics.get_statistics()
        trends = analytics.get_trends()
        agent_perf = analytics.get_agent_performance()
        top_cats = analytics.get_top_categories()
        sla = analytics.get_sla_report()
        
        return TicketAnalyticsResponse(
            statistics=stats,
            trends=trends,
            agent_performance=agent_perf,
            top_categories=top_cats,
            sla_report=sla,
        )
    
    async def get_agents(self) -> AgentListResponse:
        """获取Agent列表"""
        assignment = get_agent_assignment()
        agents = assignment.get_available_agents()
        
        return AgentListResponse(
            success=True,
            agents=[
                {
                    "agent_id": a["agent_id"],
                    "agent_name": a["agent_name"],
                    "skills": a["skills"],
                    "current_load": a["current_load"],
                    "max_load": a["max_load"],
                    "status": a["status"],
                }
                for a in agents
            ],
        )
    
    async def assign_ticket(self, request: AssignmentRequest) -> AssignmentResponse:
        """分配工单"""
        assignment = get_agent_assignment()
        result = assignment.assign_ticket(request.ticket_id, request.agent_id)
        
        return AssignmentResponse(
            ticket_id=request.ticket_id,
            assigned_agent=result["agent_id"],
            assignment_reason=result["reason"],
            estimated_time=result["estimated_time"],
        )
    
    async def escalate_ticket(self, request: EscalationRequest) -> EscalationResponse:
        """升级工单"""
        ticket = MOCK_TICKETS.get(request.ticket_id)
        if not ticket:
            return EscalationResponse(
                success=False,
                escalation={},
                message="工单不存在",
            )
        
        from opspilot.agents.base import AgentContext
        from opspilot.core.state_machine import State
        
        context = AgentContext(
            task_id=request.ticket_id,
            state=State.EXECUTING,
            user_input=ticket.content,
            metadata={"ticket_id": request.ticket_id, "reason": request.reason},
        )
        
        result = await self.escalate_agent.execute(context)
        escalation_data = result.result or {}
        
        # 更新工单状态
        ticket.status = "escalated"
        ticket.priority = "high"
        
        return EscalationResponse(
            success=True,
            escalation={
                "ticket_id": request.ticket_id,
                "escalated_at": datetime.now().isoformat(),
                "escalation_reason": request.reason,
                "original_agent": escalation_data.get("original_agent", ""),
                "expert_agent": escalation_data.get("expert_agent", ""),
                "priority_boost": escalation_data.get("priority_boost", 0),
            },
            message="工单已升级",
        )
    
    async def create_followup(self, request: FollowUpRequest) -> FollowUpResponse:
        """创建跟进"""
        ticket = MOCK_TICKETS.get(request.ticket_id)
        if not ticket:
            return FollowUpResponse(
                success=False,
                follow_up={},
                message="工单不存在",
            )
        
        from opspilot.agents.base import AgentContext
        from opspilot.core.state_machine import State
        
        context = AgentContext(
            task_id=request.ticket_id,
            state=State.EXECUTING,
            user_input=ticket.content,
            metadata={"ticket_id": request.ticket_id, "follow_up_type": request.follow_up_type},
        )
        
        result = await self.followup_agent.execute(context)
        follow_up_data = result.result or {}
        
        return FollowUpResponse(
            success=True,
            follow_up={
                "ticket_id": request.ticket_id,
                "customer_id": ticket.customer_id,
                "follow_up_type": request.follow_up_type,
                "sent_at": datetime.now().isoformat(),
                "response": follow_up_data.get("response", ""),
                "satisfaction_score": follow_up_data.get("satisfaction_score"),
            },
            message="跟进已创建",
        )


# 全局API实例
customer_service_api = CustomerServiceAPI()