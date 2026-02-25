"""
短期记忆模块单元测试
"""
import pytest
from datetime import datetime, timedelta

from opspilot.memory.base import MemoryEntry, MemoryType, MemoryPriority
from opspilot.memory.short_term import InMemoryShortTermStore, ShortTermMemory


class TestMemoryEntry:
    """记忆条目测试"""

    def test_create_entry(self):
        """测试创建条目"""
        entry = MemoryEntry(
            id="test-1",
            content="测试内容",
            memory_type=MemoryType.SHORT_TERM
        )
        assert entry.id == "test-1"
        assert entry.content == "测试内容"

    def test_entry_expiration(self):
        """测试条目过期"""
        # 未过期
        entry = MemoryEntry(
            id="test-1",
            content="测试",
            memory_type=MemoryType.SHORT_TERM,
            expires_at=datetime.now() + timedelta(hours=1)
        )
        assert entry.is_expired() is False

        # 已过期
        entry.expires_at = datetime.now() - timedelta(hours=1)
        assert entry.is_expired() is True

    def test_entry_to_dict(self):
        """测试条目序列化"""
        entry = MemoryEntry(
            id="test-1",
            content="测试内容",
            memory_type=MemoryType.SHORT_TERM,
            task_id="task-123"
        )
        data = entry.to_dict()

        assert data["id"] == "test-1"
        assert data["content"] == "测试内容"
        assert data["memory_type"] == "short_term"
        assert data["task_id"] == "task-123"

    def test_entry_from_dict(self):
        """测试从字典创建条目"""
        data = {
            "id": "test-1",
            "content": "测试内容",
            "memory_type": "short_term",
            "task_id": "task-123",
            "priority": "medium",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
            "expires_at": None,
            "metadata": {}
        }
        entry = MemoryEntry.from_dict(data)

        assert entry.id == "test-1"
        assert entry.memory_type == MemoryType.SHORT_TERM


class TestInMemoryShortTermStore:
    """内存短期记忆存储测试"""

    @pytest.fixture
    def store(self):
        return InMemoryShortTermStore()

    @pytest.fixture
    def sample_entry(self):
        return MemoryEntry(
            id="test-1",
            content="这是一条测试记忆",
            memory_type=MemoryType.SHORT_TERM,
            task_id="task-123"
        )

    @pytest.mark.asyncio
    async def test_store(self, store, sample_entry):
        """测试存储"""
        result = await store.store(sample_entry)
        assert result is True

    @pytest.mark.asyncio
    async def test_retrieve(self, store, sample_entry):
        """测试获取"""
        await store.store(sample_entry)
        entry = await store.retrieve("test-1")

        assert entry is not None
        assert entry.content == "这是一条测试记忆"

    @pytest.mark.asyncio
    async def test_retrieve_not_found(self, store):
        """测试获取不存在的条目"""
        entry = await store.retrieve("nonexistent")
        assert entry is None

    @pytest.mark.asyncio
    async def test_delete(self, store, sample_entry):
        """测试删除"""
        await store.store(sample_entry)
        result = await store.delete("test-1")

        assert result is True
        entry = await store.retrieve("test-1")
        assert entry is None

    @pytest.mark.asyncio
    async def test_search(self, store):
        """测试搜索"""
        entries = [
            MemoryEntry(id="1", content="苹果是一种水果", memory_type=MemoryType.SHORT_TERM),
            MemoryEntry(id="2", content="香蕉也是一种水果", memory_type=MemoryType.SHORT_TERM),
            MemoryEntry(id="3", content="汽车是交通工具", memory_type=MemoryType.SHORT_TERM),
        ]
        for e in entries:
            await store.store(e)

        results = await store.search("水果")

        assert len(results) == 2
        assert all("水果" in r.entry.content for r in results)

    @pytest.mark.asyncio
    async def test_search_with_filters(self, store):
        """测试带过滤条件的搜索"""
        entries = [
            MemoryEntry(id="1", content="测试内容", memory_type=MemoryType.SHORT_TERM, task_id="task-1"),
            MemoryEntry(id="2", content="测试内容", memory_type=MemoryType.SHORT_TERM, task_id="task-2"),
        ]
        for e in entries:
            await store.store(e)
        
        results = await store.search("测试", filters={"task_id": "task-1"})
    
        assert len(results) == 1
        assert results[0].entry.task_id == "task-1"

    @pytest.mark.asyncio
    async def test_count(self, store):
        """测试计数"""
        for i in range(5):
            await store.store(MemoryEntry(
                id=str(i),
                content=f"内容{i}",
                memory_type=MemoryType.SHORT_TERM
            ))

        count = await store.count()
        assert count == 5

    @pytest.mark.asyncio
    async def test_clear(self, store):
        """测试清空"""
        await store.store(MemoryEntry(
            id="test",
            content="内容",
            memory_type=MemoryType.SHORT_TERM
        ))

        await store.clear()
        count = await store.count()
        assert count == 0

    @pytest.mark.asyncio
    async def test_expired_cleanup(self, store):
        """测试过期清理"""
        entry = MemoryEntry(
            id="test",
            content="内容",
            memory_type=MemoryType.SHORT_TERM,
            expires_at=datetime.now() - timedelta(hours=1)
        )
        await store.store(entry)

        # 过期条目应该被过滤
        result = await store.retrieve("test")
        assert result is None


class TestShortTermMemory:
    """短期记忆管理器测试"""

    @pytest.fixture
    def memory(self):
        return ShortTermMemory()

    @pytest.mark.asyncio
    async def test_remember(self, memory):
        """测试记住"""
        entry = await memory.remember(
            content="测试记忆",
            task_id="task-123",
            agent_name="TestAgent"
        )

        assert entry.id is not None
        assert entry.content == "测试记忆"
        assert entry.task_id == "task-123"

    @pytest.mark.asyncio
    async def test_recall(self, memory):
        """测试回忆"""
        await memory.remember("苹果是水果")
        await memory.remember("香蕉是水果")
        await memory.remember("汽车是工具")

        results = await memory.recall("水果")

        assert len(results) <= 5
        assert all("水果" in r.entry.content for r in results)

    @pytest.mark.asyncio
    async def test_forget(self, memory):
        """测试遗忘"""
        entry = await memory.remember("测试内容")
        result = await memory.forget(entry.id)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_context(self, memory):
        """测试获取上下文"""
        await memory.remember("第一条消息", task_id="task-1", agent_name="AgentA")
        await memory.remember("第二条消息", task_id="task-1", agent_name="AgentB")
        await memory.remember("其他任务消息", task_id="task-2")

        context = await memory.get_context("task-1")

        assert "第一条消息" in context
        assert "第二条消息" in context
        assert "其他任务消息" not in context

