"""
工具索引器 - Tool Indexer

将工具定义向量化并构建索引，支持基于语义相似度的工具检索。

核心功能：
1. 工具定义向量化（使用简单的TF-IDF或字符频率向量）
2. 工具索引构建（支持类别分组）
3. 索引持久化与加载
"""

from __future__ import annotations

import json
import math
import pickle
import re
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from opspilot.tools.base import ToolSchema
from opspilot.utils.exceptions import ToolError


class ToolCategory(Enum):
    """工具类别"""
    ERP = "erp"                    # 企业资源计划
    COMPLIANCE = "compliance"      # 合规检查
    QUERY = "query"                # 查询类
    ACTION = "action"              # 操作类
    CALCULATION = "calculation"    # 计算类
    VALIDATION = "validation"      # 验证类
    INTERNAL = "internal"          # 内部工具
    EXTERNAL = "external"          # 外部服务
    UNKNOWN = "unknown"            # 未知类别


@dataclass
class ToolEmbedding:
    """工具向量表示"""
    tool_name: str
    category: ToolCategory
    embedding: List[float]
    keywords: Set[str]
    description_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "tool_name": self.tool_name,
            "category": self.category.value,
            "embedding": self.embedding,
            "keywords": list(self.keywords),
            "description_text": self.description_text,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ToolEmbedding:
        """从字典反序列化"""
        return cls(
            tool_name=data["tool_name"],
            category=ToolCategory(data["category"]),
            embedding=data["embedding"],
            keywords=set(data["keywords"]),
            description_text=data["description_text"],
            metadata=data.get("metadata", {}),
        )


@dataclass
class ToolIndex:
    """工具索引"""
    embeddings: List[ToolEmbedding]
    vocabulary: Dict[str, int]  # 词到索引的映射
    idf_scores: Dict[str, float]  # 逆文档频率
    category_index: Dict[ToolCategory, List[int]]  # 类别到工具索引的映射
    keyword_index: Dict[str, List[int]]  # 关键词到工具索引的映射
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "embeddings": [e.to_dict() for e in self.embeddings],
            "vocabulary": self.vocabulary,
            "idf_scores": self.idf_scores,
            "category_index": {k.value: v for k, v in self.category_index.items()},
            "keyword_index": self.keyword_index,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ToolIndex:
        """从字典反序列化"""
        return cls(
            embeddings=[ToolEmbedding.from_dict(e) for e in data["embeddings"]],
            vocabulary=data["vocabulary"],
            idf_scores=data["idf_scores"],
            category_index={ToolCategory(k): v for k, v in data["category_index"].items()},
            keyword_index=data["keyword_index"],
        )


class SimpleTokenizer:
    """简单分词器"""
    
    # 停用词
    STOP_WORDS = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "need", "dare",
        "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
        "into", "through", "during", "before", "after", "above", "below",
        "between", "under", "again", "further", "then", "once", "here",
        "there", "when", "where", "why", "how", "all", "each", "few",
        "more", "most", "other", "some", "such", "no", "nor", "not",
        "only", "own", "same", "so", "than", "too", "very", "just",
        "and", "but", "if", "or", "because", "until", "while",
        "的", "是", "在", "有", "和", "了", "不", "这", "个", "也",
        "就", "人", "都", "一", "一个", "上", "也", "很", "到",
        "说", "要", "去", "你", "会", "着", "没有", "看", "好",
    }
    
    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        """分词"""
        # 转小写
        text = text.lower()
        
        # 提取英文单词
        english_words = re.findall(r'[a-z_]+', text)
        
        # 提取中文词（简单按字符分割）
        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', text)
        
        # 提取数字
        numbers = re.findall(r'\d+', text)
        
        # 合并并过滤停用词
        tokens = []
        for word in english_words:
            if word not in cls.STOP_WORDS and len(word) > 1:
                tokens.append(word)
        
        for chars in chinese_chars:
            # 中文按字符分割
            for char in chars:
                tokens.append(char)
        
        tokens.extend(numbers)
        
        return tokens
    
    @classmethod
    def extract_keywords(cls, text: str, top_k: int = 10) -> Set[str]:
        """提取关键词"""
        tokens = cls.tokenize(text)
        counter = Counter(tokens)
        return set(word for word, _ in counter.most_common(top_k))


