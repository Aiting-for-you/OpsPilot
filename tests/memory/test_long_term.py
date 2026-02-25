"""
长期记忆模块单元测试
"""
import pytest
from datetime import datetime

from opspilot.memory.base import MemoryEntry, MemoryType, MemoryPriority
from opspilot.memory.long_term import InMemoryLongTermStore, LongTermMemory


class TestInMemoryLongTermStore:
    """内存长期记忆存储测试"""

    @pytest.fixture
    def store(self):
        return InMemoryLongTermStore()

    @pytest.fixture
    def sample_entry(self):
        return MemoryEntry(
            id="test-1",
            content="这是一条重要记忆",
            memory_type=MemoryType.LONG_TERM,
            priority=MemoryPriority.HIGH
        )

    @pytest.mark.asyncio
    async def test_store(self, store, sample_entry):
        """测试存储"""
        result = await store.store(sample_entry)
        assert result is True

    @pytest.mark.asyncio
    async def test_store_with_embedding(self, store):
        """测试存储时生成向量"""
        entry = MemoryEntry(
            id="test-1",
            content="测试内容",
            memory_type=MemoryType.LONG_TERM
        )
        await store.store(entry)

        # 检查是否生成了向量
        assert entry.embedding is not None
        assert len(entry.embedding) == 128

    @pytest.mark.asyncio
    async def test_search_by_similarity(self, store):
        """测试向量相似度搜索"""
        entries = [
            MemoryEntry(id="1", content="苹果是一种红色的水果", memory_type=MemoryType.LONG_TERM),
            MemoryEntry(id="2", content="香蕉是一种黄色的水果", memory_type=MemoryType.LONG_TERM),
            MemoryEntry(id="3", content="汽车是一种交通工具", memory_type=MemoryType.LONG_TERM),
        ]
        for e in entries:
            await store.store(e)

        results = await store.search("水果")

        assert len(results) <= 3
        # 水果相关的应该排在前面
        assert results[0].entry.content != "汽车是一种交通工具"

    @pytest.mark.asyncio
    async def test_search_with_filters(self, store):
        """测试带过滤条件的搜索"""
        entries = [
            MemoryEntry(id="1", content="内容A", memory_type=MemoryType.LONG_TERM, metadata={"category": "work"}),
            MemoryEntry(id="2", content="内容B", memory_type=MemoryType.LONG_TERM, metadata={"category": "personal"}),
        ]
        for e in entries:
            await store.store(e)

        results = await store.search("内容", filters={"category": "work"})

        assert len(results) == 1
        assert results[0].entry.metadata["category"] == "work"


class TestLongTermMemory:
    """长期记忆管理器测试"""

    @pytest.fixture
    def memory(self):
        return LongTermMemory()

    @pytest.mark.asyncio
    async def test_memorize(self, memory):
        """测试记忆"""
        entry = await memory.memorize(
            content="这是一条重要信息",
            priority=MemoryPriority.HIGH
        )

        assert entry.id is not None
        assert entry.priority == MemoryPriority.HIGH

    @pytest.mark.asyncio
    async def test_recall(self, memory):
        """测试回忆"""
        await memory.memorize("今天天气很好")
        await memory.memorize("明天会下雨")

        results = await memory.recall("天气")

        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_recall_with_threshold(self, memory):
        """测试带阈值的回忆"""
        await memory.memorize("测试内容A")
        await memory.memorize("测试内容B")

        results = await memory.recall("测试", min_score=0.5)

        # 根据阈值过滤
        assert all(r.score >= 0.5 for r in results)

    @pytest.mark.asyncio
    async def test_reinforce(self, memory):
        """测试记忆强化"""
        entry = await memory.memorize("普通记忆", priority=MemoryPriority.LOW)

        # 强化记忆
        result = await memory.reinforce(entry.id)
        assert result is True

        # 检查优先级提升
        updated = await memory.store.retrieve(entry.id)
        assert updated.priority == MemoryPriority.MEDIUM

    @pytest.mark.asyncio
    async def test_reinforce_high_priority(self, memory):
        """测试高优先级记忆强化"""
        entry = await memory.memorize("重要记忆", priority=MemoryPriority.HIGH)

        # 高优先级再强化保持不变
        await memory.reinforce(entry.id)

        updated = await memory.store.retrieve(entry.id)
        assert updated.priority == MemoryPriority.HIGH

    @pytest.mark.asyncio
    async def test_forget(self, memory):
        """测试遗忘"""
        entry = await memory.memorize("要遗忘的记忆")

        result = await memory.forget(entry.id)
        assert result is True

        # 确认已删除
        retrieved = await memory.store.retrieve(entry.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_important_memories(self, memory):
        """测试获取重要记忆"""
        await memory.memorize("普通记忆", priority=MemoryPriority.LOW)
        await memory.memorize("重要记忆A", priority=MemoryPriority.HIGH)
        await memory.memorize("重要记忆B", priority=MemoryPriority.HIGH)

        important = await memory.get_important_memories(limit=2)

        assert len(important) <= 2
        assert all(e.priority == MemoryPriority.HIGH for e in important)

    @pytest.mark.asyncio
    async def test_consolidate(self, memory):
        """测试记忆巩固"""
        short_term_entries = [
            MemoryEntry(id="st1", content="短期记忆1", memory_type=MemoryType.SHORT_TERM),
            MemoryEntry(id="st2", content="短期记忆2", memory_type=MemoryType.SHORT_TERM),
        ]

        consolidated = await memory.consolidate(short_term_entries)

        assert len(consolidated) >= 1  # 至少巩固1个记忆
        for entry in consolidated:
            assert entry.memory_type == MemoryType.LONG_TERM

