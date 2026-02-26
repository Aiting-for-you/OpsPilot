"""
评估指标模块

定义各种评估指标
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any


class MetricType(str, Enum):
    """指标类型"""
    SUCCESS_RATE = "success_rate"          # 成功率
    LATENCY = "latency"                    # 响应时间
    COST = "cost"                          # 成本
    ACCURACY = "accuracy"                  # 准确率
    USER_SATISFACTION = "user_satisfaction" # 用户满意度
    TOOL_CALL_RATE = "tool_call_rate"      # 工具调用率
    ERROR_RATE = "error_rate"              # 错误率
    THROUGHPUT = "throughput"              # 吞吐量


@dataclass
class EvaluationMetric:
    """评估指标基类"""
    name: str
    type: MetricType
    value: float
    unit: str = ""
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type.value,
            "value": self.value,
            "unit": self.unit,
            "description": self.description,
            "metadata": self.metadata,
        }


@dataclass
class TaskMetric(EvaluationMetric):
    """任务指标"""
    task_id: str = ""
    agent_id: str = ""
    duration: float = 0.0  # 执行时长（秒）
    success: bool = False
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "duration": self.duration,
            "success": self.success,
            "error_message": self.error_message,
        })
        return data


@dataclass
class AgentMetric(EvaluationMetric):
    """Agent指标"""
    agent_id: str = ""
    agent_name: str = ""
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    avg_duration: float = 0.0
    tool_calls: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "avg_duration": self.avg_duration,
            "tool_calls": self.tool_calls,
        })
        return data
