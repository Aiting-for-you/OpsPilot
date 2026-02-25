"""
评估模块测试

测试 OpsPilotEvaluator, EvaluationFactory, 指标类等
"""

import pytest
from datetime import datetime, timedelta

from opspilot.evaluation.metrics import (
    MetricType,
    EvaluationMetric,
    TaskMetric,
    AgentMetric,
)
from opspilot.evaluation.opspilot_evaluator import (
    OpsPilotEvaluator,
    EvaluationResult,
)
from opspilot.evaluation.factory import (
    EvaluationProvider,
    EvaluationFactory,
    create_evaluator,
    get_evaluator,
)


class TestMetricType:
    """测试 MetricType 枚举"""

    def test_metric_types(self):
        """测试指标类型定义"""
        assert MetricType.SUCCESS_RATE.value == "success_rate"
        assert MetricType.LATENCY.value == "latency"
        assert MetricType.COST.value == "cost"
        assert MetricType.ACCURACY.value == "accuracy"
        assert MetricType.USER_SATISFACTION.value == "user_satisfaction"
        assert MetricType.TOOL_CALL_RATE.value == "tool_call_rate"
        assert MetricType.ERROR_RATE.value == "error_rate"
        assert MetricType.THROUGHPUT.value == "throughput"


class TestEvaluationMetric:
    """测试 EvaluationMetric 基类"""

    def test_create_metric(self):
        """测试创建指标"""
        metric = EvaluationMetric(
            name="test_metric",
            type=MetricType.SUCCESS_RATE,
            value=0.95,
            unit="%",
            description="测试指标",
        )
        
        assert metric.name == "test_metric"
        assert metric.type == MetricType.SUCCESS_RATE
        assert metric.value == 0.95
        assert metric.unit == "%"
        assert metric.description == "测试指标"

    def test_to_dict(self):
        """测试转换为字典"""
        metric = EvaluationMetric(
            name="test_metric",
            type=MetricType.LATENCY,
            value=1.5,
            unit="秒",
        )
        
        data = metric.to_dict()
        assert data["name"] == "test_metric"
        assert data["type"] == "latency"
        assert data["value"] == 1.5
        assert data["unit"] == "秒"


class TestTaskMetric:
    """测试 TaskMetric"""

    def test_create_task_metric(self):
        """测试创建任务指标"""
        metric = TaskMetric(
            name="任务成功率",
            type=MetricType.SUCCESS_RATE,
            value=0.85,
            unit="%",
            task_id="task-001",
            agent_id="agent-001",
            duration=2.5,
            success=True,
        )
        
        assert metric.task_id == "task-001"
        assert metric.agent_id == "agent-001"
        assert metric.duration == 2.5
        assert metric.success is True

    def test_task_metric_to_dict(self):
        """测试任务指标转字典"""
        metric = TaskMetric(
            name="任务成功率",
            type=MetricType.SUCCESS_RATE,
            value=0.85,
            task_id="task-001",
        )
        
        data = metric.to_dict()
        assert "task_id" in data
        assert data["task_id"] == "task-001"


class TestAgentMetric:
    """测试 AgentMetric"""

    def test_create_agent_metric(self):
        """测试创建Agent指标"""
        metric = AgentMetric(
            name="Agent成功率",
            type=MetricType.SUCCESS_RATE,
            value=0.9,
            agent_id="agent-001",
            agent_name="IntentAgent",
            total_tasks=100,
            successful_tasks=90,
            failed_tasks=10,
            avg_duration=1.5,
            tool_calls=50,
        )
        
        assert metric.agent_id == "agent-001"
        assert metric.agent_name == "IntentAgent"
        assert metric.total_tasks == 100
        assert metric.successful_tasks == 90
        assert metric.tool_calls == 50


class TestOpsPilotEvaluator:
    """测试 OpsPilotEvaluator"""

    @pytest.fixture
    def evaluator(self):
        """创建评估器实例"""
        return OpsPilotEvaluator()

    def test_record_task(self, evaluator):
        """测试记录任务"""
        evaluator.record_task(
            task_id="task-001",
            agent_id="agent-001",
            success=True,
            duration=1.5,
        )
        
        stats = evaluator.get_statistics()
        assert stats["total_tasks"] == 1
        assert stats["successful_tasks"] == 1

    def test_record_task_with_error(self, evaluator):
        """测试记录失败任务"""
        evaluator.record_task(
            task_id="task-002",
            agent_id="agent-001",
            success=False,
            duration=2.0,
            error_message="Timeout",
        )
        
        stats = evaluator.get_statistics()
        assert stats["total_tasks"] == 1
        assert stats["failed_tasks"] == 1

    def test_evaluate_empty_tasks(self, evaluator):
        """测试评估无任务记录"""
        result = evaluator.evaluate_tasks()
        
        assert isinstance(result, EvaluationResult)
        assert result.summary["total_tasks"] == 0

    def test_evaluate_tasks_success_rate(self, evaluator):
        """测试任务成功率评估"""
        # 记录5个任务，4个成功
        for i in range(4):
            evaluator.record_task(
                task_id=f"task-{i}",
                agent_id="agent-001",
                success=True,
                duration=1.0,
            )
        
        evaluator.record_task(
            task_id="task-fail",
            agent_id="agent-001",
            success=False,
            duration=2.0,
        )
        
        result = evaluator.evaluate_tasks()
        
        assert result.summary["total_tasks"] == 5
        assert result.summary["successful_tasks"] == 4
        assert "80.0%" in result.summary["success_rate"]

    def test_evaluate_tasks_with_time_filter(self, evaluator):
        """测试时间过滤"""
        # 记录任务
        evaluator.record_task(
            task_id="task-001",
            agent_id="agent-001",
            success=True,
            duration=1.0,
        )
        
        # 使用时间过滤
        start_time = datetime.now() + timedelta(hours=1)
        result = evaluator.evaluate_tasks(start_time=start_time)
        
        assert result.summary["total_tasks"] == 0

    def test_evaluate_agents(self, evaluator):
        """测试Agent评估"""
        # 记录多个Agent的任务
        evaluator.record_task("task-1", "agent-a", True, 1.0)
        evaluator.record_task("task-2", "agent-a", True, 1.5)
        evaluator.record_task("task-3", "agent-b", False, 2.0)
        
        result = evaluator.evaluate_agents()
        
        assert len(result.metrics) == 2  # 2个Agent
        
        agent_a_metric = next(m for m in result.metrics if m.agent_id == "agent-a")
        assert agent_a_metric.successful_tasks == 2

    def test_get_statistics(self, evaluator):
        """测试获取统计数据"""
        evaluator.record_task("task-1", "agent-a", True, 1.0)
        evaluator.record_task("task-2", "agent-b", False, 2.0)
        
        stats = evaluator.get_statistics()
        
        assert stats["total_tasks"] == 2
        assert stats["successful_tasks"] == 1
        assert stats["failed_tasks"] == 1
        assert stats["total_agents"] == 2


