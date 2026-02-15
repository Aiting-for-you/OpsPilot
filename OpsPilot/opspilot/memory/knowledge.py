"""
知识库模块

职责：
- 政策法规存储
- 业务知识检索
- RAG 支持
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
import math

from opspilot.memory.base import (
    BaseMemoryStore,
    MemoryEntry,
    MemoryType,
    SearchResult,
)


# ==================== Mock 知识数据 ====================

MOCK_KNOWLEDGE = [
    {
        "id": "KB001",
        "title": "采购限额管理规定",
        "category": "policy",
        "content": "单笔采购金额超过10000元需经理审批，超过50000元需总监审批。紧急采购可在审批通过后先行执行，但需在24小时内补齐审批手续。",
        "tags": ["采购", "审批", "限额"],
    },
    {
        "id": "KB002",
        "title": "供应商准入标准",
        "category": "policy",
        "content": "供应商评分需达到4.0以上方可合作。新供应商需提供营业执照、税务登记证、组织机构代码证等资质文件，经采购部门审核通过后录入系统。",
        "tags": ["供应商", "准入", "资质"],
    },
    {
        "id": "KB003",
        "title": "付款条款规范",
        "category": "policy",
        "content": "标准付款条款为月结30天。特殊情况需提前申请，经财务审批后可调整为月结45天或60天。预付款比例原则上不超过订单金额的30%。",
        "tags": ["付款", "财务", "条款"],
    },
    {
        "id": "KB004",
        "title": "退货流程说明",
        "category": "process",
        "content": "质量问题退货需在收货后7天内发起，填写退货申请单并附上质检报告。经供应商确认后安排退货物流，退款周期为确认退货后15个工作日。",
        "tags": ["退货", "质量", "流程"],
    },
    {
        "id": "KB005",
        "title": "电子元件采购标准",
        "category": "specification",
        "content": "电子元件采购需符合RoHS环保标准。关键元器件需提供原厂授权书和质量保证书。批量采购前需进行样品测试，测试周期不少于7天。",
        "tags": ["电子元件", "标准", "质量"],
    },
]


class InMemoryKnowledgeStore(BaseMemoryStore):
    """
    内存知识库存储（Mock 实现）

    使用内存存储知识库数据
    生产环境可替换为 ChromaDB 或其他向量数据库
    """

    def __init__(self):
        """初始化并加载 Mock 数据"""
        self._store: Dict[str, MemoryEntry] = {}
        self._index: Dict[str, List[str]] = {}  # 简单的倒排索引
        self._load_mock_data()

    def _load_mock_data(self):
        """加载 Mock 数据"""
        for item in MOCK_KNOWLEDGE:
            entry = MemoryEntry(
                id=item["id"],
                content=f"{item['title']}\n{item['content']}",
                memory_type=MemoryType.KNOWLEDGE,
                metadata={
                    "title": item["title"],
                    "category": item["category"],
                    "tags": item["tags"],
                }
            )
            self._store[entry.id] = entry

            # 建立索引
            words = item["title"] + " " + item["content"]
            for word in words:
                if len(word) >= 2:
                    if word not in self._index:
                        self._index[word] = []
                    if entry.id not in self._index[word]:
                        self._index[word].append(entry.id)

    def _simple_embedding(self, text: str) -> List[float]:
        """简单的文本向量化"""
        vec = [0.0] * 64
        for i, char in enumerate(text[:64]):
            vec[i % 64] += ord(char) % 100 / 100.0
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
        """存储知识条目"""
        self._store[entry.id] = entry

        # 更新索引
        words = entry.content
        for word in words:
            if len(word) >= 2:
                if word not in self._index:
                    self._index[word] = []
                if entry.id not in self._index[word]:
                    self._index[word].append(entry.id)

        return True

    async def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """获取知识条目"""
        return self._store.get(entry_id)

    async def delete(self, entry_id: str) -> bool:
        """删除知识条目"""
        if entry_id in self._store:
            entry = self._store[entry_id]
            # 清理索引
            for word in entry.content:
                if word in self._index and entry_id in self._index[word]:
                    self._index[word].remove(entry_id)
            del self._store[entry_id]
            return True
        return False

    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        搜索知识库

        结合关键词匹配和向量相似度
        """
        query_vec = self._simple_embedding(query)
        results = []
        seen_ids = set()

        # 1. 关键词匹配
        query_words = [w for w in query if len(w) >= 2]
        keyword_scores: Dict[str, float] = {}

        for word in query_words:
            if word in self._index:
                for entry_id in self._index[word]:
                    if entry_id not in keyword_scores:
                        keyword_scores[entry_id] = 0
                    keyword_scores[entry_id] += 1

        # 归一化关键词分数
        max_keyword = max(keyword_scores.values()) if keyword_scores else 1

        # 2. 向量相似度
        for entry_id, entry in self._store.items():
            if entry_id in seen_ids:
                continue

            # 应用过滤条件
            if filters:
                match = True
                for key, value in filters.items():
                    if entry.metadata.get(key) != value:
                        match = False
                        break
                if not match:
                    continue

            # 计算向量相似度
            entry_vec = self._simple_embedding(entry.content)
            vec_score = self._cosine_similarity(query_vec, entry_vec)

            # 综合分数
            keyword_score = keyword_scores.get(entry_id, 0) / max_keyword
            combined_score = 0.4 * keyword_score + 0.6 * vec_score

            if combined_score > 0.1:
                results.append(SearchResult(
                    entry=entry,
                    score=combined_score,
                    highlight=self._highlight(entry.content, query_words)
                ))
                seen_ids.add(entry_id)

        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)

        return results[:limit]

    def _highlight(self, content: str, keywords: List[str]) -> str:
        """生成高亮摘要"""
        # 简单实现：找到第一个关键词位置，截取前后内容
        for keyword in keywords:
            pos = content.find(keyword)
            if pos >= 0:
                start = max(0, pos - 30)
                end = min(len(content), pos + len(keyword) + 30)
                return "..." + content[start:end] + "..."
        return content[:60] + "..." if len(content) > 60 else content

    async def clear(self) -> bool:
        """清空知识库"""
        self._store.clear()
        self._index.clear()
        return True

    async def count(self) -> int:
        """获取知识条目数量"""
        return len(self._store)

    async def get_by_category(self, category: str) -> List[MemoryEntry]:
        """按类别获取知识"""
        return [
            entry for entry in self._store.values()
            if entry.metadata.get("category") == category
        ]

    async def get_all_categories(self) -> List[str]:
        """获取所有类别"""
        categories = set()
        for entry in self._store.values():
            cat = entry.metadata.get("category")
            if cat:
                categories.add(cat)
        return list(categories)


