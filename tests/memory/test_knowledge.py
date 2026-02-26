"""
知识库模块单元测试
"""
import pytest

from opspilot.memory.base import MemoryEntry, MemoryType
from opspilot.memory.knowledge import InMemoryKnowledgeStore, KnowledgeBase, MOCK_KNOWLEDGE


class TestInMemoryKnowledgeStore:
    """内存知识库存储测试"""

    @pytest.fixture
    def store(self):
        return InMemoryKnowledgeStore()

    def test_load_mock_data(self, store):
        """测试加载 Mock 数据"""
        count = len(MOCK_KNOWLEDGE)
        # 同步获取数量
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(store.count())
        assert result == count

    @pytest.mark.asyncio
    async def test_search_by_keyword(self, store):
        """测试关键词搜索"""
        results = await store.search("采购")

        # 搜索应该返回结果
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_search_by_category(self, store):
        """测试按类别过滤搜索"""
        results = await store.search("规定", filters={"category": "policy"})

        for result in results:
            assert result.entry.metadata.get("category") == "policy"

    @pytest.mark.asyncio
    async def test_retrieve(self, store):
        """测试获取知识"""
        entry = await store.retrieve("KB001")

        assert entry is not None
        assert "采购限额" in entry.content

    @pytest.mark.asyncio
    async def test_retrieve_not_found(self, store):
        """测试获取不存在的知识"""
        entry = await store.retrieve("NONEXISTENT")
        assert entry is None

    @pytest.mark.asyncio
    async def test_store_new_knowledge(self, store):
        """测试存储新知识"""
        entry = MemoryEntry(
            id="NEW001",
            content="新知识条目\n这是新知识的内容",
            memory_type=MemoryType.KNOWLEDGE,
            metadata={
                "title": "新知识条目",
                "category": "test",
                "tags": ["测试"]
            }
        )

        result = await store.store(entry)
        assert result is True

        # 验证可以搜索到
        results = await store.search("新知识")
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_delete_knowledge(self, store):
        """测试删除知识"""
        result = await store.delete("KB001")
        assert result is True

        entry = await store.retrieve("KB001")
        assert entry is None

    @pytest.mark.asyncio
    async def test_get_by_category(self, store):
        """测试按类别获取"""
        if hasattr(store, 'get_by_category'):
            entries = await store.get_by_category("policy")
            assert len(entries) > 0
            for entry in entries:
                assert entry.metadata.get("category") == "policy"

    @pytest.mark.asyncio
    async def test_search_result_has_highlight(self, store):
        """测试搜索结果包含高亮"""
        results = await store.search("采购限额")

        for result in results:
            assert result.highlight is not None


class TestKnowledgeBase:
    """知识库管理器测试"""

    @pytest.fixture
    def kb(self):
        return KnowledgeBase()

    @pytest.mark.asyncio
    async def test_query(self, kb):
        """测试查询"""
        results = await kb.query("采购审批")

        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_query_with_limit(self, kb):
        """测试限制返回数量"""
        results = await kb.query("规定", limit=2)

        assert len(results) <= 2

    @pytest.mark.asyncio
    async def test_add_knowledge(self, kb):
        """测试添加知识"""
        entry = await kb.add_knowledge(
            title="测试知识",
            content="这是测试知识的内容",
            category="test",
            tags=["测试", "示例"]
        )

        assert entry.id.startswith("KB")
        assert entry.metadata["title"] == "测试知识"

    @pytest.mark.asyncio
    async def test_get_context_for_task(self, kb):
        """测试获取任务相关上下文"""
        context = await kb.get_context_for_task("采购商品需要审批吗？")

        assert "相关知识" in context
        assert len(context) > 0

    @pytest.mark.asyncio
    async def test_get_categories(self, kb):
        """测试获取类别列表"""
        categories = await kb.get_categories()

        assert "policy" in categories
        assert "process" in categories


class TestMockKnowledgeData:
    """Mock 知识数据测试"""

    def test_mock_data_structure(self):
        """测试 Mock 数据结构"""
        for item in MOCK_KNOWLEDGE:
            assert "id" in item
            assert "title" in item
            assert "category" in item
            assert "content" in item
            assert "tags" in item

    def test_mock_data_categories(self):
        """测试 Mock 数据类别"""
        categories = set(item["category"] for item in MOCK_KNOWLEDGE)

        assert "policy" in categories

    def test_mock_data_has_required_policies(self):
        """测试 Mock 数据包含必要政策"""
        titles = [item["title"] for item in MOCK_KNOWLEDGE]

        assert "采购限额管理规定" in titles
        assert "供应商准入标准" in titles

