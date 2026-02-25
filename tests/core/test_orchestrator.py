"""
编排器模块单元测试
"""
import pytest

from opspilot.core.orchestrator import Orchestrator
from opspilot.core.state_machine import State
from opspilot.core.context import ContextManager
from opspilot.core.events import EventBus


class TestOrchestrator:
    """编排器测试"""

    @pytest.fixture
    def orchestrator(self):
        # 清理事件总线
        EventBus().clear()
        return Orchestrator()

    @pytest.mark.asyncio
    async def test_process_simple_query(self, orchestrator):
        """测试简单查询处理"""
        result = await orchestrator.process("查询华南地区的供应商")

        assert result["success"] is True
        assert "task_id" in result
        assert result["state"] == "SUCCESS"

    @pytest.mark.asyncio
    async def test_process_create_order(self, orchestrator):
        """测试创建订单处理"""
        result = await orchestrator.process("帮我创建一个采购订单")

        assert result["success"] is True
        assert "result" in result

    @pytest.mark.asyncio
    async def test_task_context_created(self, orchestrator):
        """测试任务上下文创建"""
        result = await orchestrator.process("测试输入")

        task_id = result["task_id"]
        context = orchestrator.get_task_context(task_id)

        assert context is not None
        assert context.user_input == "测试输入"

    @pytest.mark.asyncio
    async def test_task_status(self, orchestrator):
        """测试任务状态查询"""
        result = await orchestrator.process("查询供应商")
        task_id = result["task_id"]

        status = orchestrator.get_task_status(task_id)

        assert status is not None
        assert status["task_id"] == task_id
        assert status["state"] == "SUCCESS"

    @pytest.mark.asyncio
    async def test_task_status_not_found(self, orchestrator):
        """测试查询不存在的任务"""
        status = orchestrator.get_task_status("nonexistent-task")

        assert status is None

    @pytest.mark.asyncio
    async def test_state_transitions(self, orchestrator):
        """测试状态转换"""
        events = []

        def capture_event(event):
            events.append(event)

        EventBus().subscribe_all(capture_event)

        await orchestrator.process("查询供应商")

        # 检查状态变化事件
        state_changes = [e for e in events if hasattr(e, 'from_state')]
        assert len(state_changes) > 0

        # 验证状态转换顺序
        states = [e.to_state for e in state_changes]
        assert "PLANNING" in states
        assert "SUCCESS" in states


class TestOrchestratorIntegration:
    """编排器集成测试"""

    @pytest.fixture
    def orchestrator(self):
        EventBus().clear()
        return Orchestrator()

    @pytest.mark.asyncio
    async def test_full_workflow(self, orchestrator):
        """测试完整工作流"""
        result = await orchestrator.process("查询华南供应商")

        assert result["success"] is True

        # 检查任务上下文
        context = orchestrator.get_task_context(result["task_id"])
        assert context is not None
        assert context.intent is not None
        assert context.plan is not None

    @pytest.mark.asyncio
    async def test_multiple_tasks(self, orchestrator):
        """测试多个任务"""
        result1 = await orchestrator.process("查询供应商")
        result2 = await orchestrator.process("查询库存")

        assert result1["task_id"] != result2["task_id"]

        # 两个任务都应该可以查询
        status1 = orchestrator.get_task_status(result1["task_id"])
        status2 = orchestrator.get_task_status(result2["task_id"])

        assert status1 is not None
        assert status2 is not None

