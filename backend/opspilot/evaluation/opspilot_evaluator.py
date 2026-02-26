"""
OpsPilot自研评估器

基于现有的数据分析模块实现评估功能
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import logging

from opspilot.evaluation.metrics import (
    MetricType,
    EvaluationMetric,
    TaskMetric,
    AgentMetric,
)

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """评估结果"""
    evaluation_id: str
    timestamp: datetime
    metrics: List[EvaluationMetric]
    summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "timestamp": self.timestamp.isoformat(),
            "metrics": [m.to_dict() for m in self.metrics],
            "summary": self.summary,
            "recommendations": self.recommendations,
        }


class OpsPilotEvaluator:
    """
    OpsPilot评估器
    
    基于已有的数据分析模块，提供评估功能
    """
    
    def __init__(self):
        self._task_records: List[Dict[str, Any]] = []
        self._agent_records: List[Dict[str, Any]] = []
    
    def record_task(
        self,
        task_id: str,
        agent_id: str,
        success: bool,
        duration: float,
        error_message: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """记录任务执行"""
        record = {
            "task_id": task_id,
            "agent_id": agent_id,
            "success": success,
            "duration": duration,
            "error_message": error_message,
            "timestamp": datetime.now(),
            "metadata": metadata or {},
        }
        self._task_records.append(record)
        logger.debug(f"记录任务: {task_id}, 成功: {success}")
    
    def evaluate_tasks(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> EvaluationResult:
        """
        评估任务执行情况
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            评估结果
        """
        # 过滤时间范围
        records = self._task_records
        if start_time:
            records = [r for r in records if r["timestamp"] >= start_time]
        if end_time:
            records = [r for r in records if r["timestamp"] <= end_time]
        
        if not records:
            return EvaluationResult(
                evaluation_id=f"eval-{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                metrics=[],
                summary={"total_tasks": 0},
                recommendations=["无任务记录"],
            )
        
        # 计算指标
        total_tasks = len(records)
        successful_tasks = sum(1 for r in records if r["success"])
        failed_tasks = total_tasks - successful_tasks
        success_rate = successful_tasks / total_tasks if total_tasks > 0 else 0
        
        durations = [r["duration"] for r in records]
        avg_duration = sum(durations) / len(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        
        # 创建评估指标
        metrics: List[EvaluationMetric] = [
            TaskMetric(
                name="任务成功率",
                type=MetricType.SUCCESS_RATE,
                value=success_rate,
                unit="%",
                description="成功完成的任务占比",
                task_id="all",
                success=success_rate > 0.8,
            ),
            TaskMetric(
                name="平均响应时间",
                type=MetricType.LATENCY,
                value=avg_duration,
                unit="秒",
                description="任务平均执行时长",
                task_id="all",
                duration=avg_duration,
            ),
            TaskMetric(
                name="最小响应时间",
                type=MetricType.LATENCY,
                value=min_duration,
                unit="秒",
                description="最快任务执行时长",
                task_id="all",
                duration=min_duration,
            ),
            TaskMetric(
                name="最大响应时间",
                type=MetricType.LATENCY,
                value=max_duration,
                unit="秒",
                description="最慢任务执行时长",
                task_id="all",
                duration=max_duration,
            ),
        ]
        
        # 生成摘要
        summary = {
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": f"{success_rate * 100:.1f}%",
            "avg_duration": f"{avg_duration:.2f}秒",
        }
        
        # 生成建议
        recommendations = []
        if success_rate < 0.8:
            recommendations.append("成功率低于80%，建议检查错误日志优化Agent逻辑")
        if avg_duration > 10:
            recommendations.append("平均响应时间较长，建议优化工具调用性能")
        if max_duration > avg_duration * 3:
            recommendations.append("存在异常耗时的任务，建议排查慢查询")
        
        return EvaluationResult(
            evaluation_id=f"eval-{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            metrics=metrics,
            summary=summary,
            recommendations=recommendations,
        )
    
    def evaluate_agents(self) -> EvaluationResult:
        """
        评估Agent性能
        
        Returns:
            评估结果
        """
        # 按Agent分组统计
        agent_stats: Dict[str, Dict[str, Any]] = {}
        
        for record in self._task_records:
            agent_id = record["agent_id"]
            if agent_id not in agent_stats:
                agent_stats[agent_id] = {
                    "agent_id": agent_id,
                    "total_tasks": 0,
                    "successful_tasks": 0,
                    "failed_tasks": 0,
                    "durations": [],
                }
            
            stats = agent_stats[agent_id]
            stats["total_tasks"] += 1
            if record["success"]:
                stats["successful_tasks"] += 1
            else:
                stats["failed_tasks"] += 1
            stats["durations"].append(record["duration"])
        
        # 创建Agent指标
        metrics: List[AgentMetric] = []
        for agent_id, stats in agent_stats.items():
            success_rate = stats["successful_tasks"] / stats["total_tasks"] if stats["total_tasks"] > 0 else 0
            avg_duration = sum(stats["durations"]) / len(stats["durations"]) if stats["durations"] else 0
            
            metrics.append(AgentMetric(
                name=f"Agent {agent_id} 成功率",
                type=MetricType.SUCCESS_RATE,
                value=success_rate,
                unit="%",
                description=f"Agent {agent_id} 的任务成功率",
                agent_id=agent_id,
                total_tasks=stats["total_tasks"],
                successful_tasks=stats["successful_tasks"],
                failed_tasks=stats["failed_tasks"],
                avg_duration=avg_duration,
            ))
        
        # 生成摘要
        total_agents = len(agent_stats)
        avg_success_rate = sum(m.value for m in metrics if m.type == MetricType.SUCCESS_RATE) / total_agents if total_agents > 0 else 0
        
        summary = {
            "total_agents": total_agents,
            "avg_success_rate": f"{avg_success_rate * 100:.1f}%",
        }
        
        # 生成建议
        recommendations = []
        if avg_success_rate < 0.9:
            recommendations.append("部分Agent成功率较低，建议优化")
        
        return EvaluationResult(
            evaluation_id=f"agent-eval-{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            metrics=metrics,
            summary=summary,
            recommendations=recommendations,
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计数据"""
        total_tasks = len(self._task_records)
        successful_tasks = sum(1 for r in self._task_records if r["success"])
        
        return {
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "failed_tasks": total_tasks - successful_tasks,
            "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0,
            "total_agents": len(set(r["agent_id"] for r in self._task_records)),
        }
