"""
持久化存储测试

测试任务、审批、Token追踪的数据库持久化功能
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import json

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestTaskPersistence:
    """任务持久化测试"""
    
    @pytest.fixture
    def mock_pool(self):
        """模拟数据库连接池"""
        pool = AsyncMock()
        return pool
    
    @pytest.mark.asyncio
    async def test_create_task(self, mock_pool):
        """测试创建任务记录"""
        from opspilot.db.persistence import TaskPersistence
        
        mock_pool.fetchrow = AsyncMock(return_value={"task_id": "task-001"})
        
        with patch('opspilot.db.persistence.get_database_pool', return_value=mock_pool):
            task_id = await TaskPersistence.create_task({
                "task_id": "task-001",
                "name": "测试任务",
                "task_type": "one_time",
                "priority": "high",
            })
        
        assert task_id == "task-001"
        mock_pool.fetchrow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_task_status(self, mock_pool):
        """测试更新任务状态"""
        from opspilot.db.persistence import TaskPersistence
        
        mock_pool.execute = AsyncMock(return_value="UPDATE 1")
        
        with patch('opspilot.db.persistence.get_database_pool', return_value=mock_pool):
            result = await TaskPersistence.update_task_status(
                task_id="task-001",
                status="completed",
                execution_time_ms=1500,
            )
        
        assert result is True
        mock_pool.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_task(self, mock_pool):
        """测试获取任务"""
        from opspilot.db.persistence import TaskPersistence
        
        mock_record = {
            "task_id": "task-001",
            "name": "测试任务",
            "status": "completed",
        }
        mock_pool.fetchrow = AsyncMock(return_value=mock_record)
        
        with patch('opspilot.db.persistence.get_database_pool', return_value=mock_pool):
            task = await TaskPersistence.get_task("task-001")
        
        assert task is not None
        assert task["task_id"] == "task-001"
        assert task["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_get_task_not_found(self, mock_pool):
        """测试获取不存在的任务"""
        from opspilot.db.persistence import TaskPersistence
        
        mock_pool.fetchrow = AsyncMock(return_value=None)
        
        with patch('opspilot.db.persistence.get_database_pool', return_value=mock_pool):
            task = await TaskPersistence.get_task("nonexistent")
        
        assert task is None
    
    @pytest.mark.asyncio
    async def test_get_tasks_by_status(self, mock_pool):
        """测试按状态获取任务列表"""
        from opspilot.db.persistence import TaskPersistence
        
        mock_records = [
            {"task_id": "task-001", "status": "pending"},
            {"task_id": "task-002", "status": "pending"},
        ]
        mock_pool.fetch = AsyncMock(return_value=mock_records)
        
        with patch('opspilot.db.persistence.get_database_pool', return_value=mock_pool):
            tasks = await TaskPersistence.get_tasks_by_status("pending")
        
        assert len(tasks) == 2


class TestApprovalPersistence:
    """审批持久化测试"""
    
    @pytest.fixture
    def mock_pool(self):
        """模拟数据库连接池"""
        pool = AsyncMock()
        return pool
    
    @pytest.mark.asyncio
    async def test_create_request(self, mock_pool):
        """测试创建审批请求"""
        from opspilot.db.persistence import ApprovalPersistence
        
        mock_pool.fetchrow = AsyncMock(return_value={"request_id": "approval-001"})
        
        with patch('opspilot.db.persistence.get_database_pool', return_value=mock_pool):
            request_id = await ApprovalPersistence.create_request({
                "request_id": "approval-001",
                "approval_type": "amount_exceeded",
                "user_id": "user-001",
                "title": "超额订单审批",
            })
        
        assert request_id == "approval-001"
    
    @pytest.mark.asyncio
    async def test_update_request_status(self, mock_pool):
        """测试更新审批状态"""
        from opspilot.db.persistence import ApprovalPersistence
        
        mock_pool.execute = AsyncMock(return_value="UPDATE 1")
        
        with patch('opspilot.db.persistence.get_database_pool', return_value=mock_pool):
            result = await ApprovalPersistence.update_request_status(
                request_id="approval-001",
                status="approved",
                approved_by="finance-001",
                approval_comment="同意",
            )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_add_approval_history(self, mock_pool):
        """测试添加审批历史"""
        from opspilot.db.persistence import ApprovalPersistence
        
        mock_pool.execute = AsyncMock(return_value="INSERT 0 1")
        
        with patch('opspilot.db.persistence.get_database_pool', return_value=mock_pool):
            result = await ApprovalPersistence.add_approval_history(
                request_id="approval-001",
                approver_id="finance-001",
                action="approved",
                comment="同意审批",
            )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_pending_requests(self, mock_pool):
        """测试获取待审批列表"""
        from opspilot.db.persistence import ApprovalPersistence
        
        mock_records = [
            {"request_id": "approval-001", "status": "pending"},
            {"request_id": "approval-002", "status": "pending"},
        ]
        mock_pool.fetch = AsyncMock(return_value=mock_records)
        
        with patch('opspilot.db.persistence.get_database_pool', return_value=mock_pool):
            requests = await ApprovalPersistence.get_pending_requests()
        
        assert len(requests) == 2
    
    @pytest.mark.asyncio
    async def test_get_user_requests(self, mock_pool):
        """测试获取用户发起的审批"""
        from opspilot.db.persistence import ApprovalPersistence
        
        mock_records = [
            {"request_id": "approval-001", "user_id": "user-001"},
        ]
        mock_pool.fetch = AsyncMock(return_value=mock_records)
        
        with patch('opspilot.db.persistence.get_database_pool', return_value=mock_pool):
            requests = await ApprovalPersistence.get_user_requests("user-001")
        
        assert len(requests) == 1


class TestTokenPersistence:
    """Token 持久化测试"""
    
    @pytest.fixture
    def mock_pool(self):
        """模拟数据库连接池"""
        pool = AsyncMock()
        return pool
    
    @pytest.mark.asyncio
    async def test_record_usage(self, mock_pool):
        """测试记录 Token 使用"""
        from opspilot.db.persistence import TokenPersistence
        
        mock_pool.fetchrow = AsyncMock(return_value={"id": 1})
        
        with patch('opspilot.db.persistence.get_database_pool', return_value=mock_pool):
            record_id = await TokenPersistence.record_usage({
                "model": "gpt-4o",
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "agent_id": "agent-001",
            })
        
        assert record_id == 1
    
    def test_estimate_cost(self):
        """测试成本估算"""
        from opspilot.db.persistence import TokenPersistence
        from decimal import Decimal
        
        # GPT-4o 成本估算
        cost = TokenPersistence._estimate_cost("gpt-4o", 1000, 500)
        
        # 预期: 0.005 * 1 + 0.015 * 0.5 = 0.005 + 0.0075 = 0.0125
        expected = Decimal("0.0125")
        assert abs(cost - expected) < Decimal("0.0001")
    
    def test_estimate_cost_unknown_model(self):
        """测试未知模型的成本估算"""
        from opspilot.db.persistence import TokenPersistence
        from decimal import Decimal
        
        cost = TokenPersistence._estimate_cost("unknown-model", 1000, 1000)
        
        # 应该使用默认值
        assert cost > 0
    
    @pytest.mark.asyncio
    async def test_get_usage_statistics(self, mock_pool):
        """测试获取使用统计"""
        from opspilot.db.persistence import TokenPersistence
        
        mock_records = [
            {
                "model": "gpt-4o",
                "total_requests": 100,
                "total_tokens": 50000,
                "total_cost": 10.5,
            },
        ]
        mock_pool.fetch = AsyncMock(return_value=mock_records)
        
        with patch('opspilot.db.persistence.get_database_pool', return_value=mock_pool):
            stats = await TokenPersistence.get_usage_statistics(group_by="model")
        
        assert len(stats) == 1
        assert stats[0]["model"] == "gpt-4o"
    
    @pytest.mark.asyncio
    async def test_get_recent_usage(self, mock_pool):
        """测试获取最近使用记录"""
        from opspilot.db.persistence import TokenPersistence
        
        mock_records = [
            {"id": 1, "model": "gpt-4o"},
            {"id": 2, "model": "gpt-4o"},
        ]
        mock_pool.fetch = AsyncMock(return_value=mock_records)
        
        with patch('opspilot.db.persistence.get_database_pool', return_value=mock_pool):
            records = await TokenPersistence.get_recent_usage(limit=10)
        
        assert len(records) == 2


class TestTicketPersistence:
    """工单持久化测试"""
    
    @pytest.fixture
    def mock_pool(self):
        """模拟数据库连接池"""
        pool = AsyncMock()
        return pool
    
    @pytest.mark.asyncio
    async def test_create_ticket(self, mock_pool):
        """测试创建工单"""
        from opspilot.db.persistence import TicketPersistence
        
        mock_pool.fetchrow = AsyncMock(return_value={"ticket_id": "TKT-001"})
        
        with patch('opspilot.db.persistence.get_database_pool', return_value=mock_pool):
            ticket_id = await TicketPersistence.create_ticket({
                "ticket_id": "TKT-001",
                "subject": "订单问题",
                "customer_id": "customer-001",
            })
        
        assert ticket_id == "TKT-001"
    
    @pytest.mark.asyncio
    async def test_update_ticket(self, mock_pool):
        """测试更新工单"""
        from opspilot.db.persistence import TicketPersistence
        
        mock_pool.execute = AsyncMock(return_value="UPDATE 1")
        
        with patch('opspilot.db.persistence.get_database_pool', return_value=mock_pool):
            result = await TicketPersistence.update_ticket(
                ticket_id="TKT-001",
                update_data={
                    "status": "resolved",
                    "solution": "已解决",
                }
            )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_ticket(self, mock_pool):
        """测试获取工单"""
        from opspilot.db.persistence import TicketPersistence
        
        mock_record = {
            "ticket_id": "TKT-001",
            "subject": "订单问题",
            "status": "open",
        }
        mock_pool.fetchrow = AsyncMock(return_value=mock_record)
        
        with patch('opspilot.db.persistence.get_database_pool', return_value=mock_pool):
            ticket = await TicketPersistence.get_ticket("TKT-001")
        
        assert ticket is not None
        assert ticket["ticket_id"] == "TKT-001"


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_task_lifecycle(self):
        """测试完整的任务生命周期"""
        from opspilot.db.persistence import TaskPersistence
        
        mock_pool = AsyncMock()
        
        # 创建任务
        mock_pool.fetchrow = AsyncMock(return_value={"task_id": "task-001"})
        
        with patch('opspilot.db.persistence.get_database_pool', return_value=mock_pool):
            task_id = await TaskPersistence.create_task({
                "task_id": "task-001",
                "name": "测试任务",
            })
        
        assert task_id == "task-001"
        
        # 更新状态为运行中
        mock_pool.execute = AsyncMock(return_value="UPDATE 1")
        
        with patch('opspilot.db.persistence.get_database_pool', return_value=mock_pool):
            result = await TaskPersistence.update_task_status(
                task_id="task-001",
                status="running",
                started_at=datetime.now(),
            )
        
        assert result is True
        
        # 更新状态为完成
        with patch('opspilot.db.persistence.get_database_pool', return_value=mock_pool):
            result = await TaskPersistence.update_task_status(
                task_id="task-001",
                status="completed",
                completed_at=datetime.now(),
                execution_time_ms=1500,
            )
        
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
