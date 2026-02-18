"""
LLM 可靠性机制

使用 LangChain 的 with_retry 和 with_fallbacks 实现可靠的 LLM 调用。

特性：
- 自动重试（指数退避）
- 多模型降级
- 统一的错误处理
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

# LangChain imports
try:
    from langchain_core.language_models import BaseLanguageModel
    from langchain_core.runnables import Runnable, RunnableLambda
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseLanguageModel = None
    Runnable = None
    RunnableLambda = None
    ChatPromptTemplate = None
    StrOutputParser = None

logger = logging.getLogger(__name__)

T = TypeVar("T")


class FallbackStrategy(str, Enum):
    """降级策略"""
    SEQUENTIAL = "sequential"  # 顺序降级
    PARALLEL = "parallel"      # 并行尝试，取最快
    PRIORITY = "priority"      # 按优先级降级


@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3
    wait_exponential: bool = True
    min_wait: float = 1.0
    max_wait: float = 60.0
    jitter: bool = True  # 添加随机抖动
    
    # 重试特定异常
    retry_exceptions: tuple = (
        ConnectionError,
        TimeoutError,
    )
    
    def to_langchain_config(self) -> Dict[str, Any]:
        """转换为 LangChain 配置"""
        return {
            "stop_after_attempt": self.max_attempts,
            "wait_exponential_jitter": self.wait_exponential and self.jitter,
        }


@dataclass
class FallbackConfig:
    """降级配置"""
    strategy: FallbackStrategy = FallbackStrategy.SEQUENTIAL
    timeout: float = 30.0
    
    # 降级 LLM 配置列表（按优先级排序）
    fallback_llms: List[Dict[str, Any]] = field(default_factory=list)
    
    # 示例：
    # [
    #     {"provider": "openai", "model": "gpt-4", "priority": 1},
    #     {"provider": "openai", "model": "gpt-3.5-turbo", "priority": 2},
    #     {"provider": "ollama", "model": "llama3", "priority": 3},
    # ]


class ReliableLLMChain:
    """
    可靠的 LLM 链
    
    整合重试和降级机制，提供高可用的 LLM 调用。
    
    示例:
        >>> chain = ReliableLLMChain(
        ...     primary_llm=gpt4,
        ...     fallback_llms=[gpt35, local_llm],
        ...     retry_config=RetryConfig(max_attempts=3),
        ... )
        >>> result = await chain.ainvoke("查询供应商信息")
    """
    
    def __init__(
        self,
        primary_llm: "BaseLanguageModel",
        fallback_llms: Optional[List["BaseLanguageModel"]] = None,
        retry_config: Optional[RetryConfig] = None,
        fallback_config: Optional[FallbackConfig] = None,
        prompt_template: Optional[str] = None,
    ):
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain 未安装，请运行: pip install langchain-core")
        
        self._primary_llm = primary_llm
        self._fallback_llms = fallback_llms or []
        self._retry_config = retry_config or RetryConfig()
        self._fallback_config = fallback_config or FallbackConfig()
        self._prompt_template = prompt_template
        
        # 构建可靠的链
        self._chain = self._build_reliable_chain()
        
        # 统计
        self._stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "retried_calls": 0,
            "fallback_calls": 0,
            "failed_calls": 0,
        }
    
    def _build_reliable_chain(self) -> "Runnable":
        """构建可靠的链"""
        # 基础链
        if self._prompt_template:
            prompt = ChatPromptTemplate.from_template(self._prompt_template)
            base_chain = prompt | self._primary_llm | StrOutputParser()
        else:
            base_chain = RunnableLambda(lambda x: self._primary_llm.invoke(x))
        
        # 添加重试
        chain_with_retry = self._add_retry(base_chain)
        
        # 添加降级
        if self._fallback_llms:
            chain_with_fallback = self._add_fallback(chain_with_retry)
            return chain_with_fallback
        
        return chain_with_retry
    
    def _add_retry(self, chain: "Runnable") -> "Runnable":
        """添加重试机制"""
        return chain.with_retry(
            stop_after_attempt=self._retry_config.max_attempts,
            wait_exponential_jitter=self._retry_config.wait_exponential,
        )
    
    def _add_fallback(self, chain: "Runnable") -> "Runnable":
        """添加降级机制"""
        # 构建 fallback 链列表
        fallback_chains = []
        
        for llm in self._fallback_llms:
            if self._prompt_template:
                prompt = ChatPromptTemplate.from_template(self._prompt_template)
                fallback_chain = prompt | llm | StrOutputParser()
            else:
                fallback_chain = RunnableLambda(lambda x, l=llm: l.invoke(x))
            
            # 每个 fallback 也添加重试
            fallback_chain = fallback_chain.with_retry(
                stop_after_attempt=self._retry_config.max_attempts,
            )
            fallback_chains.append(fallback_chain)
        
        return chain.with_fallbacks(fallback_chains)
    
    async def ainvoke(
        self,
        input_data: Union[str, Dict[str, Any]],
        config: Optional[Dict] = None,
    ) -> str:
        """
        异步调用
        
        Args:
            input_data: 输入数据
            config: 配置选项
        
        Returns:
            str: LLM 输出
        """
        self._stats["total_calls"] += 1
        
        try:
            result = await self._chain.ainvoke(input_data, config=config)
            self._stats["successful_calls"] += 1
            return result
            
        except Exception as e:
            self._stats["failed_calls"] += 1
            logger.error(f"LLM call failed after all retries and fallbacks: {e}")
            raise
    
    def invoke(
        self,
        input_data: Union[str, Dict[str, Any]],
        config: Optional[Dict] = None,
    ) -> str:
        """同步调用"""
        self._stats["total_calls"] += 1
        
        try:
            result = self._chain.invoke(input_data, config=config)
            self._stats["successful_calls"] += 1
            return result
            
        except Exception as e:
            self._stats["failed_calls"] += 1
            logger.error(f"LLM call failed: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            "success_rate": (
                self._stats["successful_calls"] / self._stats["total_calls"]
                if self._stats["total_calls"] > 0 else 0
            ),
        }


# ============================================================================
# 便捷函数
# ============================================================================

def with_retry(
    chain: "Runnable",
    max_attempts: int = 3,
    wait_exponential: bool = True,
) -> "Runnable":
    """
    为链添加重试机制
    
    Args:
        chain: LangChain Runnable
        max_attempts: 最大尝试次数
        wait_exponential: 是否使用指数退避
    
    Returns:
        带重试机制的 Runnable
    
    示例:
        >>> chain = prompt | llm | parser
        >>> reliable_chain = with_retry(chain, max_attempts=3)
        >>> result = await reliable_chain.ainvoke("query")
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain 未安装")
    
    return chain.with_retry(
        stop_after_attempt=max_attempts,
        wait_exponential_jitter=wait_exponential,
    )


