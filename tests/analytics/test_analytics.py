"""
数据分析引擎测试

测试数据分析功能：
- 任务统计
- Agent 性能分析
- 工具调用分析
- 系统指标
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from opspilot.analytics.analytics_engine import (
    TaskStatistics,
    AgentPerformance,
    ToolCallAnalytics,
    SystemMetrics,
    AnalyticsEngine,
    get_analytics_engine,
)


class TestTaskStatistics:
    """任务统计测试"""
    
    def test_default_statistics(self):
        """测试默认统计"""
        stats = TaskStatistics()
        
        assert stats.total_tasks == 0
        assert stats.completed_tasks == 0
        assert stats.failed_tasks == 0
        assert stats.cancelled_tasks == 0
        assert stats.success_rate == 0.0
        assert stats.avg_execution_time == 0.0
    
    def test_calculate_success_rate(self):
        """测试成功率计算"""
        stats = TaskStatistics(
            total_tasks=100,
            completed_tasks=85,
            failed_tasks=10,
            cancelled_tasks=5,
        )
        
        # 成功率 = 完成 / 总数
        expected_rate = 85 / 100
        assert abs(stats.success_rate - expected_rate) < 0.01
    
    def test_statistics_with_trends(self):
        """测试带趋势的统计"""
        now = datetime.now()
        stats = TaskStatistics(
            total_tasks=50,
            completed_tasks=40,
            daily_completion_trend=[
                {"date": (now - timedelta(days=i)).strftime("%Y-%m-%d"), "count": 5 + i}
                for i in range(7)
            ],
            daily_failure_trend=[
                {"date": (now - timedelta(days=i)).strftime("%Y-%m-%d"), "count": 1}
                for i in range(7)
            ],
        )
        
        assert len(stats.daily_completion_trend) == 7
        assert len(stats.daily_failure_trend) == 7


class TestAgentPerformance:
    """Agent 性能测试"""
    
    def test_default_performance(self):
        """测试默认性能数据"""
        perf = AgentPerformance(
            agent_id="agent-001",
            agent_name="IntentAgent",
        )
        
        assert perf.agent_id == "agent-001"
        assert perf.agent_name == "IntentAgent"
        assert perf.total_tasks == 0
        assert perf.successful_tasks == 0
        assert perf.avg_execution_time == 0.0
    
    def test_performance_calculation(self):
        """测试性能计算"""
        perf = AgentPerformance(
            agent_id="agent-001",
            agent_name="IntentAgent",
            total_tasks=100,
            successful_tasks=92,
            avg_execution_time=1.5,
        )
        
        expected_rate = 92 / 100
        assert abs(perf.success_rate - expected_rate) < 0.01
        assert perf.avg_execution_time == 1.5


class TestToolCallAnalytics:
    """工具调用分析测试"""
    
    def test_default_analytics(self):
        """测试默认分析数据"""
        analytics = ToolCallAnalytics(tool_name="query_supplier")
        
        assert analytics.tool_name == "query_supplier"
        assert analytics.total_calls == 0
        assert analytics.successful_calls == 0
        assert analytics.avg_execution_time == 0.0
    
    def test_analytics_with_errors(self):
        """测试带错误的分析"""
        analytics = ToolCallAnalytics(
            tool_name="query_supplier",
            total_calls=100,
            successful_calls=95,
            failed_calls=5,
        )
        
        assert analytics.failed_calls == 5


class TestSystemMetrics:
    """系统指标测试"""
    
    def test_default_metrics(self):
        """测试默认指标"""
        metrics = SystemMetrics()
        
        assert metrics.task_queue_size == 0
        assert metrics.active_tasks == 0
        assert metrics.active_agents == 0
        assert metrics.system_load == 0.0
    
    def test_metrics_with_values(self):
        """测试带值的指标"""
        metrics = SystemMetrics(
            task_queue_size=15,
            active_tasks=8,
            active_agents=5,
            available_tools=45,
            memory_usage=512.5,
            system_load=0.75,
        )
        
        assert metrics.task_queue_size == 15
        assert metrics.active_tasks == 8
        assert metrics.memory_usage == 512.5


class TestAnalyticsEngine:
    """分析引擎测试"""
    
    @pytest.fixture
    def engine(self):
        """创建分析引擎实例"""
        return AnalyticsEngine()
    
    def test_engine_creation(self, engine):
        """测试引擎创建"""
        assert engine is not None
        assert len(engine.task_history) == 0
        assert len(engine.agent_history) == 0
        assert len(engine.tool_call_history) == 0
    
    def test_record_task_execution(self, engine):
        """测试记录任务执行"""
        engine.record_task_execution(
            task_id="task-001",
            task_name="test_task",
            status="completed",
            execution_time=1.5,
            agent_id="agent-001",
        )
        
        assert len(engine.task_history) == 1
        assert engine.task_history[0]["task_id"] == "task-001"
        assert engine.task_history[0]["status"] == "completed"
    
    def test_record_agent_execution(self, engine):
        """测试记录 Agent 执行"""
        engine.record_agent_execution(
            agent_id="agent-001",
            agent_name="IntentAgent",
            task_id="task-001",
            status="completed",
            execution_time=0.8,
            tool_calls=2,
        )
        
        assert len(engine.agent_history) == 1
        assert engine.agent_history[0]["agent_id"] == "agent-001"
    
    def test_record_tool_call(self, engine):
        """测试记录工具调用"""
        engine.record_tool_call(
            tool_name="query_supplier",
            status="success",
            execution_time=0.2,
        )
        
        assert len(engine.tool_call_history) == 1
        assert engine.tool_call_history[0]["tool_name"] == "query_supplier"
    
    def test_get_task_statistics(self, engine):
        """测试获取任务统计"""
        # 记录多个任务
        for i in range(10):
            engine.record_task_execution(
                task_id=f"task-{i}",
                task_name=f"task_{i}",
                status="completed" if i < 8 else "failed",
                execution_time=1.0 + i * 0.1,
            )
        
        stats = engine.get_task_statistics()
        
        assert stats.total_tasks == 10
        assert stats.completed_tasks == 8
        assert stats.failed_tasks == 2
    
    def test_get_agent_performance(self, engine):
        """测试获取 Agent 性能"""
        # 记录 Agent 执行
        for i in range(5):
            engine.record_agent_execution(
                agent_id="agent-001",
                agent_name="IntentAgent",
                task_id=f"task-{i}",
                status="completed",
                execution_time=0.5 + i * 0.1,
            )
        
        # 获取单个 Agent 性能（返回列表）
        perfs = engine.get_agent_performance("agent-001")
        
        assert perfs is not None
        assert len(perfs) > 0
        perf = perfs[0]
        assert perf.agent_name == "IntentAgent"
        assert perf.total_tasks == 5
    
    def test_get_tool_analytics(self, engine):
        """测试获取工具调用分析"""
        # 记录工具调用
        for i in range(10):
            engine.record_tool_call(
                tool_name="query_supplier",
                status="success" if i < 9 else "failed",
                execution_time=0.1 + i * 0.02,
            )
        
        analytics_list = engine.get_tool_analytics("query_supplier")
        
        assert analytics_list is not None
        assert len(analytics_list) > 0
        analytics = analytics_list[0]
        assert analytics.total_calls == 10
        assert analytics.successful_calls == 9
    
    def test_get_system_metrics(self, engine):
        """测试获取系统指标"""
        # 记录一些数据
        engine.record_task_execution("task-1", "test", "running", 0.5)
        engine.record_task_execution("task-2", "test", "pending", 0.0)
        engine.record_agent_execution("agent-1", "IntentAgent", "task-1", "completed", 0.5)
        
        metrics = engine.get_system_metrics()
        
        assert metrics.active_tasks >= 0
        assert metrics.active_agents >= 0
    
    def test_get_dashboard_data(self, engine):
        """测试获取看板数据"""
        # 记录各种数据
        engine.record_task_execution("task-1", "test", "completed", 1.0)
        engine.record_agent_execution("agent-1", "IntentAgent", "task-1", "completed", 0.5)
        engine.record_tool_call("tool-1", "success", 0.1)
        
        dashboard = engine.get_dashboard_data()
        
        assert "task_statistics" in dashboard
        assert "agent_performance" in dashboard
        assert "tool_analytics" in dashboard
        assert "system_metrics" in dashboard
    
    def test_clear_records(self, engine):
        """测试清除记录"""
        engine.record_task_execution("task-1", "test", "completed", 1.0)
        engine.record_agent_execution("agent-1", "IntentAgent", "task-1", "completed", 0.5)
        engine.record_tool_call("tool-1", "success", 0.1)
        
        engine.clear_records()
        
        assert len(engine.task_history) == 0
        assert len(engine.agent_history) == 0
        assert len(engine.tool_call_history) == 0


class TestGetAnalyticsEngine:
    """全局引擎测试"""
    
    def test_get_engine_singleton(self):
        """测试获取全局引擎（单例）"""
        engine1 = get_analytics_engine()
        engine2 = get_analytics_engine()
        
        assert engine1 is engine2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
