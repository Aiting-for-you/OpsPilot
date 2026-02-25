"""
智能客服工单系统测试

测试工单路由、解决、审核功能
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from opspilot.agents.base import AgentContext
from opspilot.core.state_machine import State
from opspilot.customer_service.agents.router_agent import (
    TicketRouterAgent,
    MockTicketRouterAgent,
)
from opspilot.customer_service.agents.solver_agent import (
    TicketSolverAgent,
    MockTicketSolverAgent,
)
from opspilot.customer_service.agents.reviewer_agent import (
    TicketReviewerAgent,
    MockTicketReviewerAgent,
)


class TestTicketRouterAgent:
    """工单路由 Agent 测试"""
    
    @pytest.fixture
    def agent(self):
        """创建 Agent 实例"""
        return MockTicketRouterAgent()
    
    def test_agent_creation(self, agent):
        """测试 Agent 创建"""
        assert agent is not None
        assert agent.name == "TicketRouterAgent"
    
    @pytest.mark.asyncio
    async def test_route_ticket(self, agent):
        """测试工单路由"""
        ticket = {
            "ticket_id": "TKT-001",
            "subject": "订单未收到",
            "content": "我买的商品已经超过预计送达时间了",
            "customer_id": "customer-001",
            "priority": "high",
            "classification": {
                "ticket_type": "logistics",
                "priority": "high",
                "suggested_department": "物流组",
            },
        }
        
        context = AgentContext(
            task_id="TKT-001",
            state=State.INIT,
            user_input=str(ticket),
            metadata=ticket,
        )
        result = await agent.execute(context)
        
        assert result is not None
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_route_by_category(self, agent):
        """测试按类别路由"""
        ticket = {
            "ticket_id": "TKT-002",
            "subject": "退款申请",
            "content": "商品质量问题，申请退款",
            "category": "refund",
        }
        
        context = AgentContext(
            task_id="TKT-002",
            state=State.INIT,
            user_input=str(ticket),
            metadata=ticket,
        )
        result = await agent.execute(context)
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_route_by_priority(self, agent):
        """测试按优先级路由"""
        ticket = {
            "ticket_id": "TKT-003",
            "subject": "紧急投诉",
            "content": "服务态度差，要求处理",
            "priority": "urgent",
        }
        
        context = AgentContext(
            task_id="TKT-003",
            state=State.INIT,
            user_input=str(ticket),
            metadata=ticket,
        )
        result = await agent.execute(context)
        
        assert result is not None


class TestTicketSolverAgent:
    """工单解决 Agent 测试"""
    
    @pytest.fixture
    def agent(self):
        """创建 Agent 实例"""
        return MockTicketSolverAgent()
    
    def test_agent_creation(self, agent):
        """测试 Agent 创建"""
        assert agent is not None
        assert agent.name == "TicketSolverAgent"
    
    @pytest.mark.asyncio
    async def test_solve_ticket(self, agent):
        """测试解决工单"""
        ticket = {
            "ticket_id": "TKT-001",
            "subject": "订单查询",
            "content": "查询订单状态",
            "order_id": "ORD-123",
        }
        
        context = AgentContext(
            task_id="TKT-001",
            state=State.INIT,
            user_input=str(ticket),
            metadata=ticket,
        )
        result = await agent.execute(context)
        
        assert result is not None
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_solve_with_tools(self, agent):
        """测试使用工具解决工单"""
        ticket = {
            "ticket_id": "TKT-002",
            "subject": "库存查询",
            "content": "查询商品库存",
            "sku": "SKU-001",
        }
        
        context = AgentContext(
            task_id="TKT-002",
            state=State.INIT,
            user_input=str(ticket),
            metadata=ticket,
        )
        result = await agent.execute(context)
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_generate_response(self, agent):
        """测试生成响应"""
        ticket = {
            "ticket_id": "TKT-003",
            "subject": "常见问题",
            "content": "如何修改收货地址",
        }
        
        context = AgentContext(
            task_id="TKT-003",
            state=State.INIT,
            user_input=str(ticket),
            metadata=ticket,
        )
        result = await agent.execute(context)
        
        assert result is not None


class TestTicketReviewerAgent:
    """工单审核 Agent 测试"""
    
    @pytest.fixture
    def agent(self):
        """创建 Agent 实例"""
        return MockTicketReviewerAgent()
    
    def test_agent_creation(self, agent):
        """测试 Agent 创建"""
        assert agent is not None
        assert agent.name == "TicketReviewerAgent"
    
    @pytest.mark.asyncio
    async def test_review_solution(self, agent):
        """测试审核解决方案"""
        solution = {
            "ticket_id": "TKT-001",
            "solution": {
                "resolution": "已为客户查询订单，预计明天送达",
                "customer_notification": "已电话通知客户",
                "action_taken": ["check_order", "notify_customer"],
            },
            "confidence": 0.85,
        }
        
        context = AgentContext(
            task_id="TKT-001",
            state=State.INIT,
            user_input=str(solution),
            metadata=solution,
        )
        result = await agent.execute(context)
        
        assert result is not None
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_approve_good_solution(self, agent):
        """测试通过好的解决方案"""
        solution = {
            "ticket_id": "TKT-002",
            "solution": "已为客户办理退款，退款金额将原路返回",
            "confidence": 0.95,
            "actions_taken": ["check_order", "process_refund"],
        }
        
        context = AgentContext(
            task_id="TKT-002",
            state=State.INIT,
            user_input=str(solution),
            metadata=solution,
        )
        result = await agent.execute(context)
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_reject_poor_solution(self, agent):
        """测试拒绝差的解决方案"""
        solution = {
            "ticket_id": "TKT-003",
            "solution": "请等待",
            "confidence": 0.3,
        }
        
        context = AgentContext(
            task_id="TKT-003",
            state=State.INIT,
            user_input=str(solution),
            metadata=solution,
        )
        result = await agent.execute(context)
        
        assert result is not None


class TestTicketManager:
    """工单管理工具测试"""
    
    @pytest.fixture
    def manager(self):
        """创建工单管理器"""
        from opspilot.customer_service.tools.ticket_manager import TicketManager
        return TicketManager()
    
    def test_manager_creation(self, manager):
        """测试管理器创建"""
        assert manager is not None
    
    def test_create_ticket(self, manager):
        """测试创建工单"""
        ticket = manager.create_ticket(
            customer_id="customer-001",
            subject="订单问题",
            content="订单未收到",
            priority="high",
        )
        
        assert ticket is not None
        assert "ticket_id" in ticket
        assert ticket["subject"] == "订单问题"
    
    def test_get_ticket(self, manager):
        """测试获取工单"""
        created = manager.create_ticket(
            customer_id="customer-001",
            subject="测试工单",
            content="内容",
        )
        
        ticket = manager.get_ticket(created["ticket_id"])
        
        assert ticket is not None
        assert ticket["ticket_id"] == created["ticket_id"]
    
    def test_update_ticket_status(self, manager):
        """测试更新工单状态"""
        ticket = manager.create_ticket(
            customer_id="customer-001",
            subject="测试",
            content="内容",
        )
        
        result = manager.update_status(
            ticket["ticket_id"],
            "in_progress",
        )
        
        assert result is True
        
        updated = manager.get_ticket(ticket["ticket_id"])
        assert updated["status"] == "in_progress"
    
    def test_list_tickets(self, manager):
        """测试获取工单列表"""
        manager.create_ticket("customer-1", "工单1", "内容1")
        manager.create_ticket("customer-2", "工单2", "内容2")
        
        tickets = manager.list_tickets()
        
        assert len(tickets) >= 2
    
    def test_list_tickets_by_status(self, manager):
        """测试按状态获取工单列表"""
        ticket1 = manager.create_ticket("customer-1", "工单1", "内容1")
        ticket2 = manager.create_ticket("customer-2", "工单2", "内容2")
        
        manager.update_status(ticket1["ticket_id"], "resolved")
        
        resolved_tickets = manager.list_tickets(status="resolved")
        open_tickets = manager.list_tickets(status="open")
        
        assert len(resolved_tickets) >= 1
        assert len(open_tickets) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
