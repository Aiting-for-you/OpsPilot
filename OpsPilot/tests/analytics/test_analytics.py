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
            completion_trend=[
                {"date": (now - timedelta(days=i)).strftime("%Y-%m-%d"), "count": 5 + i}
                for i in range(7)
            ],
            failure_trend=[
                {"date": (now - timedelta(days=i)).strftime("%Y-%m-%d"), "count": 1}
                for i in range(7)
            ],
        )
        
        assert len(stats.completion_trend) == 7
        assert len(stats.failure_trend) == 7


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
        assert perf.task_count == 0
        assert perf.success_count == 0
        assert perf.avg_execution_time == 0.0
    
    def test_performance_calculation(self):
        """测试性能计算"""
        perf = AgentPerformance(
            agent_id="agent-001",
            agent_name="IntentAgent",
            task_count=100,
            success_count=92,
            avg_execution_time=1.5,
            tool_calls={"query_supplier": 50, "check_inventory": 30},
        )
        
        expected_rate = 92 / 100
        assert abs(perf.success_rate - expected_rate) < 0.01
        assert perf.avg_execution_time == 1.5
        assert perf.tool_calls["query_supplier"] == 50


class TestToolCallAnalytics:
    """工具调用分析测试"""
    
    def test_default_analytics(self):
        """测试默认分析数据"""
        analytics = ToolCallAnalytics(tool_name="query_supplier")
        
        assert analytics.tool_name == "query_supplier"
        assert analytics.call_count == 0
        assert analytics.success_count == 0
        assert analytics.avg_execution_time == 0.0
    
    def test_analytics_with_errors(self):
        """测试带错误的分析"""
        analytics = ToolCallAnalytics(
            tool_name="query_supplier",
            call_count=100,
            success_count=95,
            error_count=5,
            common_errors=[
                {"error": "TimeoutError", "count": 3},
                {"error": "ConnectionError", "count": 2},
            ],
        )
        
        assert analytics.error_count == 5
        assert len(analytics.common_errors) == 2


class TestSystemMetrics:
    """系统指标测试"""
    
    def test_default_metrics(self):
        """测试默认指标"""
        metrics = SystemMetrics()
        
        assert metrics.queue_size == 0
        assert metrics.active_tasks == 0
        assert metrics.active_agents == 0
        assert metrics.system_load == 0.0
    
    def test_metrics_with_values(self):
        """测试带值的指标"""
        metrics = SystemMetrics(
            queue_size=15,
            active_tasks=8,
            active_agents=5,
            active_tools=45,
            memory_usage_mb=512.5,
            cpu_usage_percent=45.2,
            system_load=0.75,
        )
        
        assert metrics.queue_size == 15
        assert metrics.active_tasks == 8
        assert metrics.memory_usage_mb == 512.5
        assert metrics.cpu_usage_percent == 45.2


