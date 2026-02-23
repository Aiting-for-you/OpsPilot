"""数据分析引擎 - 任务统计、Agent性能、工具调用分析"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class TaskStatistics:
    """任务统计"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    cancelled_tasks: int = 0
    pending_tasks: int = 0
    running_tasks: int = 0
    
    success_rate: float = 0.0
    avg_execution_time: float = 0.0  # 秒
    
    tasks_by_status: Dict[str, int] = field(default_factory=dict)
    tasks_by_day: Dict[str, int] = field(default_factory=dict)
    tasks_by_hour: Dict[int, int] = field(default_factory=dict)
    
    # 趋势数据
    daily_completion_trend: List[Dict[str, Any]] = field(default_factory=list)
    daily_failure_trend: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        """自动计算成功率"""
        if self.total_tasks > 0 and self.success_rate == 0.0:
            self.success_rate = self.completed_tasks / self.total_tasks


@dataclass
class AgentPerformance:
    """Agent 性能统计"""
    agent_id: str
    agent_name: str
    
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    
    success_rate: float = 0.0
    avg_execution_time: float = 0.0
    
    # 工具调用统计
    total_tool_calls: int = 0
    successful_tool_calls: int = 0
    
    # 性能趋势
    performance_trend: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        """自动计算成功率"""
        if self.total_tasks > 0 and self.success_rate == 0.0:
            self.success_rate = self.successful_tasks / self.total_tasks


@dataclass
class ToolCallAnalytics:
    """工具调用分析"""
    tool_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    
    success_rate: float = 0.0
    avg_execution_time: float = 0.0
    
    # 调用趋势
    calls_by_day: Dict[str, int] = field(default_factory=dict)
    calls_by_hour: Dict[int, int] = field(default_factory=dict)
    
    # 错误分析
    common_errors: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SystemMetrics:
    """系统指标"""
    # 任务指标
    task_queue_size: int = 0
    active_tasks: int = 0
    
    # Agent 指标
    active_agents: int = 0
    total_agents: int = 0
    
    # 工具指标
    available_tools: int = 0
    
    # 性能指标
    system_load: float = 0.0  # 0-100
    memory_usage: float = 0.0  # MB
    
    # 时间戳
    timestamp: datetime = field(default_factory=datetime.now)


