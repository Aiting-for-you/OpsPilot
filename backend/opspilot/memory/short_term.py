"""
短期记忆模块

职责：
- 会话级别的临时记忆
- 基于 Redis 的存储
- 自动过期机制

文档要求：
- "会话存储：Redis - 高性能，支持过期策略"
- "记忆管理：对话历史、会话状态持久化"
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import uuid
import json

from opspilot.memory.base import (
    BaseMemoryStore,
    MemoryEntry,
    MemoryType,
    MemoryPriority,
    SearchResult,
)

# 尝试导入 Redis 存储
try:
    from opspilot.memory.redis_store import RedisSessionStore, REDIS_AVAILABLE
except ImportError:
    REDIS_AVAILABLE = False
    RedisSessionStore = None


class InMemoryShortTermStore(BaseMemoryStore):
    """
    内存短期记忆存储（降级实现）
    
    当 Redis 不可用时使用
    生产环境请确保安装 Redis 以使用高性能会话存储
    """

    def __init__(self, default_ttl_seconds: int = 3600):
        """初始化"""
        self._store: Dict[str, MemoryEntry] = {}
        self._default_ttl = default_ttl_seconds

    async def store(self, entry: MemoryEntry) -> bool:
        """存储记忆条目"""
        if entry.expires_at is None:
            entry.expires_at = datetime.now() + timedelta(seconds=self._default_ttl)
        self._store[entry.id] = entry
        return True

    async def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """获取记忆条目"""
        entry = self._store.get(entry_id)
        if entry and entry.is_expired():
            del self._store[entry_id]
            return None
        return entry

    async def delete(self, entry_id: str) -> bool:
        """删除记忆条目"""
        if entry_id in self._store:
            del self._store[entry_id]
            return True
        return False

    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """搜索记忆"""
        results = []
        query_lower = query.lower()

        for entry in self._store.values():
            if entry.is_expired():
                continue

            if query_lower in entry.content.lower():
                if filters:
                    match = True
                    for key, value in filters.items():
                        # 检查属性和metadata
                        entry_value = getattr(entry, key, None) or entry.metadata.get(key)
                        if entry_value != value:
                            match = False
                            break
                    if not match:
                        continue

                pos = entry.content.lower().find(query_lower)
                score = 1.0 - (pos / max(len(entry.content), 1))
                results.append(SearchResult(entry=entry, score=score))

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    async def clear(self) -> bool:
        """清空所有记忆"""
        self._store.clear()
        return True

    async def count(self) -> int:
        """获取记忆条目数量"""
        expired = [k for k, v in self._store.items() if v.is_expired()]
        for k in expired:
            del self._store[k]
        return len(self._store)

    async def get_by_task(self, task_id: str) -> List[MemoryEntry]:
        """获取指定任务的所有记忆"""
        results = []
        for entry in self._store.values():
            if entry.task_id == task_id and not entry.is_expired():
                results.append(entry)
        return results

    async def cleanup_expired(self) -> int:
        """清理过期记忆"""
        expired = [k for k, v in self._store.items() if v.is_expired()]
        for k in expired:
            del self._store[k]
        return len(expired)


class ShortTermMemory:
    """
    短期记忆管理器
    
    按文档要求，默认使用 Redis 作为会话存储。
    提供对话历史、会话状态持久化功能。
    
    示例:
        >>> memory = ShortTermMemory()  # 自动使用 Redis
        >>> await memory.remember("用户查询供应商信息", task_id="task-001")
        >>> context = await memory.get_context("task-001")
    """

    def __init__(
        self,
        store: Optional[BaseMemoryStore] = None,
        redis_url: str = "redis://localhost:6379",
        session_ttl: int = 3600,
    ):
        """
        初始化短期记忆管理器
        
        Args:
            store: 自定义存储后端（可选）
            redis_url: Redis 连接URL
            session_ttl: 会话过期时间（秒）
        """
        if store is not None:
            self._store = store
        elif REDIS_AVAILABLE and RedisSessionStore is not None:
            # 按文档要求，优先使用 Redis
            self._store = RedisSessionStore(
                redis_url=redis_url,
                session_ttl=session_ttl,
            )
        else:
            # 降级到内存存储
            print("警告: Redis 不可用，使用内存存储。生产环境请安装 Redis。")
            self._store = InMemoryShortTermStore(default_ttl_seconds=session_ttl)
        
        self._using_redis = isinstance(self._store, RedisSessionStore) if RedisSessionStore else False

    @property
    def store(self) -> BaseMemoryStore:
        return self._store

    @property
    def is_using_redis(self) -> bool:
        """是否使用 Redis"""
        return self._using_redis

    async def remember(
        self,
        content: str,
        task_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryEntry:
        """
        记住内容
        
        Args:
            content: 记忆内容
            task_id: 关联任务ID
            agent_name: 关联Agent名称
            metadata: 元数据
        
        Returns:
            MemoryEntry: 创建的记忆条目
        """
        entry = MemoryEntry(
            id=str(uuid.uuid4()),
            content=content,
            memory_type=MemoryType.SHORT_TERM,
            task_id=task_id,
            agent_name=agent_name,
            metadata=metadata or {},
        )

        await self._store.store(entry)
        return entry

    async def recall(
        self,
        query: str,
        task_id: Optional[str] = None,
        limit: int = 5
    ) -> List[SearchResult]:
        """
        回忆相关内容
        
        Args:
            query: 搜索查询
            task_id: 限定任务ID
            limit: 返回数量
        
        Returns:
            List[SearchResult]: 搜索结果
        """
        filters = {}
        if task_id:
            filters["task_id"] = task_id

        return await self._store.search(query, limit=limit, filters=filters or None)

    async def forget(self, entry_id: str) -> bool:
        """
        遗忘指定记忆
        
        Args:
            entry_id: 条目ID
        
        Returns:
            bool: 是否成功
        """
        return await self._store.delete(entry_id)

    async def clear_all(self) -> bool:
        """清空所有短期记忆"""
        return await self._store.clear()

    async def get_context(self, task_id: str) -> str:
        """
        获取任务的上下文
        
        将任务相关的所有记忆合并为上下文字符串
        
        Args:
            task_id: 任务ID
        
        Returns:
            str: 上下文字符串
        """
        if isinstance(self._store, InMemoryShortTermStore):
            entries = await self._store.get_by_task(task_id)
        else:
            results = await self._store.search("", limit=100, filters={"task_id": task_id})
            entries = [r.entry for r in results]

        if not entries:
            return ""

        # 按时间排序
        entries.sort(key=lambda x: x.created_at)

        # 合并为上下文
        lines = []
        for entry in entries:
            timestamp = entry.created_at.strftime("%H:%M:%S")
            agent = f"[{entry.agent_name}]" if entry.agent_name else ""
            lines.append(f"[{timestamp}]{agent} {entry.content}")

        return "\n".join(lines)

    async def get_chat_history(self, session_id: str):
        """
        获取 LangChain ChatMessageHistory
        
        按文档要求，LangChain 负责记忆管理
        仅当使用 Redis 时可用
        
        Args:
            session_id: 会话ID
        
        Returns:
            RedisChatMessageHistory: LangChain 消息历史
        """
        if hasattr(self._store, 'get_session_messages'):
            return await self._store.get_session_messages(session_id)
        raise NotImplementedError(
            "ChatHistory 仅在使用 Redis 存储时可用。"
            "请确保安装了 langchain-redis。"
        )


def create_short_term_memory(
    redis_url: str = "redis://localhost:6379",
    session_ttl: int = 3600,
) -> ShortTermMemory:
    """
    创建短期记忆管理器的便捷函数
    
    按文档要求使用 Redis
    
    Args:
        redis_url: Redis 连接URL
        session_ttl: 会话过期时间
    
    Returns:
        ShortTermMemory: 短期记忆管理器
    """
    return ShortTermMemory(
        redis_url=redis_url,
        session_ttl=session_ttl,
    )

