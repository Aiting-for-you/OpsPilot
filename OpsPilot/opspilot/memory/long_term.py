"""
长期记忆模块

职责：
- 持久化的长期记忆存储
- 向量化存储和检索
- 记忆衰减和强化

文档要求：
- "向量存储：ChromaDB - 轻量级，适合中小规模"
- "RAG 管道：文档加载、分割、向量化、检索"
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import uuid
import math

from opspilot.memory.base import (
    BaseMemoryStore,
    MemoryEntry,
    MemoryType,
    MemoryPriority,
    SearchResult,
)

# 尝试导入 ChromaDB 存储
try:
    from opspilot.memory.vectorstore import ChromaDBStore, LANGCHAIN_AVAILABLE
except ImportError:
    LANGCHAIN_AVAILABLE = False
    ChromaDBStore = None


class InMemoryLongTermStore(BaseMemoryStore):
    """
    内存长期记忆存储（降级实现）
    
    当 LangChain/ChromaDB 不可用时使用
    生产环境请确保安装 LangChain 以使用 ChromaDB
    """

    def __init__(self):
        """初始化"""
        self._store: Dict[str, MemoryEntry] = {}
        self._embeddings: Dict[str, List[float]] = {}

    def _simple_embedding(self, text: str) -> List[float]:
        """简单的文本向量化（降级实现）"""
        vec = [0.0] * 128
        for i, char in enumerate(text[:128]):
            vec[i % 128] += ord(char) % 100 / 100.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    async def store(self, entry: MemoryEntry) -> bool:
        """存储记忆条目"""
        if entry.embedding is None:
            entry.embedding = self._simple_embedding(entry.content)
        self._store[entry.id] = entry
        self._embeddings[entry.id] = entry.embedding
        return True

    async def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """获取记忆条目"""
        return self._store.get(entry_id)

    async def delete(self, entry_id: str) -> bool:
        """删除记忆条目"""
        if entry_id in self._store:
            del self._store[entry_id]
            self._embeddings.pop(entry_id, None)
            return True
        return False

    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """向量搜索"""
        query_vec = self._simple_embedding(query)
        results = []

        for entry_id, entry in self._store.items():
            if filters:
                match = True
                for key, value in filters.items():
                    if key == "memory_type":
                        if entry.memory_type.value != value:
                            match = False
                            break
                    elif entry.metadata.get(key) != value:
                        match = False
                        break
                if not match:
                    continue

            entry_vec = self._embeddings.get(entry_id)
            if entry_vec:
                score = self._cosine_similarity(query_vec, entry_vec)
                results.append(SearchResult(entry=entry, score=score))

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    async def clear(self) -> bool:
        """清空所有记忆"""
        self._store.clear()
        self._embeddings.clear()
        return True

    async def count(self) -> int:
        """获取记忆条目数量"""
        return len(self._store)

    async def get_by_time_range(
        self,
        start: datetime,
        end: datetime
    ) -> List[MemoryEntry]:
        """获取时间范围内的记忆"""
        results = []
        for entry in self._store.values():
            if start <= entry.created_at <= end:
                results.append(entry)
        return results

    async def get_by_priority(
        self,
        priority: MemoryPriority,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """获取指定优先级的记忆"""
        results = [
            entry for entry in self._store.values()
            if entry.priority == priority
        ]
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results[:limit]


class LongTermMemory:
    """
    长期记忆管理器
    
    按文档要求，默认使用 ChromaDB 作为向量存储。
    提供 RAG 检索增强功能。
    
    示例:
        >>> memory = LongTermMemory()  # 自动使用 ChromaDB
        >>> await memory.memorize("供应商A的库存充足")
        >>> results = await memory.recall("供应商库存")
    """

    def __init__(
        self,
        store: Optional[BaseMemoryStore] = None,
        persist_directory: Optional[str] = None,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        """
        初始化长期记忆管理器
        
        Args:
            store: 自定义存储后端（可选）
            persist_directory: ChromaDB 持久化目录
            embedding_model: 嵌入模型名称
        """
        if store is not None:
            self._store = store
        elif LANGCHAIN_AVAILABLE and ChromaDBStore is not None:
            # 按文档要求，优先使用 ChromaDB
            self._store = ChromaDBStore(
                persist_directory=persist_directory,
                embedding_model=embedding_model,
            )
        else:
            # 降级到内存存储
            print("警告: LangChain 不可用，使用内存存储。生产环境请安装 LangChain。")
            self._store = InMemoryLongTermStore()
        
        self._using_chroma = isinstance(self._store, ChromaDBStore) if ChromaDBStore else False

    @property
    def store(self) -> BaseMemoryStore:
        return self._store

    @property
    def is_using_chroma(self) -> bool:
        """是否使用 ChromaDB"""
        return self._using_chroma

    async def memorize(
        self,
        content: str,
        priority: MemoryPriority = MemoryPriority.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryEntry:
        """
        形成长期记忆
        
        Args:
            content: 记忆内容
            priority: 优先级
            metadata: 元数据
        
        Returns:
            MemoryEntry: 创建的记忆条目
        """
        entry = MemoryEntry(
            id=str(uuid.uuid4()),
            content=content,
            memory_type=MemoryType.LONG_TERM,
            priority=priority,
            metadata=metadata or {},
        )

        await self._store.store(entry)
        return entry

    async def recall(
        self,
        query: str,
        limit: int = 5,
        min_score: float = 0.0
    ) -> List[SearchResult]:
        """
        回忆相关内容
        
        使用向量相似度检索
        
        Args:
            query: 搜索查询
            limit: 返回数量
            min_score: 最小相似度阈值
        
        Returns:
            List[SearchResult]: 搜索结果
        """
        results = await self._store.search(query, limit=limit)
        return [r for r in results if r.score >= min_score]

    async def reinforce(self, entry_id: str) -> bool:
        """
        强化记忆
        
        提高记忆的优先级，防止被遗忘
        
        Args:
            entry_id: 条目ID
        
        Returns:
            bool: 是否成功
        """
        entry = await self._store.retrieve(entry_id)
        if not entry:
            return False

        # 提升优先级
        if entry.priority == MemoryPriority.LOW:
            entry.priority = MemoryPriority.MEDIUM
        elif entry.priority == MemoryPriority.MEDIUM:
            entry.priority = MemoryPriority.HIGH

        entry.updated_at = datetime.now()
        await self._store.store(entry)
        return True

    async def forget(self, entry_id: str) -> bool:
        """
        遗忘记忆
        
        Args:
            entry_id: 条目ID
        
        Returns:
            bool: 是否成功
        """
        return await self._store.delete(entry_id)

    async def get_important_memories(self, limit: int = 10) -> List[MemoryEntry]:
        """
        获取重要记忆
        
        Args:
            limit: 返回数量
        
        Returns:
            List[MemoryEntry]: 高优先级记忆列表
        """
        if isinstance(self._store, InMemoryLongTermStore):
            return await self._store.get_by_priority(MemoryPriority.HIGH, limit)
        return []

    async def consolidate(
        self,
        short_term_entries: List[MemoryEntry],
        threshold: int = 3
    ) -> List[MemoryEntry]:
        """
        记忆巩固
        
        将重要的短期记忆转化为长期记忆
        
        Args:
            short_term_entries: 短期记忆条目
            threshold: 巩固阈值（重复出现次数）
        
        Returns:
            List[MemoryEntry]: 巩固后的长期记忆
        """
        consolidated = []

        for entry in short_term_entries:
            # 检查是否已存在类似记忆
            results = await self._store.search(entry.content, limit=1)

            if results and results[0].score > 0.8:
                # 强化已有记忆
                await self.reinforce(results[0].entry.id)
            else:
                # 创建新的长期记忆
                new_entry = await self.memorize(
                    content=entry.content,
                    priority=entry.priority,
                    metadata=entry.metadata
                )
                consolidated.append(new_entry)

        return consolidated

    def as_retriever(self, **kwargs):
        """
        返回 LangChain Retriever
        
        按文档要求，LangChain 负责 RAG 检索
        仅当使用 ChromaDB 时可用
        
        Returns:
            VectorStoreRetriever: LangChain 检索器
        """
        if hasattr(self._store, 'as_retriever'):
            return self._store.as_retriever(**kwargs)
        raise NotImplementedError(
            "Retriever 仅在使用 ChromaDB 存储时可用。"
            "请确保安装了 langchain-chroma。"
        )


def create_long_term_memory(
    persist_directory: Optional[str] = None,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> LongTermMemory:
    """
    创建长期记忆管理器的便捷函数
    
    按文档要求使用 ChromaDB
    
    Args:
        persist_directory: ChromaDB 持久化目录
        embedding_model: 嵌入模型名称
    
    Returns:
        LongTermMemory: 长期记忆管理器
    """
    return LongTermMemory(
        persist_directory=persist_directory,
        embedding_model=embedding_model,
    )

