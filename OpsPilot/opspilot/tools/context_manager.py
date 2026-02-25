"""
工具上下文管理器 - Tool Context Manager

整合工具检索、压缩和上下文预算管理，提供完整的工具选择流程。

核心功能：
1. 统一的工具选择接口
2. 自动检索相关工具
3. 自动压缩适应上下文
4. 缓存机制
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from opspilot.tools.base import ToolSchema
from opspilot.tools.indexer import ToolIndex, create_tool_index
from opspilot.tools.retriever import (
    ToolRetriever,
    RetrievalResult,
    RetrievalStrategy,
    ToolContextBudget,
)
from opspilot.tools.compressor import (
    ToolCompressor,
    CompressedTool,
    CompressionLevel,
    get_compression_stats,
)


@dataclass
class ToolSelectionResult:
    """工具选择结果"""
    selected_tools: List[ToolSchema]
    compressed_tools: List[CompressedTool]
    retrieval_results: List[RetrievalResult]
    total_tokens: int
    original_tokens: int
    compression_stats: Dict[str, Any]
    query_hash: str
    elapsed_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected_count": len(self.selected_tools),
            "total_tokens": self.total_tokens,
            "original_tokens": self.original_tokens,
            "saved_tokens": self.original_tokens - self.total_tokens,
            "compression_ratio": self.compression_stats.get("compression_ratio", 0),
            "query_hash": self.query_hash,
            "elapsed_ms": self.elapsed_ms,
        }


@dataclass
class CacheEntry:
    """缓存条目"""
    result: ToolSelectionResult
    timestamp: float
    hits: int = 0


class ToolContextManager:
    """
    工具上下文管理器
    
    整合检索、压缩、预算管理，提供一站式工具选择服务。
    
    示例:
        >>> manager = ToolContextManager(tools_dict)
        >>> result = manager.select_tools("查询供应商信息")
        >>> tools_for_llm = result.compressed_tools
    """
    
    # 默认配置
    DEFAULT_MAX_TOKENS = 2000
    DEFAULT_TOP_K = 20
    DEFAULT_CACHE_TTL = 300  # 5分钟
    
    def __init__(
        self,
        tools_dict: Dict[str, ToolSchema],
        index: Optional[ToolIndex] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        default_top_k: int = DEFAULT_TOP_K,
        default_strategy: RetrievalStrategy = RetrievalStrategy.HYBRID,
        default_compression: CompressionLevel = CompressionLevel.MODERATE,
        enable_cache: bool = True,
        cache_ttl: int = DEFAULT_CACHE_TTL,
    ):
        """
        初始化上下文管理器
        
        Args:
            tools_dict: 工具名称到定义的映射
            index: 工具索引（可选，不传则自动构建）
            max_tokens: 最大token预算
            default_top_k: 默认检索数量
            default_strategy: 默认检索策略
            default_compression: 默认压缩级别
            enable_cache: 是否启用缓存
            cache_ttl: 缓存过期时间（秒）
        """
        self.tools_dict = tools_dict
        self.max_tokens = max_tokens
        self.default_top_k = default_top_k
        self.default_strategy = default_strategy
        self.default_compression = default_compression
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl
        
        # 构建或使用索引
        if index is None:
            self.index = create_tool_index(list(tools_dict.values()))
        else:
            self.index = index
        
        # 初始化组件
        self.retriever = ToolRetriever(self.index)
        self.compressor = ToolCompressor()
        self.budget = ToolContextBudget(max_tokens=max_tokens)
        
        # 缓存
        self._cache: Dict[str, CacheEntry] = {}
    
    def _compute_query_hash(self, query: str, **kwargs) -> str:
        """计算查询哈希"""
        key = f"{query}|{kwargs}"
        return hashlib.md5(key.encode()).hexdigest()[:16]
    
    def _check_cache(self, query_hash: str) -> Optional[ToolSelectionResult]:
        """检查缓存"""
        if not self.enable_cache:
            return None
        
        entry = self._cache.get(query_hash)
        if entry:
            # 检查是否过期
            if time.time() - entry.timestamp < self.cache_ttl:
                entry.hits += 1
                return entry.result
            else:
                # 删除过期缓存
                del self._cache[query_hash]
        
        return None
    
    def _update_cache(self, query_hash: str, result: ToolSelectionResult) -> None:
        """更新缓存"""
        if self.enable_cache:
            self._cache[query_hash] = CacheEntry(
                result=result,
                timestamp=time.time(),
            )
    
    def select_tools(
        self,
        query: str,
        top_k: Optional[int] = None,
        strategy: Optional[RetrievalStrategy] = None,
        compression: Optional[CompressionLevel] = None,
        max_tokens: Optional[int] = None,
        category_filter: Optional[List[str]] = None,
    ) -> ToolSelectionResult:
        """
        选择工具
        
        完整流程：
        1. 检查缓存
        2. 检索相关工具
        3. 应用上下文预算
        4. 压缩工具描述
        5. 更新缓存
        
        Args:
            query: 用户查询
            top_k: 检索数量
            strategy: 检索策略
            compression: 压缩级别
            max_tokens: 最大token数
            category_filter: 类别过滤
        
        Returns:
            工具选择结果
        """
        start_time = time.time()
        
        # 使用默认值
        top_k = top_k or self.default_top_k
        strategy = strategy or self.default_strategy
        compression = compression or self.default_compression
        max_tokens = max_tokens or self.max_tokens
        
        # 计算查询哈希
        query_hash = self._compute_query_hash(
            query, top_k, strategy.value, compression.value, max_tokens
        )
        
        # 检查缓存
        cached = self._check_cache(query_hash)
        if cached:
            cached.elapsed_ms = (time.time() - start_time) * 1000
            return cached
        
        # 检索工具
        retrieval_results = self.retriever.retrieve(
            query,
            top_k=top_k,
            strategy=strategy,
        )
        
        # 获取工具定义
        tools = self.retriever.get_tool_schemas(retrieval_results, self.tools_dict)
        
        # 应用上下文预算
        selected_tools, estimated_tokens = self.budget.select_tools(
            tools, retrieval_results
        )
        
        # 压缩工具
        compressed_tools = self.compressor.batch_compress(selected_tools, compression)
        
        # 计算实际token
        total_tokens = sum(c.compressed_tokens for c in compressed_tools)
        original_tokens = sum(c.original_tokens for c in compressed_tools)
        
        # 压缩统计
        stats = get_compression_stats(compressed_tools)
        
        # 创建结果
        result = ToolSelectionResult(
            selected_tools=selected_tools,
            compressed_tools=compressed_tools,
            retrieval_results=retrieval_results,
            total_tokens=total_tokens,
            original_tokens=original_tokens,
            compression_stats=stats,
            query_hash=query_hash,
            elapsed_ms=(time.time() - start_time) * 1000,
        )
        
        # 更新缓存
        self._update_cache(query_hash, result)
        
        return result
    
    def get_tools_for_llm(
        self,
        query: str,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        获取供LLM使用的工具定义（OpenAI格式）
        
        Args:
            query: 用户查询
            **kwargs: 其他参数
        
        Returns:
            OpenAI格式的工具定义列表
        """
        result = self.select_tools(query, **kwargs)
        return [c.to_openai_format() for c in result.compressed_tools]
    
    def get_tool_by_name(self, name: str) -> Optional[ToolSchema]:
        """按名称获取工具"""
        return self.tools_dict.get(name)
    
    def get_all_tool_names(self) -> List[str]:
        """获取所有工具名称"""
        return list(self.tools_dict.keys())
    
    def get_tool_count(self) -> int:
        """获取工具总数"""
        return len(self.tools_dict)
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        if not self._cache:
            return {"entries": 0, "total_hits": 0}
        
        total_hits = sum(e.hits for e in self._cache.values())
        return {
            "entries": len(self._cache),
            "total_hits": total_hits,
            "entries_detail": [
                {
                    "query_hash": h,
                    "hits": e.hits,
                    "age_seconds": time.time() - e.timestamp,
                }
                for h, e in self._cache.items()
            ],
        }
    
    def update_max_tokens(self, max_tokens: int) -> None:
        """更新最大token预算"""
        self.max_tokens = max_tokens
        self.budget = ToolContextBudget(max_tokens=max_tokens)
        self.clear_cache()  # 清空缓存以应用新设置
    
    def add_tool(self, tool: ToolSchema) -> None:
        """添加新工具"""
        self.tools_dict[tool.name] = tool
        # 需要重建索引
        self.index = create_tool_index(list(self.tools_dict.values()))
        self.retriever = ToolRetriever(self.index)
        self.clear_cache()
    
    def remove_tool(self, name: str) -> bool:
        """移除工具"""
        if name in self.tools_dict:
            del self.tools_dict[name]
            # 需要重建索引
            self.index = create_tool_index(list(self.tools_dict.values()))
            self.retriever = ToolRetriever(self.index)
            self.clear_cache()
            return True
        return False


