"""
评估工厂模块

根据配置选择评估实现
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from opspilot.evaluation.opspilot_evaluator import OpsPilotEvaluator
from opspilot.evaluation.agentscope_evaluator import AgentScopeEvaluator


class EvaluationProvider(str, Enum):
    """评估提供者"""
    OPSPILOT = "opspilot"
    AGENTSCOPE = "agentscope"


class EvaluationFactory:
    """评估工厂类"""
    
    _instance: Optional[EvaluationFactory] = None
    _current_provider: EvaluationProvider = EvaluationProvider.AGENTSCOPE
    _evaluators: dict = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def create_evaluator(
        cls,
        provider: Optional[EvaluationProvider] = None,
        config: Optional[dict] = None,
    ):
        """
        创建评估器
        
        Args:
            provider: 提供者类型，None则使用默认
            config: 评估配置
            
        Returns:
            评估器实例
        """
        if provider is None:
            provider = cls._current_provider
        
        config = config or {}
        
        # 检查缓存
        cache_key = f"{provider.value}"
        if cache_key in cls._evaluators:
            return cls._evaluators[cache_key]
        
        # 创建新实例
        if provider == EvaluationProvider.OPSPILOT:
            evaluator = OpsPilotEvaluator()
        elif provider == EvaluationProvider.AGENTSCOPE:
            if not AgentScopeEvaluator.is_available():
                raise ImportError("AgentScope未安装，无法使用AgentScopeEvaluator")
            evaluator = AgentScopeEvaluator(config)
        else:
            raise ValueError(f"不支持的评估提供者: {provider}")
        
        cls._evaluators[cache_key] = evaluator
        return evaluator
    
    @classmethod
    def set_provider(cls, provider: EvaluationProvider):
        """设置当前提供者"""
        cls._current_provider = provider
    
    @classmethod
    def get_current_provider(cls) -> EvaluationProvider:
        """获取当前提供者"""
        return cls._current_provider
    
    @classmethod
    def clear_cache(cls):
        """清除缓存"""
        cls._evaluators.clear()


def create_evaluator(
    provider: Optional[str] = None,
    config: Optional[dict] = None,
):
    """
    创建评估器（便捷函数）
    
    Args:
        provider: 提供者名称（字符串）
        config: 评估配置
        
    Returns:
        评估器实例
    """
    if provider is None:
        provider_enum = None
    else:
        provider_enum = EvaluationProvider(provider)
    
    return EvaluationFactory.create_evaluator(provider_enum, config)


def get_evaluator() -> OpsPilotEvaluator | AgentScopeEvaluator:
    """
    获取当前评估器（单例）
    
    Returns:
        当前配置的评估器
    """
    return EvaluationFactory.create_evaluator()
