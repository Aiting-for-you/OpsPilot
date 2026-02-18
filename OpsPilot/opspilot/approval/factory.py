"""
审批工厂模块

根据配置选择审批实现
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from opspilot.approval.config import ApprovalConfig
from opspilot.approval.opspilot_approval import OpsPilotApprovalHandler
from opspilot.approval.langchain_approval import LangChainApprovalHandler


class ApprovalProvider(str, Enum):
    """审批提供者"""
    OPSPILOT = "opspilot"
    LANGCHAIN = "langchain"


class ApprovalFactory:
    """审批工厂类"""
    
    _instance: Optional[ApprovalFactory] = None
    _current_provider: ApprovalProvider = ApprovalProvider.LANGCHAIN
    _handlers: dict = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def create_handler(
        cls,
        provider: Optional[ApprovalProvider] = None,
        config: Optional[ApprovalConfig] = None,
    ):
        """
        创建审批处理器
        
        Args:
            provider: 提供者类型，None则使用默认
            config: 审批配置
            
        Returns:
            审批处理器实例
        """
        if provider is None:
            provider = cls._current_provider
        
        config = config or ApprovalConfig()
        
        # 检查缓存
        cache_key = f"{provider.value}-{id(config)}"
        if cache_key in cls._handlers:
            return cls._handlers[cache_key]
        
        # 创建新实例
        if provider == ApprovalProvider.OPSPILOT:
            handler = OpsPilotApprovalHandler(config)
        elif provider == ApprovalProvider.LANGCHAIN:
            if not LangChainApprovalHandler.is_available():
                raise ImportError("LangChain未安装，无法使用LangChainApprovalHandler")
            handler = LangChainApprovalHandler(config)
        else:
            raise ValueError(f"不支持的审批提供者: {provider}")
        
        cls._handlers[cache_key] = handler
        return handler
    
    @classmethod
    def set_provider(cls, provider: ApprovalProvider):
        """设置当前提供者"""
        cls._current_provider = provider
    
    @classmethod
    def get_current_provider(cls) -> ApprovalProvider:
        """获取当前提供者"""
        return cls._current_provider
    
    @classmethod
    def clear_cache(cls):
        """清除缓存"""
        cls._handlers.clear()


def create_approval_handler(
    provider: Optional[str] = None,
    config: Optional[ApprovalConfig] = None,
):
    """
    创建审批处理器（便捷函数）
    
    Args:
        provider: 提供者名称（字符串）
        config: 审批配置
        
    Returns:
        审批处理器实例
    """
    if provider is None:
        provider_enum = None
    else:
        provider_enum = ApprovalProvider(provider)
    
    return ApprovalFactory.create_handler(provider_enum, config)


def get_approval_handler() -> OpsPilotApprovalHandler | LangChainApprovalHandler:
    """
    获取当前审批处理器（单例）
    
    Returns:
        当前配置的审批处理器
    """
    return ApprovalFactory.create_handler()