class AnalyticsEngine:
    """数据分析引擎"""
    
    def __init__(self):
        # 数据存储（实际应用中应使用数据库）
        self.task_history: List[Dict[str, Any]] = []
        self.agent_history: List[Dict[str, Any]] = []
        self.tool_call_history: List[Dict[str, Any]] = []
        
        # 缓存
        self._cache: Dict[str, Any] = {}
        self._cache_time: Dict[str, datetime] = {}
    
    def record_task_execution(
        self,
        task_id: str,
        task_name: str,
        status: str,
        agent_id: Optional[str] = None,
        execution_time: Optional[float] = None,
        error: Optional[str] = None,
    ):
        """记录任务执行"""
        record = {
            "task_id": task_id,
            "task_name": task_name,
            "status": status,
            "agent_id": agent_id,
            "execution_time": execution_time,
            "error": error,
            "timestamp": datetime.now(),
        }
        self.task_history.append(record)
        
        # 清除相关缓存
        self._clear_cache("task_stats")
        
        logger.debug(f"记录任务执行: {task_id} - {status}")
    
    def record_agent_execution(
        self,
        agent_id: str,
        agent_name: str,
        task_id: str,
        status: str,
        execution_time: Optional[float] = None,
        tool_calls: int = 0,
    ):
        """记录 Agent 执行"""
        record = {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "task_id": task_id,
            "status": status,
            "execution_time": execution_time,
            "tool_calls": tool_calls,
            "timestamp": datetime.now(),
        }
        self.agent_history.append(record)
        
        self._clear_cache("agent_stats")
        
        logger.debug(f"记录Agent执行: {agent_id} - {task_id}")
    
    def record_tool_call(
        self,
        tool_name: str,
        status: str,
        execution_time: Optional[float] = None,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        error: Optional[str] = None,
    ):
        """记录工具调用"""
        record = {
            "tool_name": tool_name,
            "status": status,
            "execution_time": execution_time,
            "agent_id": agent_id,
            "task_id": task_id,
            "error": error,
            "timestamp": datetime.now(),
        }
        self.tool_call_history.append(record)
        
        self._clear_cache("tool_stats")
        
        logger.debug(f"记录工具调用: {tool_name} - {status}")
    
    def get_task_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> TaskStatistics:
        """获取任务统计"""
        cache_key = f"task_stats_{start_time}_{end_time}"
        
        if cached := self._get_cache(cache_key):
            return cached
        
        # 过滤时间范围
        tasks = self._filter_by_time(self.task_history, start_time, end_time)
        
        # 基础统计
        stats = TaskStatistics()
        stats.total_tasks = len(tasks)
        
        status_counts = defaultdict(int)
        execution_times = []
        
        for task in tasks:
            status_counts[task["status"]] += 1
            
            if task["execution_time"]:
                execution_times.append(task["execution_time"])
            
            # 按天统计
            day = task["timestamp"].strftime("%Y-%m-%d")
            stats.tasks_by_day[day] = stats.tasks_by_day.get(day, 0) + 1
            
            # 按小时统计
            hour = task["timestamp"].hour
            stats.tasks_by_hour[hour] = stats.tasks_by_hour.get(hour, 0) + 1
        
        # 计算状态统计
        stats.completed_tasks = status_counts.get("completed", 0)
        stats.failed_tasks = status_counts.get("failed", 0)
        stats.cancelled_tasks = status_counts.get("cancelled", 0)
        stats.pending_tasks = status_counts.get("pending", 0)
        stats.running_tasks = status_counts.get("running", 0)
        stats.tasks_by_status = dict(status_counts)
        
        # 成功率
        if stats.total_tasks > 0:
            stats.success_rate = stats.completed_tasks / stats.total_tasks
        
        # 平均执行时间
        if execution_times:
            stats.avg_execution_time = sum(execution_times) / len(execution_times)
        
        # 趋势数据（最近7天）
        stats.daily_completion_trend = self._get_daily_trend(tasks, "completed")
        stats.daily_failure_trend = self._get_daily_trend(tasks, "failed")
        
        self._set_cache(cache_key, stats)
        
        return stats
    
    def get_agent_performance(
        self,
        agent_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[AgentPerformance]:
        """获取 Agent 性能统计"""
        cache_key = f"agent_stats_{agent_id}_{start_time}_{end_time}"
        
        if cached := self._get_cache(cache_key):
            return cached
        
        # 过滤数据
        records = self._filter_by_time(self.agent_history, start_time, end_time)
        
        if agent_id:
            records = [r for r in records if r["agent_id"] == agent_id]
        
        # 按 Agent 分组
        agent_data = defaultdict(list)
        for record in records:
            agent_data[record["agent_id"]].append(record)
        
        # 计算性能指标
        performances = []
        for aid, records in agent_data.items():
            perf = AgentPerformance(
                agent_id=aid,
                agent_name=records[0]["agent_name"],
            )
            
            perf.total_tasks = len(records)
            perf.successful_tasks = sum(1 for r in records if r["status"] == "completed")
            perf.failed_tasks = sum(1 for r in records if r["status"] == "failed")
            
            if perf.total_tasks > 0:
                perf.success_rate = perf.successful_tasks / perf.total_tasks
            
            execution_times = [r["execution_time"] for r in records if r["execution_time"]]
            if execution_times:
                perf.avg_execution_time = sum(execution_times) / len(execution_times)
            
            perf.total_tool_calls = sum(r["tool_calls"] for r in records)
            
            performances.append(perf)
        
        # 按成功率排序
        performances.sort(key=lambda p: p.success_rate, reverse=True)
        
        self._set_cache(cache_key, performances)
        
        return performances
    
    def get_tool_analytics(
        self,
        tool_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[ToolCallAnalytics]:
        """获取工具调用分析"""
        cache_key = f"tool_stats_{tool_name}_{start_time}_{end_time}"
        
        if cached := self._get_cache(cache_key):
            return cached
        
        # 过滤数据
        records = self._filter_by_time(self.tool_call_history, start_time, end_time)
        
        if tool_name:
            records = [r for r in records if r["tool_name"] == tool_name]
        
        # 按工具分组
        tool_data = defaultdict(list)
        for record in records:
            tool_data[record["tool_name"]].append(record)
        
        # 计算分析指标
        analytics_list = []
        for tname, records in tool_data.items():
            analytics = ToolCallAnalytics(tool_name=tname)
            
            analytics.total_calls = len(records)
            analytics.successful_calls = sum(1 for r in records if r["status"] == "success")
            analytics.failed_calls = sum(1 for r in records if r["status"] == "error")
            
            if analytics.total_calls > 0:
                analytics.success_rate = analytics.successful_calls / analytics.total_calls
            
            execution_times = [r["execution_time"] for r in records if r["execution_time"]]
            if execution_times:
                analytics.avg_execution_time = sum(execution_times) / len(execution_times)
            
            # 按天/小时统计
            for record in records:
                day = record["timestamp"].strftime("%Y-%m-%d")
                analytics.calls_by_day[day] = analytics.calls_by_day.get(day, 0) + 1
                
                hour = record["timestamp"].hour
                analytics.calls_by_hour[hour] = analytics.calls_by_hour.get(hour, 0) + 1
            
            # 错误分析
            errors = [r["error"] for r in records if r["error"]]
            error_counts = defaultdict(int)
            for error in errors:
                error_counts[error] += 1
            
            analytics.common_errors = [
                {"error": error, "count": count}
                for error, count in sorted(
                    error_counts.items(), key=lambda x: x[1], reverse=True
                )[:5]
            ]
            
            analytics_list.append(analytics)
        
        # 按调用次数排序
        analytics_list.sort(key=lambda a: a.total_calls, reverse=True)
        
        self._set_cache(cache_key, analytics_list)
        
        return analytics_list
    
    def get_system_metrics(self) -> SystemMetrics:
        """获取系统指标"""
        # 基础指标
        metrics = SystemMetrics()
        
        # 任务队列大小
        metrics.task_queue_size = sum(
            1 for t in self.task_history
            if t["status"] in ["pending", "queued"]
        )
        
        # 活跃任务
        metrics.active_tasks = sum(
            1 for t in self.task_history
            if t["status"] == "running"
        )
        
        # Agent 指标
        agent_ids = set(r["agent_id"] for r in self.agent_history if r["agent_id"])
        metrics.total_agents = len(agent_ids)
        
        recent = datetime.now() - timedelta(hours=1)
        metrics.active_agents = len([
            aid for aid in agent_ids
            if any(
                r["agent_id"] == aid and r["timestamp"] > recent
                for r in self.agent_history
            )
        ])
        
        # 系统负载估算（基于活跃任务）
        if metrics.active_tasks > 0:
            metrics.system_load = min(100, metrics.active_tasks * 10)
        
        return metrics
    
    def get_dashboard_data(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """获取看板数据（汇总）"""
        return {
            "task_statistics": self.get_task_statistics(start_time, end_time),
            "agent_performance": self.get_agent_performance(None, start_time, end_time),
            "tool_analytics": self.get_tool_analytics(None, start_time, end_time),
            "system_metrics": self.get_system_metrics(),
            "generated_at": datetime.now().isoformat(),
        }
    
    def clear_records(self):
        """清除所有记录"""
        self.task_history.clear()
        self.agent_history.clear()
        self.tool_call_history.clear()
        self._cache.clear()
        self._cache_time.clear()
    
    # ==================== 辅助方法 ====================
    
    def _filter_by_time(
        self,
        records: List[Dict[str, Any]],
        start_time: Optional[datetime],
        end_time: Optional[datetime],
    ) -> List[Dict[str, Any]]:
        """按时间过滤记录"""
        if not start_time and not end_time:
            return records
        
        filtered = records
        if start_time:
            filtered = [r for r in filtered if r["timestamp"] >= start_time]
        if end_time:
            filtered = [r for r in filtered if r["timestamp"] <= end_time]
        
        return filtered
    
    def _get_daily_trend(
        self,
        tasks: List[Dict[str, Any]],
        status: str,
    ) -> List[Dict[str, Any]]:
        """获取每日趋势"""
        daily_counts = defaultdict(int)
        
        for task in tasks:
            if task["status"] == status:
                day = task["timestamp"].strftime("%Y-%m-%d")
                daily_counts[day] += 1
        
        # 最近7天
        trend = []
        for i in range(7):
            day = (datetime.now() - timedelta(days=6-i)).strftime("%Y-%m-%d")
            trend.append({
                "date": day,
                "count": daily_counts.get(day, 0),
            })
        
        return trend
    
    def _get_cache(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self._cache:
            cache_time = self._cache_time.get(key)
            if cache_time and (datetime.now() - cache_time).seconds < 60:
                return self._cache[key]
        return None
    
    def _set_cache(self, key: str, value: Any):
        """设置缓存"""
        self._cache[key] = value
        self._cache_time[key] = datetime.now()
    
    def _clear_cache(self, prefix: str):
        """清除缓存"""
        keys_to_delete = [k for k in self._cache if k.startswith(prefix)]
        for key in keys_to_delete:
            del self._cache[key]
            del self._cache_time[key]


# 全局分析引擎实例
_analytics_engine: Optional[AnalyticsEngine] = None


def get_analytics_engine() -> AnalyticsEngine:
    """获取全局分析引擎实例"""
    global _analytics_engine
    if _analytics_engine is None:
        _analytics_engine = AnalyticsEngine()
    return _analytics_engine
