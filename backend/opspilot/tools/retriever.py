"""
工具检索器 - Tool Retriever

基于查询检索相关工具，支持两级检索（类别→工具）和混合检索策略。

核心功能：
1. 语义相似度检索
2. 关键词匹配检索
3. 两级检索机制
4. 上下文预算约束
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from opspilot.tools.base import ToolSchema
from opspilot.tools.indexer import (
    ToolIndex,
    ToolEmbedding,
    ToolCategory,
    SimpleTokenizer,
)


class RetrievalStrategy(Enum):
    """检索策略"""
    SEMANTIC = "semantic"      # 语义相似度
    KEYWORD = "keyword"        # 关键词匹配
    HYBRID = "hybrid"          # 混合检索
    TWO_LEVEL = "two_level"    # 两级检索


@dataclass
class RetrievalResult:
    """检索结果"""
    tool_name: str
    relevance_score: float
    category: ToolCategory
    match_type: str  # "semantic", "keyword", "category"
    matched_keywords: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "relevance_score": self.relevance_score,
            "category": self.category.value,
            "match_type": self.match_type,
            "matched_keywords": self.matched_keywords,
            "metadata": self.metadata,
        }


@dataclass
class CategoryScore:
    """类别得分"""
    category: ToolCategory
    score: float
    matched_tools: int


class ToolRetriever:
    """
    工具检索器
    
    支持多种检索策略：
    - 语义检索：基于向量相似度
    - 关键词检索：基于关键词匹配
    - 混合检索：结合语义和关键词
    - 两级检索：先检索类别，再检索工具
    
    示例:
        >>> retriever = ToolRetriever(index)
        >>> results = retriever.retrieve("查询供应商信息", top_k=5)
        >>> tools = retriever.get_tools(results, tools_dict)
    """
    
    def __init__(
        self,
        index: ToolIndex,
        embedding_dim: int = 256,
    ):
        """
        初始化检索器
        
        Args:
            index: 工具索引
            embedding_dim: 向量维度
        """
        self.index = index
        self.embedding_dim = embedding_dim
        self.tokenizer = SimpleTokenizer()
    
    def _compute_query_embedding(self, query: str) -> List[float]:
        """计算查询的向量表示"""
        tokens = self.tokenizer.tokenize(query)
        tf = {token: 1 for token in tokens}  # 查询中每个词出现一次
        
        embedding = [0.0] * self.embedding_dim
        
        for token in tf:
            idf_score = self.index.idf_scores.get(token, 1.0)
            tfidf = idf_score
            
            hash_val = hash(token)
            idx = abs(hash_val) % self.embedding_dim
            embedding[idx] += tfidf
        
        # L2归一化
        norm = math.sqrt(sum(x * x for x in embedding))
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _semantic_search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
    ) -> List[Tuple[int, float]]:
        """
        语义相似度检索
        
        Returns:
            List of (index, score) tuples
        """
        scores = []
        for idx, tool_emb in enumerate(self.index.embeddings):
            score = self._cosine_similarity(query_embedding, tool_emb.embedding)
            scores.append((idx, score))
        
        # 按分数降序排序
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
    
    def _keyword_search(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[Tuple[int, float, List[str]]]:
        """
        关键词匹配检索
        
        Returns:
            List of (index, score, matched_keywords) tuples
        """
        query_tokens = set(self.tokenizer.tokenize(query))
        
        results = []
        for idx, tool_emb in enumerate(self.index.embeddings):
            # 计算匹配的关键词
            matched = query_tokens & tool_emb.keywords
            
            if matched:
                # 得分 = 匹配关键词数量 / 查询词数
                score = len(matched) / max(len(query_tokens), 1)
                results.append((idx, score, list(matched)))
        
        # 按分数降序排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def _retrieve_categories(
        self,
        query: str,
        top_k: int = 3,
    ) -> List[CategoryScore]:
        """
        检索相关类别（第一级检索）
        
        根据查询匹配每个类别中的工具数量来评估类别相关性
        """
        query_tokens = set(self.tokenizer.tokenize(query))
        
        category_scores = []
        for category, tool_indices in self.index.category_index.items():
            if category == ToolCategory.UNKNOWN:
                continue
            
            matched_tools = 0
            for idx in tool_indices:
                tool_emb = self.index.embeddings[idx]
                if query_tokens & tool_emb.keywords:
                    matched_tools += 1
            
            if matched_tools > 0:
                score = matched_tools / max(len(tool_indices), 1)
                category_scores.append(CategoryScore(
                    category=category,
                    score=score,
                    matched_tools=matched_tools,
                ))
        
        # 按分数降序排序
        category_scores.sort(key=lambda x: x.score, reverse=True)
        return category_scores[:top_k]
    
    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        strategy: RetrievalStrategy = RetrievalStrategy.HYBRID,
        category_filter: Optional[List[ToolCategory]] = None,
    ) -> List[RetrievalResult]:
        """
        检索相关工具
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            strategy: 检索策略
            category_filter: 类别过滤器
        
        Returns:
            检索结果列表
        """
        if strategy == RetrievalStrategy.SEMANTIC:
            return self._semantic_retrieve(query, top_k, category_filter)
        elif strategy == RetrievalStrategy.KEYWORD:
            return self._keyword_retrieve(query, top_k, category_filter)
        elif strategy == RetrievalStrategy.TWO_LEVEL:
            return self._two_level_retrieve(query, top_k)
        else:  # HYBRID
            return self._hybrid_retrieve(query, top_k, category_filter)
    
    def _semantic_retrieve(
        self,
        query: str,
        top_k: int,
        category_filter: Optional[List[ToolCategory]] = None,
    ) -> List[RetrievalResult]:
        """语义检索"""
        query_embedding = self._compute_query_embedding(query)
        
        # 应用类别过滤
        candidates = self.index.embeddings
        if category_filter:
            candidates = [
                emb for emb in self.index.embeddings
                if emb.category in category_filter
            ]
        
        scores = []
        for idx, tool_emb in enumerate(candidates):
            actual_idx = self.index.embeddings.index(tool_emb)
            score = self._cosine_similarity(query_embedding, tool_emb.embedding)
            scores.append((actual_idx, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, score in scores[:top_k]:
            tool_emb = self.index.embeddings[idx]
            results.append(RetrievalResult(
                tool_name=tool_emb.tool_name,
                relevance_score=score,
                category=tool_emb.category,
                match_type="semantic",
                metadata=tool_emb.metadata,
            ))
        
        return results
    
    def _keyword_retrieve(
        self,
        query: str,
        top_k: int,
        category_filter: Optional[List[ToolCategory]] = None,
    ) -> List[RetrievalResult]:
        """关键词检索"""
        keyword_results = self._keyword_search(query, top_k * 2)
        
        results = []
        for idx, score, matched_kw in keyword_results:
            tool_emb = self.index.embeddings[idx]
            
            # 应用类别过滤
            if category_filter and tool_emb.category not in category_filter:
                continue
            
            results.append(RetrievalResult(
                tool_name=tool_emb.tool_name,
                relevance_score=score,
                category=tool_emb.category,
                match_type="keyword",
                matched_keywords=matched_kw,
                metadata=tool_emb.metadata,
            ))
            
            if len(results) >= top_k:
                break
        
        return results
    
    def _hybrid_retrieve(
        self,
        query: str,
        top_k: int,
        category_filter: Optional[List[ToolCategory]] = None,
    ) -> List[RetrievalResult]:
        """
        混合检索
        
        结合语义相似度和关键词匹配：
        final_score = α * semantic_score + (1-α) * keyword_score
        """
        alpha = 0.6  # 语义权重
        
        # 获取语义检索结果
        query_embedding = self._compute_query_embedding(query)
        semantic_scores = {}
        for idx, tool_emb in enumerate(self.index.embeddings):
            score = self._cosine_similarity(query_embedding, tool_emb.embedding)
            semantic_scores[idx] = score
        
        # 获取关键词检索结果
        keyword_scores = {}
        keyword_matches = {}
        query_tokens = set(self.tokenizer.tokenize(query))
        for idx, tool_emb in enumerate(self.index.embeddings):
            matched = query_tokens & tool_emb.keywords
            if matched:
                keyword_scores[idx] = len(matched) / max(len(query_tokens), 1)
                keyword_matches[idx] = list(matched)
        
        # 合并分数
        all_indices = set(semantic_scores.keys()) | set(keyword_scores.keys())
        combined_scores = []
        
        for idx in all_indices:
            tool_emb = self.index.embeddings[idx]
            
            # 应用类别过滤
            if category_filter and tool_emb.category not in category_filter:
                continue
            
            sem_score = semantic_scores.get(idx, 0.0)
            kw_score = keyword_scores.get(idx, 0.0)
            
            final_score = alpha * sem_score + (1 - alpha) * kw_score
            
            combined_scores.append((
                idx,
                final_score,
                keyword_matches.get(idx, []),
            ))
        
        # 排序并返回
        combined_scores.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, score, matched_kw in combined_scores[:top_k]:
            tool_emb = self.index.embeddings[idx]
            results.append(RetrievalResult(
                tool_name=tool_emb.tool_name,
                relevance_score=score,
                category=tool_emb.category,
                match_type="hybrid",
                matched_keywords=matched_kw,
                metadata=tool_emb.metadata,
            ))
        
        return results
    
    def _two_level_retrieve(
        self,
        query: str,
        top_k: int,
    ) -> List[RetrievalResult]:
        """
        两级检索
        
        第一级：检索相关类别
        第二级：在相关类别内检索工具
        """
        # 第一级：检索类别
        category_scores = self._retrieve_categories(query, top_k=3)
        
        if not category_scores:
            # 如果没有匹配的类别，退化为混合检索
            return self._hybrid_retrieve(query, top_k)
        
        # 获取相关类别的工具索引
        relevant_indices = []
        for cat_score in category_scores:
            relevant_indices.extend(self.index.category_index[cat_score.category])
        
        # 在相关类别内进行混合检索
        query_embedding = self._compute_query_embedding(query)
        query_tokens = set(self.tokenizer.tokenize(query))
        
        results = []
        for idx in relevant_indices:
            tool_emb = self.index.embeddings[idx]
            
            # 计算语义分数
            sem_score = self._cosine_similarity(query_embedding, tool_emb.embedding)
            
            # 计算关键词分数
            matched = query_tokens & tool_emb.keywords
            kw_score = len(matched) / max(len(query_tokens), 1)
            
            # 合并分数
            final_score = 0.6 * sem_score + 0.4 * kw_score
            
            results.append(RetrievalResult(
                tool_name=tool_emb.tool_name,
                relevance_score=final_score,
                category=tool_emb.category,
                match_type="two_level",
                matched_keywords=list(matched),
                metadata=tool_emb.metadata,
            ))
        
        # 排序并返回
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:top_k]
    
    def get_tool_schemas(
        self,
        results: List[RetrievalResult],
        tools_dict: Dict[str, ToolSchema],
    ) -> List[ToolSchema]:
        """
        从检索结果获取工具定义
        
        Args:
            results: 检索结果
            tools_dict: 工具名称到工具定义的映射
        
        Returns:
            工具定义列表
        """
        schemas = []
        for result in results:
            if result.tool_name in tools_dict:
                schemas.append(tools_dict[result.tool_name])
        return schemas
    
    def get_tool_names(self, results: List[RetrievalResult]) -> List[str]:
        """获取检索结果的工具名称列表"""
        return [r.tool_name for r in results]


class ToolContextBudget:
    """
    工具上下文预算管理
    
    控制传递给LLM的工具定义总token数，避免上下文溢出。
    """
    
    # 默认预算
    DEFAULT_MAX_TOKENS = 2000
    DEFAULT_TOOL_TOKENS = 100  # 每个工具的预估token数
    
    def __init__(
        self,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        tool_token_estimator: Optional[callable] = None,
    ):
        """
        初始化上下文预算
        
        Args:
            max_tokens: 最大token数
            tool_token_estimator: 工具token估算函数
        """
        self.max_tokens = max_tokens
        self.tool_token_estimator = tool_token_estimator or self._default_estimator
    
    def _default_estimator(self, tool: ToolSchema) -> int:
        """默认的token估算器"""
        # 简单估算：描述长度 / 4 + 参数数量 * 20
        desc_tokens = len(tool.description) // 4
        
        param_count = 0
        if tool.input_schema and isinstance(tool.input_schema, dict):
            props = tool.input_schema.get("properties", {})
            param_count = len(props)
        
        return desc_tokens + param_count * 20 + self.DEFAULT_TOOL_TOKENS
    
    def select_tools(
        self,
        tools: List[ToolSchema],
        retrieval_results: List[RetrievalResult],
    ) -> Tuple[List[ToolSchema], int]:
        """
        选择工具，确保不超过上下文预算
        
        Args:
            tools: 候选工具列表
            retrieval_results: 检索结果（用于排序）
        
        Returns:
            (选中的工具列表, 总token数)
        """
        # 按相关性排序工具
        relevance_map = {r.tool_name: r.relevance_score for r in retrieval_results}
        sorted_tools = sorted(
            tools,
            key=lambda t: relevance_map.get(t.name, 0),
            reverse=True,
        )
        
        selected = []
        total_tokens = 0
        
        for tool in sorted_tools:
            tool_tokens = self.tool_token_estimator(tool)
            
            if total_tokens + tool_tokens <= self.max_tokens:
                selected.append(tool)
                total_tokens += tool_tokens
            else:
                # 达到预算上限
                break
        
        return selected, total_tokens
    
    def estimate_total_tokens(self, tools: List[ToolSchema]) -> int:
        """估算工具列表的总token数"""
        return sum(self.tool_token_estimator(t) for t in tools)
    
    def can_add_tool(
        self,
        current_tokens: int,
        tool: ToolSchema,
    ) -> bool:
        """检查是否可以添加工具"""
        tool_tokens = self.tool_token_estimator(tool)
        return current_tokens + tool_tokens <= self.max_tokens


# 便捷函数
def retrieve_tools(
    query: str,
    index: ToolIndex,
    tools_dict: Dict[str, ToolSchema],
    top_k: int = 10,
    strategy: RetrievalStrategy = RetrievalStrategy.HYBRID,
    max_tokens: int = 2000,
) -> List[ToolSchema]:
    """
    检索工具的便捷函数
    
    Args:
        query: 查询文本
        index: 工具索引
        tools_dict: 工具名称到定义的映射
        top_k: 最大返回数量
        strategy: 检索策略
        max_tokens: 最大token预算
    
    Returns:
        选中的工具列表
    """
    retriever = ToolRetriever(index)
    results = retriever.retrieve(query, top_k, strategy)
    tools = retriever.get_tool_schemas(results, tools_dict)
    
    # 应用上下文预算
    budget = ToolContextBudget(max_tokens=max_tokens)
    selected, _ = budget.select_tools(tools, results)
    
    return selected

