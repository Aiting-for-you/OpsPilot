"""
Redis 会话存储模块 - Redis Session Store

使用 LangChain Redis 作为会话存储后端，符合文档要求。

职责：
- 会话级别的短期记忆存储
- 对话历史、会话状态持久化
- 自动过期机制

文档原文：
"会话存储：Redis - 高性能，支持过期策略"
"记忆管理：对话历史、会话状态持久化"
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from opspilot.memory.base import (
    BaseMemoryStore,
    MemoryEntry,
    MemoryType,
    SearchResult,
)


# LangChain imports - 按文档要求使用 Redis
try:
    from langchain_community.chat_message_histories import RedisChatMessageHistory
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    RedisChatMessageHistory = None
    BaseMessage = None
    HumanMessage = None
    AIMessage = None


class RedisSessionStore(BaseMemoryStore):
    """
    Redis 会话存储 - 按文档要求使用 LangChain Redis
    
    用于短期记忆和会话状态管理
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        session_ttl: int = 3600,  # 默认1小时过期
        key_prefix: str = "opspilot:session:",
    ):
        """
        初始化 Redis 会话存储
        
        Args:
            redis_url: Redis 连接URL
            session_ttl: 会话过期时间（秒）
            key_prefix: 键前缀
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "LangChain Redis 未安装。请运行: pip install langchain-redis redis"
            )
        
        self._redis_url = redis_url
        self._session_ttl = session_ttl
        self._key_prefix = key_prefix
        
        # 内存缓存，用于快速访问
        self._cache: Dict[str, MemoryEntry] = {}
    
    def _get_session_key(self, session_id: str) -> str:
        """获取会话键"""
        return f"{self._key_prefix}{session_id}"
    
    def _get_message_history(self, session_id: str) -> "RedisChatMessageHistory":
        """获取 LangChain Redis 消息历史"""
        return RedisChatMessageHistory(
            session_id=session_id,
            url=self._redis_url,
            ttl=self._session_ttl,
        )
    
    async def store(self, entry: MemoryEntry) -> bool:
        """存储记忆条目"""
        try:
            # 使用 session_id 或 task_id 作为会话标识
            session_id = entry.task_id or entry.id
            
            # 获取消息历史
            history = self._get_message_history(session_id)
            
            # 创建消息
            message_data = {
                "entry_id": entry.id,
                "content": entry.content,
                "memory_type": entry.memory_type.value,
                "agent_name": entry.agent_name,
                "timestamp": entry.created_at.isoformat(),
                "metadata": entry.metadata,
            }
            
            # 添加到历史（使用 AIMessage 存储结构化数据）
            msg = AIMessage(content=json.dumps(message_data, ensure_ascii=False))
            history.add_message(msg)
            
            # 内存缓存
            self._cache[entry.id] = entry
            
            return True
        except Exception as e:
            print(f"Redis 存储错误: {e}")
            return False
    
    async def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """获取记忆条目"""
        # 先查缓存
        if entry_id in self._cache:
            return self._cache[entry_id]
        return None
    
    async def delete(self, entry_id: str) -> bool:
        """删除记忆条目"""
        if entry_id in self._cache:
            del self._cache[entry_id]
            return True
        return False
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        搜索记忆
        
        简单的关键词匹配，短期记忆通常不需要复杂检索
        """
        results = []
        query_lower = query.lower()
        
        for entry_id, entry in self._cache.items():
            if query_lower in entry.content.lower():
                # 应用过滤条件
                if filters:
                    match = True
                    for key, value in filters.items():
                        if entry.metadata.get(key) != value:
                            match = False
                            break
                    if not match:
                        continue
                
                # 计算简单分数
                pos = entry.content.lower().find(query_lower)
                score = 1.0 - (pos / max(len(entry.content), 1))
                
                results.append(SearchResult(entry=entry, score=score))
        
        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:limit]
    
    async def clear(self) -> bool:
        """清空缓存"""
        self._cache.clear()
        return True
    
    async def count(self) -> int:
        """获取记忆条目数量"""
        return len(self._cache)
    
    async def get_session_messages(
        self,
        session_id: str,
    ) -> List["BaseMessage"]:
        """
        获取会话的所有消息
        
        返回 LangChain BaseMessage 列表，用于 Chain 执行
        """
        history = self._get_message_history(session_id)
        return history.messages
    
    async def add_user_message(
        self,
        session_id: str,
        message: str,
    ) -> None:
        """添加用户消息"""
        history = self._get_message_history(session_id)
        history.add_user_message(message)
    
    async def add_ai_message(
        self,
        session_id: str,
        message: str,
    ) -> None:
        """添加 AI 消息"""
        history = self._get_message_history(session_id)
        history.add_ai_message(message)
    
    async def clear_session(self, session_id: str) -> None:
        """清空指定会话"""
        history = self._get_message_history(session_id)
        history.clear()


class RedisMemoryManager:
    """
    Redis 记忆管理器
    
    整合 LangChain Redis 功能，提供统一的记忆管理接口
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        session_ttl: int = 3600,
    ):
        """
        初始化记忆管理器
        
        Args:
            redis_url: Redis 连接URL
            session_ttl: 会话过期时间
        """
        self._store = RedisSessionStore(
            redis_url=redis_url,
            session_ttl=session_ttl,
        )
    
    @property
    def store(self) -> RedisSessionStore:
        return self._store
    
    async def get_chat_history(
        self,
        session_id: str,
    ) -> "RedisChatMessageHistory":
        """
        获取 LangChain ChatMessageHistory
        
        用于 LangChain Chain 执行
        """
        return self._store._get_message_history(session_id)
    
    async def remember(
        self,
        content: str,
        session_id: str,
        agent_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryEntry:
        """
        记住内容
        
        Args:
            content: 记忆内容
            session_id: 会话ID
            agent_name: Agent名称
            metadata: 元数据
        
        Returns:
            MemoryEntry: 创建的记忆条目
        """
        import uuid
        
        entry = MemoryEntry(
            id=str(uuid.uuid4()),
            content=content,
            memory_type=MemoryType.SHORT_TERM,
            task_id=session_id,
            agent_name=agent_name,
            metadata=metadata or {},
        )
        
        await self._store.store(entry)
        return entry
    
    async def recall(
        self,
        query: str,
        session_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[SearchResult]:
        """
        回忆相关内容
        
        Args:
            query: 搜索查询
            session_id: 限定会话ID
            limit: 返回数量
        
        Returns:
            List[SearchResult]: 搜索结果
        """
        filters = {}
        if session_id:
            filters["task_id"] = session_id
        
        return await self._store.search(query, limit=limit, filters=filters or None)


def create_redis_store(
    redis_url: str = "redis://localhost:6379",
    session_ttl: int = 3600,
) -> RedisSessionStore:
    """
    创建 Redis 会话存储的便捷函数
    
    Args:
        redis_url: Redis 连接URL
        session_ttl: 会话过期时间
    
    Returns:
        RedisSessionStore: Redis 存储实例
    """
    return RedisSessionStore(
        redis_url=redis_url,
        session_ttl=session_ttl,
    )

