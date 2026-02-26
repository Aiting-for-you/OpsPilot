"""
Token 追踪模块

使用 LangChain 的 get_openai_callback 实现精确的 Token 使用追踪。

特性：
- 实时 Token 统计
- 成本计算
- 预算控制
- 多模型支持
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

# LangChain imports
try:
    from langchain_community.callbacks import get_openai_callback
    from langchain_core.callbacks import BaseCallbackHandler
    LANGCHAIN_CALLBACKS_AVAILABLE = True
except ImportError:
    LANGCHAIN_CALLBACKS_AVAILABLE = False
    get_openai_callback = None
    BaseCallbackHandler = object

logger = logging.getLogger(__name__)


class TokenBudgetExceeded(Exception):
    """Token 预算超限异常"""
    pass


@dataclass
class TokenUsage:
    """Token 使用记录"""
    timestamp: datetime
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    total_cost: float
    model_name: str
    agent_name: Optional[str] = None
    task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "model_name": self.model_name,
            "agent_name": self.agent_name,
            "task_id": self.task_id,
            "metadata": self.metadata,
        }


class TokenTracker:
    """
    Token 追踪器
    
    提供精确的 Token 使用追踪和成本控制。
    
    示例:
        >>> tracker = TokenTracker(daily_budget=10.0)
        >>> 
        >>> with tracker.track("intent_agent", "task-123"):
        ...     result = await chain.ainvoke("query")
        >>> 
        >>> print(tracker.get_usage_summary())
    """
    
    # OpenAI 定价（美元/1K tokens）
    PRICING = {
        "gpt-4": {"prompt": 0.03, "completion": 0.06},
        "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
        "gpt-4o": {"prompt": 0.005, "completion": 0.015},
        "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002},
        "gpt-3.5-turbo-16k": {"prompt": 0.003, "completion": 0.004},
        "claude-3-opus": {"prompt": 0.015, "completion": 0.075},
        "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
        "deepseek-chat": {"prompt": 0.0001, "completion": 0.0002},
        "deepseek-reasoner": {"prompt": 0.00055, "completion": 0.00219},
        # 默认定价
        "default": {"prompt": 0.002, "completion": 0.002},
    }
    
    def __init__(
        self,
        daily_budget: Optional[float] = None,
        monthly_budget: Optional[float] = None,
        enable_budget_check: bool = True,
    ):
        self.daily_budget = daily_budget
        self.monthly_budget = monthly_budget
        self.enable_budget_check = enable_budget_check
        
        # 使用记录
        self._usage_records: List[TokenUsage] = []
        
        # 统计缓存
        self._total_prompt_tokens: int = 0
        self._total_completion_tokens: int = 0
        self._total_cost: float = 0.0
    
    @contextmanager
    def track(
        self,
        agent_name: Optional[str] = None,
        task_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        """
        Token 追踪上下文管理器
        
        Args:
            agent_name: Agent 名称
            task_id: 任务 ID
            metadata: 额外元数据
        
        Yields:
            TokenTracker: 自身，用于访问统计
        
        Raises:
            TokenBudgetExceeded: 预算超限时抛出
        """
        if not LANGCHAIN_CALLBACKS_AVAILABLE:
            logger.warning("LangChain callbacks not available, skipping token tracking")
            yield self
            return
        
        # 预算检查
        if self.enable_budget_check and self.daily_budget:
            if self._total_cost >= self.daily_budget:
                raise TokenBudgetExceeded(
                    f"Daily budget exceeded: ${self._total_cost:.4f} >= ${self.daily_budget}"
                )
        
        with get_openai_callback() as cb:
            try:
                yield self
            finally:
                # 记录使用
                if cb.total_tokens > 0:
                    usage = TokenUsage(
                        timestamp=datetime.now(),
                        prompt_tokens=cb.prompt_tokens,
                        completion_tokens=cb.completion_tokens,
                        total_tokens=cb.total_tokens,
                        total_cost=cb.total_cost,
                        model_name=cb.model_name or "unknown",
                        agent_name=agent_name,
                        task_id=task_id,
                        metadata=metadata or {},
                    )
                    self._record_usage(usage)
    
    def _record_usage(self, usage: TokenUsage) -> None:
        """记录使用"""
        self._usage_records.append(usage)
        self._total_prompt_tokens += usage.prompt_tokens
        self._total_completion_tokens += usage.completion_tokens
        self._total_cost += usage.total_cost
        
        logger.debug(
            f"Token usage recorded: {usage.total_tokens} tokens, "
            f"${usage.total_cost:.6f}, model={usage.model_name}"
        )
    
    def get_total_usage(self) -> Dict[str, Any]:
        """获取总使用量"""
        return {
            "prompt_tokens": self._total_prompt_tokens,
            "completion_tokens": self._total_completion_tokens,
            "total_tokens": self._total_prompt_tokens + self._total_completion_tokens,
            "total_cost": self._total_cost,
            "record_count": len(self._usage_records),
        }
    
    def get_usage_by_agent(self) -> Dict[str, Dict[str, Any]]:
        """按 Agent 分组统计"""
        agent_usage: Dict[str, Dict[str, Any]] = {}
        
        for record in self._usage_records:
            agent = record.agent_name or "unknown"
            if agent not in agent_usage:
                agent_usage[agent] = {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "call_count": 0,
                }
            
            agent_usage[agent]["prompt_tokens"] += record.prompt_tokens
            agent_usage[agent]["completion_tokens"] += record.completion_tokens
            agent_usage[agent]["total_tokens"] += record.total_tokens
            agent_usage[agent]["total_cost"] += record.total_cost
            agent_usage[agent]["call_count"] += 1
        
        return agent_usage
    
    def get_usage_by_model(self) -> Dict[str, Dict[str, Any]]:
        """按模型分组统计"""
        model_usage: Dict[str, Dict[str, Any]] = {}
        
        for record in self._usage_records:
            model = record.model_name
            if model not in model_usage:
                model_usage[model] = {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "call_count": 0,
                }
            
            model_usage[model]["prompt_tokens"] += record.prompt_tokens
            model_usage[model]["completion_tokens"] += record.completion_tokens
            model_usage[model]["total_tokens"] += record.total_tokens
            model_usage[model]["total_cost"] += record.total_cost
            model_usage[model]["call_count"] += 1
        
        return model_usage
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """获取使用摘要"""
        return {
            "total": self.get_total_usage(),
            "by_agent": self.get_usage_by_agent(),
            "by_model": self.get_usage_by_model(),
            "budget": {
                "daily": self.daily_budget,
                "monthly": self.monthly_budget,
                "daily_remaining": (
                    self.daily_budget - self._total_cost 
                    if self.daily_budget else None
                ),
                "monthly_remaining": (
                    self.monthly_budget - self._total_cost 
                    if self.monthly_budget else None
                ),
            },
        }
    
    def get_recent_usage(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的使用记录"""
        return [r.to_dict() for r in self._usage_records[-limit:]]
    
    def reset(self) -> None:
        """重置统计"""
        self._usage_records.clear()
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0
        self._total_cost = 0.0
    
    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str = "gpt-3.5-turbo",
    ) -> float:
        """
        估算成本
        
        Args:
            prompt_tokens: 提示词 Token 数
            completion_tokens: 补全 Token 数
            model: 模型名称
        
        Returns:
            float: 预估成本（美元）
        """
        pricing = self.PRICING.get(model, self.PRICING["default"])
        
        prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
        completion_cost = (completion_tokens / 1000) * pricing["completion"]
        
        return prompt_cost + completion_cost


# ============================================================================
# 全局 Token 追踪器
# ============================================================================

_token_tracker: Optional[TokenTracker] = None


def get_token_tracker() -> TokenTracker:
    """获取全局 Token 追踪器"""
    global _token_tracker
    if _token_tracker is None:
        _token_tracker = TokenTracker()
    return _token_tracker


def set_token_tracker(tracker: TokenTracker) -> None:
    """设置全局 Token 追踪器"""
    global _token_tracker
    _token_tracker = tracker


@contextmanager
def track_tokens(
    agent_name: Optional[str] = None,
    task_id: Optional[str] = None,
):
    """便捷的 Token 追踪上下文管理器"""
    tracker = get_token_tracker()
    with tracker.track(agent_name, task_id):
        yield tracker
