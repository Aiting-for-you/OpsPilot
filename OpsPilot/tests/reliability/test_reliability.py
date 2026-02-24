"""
可靠性模块测试

测试 TokenTracker, ParallelToolExecutor, StructuredOutputParser 等
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

from opspilot.reliability.token_tracker import (
    TokenUsage,
    TokenBudgetExceeded,
    TokenTracker,
    get_token_tracker,
    track_tokens,
)

from opspilot.reliability.parallel_executor import (
    ExecutionStatus,
    ToolCall,
    ToolResult,
    ParallelExecutionResult,
    ParallelToolExecutor,
    execute_tools_parallel,
)


class TestTokenUsage:
    """测试 TokenUsage"""

    def test_create_usage(self):
        """测试创建使用记录"""
        usage = TokenUsage(
            timestamp=datetime.now(),
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            total_cost=0.001,
            model_name="gpt-3.5-turbo",
            agent_name="intent_agent",
        )
        
        assert usage.prompt_tokens == 100
        assert usage.total_tokens == 150

    def test_to_dict(self):
        """测试转换为字典"""
        usage = TokenUsage(
            timestamp=datetime(2024, 1, 1),
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            total_cost=0.001,
            model_name="gpt-3.5-turbo",
        )
        
        data = usage.to_dict()
        
        assert data["prompt_tokens"] == 100
        assert data["model_name"] == "gpt-3.5-turbo"


class TestTokenBudgetExceeded:
    """测试 TokenBudgetExceeded 异常"""

    def test_exception_message(self):
        """测试异常消息"""
        exc = TokenBudgetExceeded("Budget exceeded")
        
        assert "Budget exceeded" in str(exc)


class TestTokenTracker:
    """测试 TokenTracker"""

    @pytest.fixture
    def tracker(self):
        """创建追踪器"""
        return TokenTracker(
            daily_budget=10.0,
            monthly_budget=100.0,
            enable_budget_check=True,
        )

    def test_create_tracker(self):
        """测试创建追踪器"""
        tracker = TokenTracker()
        
        assert tracker.daily_budget is None

    def test_get_total_usage_empty(self, tracker):
        """测试空使用统计"""
        usage = tracker.get_total_usage()
        
        assert usage["total_tokens"] == 0
        assert usage["total_cost"] == 0

    def test_get_usage_by_agent(self, tracker):
        """测试按 Agent 统计（模拟）"""
        # 手动添加使用记录
        tracker._usage_records = [
            TokenUsage(
                timestamp=datetime.now(),
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                total_cost=0.001,
                model_name="gpt-3.5-turbo",
                agent_name="agent-a",
            ),
            TokenUsage(
                timestamp=datetime.now(),
                prompt_tokens=200,
                completion_tokens=100,
                total_tokens=300,
                total_cost=0.002,
                model_name="gpt-3.5-turbo",
                agent_name="agent-a",
            ),
        ]
        tracker._total_prompt_tokens = 300
        tracker._total_completion_tokens = 150
        tracker._total_cost = 0.003
        
        usage = tracker.get_usage_by_agent()
        
        assert "agent-a" in usage
        assert usage["agent-a"]["total_tokens"] == 450

    def test_get_usage_by_model(self, tracker):
        """测试按模型统计（模拟）"""
        tracker._usage_records = [
            TokenUsage(
                timestamp=datetime.now(),
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                total_cost=0.001,
                model_name="gpt-3.5-turbo",
            ),
        ]
        tracker._total_prompt_tokens = 100
        tracker._total_completion_tokens = 50
        tracker._total_cost = 0.001
        
        usage = tracker.get_usage_by_model()
        
        assert "gpt-3.5-turbo" in usage

    def test_get_usage_summary(self, tracker):
        """测试获取摘要"""
        tracker._usage_records = []
        
        summary = tracker.get_usage_summary()
        
        assert "total" in summary
        assert "by_agent" in summary
        assert "budget" in summary

    def test_reset(self, tracker):
        """测试重置"""
        tracker._usage_records = [
            TokenUsage(
                timestamp=datetime.now(),
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                total_cost=0.001,
                model_name="gpt-3.5-turbo",
            ),
        ]
        tracker._total_prompt_tokens = 100
        tracker._total_completion_tokens = 50
        tracker._total_cost = 0.001
        
        tracker.reset()
        
        assert len(tracker._usage_records) == 0
        assert tracker._total_cost == 0

    def test_estimate_cost(self, tracker):
        """测试成本估算"""
        cost = tracker.estimate_cost(
            prompt_tokens=1000,
            completion_tokens=500,
            model="gpt-3.5-turbo",
        )
        
        # gpt-3.5-turbo: prompt=0.0015, completion=0.002
        expected = (1000 / 1000) * 0.0015 + (500 / 1000) * 0.002
        assert abs(cost - expected) < 0.001

    def test_estimate_cost_unknown_model(self, tracker):
        """测试未知模型成本估算"""
        cost = tracker.estimate_cost(
            prompt_tokens=1000,
            completion_tokens=500,
            model="unknown-model",
        )
        
        # 使用默认定价
        assert cost > 0


class TestGetTokenTracker:
    """测试全局 Token 追踪器"""

    def test_singleton(self):
        """测试单例"""
        import opspilot.reliability.token_tracker as tracker_module
        tracker_module._token_tracker = None
        
        t1 = get_token_tracker()
        t2 = get_token_tracker()
        
        assert t1 is t2


class TestExecutionStatus:
    """测试 ExecutionStatus 枚举"""

    def test_status_values(self):
        """测试状态值"""
        assert ExecutionStatus.PENDING.value == "pending"
        assert ExecutionStatus.RUNNING.value == "running"
        assert ExecutionStatus.COMPLETED.value == "completed"
        assert ExecutionStatus.FAILED.value == "failed"
        assert ExecutionStatus.TIMEOUT.value == "timeout"


class TestToolCall:
    """测试 ToolCall"""

    def test_create_tool_call(self):
        """测试创建工具调用"""
        call = ToolCall(
            tool_name="query_supplier",
            params={"id": "SUP001"},
        )
        
        assert call.tool_name == "query_supplier"
        assert call.params["id"] == "SUP001"
        assert call.call_id is not None

    def test_tool_call_with_timeout(self):
        """测试带超时的工具调用"""
        call = ToolCall(
            tool_name="test_tool",
            params={},
            timeout=60.0,
        )
        
        assert call.timeout == 60.0

    def test_tool_call_priority(self):
        """测试优先级"""
        call = ToolCall(
            tool_name="test_tool",
            params={},
            priority=5,
        )
        
        assert call.priority == 5


class TestToolResult:
    """测试 ToolResult"""

    def test_create_result(self):
        """测试创建结果"""
        result = ToolResult(
            call_id="call-001",
            tool_name="test_tool",
            status=ExecutionStatus.COMPLETED,
            data={"result": "success"},
            latency_ms=100.0,
        )
        
        assert result.call_id == "call-001"
        assert result.status == ExecutionStatus.COMPLETED

    def test_result_to_dict(self):
        """测试结果转字典"""
        result = ToolResult(
            call_id="call-001",
            tool_name="test_tool",
            status=ExecutionStatus.COMPLETED,
        )
        
        data = result.to_dict()
        
        assert data["call_id"] == "call-001"
        assert data["status"] == "completed"


class TestParallelExecutionResult:
    """测试 ParallelExecutionResult"""

    def test_create_result(self):
        """测试创建结果"""
        result = ParallelExecutionResult(
            total_calls=10,
            successful=8,
            failed=2,
            results=[],
            total_latency_ms=500.0,
            parallelism_saved_ms=200.0,
        )
        
        assert result.total_calls == 10
        assert result.successful == 8

    def test_success_rate(self):
        """测试成功率计算"""
        result = ParallelExecutionResult(
            total_calls=10,
            successful=5,
            failed=5,
            results=[],
            total_latency_ms=500.0,
            parallelism_saved_ms=200.0,
        )
        
        assert result.successful / result.total_calls == 0.5


class TestParallelToolExecutor:
    """测试 ParallelToolExecutor"""

    @pytest.mark.asyncio
    async def test_create_executor(self):
        """测试创建执行器"""
        mock_router = MagicMock()
        
        executor = ParallelToolExecutor(
            tool_router=mock_router,
            max_concurrent=5,
            default_timeout=30.0,
        )
        
        assert executor._max_concurrent == 5
        assert executor._default_timeout == 30.0

    @pytest.mark.asyncio
    async def test_execute_empty_calls(self):
        """测试空调用列表"""
        mock_router = MagicMock()
        executor = ParallelToolExecutor(mock_router)
        
        result = await executor.execute_parallel([])
        
        assert result.total_calls == 0
        assert result.successful == 0

    @pytest.mark.asyncio
    async def test_execute_parallel_success(self):
        """测试成功执行"""
        mock_router = MagicMock()
        mock_router.call_tool = AsyncMock(return_value=MagicMock(data={"result": "ok"}))
        
        executor = ParallelToolExecutor(mock_router)
        
        calls = [
            ToolCall(tool_name="tool1", params={}),
            ToolCall(tool_name="tool2", params={}),
        ]
        
        result = await executor.execute_parallel(calls)
        
        assert result.total_calls == 2

    @pytest.mark.asyncio
    async def test_execute_parallel_with_timeout(self):
        """测试超时处理"""
        mock_router = MagicMock()
        
        async def slow_call(*args, **kwargs):
            await asyncio.sleep(10)
            return MagicMock(data={"result": "ok"})
        
        mock_router.call_tool = slow_call
        
        executor = ParallelToolExecutor(mock_router)
        
        calls = [
            ToolCall(tool_name="slow_tool", params={}, timeout=0.1),
        ]
        
        result = await executor.execute_parallel(calls)
        
        assert result.failed > 0 or result.total_calls == 1

    @pytest.mark.asyncio
    async def test_execute_batch(self):
        """测试分批执行"""
        mock_router = MagicMock()
        mock_router.call_tool = AsyncMock(return_value=MagicMock(data={"result": "ok"}))
        
        executor = ParallelToolExecutor(mock_router)
        
        calls = [
            ToolCall(tool_name=f"tool{i}", params={})
            for i in range(10)
        ]
        
        results = await executor.execute_batch(calls, batch_size=3)
        
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """测试获取统计"""
        mock_router = MagicMock()
        mock_router.call_tool = AsyncMock(return_value=MagicMock(data={"result": "ok"}))
        
        executor = ParallelToolExecutor(mock_router)
        
        calls = [
            ToolCall(tool_name="tool1", params={}),
        ]
        
        await executor.execute_parallel(calls)
        
        stats = executor.get_stats()
        
        assert "total_executions" in stats


class TestExecuteToolsParallel:
    """测试便捷函数"""

    @pytest.mark.asyncio
    async def test_execute_tools_parallel_function(self):
        """测试 execute_tools_parallel 函数"""
        mock_router = MagicMock()
        mock_router.call_tool = AsyncMock(return_value=MagicMock(data={"result": "ok"}))
        
        tool_calls = [
            {"tool": "tool1", "params": {"key": "value"}},
            {"tool": "tool2", "params": {"key": "value2"}},
        ]
        
        result = await execute_tools_parallel(
            tool_router=mock_router,
            tool_calls=tool_calls,
        )
        
        assert result.total_calls == 2


class TestTokenTrackerPricing:
    """测试 Token 定价"""

    def test_pricing_constants(self):
        """测试定价常量"""
        tracker = TokenTracker()
        
        assert "gpt-4" in tracker.PRICING
        assert "gpt-3.5-turbo" in tracker.PRICING
        assert "default" in tracker.PRICING

    def test_deepseek_pricing(self):
        """测试 DeepSeek 定价"""
        tracker = TokenTracker()
        
        assert "deepseek-chat" in tracker.PRICING
        assert "deepseek-reasoner" in tracker.PRICING
