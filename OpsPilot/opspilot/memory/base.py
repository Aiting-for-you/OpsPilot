"""
记忆存储基础模块

职责：
- 定义记忆存储抽象接口
- 记忆条目数据结构
- 存储后端协议
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class MemoryType(str, Enum):
    """记忆类型"""
    SHORT_TERM = "short_term"   # 短期记忆（会话级别）
    LONG_TERM = "long_term"     # 长期记忆（持久化）
    KNOWLEDGE = "knowledge"     # 知识库


class MemoryPriority(str, Enum):
    """记忆优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class MemoryEntry:
    """
    记忆条目

    存储单条记忆的基本单位
    """
    id: str
    content: str
    memory_type: MemoryType
    task_id: Optional[str] = None
    agent_name: Optional[str] = None
    priority: MemoryPriority = MemoryPriority.MEDIUM
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """从字典创建"""
        return cls(
            id=data["id"],
            content=data["content"],
            memory_type=MemoryType(data["memory_type"]),
            task_id=data.get("task_id"),
            agent_name=data.get("agent_name"),
            priority=MemoryPriority(data.get("priority", "medium")),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            embedding=data.get("embedding"),
            metadata=data.get("metadata", {}),
        )

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


@dataclass
class SearchResult:
    """搜索结果"""
    entry: MemoryEntry
    score: float  # 相似度分数 (0-1)
    highlight: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry": self.entry.to_dict(),
            "score": self.score,
            "highlight": self.highlight,
        }


class BaseMemoryStore(ABC):
    """
    记忆存储抽象基类

    定义所有存储后端必须实现的接口
    """

    @abstractmethod
    async def store(self, entry: MemoryEntry) -> bool:
        """
        存储记忆条目

        Args:
            entry: 记忆条目

        Returns:
            bool: 是否成功
        """
        pass

    @abstractmethod
    async def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """
        获取记忆条目

        Args:
            entry_id: 条目ID

        Returns:
            MemoryEntry: 记忆条目，不存在则返回 None
        """
        pass

    @abstractmethod
    async def delete(self, entry_id: str) -> bool:
        """
        删除记忆条目

        Args:
            entry_id: 条目ID

        Returns:
            bool: 是否成功
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        搜索记忆

        Args:
            query: 搜索查询
            limit: 返回数量限制
            filters: 过滤条件

        Returns:
            List[SearchResult]: 搜索结果列表
        """
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """
        清空所有记忆

        Returns:
            bool: 是否成功
        """
        pass

    @abstractmethod
    async def count(self) -> int:
        """
        获取记忆条目数量

        Returns:
            int: 条目数量
        """
        pass


class MemoryManager:
    """
    记忆管理器

    统一管理短期记忆、长期记忆和知识库
    """

    def __init__(self):
        self._short_term: Optional[BaseMemoryStore] = None
        self._long_term: Optional[BaseMemoryStore] = None
        self._knowledge: Optional[BaseMemoryStore] = None

    def set_short_term_store(self, store: BaseMemoryStore) -> None:
        """设置短期记忆存储"""
        self._short_term = store

    def set_long_term_store(self, store: BaseMemoryStore) -> None:
        """设置长期记忆存储"""
        self._long_term = store

    def set_knowledge_store(self, store: BaseMemoryStore) -> None:
        """设置知识库存储"""
        self._knowledge = store

    @property
    def short_term(self) -> BaseMemoryStore:
        """获取短期记忆存储"""
        if self._short_term is None:
            raise RuntimeError("短期记忆存储未配置")
        return self._short_term

    @property
    def long_term(self) -> BaseMemoryStore:
        """获取长期记忆存储"""
        if self._long_term is None:
            raise RuntimeError("长期记忆存储未配置")
        return self._long_term

    @property
    def knowledge(self) -> BaseMemoryStore:
        """获取知识库存储"""
        if self._knowledge is None:
            raise RuntimeError("知识库存储未配置")
        return self._knowledge

    async def multi_recall(
        self,
        query: str,
        sources: List[MemoryType],
        limit_per_source: int = 5
    ) -> Dict[MemoryType, List[SearchResult]]:
        """
        多路召回

        从多个来源搜索记忆

        Args:
            query: 搜索查询
            sources: 记忆来源列表
            limit_per_source: 每个来源的返回数量

        Returns:
            Dict[MemoryType, List[SearchResult]]: 各来源的搜索结果
        """
        results = {}

        for source in sources:
            if source == MemoryType.SHORT_TERM and self._short_term:
                results[source] = await self._short_term.search(
                    query, limit=limit_per_source
                )
            elif source == MemoryType.LONG_TERM and self._long_term:
                results[source] = await self._long_term.search(
                    query, limit=limit_per_source
                )
            elif source == MemoryType.KNOWLEDGE and self._knowledge:
                results[source] = await self._knowledge.search(
                    query, limit=limit_per_source
                )

        return results

    async def store_with_decay(
        self,
        entry: MemoryEntry,
        decay_days: int = 7
    ) -> bool:
        """
        存储记忆并设置过期时间

        Args:
            entry: 记忆条目
            decay_days: 衰减天数

        Returns:
            bool: 是否成功
        """
        from datetime import timedelta

        # 设置过期时间
        entry.expires_at = datetime.now() + timedelta(days=decay_days)

        # 根据类型存储
        if entry.memory_type == MemoryType.SHORT_TERM:
            return await self.short_term.store(entry)
        elif entry.memory_type == MemoryType.LONG_TERM:
            return await self.long_term.store(entry)
        else:
            return await self.knowledge.store(entry)