class TestEvaluationFactory:
    """测试 EvaluationFactory"""

    def test_create_default_evaluator(self):
        """测试创建默认评估器"""
        # 清除缓存
        EvaluationFactory.clear_cache()
        # 设置默认提供者为 OpsPilot（避免 AgentScope 依赖问题）
        original = EvaluationFactory.get_current_provider()
        EvaluationFactory.set_provider(EvaluationProvider.OPSPILOT)
        
        try:
            evaluator = EvaluationFactory.create_evaluator()
            assert isinstance(evaluator, OpsPilotEvaluator)
        finally:
            EvaluationFactory.set_provider(original)

    def test_create_opspilot_evaluator(self):
        """测试创建OpsPilot评估器"""
        EvaluationFactory.clear_cache()
        
        evaluator = EvaluationFactory.create_evaluator(
            provider=EvaluationProvider.OPSPILOT
        )
        assert isinstance(evaluator, OpsPilotEvaluator)

    def test_set_provider(self):
        """测试设置提供者"""
        original = EvaluationFactory.get_current_provider()
        
        EvaluationFactory.set_provider(EvaluationProvider.OPSPILOT)
        assert EvaluationFactory.get_current_provider() == EvaluationProvider.OPSPILOT
        
        # 恢复
        EvaluationFactory.set_provider(original)

    def test_evaluator_cache(self):
        """测试评估器缓存"""
        EvaluationFactory.clear_cache()
        
        # 设置提供者
        original = EvaluationFactory.get_current_provider()
        EvaluationFactory.set_provider(EvaluationProvider.OPSPILOT)
        
        try:
            # 第一次创建
            evaluator1 = EvaluationFactory.create_evaluator()
            
            # 第二次获取同一实例
            evaluator2 = EvaluationFactory.create_evaluator()
            
            # 验证是同一实例（缓存）
            assert evaluator1 is evaluator2
        finally:
            EvaluationFactory.set_provider(original)

    def test_clear_cache(self):
        """测试清除缓存"""
        original = EvaluationFactory.get_current_provider()
        EvaluationFactory.set_provider(EvaluationProvider.OPSPILOT)
        
        try:
            EvaluationFactory.create_evaluator()
            
            EvaluationFactory.clear_cache()
            
            # 再次创建应该是新实例
            evaluator = EvaluationFactory.create_evaluator()
            assert isinstance(evaluator, OpsPilotEvaluator)
        finally:
            EvaluationFactory.set_provider(original)


class TestCreateEvaluator:
    """测试便捷函数"""

    def test_create_evaluator_with_string(self):
        """测试使用字符串创建评估器"""
        EvaluationFactory.clear_cache()
        
        evaluator = create_evaluator(provider="opspilot")
        assert isinstance(evaluator, OpsPilotEvaluator)

    def test_get_evaluator(self):
        """测试获取评估器"""
        EvaluationFactory.clear_cache()
        
        original = EvaluationFactory.get_current_provider()
        EvaluationFactory.set_provider(EvaluationProvider.OPSPILOT)
        
        try:
            evaluator = get_evaluator()
            assert isinstance(evaluator, OpsPilotEvaluator)
        finally:
            EvaluationFactory.set_provider(original)


class TestEvaluationResult:
    """测试 EvaluationResult"""

    def test_create_result(self):
        """测试创建评估结果"""
        metric = EvaluationMetric(
            name="test",
            type=MetricType.SUCCESS_RATE,
            value=0.9,
        )
        
        result = EvaluationResult(
            evaluation_id="eval-001",
            timestamp=datetime.now(),
            metrics=[metric],
            summary={"total": 10},
            recommendations=["建议1"],
        )
        
        assert result.evaluation_id == "eval-001"
        assert len(result.metrics) == 1
        assert len(result.recommendations) == 1

    def test_result_to_dict(self):
        """测试结果转字典"""
        result = EvaluationResult(
            evaluation_id="eval-001",
            timestamp=datetime.now(),
            metrics=[],
        )
        
        data = result.to_dict()
        assert data["evaluation_id"] == "eval-001"
        assert "timestamp" in data
        assert "metrics" in data