class DynamicToolLoader:
    """
    动态工具加载器
    
    支持按需加载工具，分阶段注入。
    """
    
    def __init__(
        self,
        context_manager: ToolContextManager,
        load_threshold: float = 0.5,  # 当token使用率低于此值时加载更多
    ):
        """
        初始化动态加载器
        
        Args:
            context_manager: 上下文管理器
            load_threshold: 加载阈值
        """
        self.context_manager = context_manager
        self.load_threshold = load_threshold
    
    def load_initial_tools(
        self,
        query: str,
        max_tokens: int = 1000,
    ) -> ToolSelectionResult:
        """加载初始工具集"""
        return self.context_manager.select_tools(
            query,
            max_tokens=max_tokens,
        )
    
    def load_additional_tools(
        self,
        query: str,
        current_tokens: int,
        max_tokens: int,
        exclude_names: Optional[List[str]] = None,
    ) -> List[CompressedTool]:
        """
        加载额外工具
        
        当上下文空间有富余时，加载更多工具。
        """
        remaining = max_tokens - current_tokens
        utilization = current_tokens / max_tokens
        
        if utilization > self.load_threshold:
            return []
        
        # 获取更多工具
        result = self.context_manager.select_tools(
            query,
            max_tokens=remaining,
        )
        
        # 排除已有的工具
        if exclude_names:
            return [
                c for c in result.compressed_tools
                if c.name not in exclude_names
            ]
        
        return result.compressed_tools


# 便捷函数
def create_context_manager(
    tools: List[ToolSchema],
    max_tokens: int = 2000,
) -> ToolContextManager:
    """
    创建上下文管理器的便捷函数
    
    Args:
        tools: 工具列表
        max_tokens: 最大token预算
    
    Returns:
        配置好的上下文管理器
    """
    tools_dict = {t.name: t for t in tools}
    return ToolContextManager(tools_dict, max_tokens=max_tokens)

