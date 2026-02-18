"""
工单管理工具 - Mock数据
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
import uuid

from opspilot.tools.base import (
    BaseToolServer,
    ToolSchema,
    ToolResult,
    ToolContext,
)


@dataclass
class Ticket:
    """工单数据模型"""
    ticket_id: str
    customer_id: str
    content: str
    ticket_type: str = "other"
    priority: str = "normal"
    status: str = "pending"  # pending/routing/solving/reviewing/resolved/closed
    assigned_department: str = ""
    classification: Dict[str, Any] = field(default_factory=dict)
    routing: Dict[str, Any] = field(default_factory=dict)
    solution: Dict[str, Any] = field(default_factory=dict)
    review: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticket_id": self.ticket_id,
            "customer_id": self.customer_id,
            "content": self.content,
            "ticket_type": self.ticket_type,
            "priority": self.priority,
            "status": self.status,
            "assigned_department": self.assigned_department,
            "classification": self.classification,
            "routing": self.routing,
            "solution": self.solution,
            "review": self.review,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# Mock工单存储
MOCK_TICKETS: Dict[str, Ticket] = {}


def generate_ticket_id() -> str:
    """生成工单ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"TKT{timestamp}{len(MOCK_TICKETS) + 1:04d}"


class TicketManagerTool(BaseToolServer):
    """
    工单管理工具
    
    提供工单CRUD操作
    """
    
    def __init__(self):
        super().__init__(
            name="ticket-manager",
            description="工单管理工具：创建、查询、更新工单"
        )
        self._register_tools()
    
    def _register_tools(self):
        """注册所有工具"""
        
        # 创建工单
        @self.register_tool(ToolSchema(
            name="create_ticket",
            description="创建新工单",
            input_schema={
                "type": "object",
                "required": ["customer_id", "content"],
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "客户ID"
                    },
                    "content": {
                        "type": "string",
                        "description": "工单内容"
                    },
                    "priority": {
                        "type": "string",
                        "description": "优先级：high/normal/low",
                        "default": "normal"
                    }
                }
            }
        ))
        async def create_ticket_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            customer_id = params.get("customer_id", "")
            content = params.get("content", "")
            priority = params.get("priority", "normal")
            
            ticket_id = generate_ticket_id()
            now = datetime.now().isoformat()
            
            ticket = Ticket(
                ticket_id=ticket_id,
                customer_id=customer_id,
                content=content,
                priority=priority,
                status="pending",
                created_at=now,
                updated_at=now,
            )
            MOCK_TICKETS[ticket_id] = ticket
            
            return ToolResult.success({
                "ticket_id": ticket_id,
                "customer_id": customer_id,
                "status": "pending",
                "created_at": now,
                "message": f"工单 {ticket_id} 创建成功",
            })
        
        # 查询工单
        @self.register_tool(ToolSchema(
            name="get_ticket",
            description="查询工单详情",
            input_schema={
                "type": "object",
                "required": ["ticket_id"],
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "工单ID"
                    }
                }
            }
        ))
        async def get_ticket_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            ticket_id = params.get("ticket_id", "")
            
            if ticket_id in MOCK_TICKETS:
                return ToolResult.success(MOCK_TICKETS[ticket_id].to_dict())
            else:
                return ToolResult.error(
                    error=f"工单不存在: {ticket_id}",
                    error_code="TICKET_NOT_FOUND"
                )
        
        # 列出工单
        @self.register_tool(ToolSchema(
            name="list_tickets",
            description="查询工单列表",
            input_schema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "状态筛选"
                    },
                    "priority": {
                        "type": "string",
                        "description": "优先级筛选"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量限制",
                        "default": 20
                    }
                }
            }
        ))
        async def list_tickets_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            status = params.get("status", "")
            priority = params.get("priority", "")
            limit = params.get("limit", 20)
            
            results = []
            for ticket in MOCK_TICKETS.values():
                if status and ticket.status != status:
                    continue
                if priority and ticket.priority != priority:
                    continue
                results.append(ticket.to_dict())
            
            # 按时间倒序
            results.sort(key=lambda x: x["created_at"], reverse=True)
            results = results[:limit]
            
            return ToolResult.success({
                "tickets": results,
                "total": len(results),
            })
        
        # 更新工单状态
        @self.register_tool(ToolSchema(
            name="update_ticket_status",
            description="更新工单状态",
            input_schema={
                "type": "object",
                "required": ["ticket_id", "status"],
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "工单ID"
                    },
                    "status": {
                        "type": "string",
                        "description": "新状态：pending/routing/solving/reviewing/resolved/closed"
                    }
                }
            }
        ))
        async def update_ticket_status_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            ticket_id = params.get("ticket_id", "")
            status = params.get("status", "")
            
            if ticket_id not in MOCK_TICKETS:
                return ToolResult.error(
                    error=f"工单不存在: {ticket_id}",
                    error_code="TICKET_NOT_FOUND"
                )
            
            ticket = MOCK_TICKETS[ticket_id]
            ticket.status = status
            ticket.updated_at = datetime.now().isoformat()
            
            return ToolResult.success({
                "ticket_id": ticket_id,
                "status": status,
                "updated_at": ticket.updated_at,
            })
        
        # 更新工单分类
        @self.register_tool(ToolSchema(
            name="update_ticket_classification",
            description="更新工单分类信息",
            input_schema={
                "type": "object",
                "required": ["ticket_id", "classification"],
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "工单ID"
                    },
                    "classification": {
                        "type": "object",
                        "description": "分类信息"
                    }
                }
            }
        ))
        async def update_classification_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            ticket_id = params.get("ticket_id", "")
            classification = params.get("classification", {})
            
            if ticket_id not in MOCK_TICKETS:
                return ToolResult.error(
                    error=f"工单不存在: {ticket_id}",
                    error_code="TICKET_NOT_FOUND"
                )
            
            ticket = MOCK_TICKETS[ticket_id]
            ticket.classification = classification
            ticket.ticket_type = classification.get("ticket_type", "other")
            ticket.priority = classification.get("priority", "normal")
            ticket.updated_at = datetime.now().isoformat()
            
            return ToolResult.success({
                "ticket_id": ticket_id,
                "classification": classification,
            })
        
        # 更新工单路由
        @self.register_tool(ToolSchema(
            name="update_ticket_routing",
            description="更新工单路由信息",
            input_schema={
                "type": "object",
                "required": ["ticket_id", "routing"],
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "工单ID"
                    },
                    "routing": {
                        "type": "object",
                        "description": "路由信息"
                    }
                }
            }
        ))
        async def update_routing_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            ticket_id = params.get("ticket_id", "")
            routing = params.get("routing", {})
            
            if ticket_id not in MOCK_TICKETS:
                return ToolResult.error(
                    error=f"工单不存在: {ticket_id}",
                    error_code="TICKET_NOT_FOUND"
                )
            
            ticket = MOCK_TICKETS[ticket_id]
            ticket.routing = routing
            ticket.assigned_department = routing.get("assigned_department", "")
            ticket.updated_at = datetime.now().isoformat()
            
            return ToolResult.success({
                "ticket_id": ticket_id,
                "routing": routing,
            })
        
        # 更新工单解决方案
        @self.register_tool(ToolSchema(
            name="update_ticket_solution",
            description="更新工单解决方案",
            input_schema={
                "type": "object",
                "required": ["ticket_id", "solution"],
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "工单ID"
                    },
                    "solution": {
                        "type": "object",
                        "description": "解决方案"
                    }
                }
            }
        ))
        async def update_solution_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            ticket_id = params.get("ticket_id", "")
            solution = params.get("solution", {})
            
            if ticket_id not in MOCK_TICKETS:
                return ToolResult.error(
                    error=f"工单不存在: {ticket_id}",
                    error_code="TICKET_NOT_FOUND"
                )
            
            ticket = MOCK_TICKETS[ticket_id]
            ticket.solution = solution
            ticket.updated_at = datetime.now().isoformat()
            
            return ToolResult.success({
                "ticket_id": ticket_id,
                "solution": solution,
            })
    
    async def health_check(self) -> bool:
        """健康检查"""
        return True


def create_ticket_manager() -> TicketManagerTool:
    """创建工单管理工具"""
    return TicketManagerTool()