class ToolIndexer:
    """
    工具索引器
    
    使用TF-IDF向量化工具描述，构建支持语义检索的索引。
    
    示例:
        >>> indexer = ToolIndexer()
        >>> indexer.add_tool(tool_schema)
        >>> index = indexer.build_index()
        >>> indexer.save_index(index, "tools_index.pkl")
    """
    
    # 工具类别关键词映射
    CATEGORY_KEYWORDS = {
        ToolCategory.ERP: {"supplier", "order", "inventory", "erp", "采购", "订单", "库存", "供应商"},
        ToolCategory.COMPLIANCE: {"compliance", "policy", "check", "regulation", "合规", "政策", "检查"},
        ToolCategory.QUERY: {"query", "get", "fetch", "retrieve", "find", "search", "查询", "获取"},
        ToolCategory.ACTION: {"create", "update", "delete", "submit", "execute", "创建", "更新", "删除"},
        ToolCategory.CALCULATION: {"calculate", "compute", "sum", "total", "计算", "统计"},
        ToolCategory.VALIDATION: {"validate", "verify", "check", "confirm", "验证", "校验"},
        ToolCategory.INTERNAL: {"format", "parse", "convert", "internal", "格式化", "转换"},
        ToolCategory.EXTERNAL: {"api", "service", "external", "外部", "接口"},
    }
    
    def __init__(self, embedding_dim: int = 256):
        """
        初始化索引器
        
        Args:
            embedding_dim: 向量维度
        """
        self.embedding_dim = embedding_dim
        self.tools: List[ToolSchema] = []
        self.tool_embeddings: List[ToolEmbedding] = []
        self.vocabulary: Dict[str, int] = {}
        self.idf_scores: Dict[str, float] = {}
    
    def add_tool(self, tool: ToolSchema) -> None:
        """添加工具"""
        self.tools.append(tool)
    
    def add_tools(self, tools: List[ToolSchema]) -> None:
        """批量添加工具"""
        self.tools.extend(tools)
    
    def _classify_tool(self, tool: ToolSchema) -> ToolCategory:
        """分类工具"""
        text = f"{tool.name} {tool.description}".lower()
        
        scores = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            scores[category] = score
        
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return ToolCategory.UNKNOWN
    
    def _extract_tool_text(self, tool: ToolSchema) -> str:
        """提取工具文本信息"""
        parts = [tool.name, tool.description]
        
        # 添加参数信息
        if tool.input_schema:
            params = tool.input_schema
            if isinstance(params, dict):
                props = params.get("properties", {})
                for prop_name, prop_info in props.items():
                    parts.append(prop_name)
                    if isinstance(prop_info, dict):
                        parts.append(prop_info.get("description", ""))
        
        return " ".join(parts)
    
    def _build_vocabulary(self) -> None:
        """构建词汇表"""
        all_tokens = set()
        doc_freq = Counter()
        
        for tool in self.tools:
            text = self._extract_tool_text(tool)
            tokens = set(SimpleTokenizer.tokenize(text))
            all_tokens.update(tokens)
            doc_freq.update(tokens)
        
        # 构建词汇表
        self.vocabulary = {token: idx for idx, token in enumerate(sorted(all_tokens))}
        
        # 计算IDF
        n_docs = len(self.tools)
        self.idf_scores = {
            token: math.log((n_docs + 1) / (freq + 1)) + 1
            for token, freq in doc_freq.items()
        }
    
    def _compute_embedding(self, text: str) -> List[float]:
        """
        计算文本的TF-IDF向量
        
        为了生成固定维度的向量，使用哈希技巧：
        - 将词哈希到固定维度空间
        - 累加TF-IDF权重
        """
        tokens = SimpleTokenizer.tokenize(text)
        tf = Counter(tokens)
        
        # 初始化向量
        embedding = [0.0] * self.embedding_dim
        
        # 使用哈希技巧映射到固定维度
        for token, freq in tf.items():
            # 计算TF-IDF
            tf_score = 1 + math.log(freq)
            idf_score = self.idf_scores.get(token, 1.0)
            tfidf = tf_score * idf_score
            
            # 哈希到向量位置
            hash_val = hash(token)
            idx = abs(hash_val) % self.embedding_dim
            
            # 累加权重
            embedding[idx] += tfidf
        
        # L2归一化
        norm = math.sqrt(sum(x * x for x in embedding))
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
    
    def _build_keyword_index(self) -> Dict[str, List[int]]:
        """构建关键词索引"""
        keyword_index: Dict[str, List[int]] = {}
        
        for idx, embedding in enumerate(self.tool_embeddings):
            for keyword in embedding.keywords:
                if keyword not in keyword_index:
                    keyword_index[keyword] = []
                keyword_index[keyword].append(idx)
        
        return keyword_index
    
    def build_index(self) -> ToolIndex:
        """
        构建工具索引
        
        Returns:
            ToolIndex: 构建好的索引
        """
        # 构建词汇表
        self._build_vocabulary()
        
        # 为每个工具生成向量
        self.tool_embeddings = []
        for tool in self.tools:
            text = self._extract_tool_text(tool)
            embedding = self._compute_embedding(text)
            keywords = SimpleTokenizer.extract_keywords(text)
            category = self._classify_tool(tool)
            
            tool_embedding = ToolEmbedding(
                tool_name=tool.name,
                category=category,
                embedding=embedding,
                keywords=keywords,
                description_text=text,
                metadata={
                    "description": tool.description[:200],
                    "timeout": tool.timeout_seconds,
                }
            )
            self.tool_embeddings.append(tool_embedding)
        
        # 构建类别索引
        category_index: Dict[ToolCategory, List[int]] = {
            cat: [] for cat in ToolCategory
        }
        for idx, emb in enumerate(self.tool_embeddings):
            category_index[emb.category].append(idx)
        
        # 构建关键词索引
        keyword_index = self._build_keyword_index()
        
        return ToolIndex(
            embeddings=self.tool_embeddings,
            vocabulary=self.vocabulary,
            idf_scores=self.idf_scores,
            category_index=category_index,
            keyword_index=keyword_index,
        )
    
    def save_index(self, index: ToolIndex, path: str | Path) -> None:
        """保存索引到文件"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "wb") as f:
            pickle.dump(index.to_dict(), f)
    
    def load_index(self, path: str | Path) -> ToolIndex:
        """从文件加载索引"""
        with open(path, "rb") as f:
            data = pickle.load(f)
        return ToolIndex.from_dict(data)


# 便捷函数
def create_tool_index(tools: List[ToolSchema], embedding_dim: int = 256) -> ToolIndex:
    """
    创建工具索引的便捷函数
    
    Args:
        tools: 工具列表
        embedding_dim: 向量维度
    
    Returns:
        ToolIndex: 构建好的索引
    """
    indexer = ToolIndexer(embedding_dim=embedding_dim)
    indexer.add_tools(tools)
    return indexer.build_index()