def with_fallbacks(
    primary_chain: "Runnable",
    fallback_chains: List["Runnable"],
    add_retry: bool = True,
    max_attempts: int = 2,
) -> "Runnable":
    """
    为链添加降级机制
    
    Args:
        primary_chain: 主链
        fallback_chains: 降级链列表
        add_retry: 是否为降级链添加重试
        max_attempts: 降级链的重试次数
    
    Returns:
        带降级机制的 Runnable
    
    示例:
        >>> primary = prompt | gpt4 | parser
        >>> fallback1 = prompt | gpt35 | parser
        >>> fallback2 = prompt | local_llm | parser
        >>> 
        >>> reliable_chain = with_fallbacks(primary, [fallback1, fallback2])
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain 未安装")
    
    if add_retry:
        fallback_chains = [
            c.with_retry(stop_after_attempt=max_attempts)
            for c in fallback_chains
        ]
    
    return primary_chain.with_fallbacks(fallback_chains)


def create_reliable_chain(
    llm: "BaseLanguageModel",
    prompt_template: str,
    fallback_llms: Optional[List["BaseLanguageModel"]] = None,
    retry_attempts: int = 3,
) -> ReliableLLMChain:
    """
    创建可靠的 LLM 链
    
    Args:
        llm: 主 LLM
        prompt_template: 提示模板
        fallback_llms: 降级 LLM 列表
        retry_attempts: 重试次数
    
    Returns:
        ReliableLLMChain 实例
    """
    return ReliableLLMChain(
        primary_llm=llm,
        fallback_llms=fallback_llms,
        retry_config=RetryConfig(max_attempts=retry_attempts),
        prompt_template=prompt_template,
    )