class KnowledgeBase:
    """
    知识库管理器

    提供知识管理和 RAG 检索接口
    """

    def __init__(self, store: Optional[BaseMemoryStore] = None):
        """
        初始化

        Args:
            store: 存储后端
        """
        self._store = store or InMemoryKnowledgeStore()

    @property
    def store(self) -> BaseMemoryStore:
        return self._store

    async def query(
        self,
        question: str,
        limit: int = 3
    ) -> List[SearchResult]:
        """
        查询知识库

        Args:
            question: 问题
            limit: 返回数量

        Returns:
            List[SearchResult]: 搜索结果
        """
        return await self._store.search(question, limit=limit)

    async def add_knowledge(
        self,
        title: str,
        content: str,
        category: str,
        tags: Optional[List[str]] = None
    ) -> MemoryEntry:
        """
        添加知识

        Args:
            title: 标题
            content: 内容
            category: 类别
            tags: 标签

        Returns:
            MemoryEntry: 创建的知识条目
        """
        entry = MemoryEntry(
            id=f"KB{uuid.uuid4().hex[:8].upper()}",
            content=f"{title}\n{content}",
            memory_type=MemoryType.KNOWLEDGE,
            metadata={
                "title": title,
                "category": category,
                "tags": tags or [],
            }
        )

        await self._store.store(entry)
        return entry

    async def get_context_for_task(
        self,
        task_description: str,
        max_items: int = 5
    ) -> str:
        """
        获取任务相关的知识上下文

        用于 RAG 场景

        Args:
            task_description: 任务描述
            max_items: 最大条目数

        Returns:
            str: 知识上下文
        """
        results = await self._store.search(task_description, limit=max_items)

        if not results:
            return ""

        lines = ["【相关知识】"]
        for i, result in enumerate(results, 1):
            title = result.entry.metadata.get("title", "未知")
            lines.append(f"{i}. {title}")
            lines.append(f"   {result.entry.content.split(chr(10))[-1][:100]}")

        return "\n".join(lines)

    async def get_categories(self) -> List[str]:
        """获取所有知识类别"""
        if isinstance(self._store, InMemoryKnowledgeStore):
            return await self._store.get_all_categories()
        return []