class TestAnalyticsEngine:
    """分析引擎测试"""
    
    @pytest.fixture
    def engine(self):
        """创建分析引擎实例"""
        return AnalyticsEngine()
    
    def test_engine_creation(self, engine):
        """测试引擎创建"""
        assert engine is not None
        assert len(engine._task_records) == 0
        assert len(engine._agent_records) == 0
        assert len(engine._tool_records) == 0
    
    def test_record_task_execution(self, engine):
        """测试记录任务执行"""
        engine.record_task_execution(
            task_id="task-001",
            status="completed",
            execution_time=1.5,
            agent_id="agent-001",
        )
        
        assert len(engine._task_records) == 1
        assert engine._task_records[0]["task_id"] == "task-001"
        assert engine._task_records[0]["status"] == "completed"
    
    def test_record_agent_execution(self, engine):
        """测试记录 Agent 执行"""
        engine.record_agent_execution(
            agent_id="agent-001",
            agent_name="IntentAgent",
            success=True,
            execution_time=0.8,
            tools_used=["query_supplier"],
        )
        
        assert len(engine._agent_records) == 1
        assert engine._agent_records[0]["agent_id"] == "agent-001"
    
    def test_record_tool_call(self, engine):
        """测试记录工具调用"""
        engine.record_tool_call(
            tool_name="query_supplier",
            success=True,
            execution_time=0.2,
        )
        
        assert len(engine._tool_records) == 1
        assert engine._tool_records[0]["tool_name"] == "query_supplier"
    
    def test_get_task_statistics(self, engine):
        """测试获取任务统计"""
        # 记录多个任务
        for i in range(10):
            engine.record_task_execution(
                task_id=f"task-{i}",
                status="completed" if i < 8 else "failed",
                execution_time=1.0 + i * 0.1,
            )
        
        stats = engine.get_task_statistics()
        
        assert stats.total_tasks == 10
        assert stats.completed_tasks == 8
        assert stats.failed_tasks == 2
        assert stats.success_rate == 0.8
    
    def test_get_task_statistics_with_time_range(self, engine):
        """测试按时间范围获取任务统计"""
        now = datetime.now()
        
        # 记录任务
        engine.record_task_execution("task-1", "completed", 1.0)
        engine.record_task_execution("task-2", "completed", 1.5)
        
        stats = engine.get_task_statistics(
            start_time=now - timedelta(days=1),
            end_time=now + timedelta(days=1),
        )
        
        assert stats.total_tasks == 2
    
    def test_get_agent_performance(self, engine):
        """测试获取 Agent 性能"""
        # 记录 Agent 执行
        for i in range(5):
            engine.record_agent_execution(
                agent_id="agent-001",
                agent_name="IntentAgent",
                success=True,
                execution_time=0.5 + i * 0.1,
            )
        
        for i in range(3):
            engine.record_agent_execution(
                agent_id="agent-002",
                agent_name="PlanAgent",
                success=i < 2,
                execution_time=1.0,
            )
        
        # 获取单个 Agent 性能
        perf = engine.get_agent_performance("agent-001")
        
        assert perf is not None
        assert perf.agent_name == "IntentAgent"
        assert perf.task_count == 5
        assert perf.success_count == 5
    
    def test_get_all_agent_performances(self, engine):
        """测试获取所有 Agent 性能"""
        engine.record_agent_execution("agent-001", "IntentAgent", True, 0.5)
        engine.record_agent_execution("agent-002", "PlanAgent", True, 1.0)
        
        performances = engine.get_all_agent_performances()
        
        assert len(performances) == 2
    
    def test_get_tool_analytics(self, engine):
        """测试获取工具调用分析"""
        # 记录工具调用
        for i in range(10):
            engine.record_tool_call(
                tool_name="query_supplier",
                success=i < 9,
                execution_time=0.1 + i * 0.02,
            )
        
        analytics = engine.get_tool_analytics("query_supplier")
        
        assert analytics is not None
        assert analytics.call_count == 10
        assert analytics.success_count == 9
        assert analytics.error_count == 1
    
    def test_get_all_tool_analytics(self, engine):
        """测试获取所有工具调用分析"""
        engine.record_tool_call("tool-1", True, 0.1)
        engine.record_tool_call("tool-2", True, 0.2)
        
        analytics = engine.get_all_tool_analytics()
        
        assert len(analytics) == 2
    
    def test_get_system_metrics(self, engine):
        """测试获取系统指标"""
        # 记录一些数据
        engine.record_task_execution("task-1", "running", 0.5)
        engine.record_task_execution("task-2", "pending", 0.0)
        engine.record_agent_execution("agent-1", "IntentAgent", True, 0.5)
        
        metrics = engine.get_system_metrics()
        
        assert metrics.total_tasks == 2
        assert metrics.active_agents == 1
    
    def test_get_dashboard_data(self, engine):
        """测试获取看板数据"""
        # 记录各种数据
        engine.record_task_execution("task-1", "completed", 1.0)
        engine.record_agent_execution("agent-1", "IntentAgent", True, 0.5)
        engine.record_tool_call("tool-1", True, 0.1)
        
        dashboard = engine.get_dashboard_data()
        
        assert "task_statistics" in dashboard
        assert "agent_performances" in dashboard
        assert "tool_analytics" in dashboard
        assert "system_metrics" in dashboard
    
    def test_cache_mechanism(self, engine):
        """测试缓存机制"""
        engine.record_task_execution("task-1", "completed", 1.0)
        
        # 第一次获取
        stats1 = engine.get_task_statistics()
        
        # 第二次获取（应该从缓存读取）
        stats2 = engine.get_task_statistics()
        
        assert stats1.total_tasks == stats2.total_tasks
    
    def test_clear_records(self, engine):
        """测试清除记录"""
        engine.record_task_execution("task-1", "completed", 1.0)
        engine.record_agent_execution("agent-1", "IntentAgent", True, 0.5)
        engine.record_tool_call("tool-1", True, 0.1)
        
        engine.clear_records()
        
        assert len(engine._task_records) == 0
        assert len(engine._agent_records) == 0
        assert len(engine._tool_records) == 0


class TestGetAnalyticsEngine:
    """全局引擎测试"""
    
    def test_get_engine_singleton(self):
        """测试获取全局引擎（单例）"""
        engine1 = get_analytics_engine()
        engine2 = get_analytics_engine()
        
        assert engine1 is engine2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
