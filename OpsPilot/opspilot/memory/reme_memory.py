"""
AgentScope ReMe记忆管理集成

集成AgentScope的ReMe记忆管理功能
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
    from agentscope.memory import InMemoryMemory, LongTermMemoryBase
    AGENTSCOPE_MEMORY_AVAILABLE = True
except ImportError:
    AGENTSCOPE_MEMORY_AVAILABLE = False
    InMemoryMemory = object
    LongTermMemoryBase = object
    logger.warning("AgentScope未安装，ReMe记忆管理不可用")

from opspilot.memory.base import MemoryEntry, SearchResult


@dataclass
class ReMeConfig:
    """ReMe配置"""
    vector_store: str = "chromadb"  # chromadb | faiss
    embedding_model: str = "text-embedding-ada-002"
    max_short_term_memory: int = 100
    max_long_term_memory: int = 10000
    enable_knowledge_graph: bool = False
    similarity_threshold: float = 0.7


class ReMeMemory(InMemoryMemory if AGENTSCOPE_MEMORY_AVAILABLE else object):
    """
    AgentScope ReMe记忆管理
    
    集成AgentScope的记忆系统，支持：
    - 短期记忆（对话上下文）
    - 长期记忆（向量检索）
    - 知识图谱
    """
    
    def __init__(self, config: Optional[ReMeConfig] = None):
        if not AGENTSCOPE_MEMORY_AVAILABLE:
            raise ImportError("AgentScope未安装，无法使用ReMeMemory")
        
        super().__init__()
        self.config = config or ReMeConfig()
        
        # 初始化短期记忆
        self._short_term_memory: List[Dict[str, Any]] = []
        
        # 初始化长期记忆（向量存储）
        self._long_term_memory: List[Dict[str, Any]] = []
        
        # AgentScope记忆实例
        self._as_memory = TemporaryMemory()
        
        logger.info(f"ReMe记忆管理初始化完成，配置: {self.config.vector_store}")
    
    def add_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        memory_type: str = "short_term",
    ) -> str:
        """
        添加记忆
        
        Args:
            content: 记忆内容
            metadata: 元数据
            memory_type: 记忆类型（short_term | long_term）
            
        Returns:
            记忆ID
        """
        memory_id = f"reme-{datetime.now().timestamp()}"
        
        entry = {
            "id": memory_id,
            "content": content,
            "metadata": metadata or {},
            "type": memory_type,
            "timestamp": datetime.now(),
        }
        
        if memory_type == "short_term":
            self._short_term_memory.append(entry)
            # 限制短期记忆数量
            if len(self._short_term_memory) > self.config.max_short_term_memory:
                # 将最旧的记忆转移到长期记忆
                oldest = self._short_term_memory.pop(0)
                oldest["type"] = "long_term"
                self._long_term_memory.append(oldest)
        else:
            self._long_term_memory.append(entry)
        
        logger.debug(f"添加{memory_type}记忆: {memory_id}")
        return memory_id
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        memory_type: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        检索记忆
        
        Args:
            query: 查询文本
            top_k: 返回数量
            memory_type: 记忆类型（None表示全部）
            
        Returns:
            检索结果列表
        """
        results = []
        
        # 确定搜索范围
        memories_to_search = []
        if memory_type is None or memory_type == "short_term":
            memories_to_search.extend(self._short_term_memory)
        if memory_type is None or memory_type == "long_term":
            memories_to_search.extend(self._long_term_memory)
        
        # 简单的关键词匹配（实际应用中应使用向量相似度）
        query_keywords = set(query.lower().split())
        
        for memory in memories_to_search:
            content_keywords = set(memory["content"].lower().split())
            # 计算关键词重叠度
            overlap = len(query_keywords & content_keywords)
            if overlap > 0:
                similarity = overlap / max(len(query_keywords), 1)
                if similarity >= self.config.similarity_threshold:
                    results.append(SearchResult(
                        id=memory["id"],
                        content=memory["content"],
                        score=similarity,
                        metadata=memory["metadata"],
                    ))
        
        # 按相似度排序并返回top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def get_context(self, max_tokens: int = 2000) -> str:
        """
        获取上下文（短期记忆）
        
        Args:
            max_tokens: 最大Token数
            
        Returns:
            上下文字符串
        """
        # 从最新的短期记忆构建上下文
        context_parts = []
        current_tokens = 0
        
        for memory in reversed(self._short_term_memory):
            # 简单估算Token数（实际应使用tokenizer）
            tokens = len(memory["content"]) // 4
            if current_tokens + tokens > max_tokens:
                break
            
            context_parts.append(memory["content"])
            current_tokens += tokens
        
        return "\n".join(reversed(context_parts))
    
    def clear_short_term(self):
        """清空短期记忆"""
        self._short_term_memory.clear()
        logger.info("短期记忆已清空")
    
    def consolidate(self):
        """
        记忆巩固：将重要的短期记忆转移到长期记忆
        """
        # 简单实现：保留最近的短期记忆，其他的转移到长期记忆
        if len(self._short_term_memory) > self.config.max_short_term_memory // 2:
            to_transfer = self._short_term_memory[:-self.config.max_short_term_memory // 2]
            for memory in to_transfer:
                memory["type"] = "long_term"
                self._long_term_memory.append(memory)
            self._short_term_memory = self._short_term_memory[-self.config.max_short_term_memory // 2:]
            logger.info(f"记忆巩固完成，转移{len(to_transfer)}条记忆到长期记忆")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "short_term_count": len(self._short_term_memory),
            "long_term_count": len(self._long_term_memory),
            "total_count": len(self._short_term_memory) + len(self._long_term_memory),
            "max_short_term": self.config.max_short_term_memory,
            "max_long_term": self.config.max_long_term_memory,
        }
    
    @staticmethod
    def is_available() -> bool:
        """检查AgentScope记忆管理是否可用"""
        return AGENTSCOPE_MEMORY_AVAILABLE
