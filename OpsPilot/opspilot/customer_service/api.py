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


# ==================== API服务 ====================

class CustomerServiceAPI:
    """客服工单API服务"""
    
    def __init__(self):
        self.classifier = MockTicketClassifierAgent()
        self.router = MockTicketRouterAgent()
        self.solver = MockTicketSolverAgent()
        self.reviewer = MockTicketReviewerAgent()
        self.ticket_manager = TicketManagerTool()
    
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


# 全局API实例
customer_service_api = CustomerServiceAPI()
