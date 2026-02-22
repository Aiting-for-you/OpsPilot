"""
AgentScope评估框架集成

集成AgentScope的评估功能
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# 尝试导入AgentScope
try:
    import agentscope
    from agentscope.evaluate import EvaluatorBase
    AGENTSCOPE_AVAILABLE = True
except ImportError:
    AGENTSCOPE_AVAILABLE = False
    EvaluatorBase = object
    logger.warning("AgentScope未安装，AgentScopeEvaluator不可用")

from opspilot.evaluation.metrics import (
    MetricType,
    EvaluationMetric,
    TaskMetric,
    AgentMetric,
)


@dataclass
class AgentMetrics:
    """AgentScope Agent指标"""
    agent_id: str
    agent_name: str
    total_interactions: int = 0
    successful_interactions: int = 0
    avg_response_time: float = 0.0
    total_tokens: int = 0
    tool_calls: int = 0
    error_count: int = 0
    user_satisfaction: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "total_interactions": self.total_interactions,
            "successful_interactions": self.successful_interactions,
            "avg_response_time": self.avg_response_time,
            "total_tokens": self.total_tokens,
            "tool_calls": self.tool_calls,
            "error_count": self.error_count,
            "user_satisfaction": self.user_satisfaction,
        }


class AgentScopeEvaluator(EvaluatorBase if AGENTSCOPE_AVAILABLE else object):
    """
    AgentScope评估器
    
    集成AgentScope的评估框架，提供专业的评估功能
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not AGENTSCOPE_AVAILABLE:
            raise ImportError("AgentScope未安装，无法使用AgentScopeEvaluator")
        
        super().__init__()
        self.config = config or {}
        self._agent_metrics: Dict[str, AgentMetrics] = {}
        self._evaluation_history: List[Dict[str, Any]] = []
    
    def record_interaction(
        self,
        agent_id: str,
        agent_name: str,
        success: bool,
        response_time: float,
        tokens: int = 0,
        tool_calls: int = 0,
        error: Optional[str] = None,
        user_feedback: Optional[float] = None,
    ):
        """
        记录Agent交互
        
        Args:
            agent_id: Agent ID
            agent_name: Agent名称
            success: 是否成功
            response_time: 响应时间（秒）
            tokens: Token消耗
            tool_calls: 工具调用次数
            error: 错误信息
            user_feedback: 用户反馈（0-1）
        """
        if agent_id not in self._agent_metrics:
            self._agent_metrics[agent_id] = AgentMetrics(
                agent_id=agent_id,
                agent_name=agent_name,
            )
        
        metrics = self._agent_metrics[agent_id]
        metrics.total_interactions += 1
        
        if success:
            metrics.successful_interactions += 1
        else:
            metrics.error_count += 1
        
        # 更新平均响应时间
        metrics.avg_response_time = (
            (metrics.avg_response_time * (metrics.total_interactions - 1) + response_time)
            / metrics.total_interactions
        )
        
        metrics.total_tokens += tokens
        metrics.tool_calls += tool_calls
        
        # 更新用户满意度
        if user_feedback is not None:
            current_satisfaction = metrics.user_satisfaction
            n = metrics.total_interactions
            metrics.user_satisfaction = (current_satisfaction * (n - 1) + user_feedback) / n
        
        logger.debug(
            f"记录Agent交互: {agent_name}, 成功: {success}, "
            f"响应时间: {response_time:.2f}s"
        )
    
    def evaluate_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        评估单个Agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            评估结果
        """
        if agent_id not in self._agent_metrics:
            logger.warning(f"Agent {agent_id} 无交互记录")
            return {}
        
        metrics = self._agent_metrics[agent_id]
        
        # 计算各项指标
        success_rate = (
            metrics.successful_interactions / metrics.total_interactions
            if metrics.total_interactions > 0
            else 0
        )
        
        error_rate = (
            metrics.error_count / metrics.total_interactions
            if metrics.total_interactions > 0
            else 0
        )
        
        avg_tool_calls = (
            metrics.tool_calls / metrics.total_interactions
            if metrics.total_interactions > 0
            else 0
        )
        
        avg_tokens = (
            metrics.total_tokens / metrics.total_interactions
            if metrics.total_interactions > 0
            else 0
        )
        
        # 生成分数（综合评分）
        score = (
            success_rate * 0.4 +  # 成功率权重40%
            metrics.user_satisfaction * 0.3 +  # 用户满意度权重30%
            (1 - min(error_rate, 1)) * 0.2 +  # 低错误率权重20%
            (1 - min(metrics.avg_response_time / 10, 1)) * 0.1  # 快速响应权重10%
        )
        
        evaluation = {
            "agent_id": agent_id,
            "agent_name": metrics.agent_name,
            "score": score,
            "success_rate": success_rate,
            "error_rate": error_rate,
            "avg_response_time": metrics.avg_response_time,
            "avg_tool_calls": avg_tool_calls,
            "avg_tokens": avg_tokens,
            "user_satisfaction": metrics.user_satisfaction,
            "total_interactions": metrics.total_interactions,
            "evaluation_time": datetime.now().isoformat(),
        }
        
        self._evaluation_history.append(evaluation)
        
        return evaluation
    
    def evaluate_all_agents(self) -> List[Dict[str, Any]]:
        """评估所有Agent"""
        return [self.evaluate_agent(agent_id) for agent_id in self._agent_metrics.keys()]
    
    def get_leaderboard(self, metric: str = "score") -> List[Dict[str, Any]]:
        """
        获取Agent排行榜
        
        Args:
            metric: 排序指标（score, success_rate, user_satisfaction等）
            
        Returns:
            排行榜列表
        """
        evaluations = self.evaluate_all_agents()
        return sorted(evaluations, key=lambda x: x.get(metric, 0), reverse=True)
    
    def generate_report(self) -> Dict[str, Any]:
        """生成评估报告"""
        all_evaluations = self.evaluate_all_agents()
        
        if not all_evaluations:
            return {
                "summary": "无评估数据",
                "agents": [],
            }
        
        # 统计汇总
        total_interactions = sum(e["total_interactions"] for e in all_evaluations)
        avg_success_rate = sum(e["success_rate"] for e in all_evaluations) / len(all_evaluations)
        avg_score = sum(e["score"] for e in all_evaluations) / len(all_evaluations)
        best_agent = max(all_evaluations, key=lambda x: x["score"])
        worst_agent = min(all_evaluations, key=lambda x: x["score"])
        
        report = {
            "summary": {
                "total_agents": len(all_evaluations),
                "total_interactions": total_interactions,
                "avg_success_rate": avg_success_rate,
                "avg_score": avg_score,
                "best_agent": best_agent["agent_name"],
                "worst_agent": worst_agent["agent_name"],
            },
            "agents": all_evaluations,
            "leaderboard": self.get_leaderboard(),
            "recommendations": self._generate_recommendations(all_evaluations),
        }
        
        return report
    
    def _generate_recommendations(self, evaluations: List[Dict[str, Any]]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        for eval_data in evaluations:
            if eval_data["success_rate"] < 0.8:
                recommendations.append(
                    f"Agent {eval_data['agent_name']} 成功率较低（{eval_data['success_rate']:.1%}），"
                    "建议优化错误处理逻辑"
                )
            
            if eval_data["avg_response_time"] > 5:
                recommendations.append(
                    f"Agent {eval_data['agent_name']} 响应时间较长（{eval_data['avg_response_time']:.2f}s），"
                    "建议优化工具调用或缓存策略"
                )
            
            if eval_data["user_satisfaction"] < 0.7:
                recommendations.append(
                    f"Agent {eval_data['agent_name']} 用户满意度较低（{eval_data['user_satisfaction']:.1%}），"
                    "建议改进交互体验"
                )
        
        return recommendations
    
    @staticmethod
    def is_available() -> bool:
        """检查AgentScope是否可用"""
        return AGENTSCOPE_AVAILABLE
