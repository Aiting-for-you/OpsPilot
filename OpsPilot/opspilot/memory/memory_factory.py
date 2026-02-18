"""
记忆管理工厂模块

根据配置选择记忆实现
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from opspilot.memory.short_term import ShortTermMemory
from opspilot.memory.reme_memory import ReMeMemory, ReMeConfig


class MemoryProvider(str, Enum):
    """记忆提供者"""
    OPSPILOT = "opspilot"
    REME = "reme"


class MemoryFactory:
    """记忆管理工厂类"""
    
    _instance: Optional[MemoryFactory] = None
    _current_provider: MemoryProvider = MemoryProvider.OPSPILOT
    _memories: dict = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def create_memory(
        cls,
        provider: Optional[MemoryProvider] = None,
        config: Optional[ReMeConfig] = None,
    ):
        """
        创建记忆管理器
        
        Args:
            provider: 提供者类型，None则使用默认
            config: 记忆配置
            
        Returns:
            记忆管理器实例
        """
        if provider is None:
            provider = cls._current_provider
        
        # 检查缓存
        cache_key = f"{provider.value}"
        if cache_key in cls._memories:
            return cls._memories[cache_key]
        
        # 创建新实例
        if provider == MemoryProvider.OPSPILOT:
            memory = ShortTermMemory()
        elif provider == MemoryProvider.REME:
            if not ReMeMemory.is_available():
                raise ImportError("AgentScope未安装，无法使用ReMeMemory")
            memory = ReMeMemory(config)
        else:
            raise ValueError(f"不支持的记忆提供者: {provider}")
        
        cls._memories[cache_key] = memory
        return memory
    
    @classmethod
    def set_provider(cls, provider: MemoryProvider):
        """设置当前提供者"""
        cls._current_provider = provider
    
    @classmethod
    def get_current_provider(cls) -> MemoryProvider:
        """获取当前提供者"""
        return cls._current_provider
    
    @classmethod
    def clear_cache(cls):
        """清除缓存"""
        cls._memories.clear()


def create_memory(
    provider: Optional[str] = None,
    config: Optional[ReMeConfig] = None,
):
    """
    创建记忆管理器（便捷函数）
    
    Args:
        provider: 提供者名称（字符串）
        config: 记忆配置
        
    Returns:
        记忆管理器实例
    """
    if provider is None:
        provider_enum = None
    else:
        provider_enum = MemoryProvider(provider)
    
    return MemoryFactory.create_memory(provider_enum, config)


def get_memory() -> ShortTermMemory | ReMeMemory:
    """
    获取当前记忆管理器（单例）
    
    Returns:
        当前配置的记忆管理器
    """
    return MemoryFactory.create_memory()
