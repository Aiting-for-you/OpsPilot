"""
工具调用优化测试

测试工具索引、检索、压缩和自愈机制。
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from opspilot.tools.base import ToolSchema
from opspilot.tools.indexer import (
    ToolCategory,
    ToolEmbedding,
    ToolIndex,
    ToolIndexer,
    SimpleTokenizer,
    create_tool_index,
)
from opspilot.tools.retriever import (
    RetrievalStrategy,
    RetrievalResult,
    ToolRetriever,
    ToolContextBudget,
)
from opspilot.tools.compressor import (
    CompressionLevel,
    CompressedTool,
    ToolCompressor,
    TokenEstimator,
)
from opspilot.tools.context_manager import (
    ToolSelectionResult,
    ToolContextManager,
)
from opspilot.tools.healing import (
    ErrorType,
    RecoveryStrategy,
    ErrorDiagnosis,
    ErrorDiagnoser,
    ToolHealer,
    ToolUnrecoverableError,
    ToolMaxRetriesExceededError,
)


# ============== 测试数据 ==============

def create_test_tools() -> list:
    """创建测试工具"""
    return [
        ToolSchema(
            name="query_supplier",
            description="查询供应商信息，支持按名称、ID、地区等多维度查询",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "供应商名称"},
                    "supplier_id": {"type": "string", "description": "供应商ID"},
                    "region": {"type": "string", "description": "地区"},
                },
            },
            timeout=30,
        ),
        ToolSchema(
            name="create_order",
            description="创建采购订单，需要提供供应商ID、商品列表和数量",
            parameters={
                "type": "object",
                "properties": {
                    "supplier_id": {"type": "string", "description": "供应商ID"},
                    "items": {"type": "array", "description": "商品列表"},
                    "quantity": {"type": "integer", "description": "数量"},
                },
                "required": ["supplier_id", "items"],
            },
            timeout=60,
        ),
        ToolSchema(
            name="query_inventory",
            description="查询库存信息，支持按商品ID、仓库等查询",
            parameters={
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "商品ID"},
                    "warehouse": {"type": "string", "description": "仓库名称"},
                },
            },
            timeout=30,
        ),
        ToolSchema(
            name="check_compliance",
            description="合规检查，验证订单是否符合公司政策和法规要求",
            parameters={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "订单ID"},
                    "policy_type": {"type": "string", "description": "政策类型"},
                },
                "required": ["order_id"],
            },
            timeout=45,
        ),
        ToolSchema(
            name="calculate_total",
            description="计算订单总价，支持折扣计算",
            parameters={
                "type": "object",
                "properties": {
                    "items": {"type": "array", "description": "商品列表"},
                    "discount": {"type": "number", "description": "折扣率"},
                },
                "required": ["items"],
            },
            timeout=10,
        ),
    ]


# ============== 索引器测试 ==============

class TestSimpleTokenizer:
    """测试简单分词器"""
    
    def test_tokenize_english(self):
        """测试英文分词"""
        tokens = SimpleTokenizer.tokenize("Query supplier information")
        assert "query" in tokens
        assert "supplier" in tokens
        assert "information" in tokens
    
    def test_tokenize_chinese(self):
        """测试中文分词"""
        tokens = SimpleTokenizer.tokenize("查询供应商信息")
        assert "查" in tokens or "询" in tokens
    
    def test_tokenize_mixed(self):
        """测试中英混合"""
        tokens = SimpleTokenizer.tokenize("Query供应商information")
        assert "query" in tokens
        assert "information" in tokens
    
    def test_stop_words_removed(self):
        """测试停用词过滤"""
        tokens = SimpleTokenizer.tokenize("the supplier is a company")
        assert "the" not in tokens
        assert "is" not in tokens
        assert "a" not in tokens
        assert "supplier" in tokens
        assert "company" in tokens
    
    def test_extract_keywords(self):
        """测试关键词提取"""
        text = "查询供应商信息，支持按名称、ID、地区等多维度查询"
        keywords = SimpleTokenizer.extract_keywords(text, top_k=5)
        assert len(keywords) <= 5
        assert len(keywords) > 0


class TestToolIndexer:
    """测试工具索引器"""
    
    def test_add_tool(self):
        """测试添加工具"""
        indexer = ToolIndexer()
        tool = create_test_tools()[0]
        indexer.add_tool(tool)
        assert len(indexer.tools) == 1
    
    def test_add_tools(self):
        """测试批量添加工具"""
        indexer = ToolIndexer()
        tools = create_test_tools()
        indexer.add_tools(tools)
        assert len(indexer.tools) == len(tools)
    
    def test_classify_tool(self):
        """测试工具分类"""
        indexer = ToolIndexer()
        tools = create_test_tools()
        
        # query_supplier 应该被分类为 ERP 或 QUERY
        category = indexer._classify_tool(tools[0])
        assert category in [ToolCategory.ERP, ToolCategory.QUERY]
        
        # check_compliance 应该被分类为 COMPLIANCE
        category = indexer._classify_tool(tools[3])
        assert category == ToolCategory.COMPLIANCE
    
    def test_build_index(self):
        """测试构建索引"""
        tools = create_test_tools()
        indexer = ToolIndexer()
        indexer.add_tools(tools)
        
        index = indexer.build_index()
        
        assert len(index.embeddings) == len(tools)
        assert len(index.vocabulary) > 0
        assert len(index.idf_scores) > 0
        assert len(index.category_index) > 0
    
    def test_embedding_normalization(self):
        """测试向量归一化"""
        tools = create_test_tools()
        indexer = ToolIndexer()
        indexer.add_tools(tools)
        index = indexer.build_index()
        
        for emb in index.embeddings:
            norm = sum(x * x for x in emb.embedding) ** 0.5
            assert abs(norm - 1.0) < 0.01  # 归一化后的向量长度应该为1
    
    def test_save_and_load_index(self, tmp_path):
        """测试索引保存和加载"""
        tools = create_test_tools()
        indexer = ToolIndexer()
        indexer.add_tools(tools)
        index = indexer.build_index()
        
        # 保存
        save_path = tmp_path / "test_index.pkl"
        indexer.save_index(index, save_path)
        assert save_path.exists()
        
        # 加载
        loaded = indexer.load_index(save_path)
        assert len(loaded.embeddings) == len(index.embeddings)


class TestCreateToolIndex:
    """测试便捷函数"""
    
    def test_create_tool_index(self):
        """测试创建工具索引"""
        tools = create_test_tools()
        index = create_tool_index(tools)
        
        assert len(index.embeddings) == len(tools)


# ============== 检索器测试 ==============

class TestToolRetriever:
    """测试工具检索器"""
    
    @pytest.fixture
    def retriever(self):
        """创建检索器"""
        tools = create_test_tools()
        index = create_tool_index(tools)
        return ToolRetriever(index)
    
    def test_semantic_retrieve(self, retriever):
        """测试语义检索"""
        results = retriever.retrieve(
            "查询供应商信息",
            top_k=3,
            strategy=RetrievalStrategy.SEMANTIC,
        )
        
        assert len(results) <= 3
        assert all(r.match_type == "semantic" for r in results)
        assert all(r.relevance_score >= 0 for r in results)
    
    def test_keyword_retrieve(self, retriever):
        """测试关键词检索"""
        results = retriever.retrieve(
            "供应商查询",
            top_k=3,
            strategy=RetrievalStrategy.KEYWORD,
        )
        
        assert len(results) <= 3
        assert all(r.match_type == "keyword" for r in results)
    
    def test_hybrid_retrieve(self, retriever):
        """测试混合检索"""
        results = retriever.retrieve(
            "创建订单",
            top_k=3,
            strategy=RetrievalStrategy.HYBRID,
        )
        
        assert len(results) <= 3
        assert all(r.match_type == "hybrid" for r in results)
    
    def test_two_level_retrieve(self, retriever):
        """测试两级检索"""
        results = retriever.retrieve(
            "查询供应商",
            top_k=3,
            strategy=RetrievalStrategy.TWO_LEVEL,
        )
        
        assert len(results) <= 3
        assert all(r.match_type == "two_level" for r in results)
    
    def test_relevance_ordering(self, retriever):
        """测试相关性排序"""
        results = retriever.retrieve(
            "供应商查询",
            top_k=5,
            strategy=RetrievalStrategy.HYBRID,
        )
        
        scores = [r.relevance_score for r in results]
        assert scores == sorted(scores, reverse=True)
    
    def test_get_tool_names(self, retriever):
        """测试获取工具名称"""
        results = retriever.retrieve("查询", top_k=3)
        names = retriever.get_tool_names(results)
        
        assert len(names) == len(results)
        assert all(isinstance(n, str) for n in names)


class TestToolContextBudget:
    """测试上下文预算"""
    
    def test_default_budget(self):
        """测试默认预算"""
        budget = ToolContextBudget()
        assert budget.max_tokens == ToolContextBudget.DEFAULT_MAX_TOKENS
    
    def test_custom_budget(self):
        """测试自定义预算"""
        budget = ToolContextBudget(max_tokens=1000)
        assert budget.max_tokens == 1000
    
    def test_select_tools_within_budget(self):
        """测试预算内选择工具"""
        tools = create_test_tools()
        budget = ToolContextBudget(max_tokens=5000)
        
        # 创建简单的检索结果
        from opspilot.tools.indexer import ToolCategory
        results = [
            RetrievalResult(
                tool_name=t.name,
                relevance_score=0.5,
                category=ToolCategory.UNKNOWN,
                match_type="test",
            )
            for t in tools
        ]
        
        selected, tokens = budget.select_tools(tools, results)
        
        assert len(selected) <= len(tools)
        assert tokens <= budget.max_tokens
    
    def test_budget_exceeded(self):
        """测试预算超出"""
        tools = create_test_tools() * 10  # 大量工具
        budget = ToolContextBudget(max_tokens=100)  # 小预算
        
        from opspilot.tools.indexer import ToolCategory
        results = [
            RetrievalResult(
                tool_name=t.name,
                relevance_score=0.5,
                category=ToolCategory.UNKNOWN,
                match_type="test",
            )
            for t in tools
        ]
        
        selected, tokens = budget.select_tools(tools, results)
        
        assert tokens <= budget.max_tokens


# ============== 压缩器测试 ==============

class TestTokenEstimator:
    """测试Token估算器"""
    
    def test_estimate_english(self):
        """测试英文token估算"""
        tokens = TokenEstimator.estimate("Hello world")
        assert tokens > 0
    
    def test_estimate_chinese(self):
        """测试中文token估算"""
        tokens = TokenEstimator.estimate("你好世界")
        assert tokens > 0
    
    def test_estimate_tool(self):
        """测试工具token估算"""
        tool = create_test_tools()[0]
        tokens = TokenEstimator.estimate_tool(tool)
        assert tokens > 0


class TestToolCompressor:
    """测试工具压缩器"""
    
    @pytest.fixture
    def compressor(self):
        return ToolCompressor()
    
    def test_no_compression(self, compressor):
        """测试不压缩"""
        tool = create_test_tools()[0]
        compressed = compressor.compress(tool, CompressionLevel.NONE)
        
        assert compressed.compression_ratio == 1.0
        assert compressed.original_tokens == compressed.compressed_tokens
    
    def test_light_compression(self, compressor):
        """测试轻度压缩"""
        tool = create_test_tools()[0]
        compressed = compressor.compress(tool, CompressionLevel.LIGHT)
        
        assert compressed.compressed_tokens <= compressed.original_tokens
        assert len(compressed.action) > 0
    
    def test_moderate_compression(self, compressor):
        """测试中度压缩"""
        tool = create_test_tools()[0]
        compressed = compressor.compress(tool, CompressionLevel.MODERATE)
        
        assert compressed.compressed_tokens <= compressed.original_tokens
        assert len(compressed.action) > 0
        assert len(compressed.params) > 0
    
    def test_aggressive_compression(self, compressor):
        """测试激进压缩"""
        tool = create_test_tools()[0]
        compressed = compressor.compress(tool, CompressionLevel.AGGRESSIVE)
        
        assert compressed.compressed_tokens <= compressed.original_tokens
        assert len(compressed.action) <= 30
    
    def test_compression_ratio(self, compressor):
        """测试压缩率"""
        tool = create_test_tools()[0]
        moderate = compressor.compress(tool, CompressionLevel.MODERATE)
        aggressive = compressor.compress(tool, CompressionLevel.AGGRESSIVE)
        
        assert aggressive.compressed_tokens <= moderate.compressed_tokens
        assert aggressive.compression_ratio <= moderate.compression_ratio
    
    def test_batch_compress(self, compressor):
        """测试批量压缩"""
        tools = create_test_tools()
        compressed = compressor.batch_compress(tools)
        
        assert len(compressed) == len(tools)
    
    def test_to_openai_format(self, compressor):
        """测试OpenAI格式转换"""
        tool = create_test_tools()[0]
        compressed = compressor.compress(tool, CompressionLevel.MODERATE)
        
        openai_format = compressed.to_openai_format()
        
        assert openai_format["type"] == "function"
        assert "name" in openai_format["function"]
        assert "description" in openai_format["function"]
        assert "parameters" in openai_format["function"]


# ============== 上下文管理器测试 ==============

class TestToolContextManager:
    """测试上下文管理器"""
    
    @pytest.fixture
    def manager(self):
        """创建管理器"""
        tools = create_test_tools()
        tools_dict = {t.name: t for t in tools}
        return ToolContextManager(tools_dict, max_tokens=2000)
    
    def test_select_tools(self, manager):
        """测试选择工具"""
        result = manager.select_tools("查询供应商信息")
        
        assert isinstance(result, ToolSelectionResult)
        assert len(result.selected_tools) > 0
        assert result.total_tokens <= manager.max_tokens
    
    def test_cache_hit(self, manager):
        """测试缓存命中"""
        query = "查询供应商"
        
        # 第一次查询
        result1 = manager.select_tools(query)
        
        # 第二次相同查询
        result2 = manager.select_tools(query)
        
        assert result1.query_hash == result2.query_hash
        stats = manager.get_cache_stats()
        assert stats["total_hits"] >= 1
    
    def test_get_tools_for_llm(self, manager):
        """测试获取LLM工具格式"""
        tools = manager.get_tools_for_llm("查询供应商")
        
        assert len(tools) > 0
        assert all("type" in t for t in tools)
        assert all(t["type"] == "function" for t in tools)
    
    def test_update_max_tokens(self, manager):
        """测试更新最大token"""
        new_max = 1000
        manager.update_max_tokens(new_max)
        
        assert manager.max_tokens == new_max
        
        result = manager.select_tools("查询")
        assert result.total_tokens <= new_max


# ============== 自愈机制测试 ==============

class TestErrorDiagnoser:
    """测试错误诊断器"""
    
    def test_diagnose_timeout(self):
        """测试超时诊断"""
        from opspilot.utils.exceptions import ToolTimeoutError
        error = ToolTimeoutError("Tool execution timed out")
        
        diagnosis = ErrorDiagnoser.diagnose(error)
        
        assert diagnosis.error_type == ErrorType.NETWORK_TIMEOUT
        assert diagnosis.is_recoverable
        assert diagnosis.suggested_strategy == RecoveryStrategy.RETRY_WITH_BACKOFF
    
    def test_diagnose_permission_denied(self):
        """测试权限错误诊断"""
        error = Exception("403 Permission denied")
        
        diagnosis = ErrorDiagnoser.diagnose(error)
        
        assert diagnosis.error_type == ErrorType.PERMISSION_DENIED
        assert diagnosis.is_recoverable
    
    def test_diagnose_missing_param(self):
        """测试缺少参数诊断"""
        error = Exception("missing required parameter: supplier_id")
        
        diagnosis = ErrorDiagnoser.diagnose(error)
        
        assert diagnosis.error_type == ErrorType.PARAM_MISSING
        assert diagnosis.is_recoverable
        assert diagnosis.suggested_strategy == RecoveryStrategy.AUTO_FIX
    
    def test_diagnose_unknown_error(self):
        """测试未知错误诊断"""
        error = Exception("Some unknown error")
        
        diagnosis = ErrorDiagnoser.diagnose(error)
        
        assert diagnosis.error_type == ErrorType.UNKNOWN
        assert not diagnosis.is_recoverable


class TestToolHealer:
    """测试工具自愈器"""
    
    @pytest.fixture
    def healer(self):
        return ToolHealer(max_retries=3)
    
    @pytest.mark.asyncio
    async def test_successful_execution(self, healer):
        """测试成功执行"""
        async def executor(call, context):
            return {"status": "success"}
        
        result = await healer.execute_with_healing(
            {"name": "test_tool", "parameters": {}},
            executor,
        )
        
        assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_retry_on_timeout(self, healer):
        """测试超时重试"""
        call_count = 0
        
        async def executor(call, context):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                from opspilot.utils.exceptions import ToolTimeoutError
                raise ToolTimeoutError("Timeout")
            return {"status": "success"}
        
        result = await healer.execute_with_healing(
            {"name": "test_tool", "parameters": {}},
            executor,
        )
        
        assert result["status"] == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, healer):
        """测试超过最大重试次数"""
        async def executor(call, context):
            from opspilot.utils.exceptions import ToolTimeoutError
            raise ToolTimeoutError("Always timeout")
        
        with pytest.raises(ToolMaxRetriesExceededError):
            await healer.execute_with_healing(
                {"name": "test_tool", "parameters": {}},
                executor,
            )
    
    @pytest.mark.asyncio
    async def test_unrecoverable_error(self, healer):
        """测试不可恢复错误"""
        async def executor(call, context):
            raise Exception("Unknown fatal error")
        
        with pytest.raises(ToolUnrecoverableError):
            await healer.execute_with_healing(
                {"name": "test_tool", "parameters": {}},
                executor,
            )
    
    @pytest.mark.asyncio
    async def test_fallback_handler(self):
        """测试降级处理"""
        async def fallback(call, diagnosis):
            return {"status": "fallback", "message": "降级响应"}
        
        healer = ToolHealer(
            max_retries=1,
            fallback_handler=fallback,
        )
        
        async def executor(call, context):
            raise Exception("503 Service unavailable")
        
        result = await healer.execute_with_healing(
            {"name": "test_tool", "parameters": {}},
            executor,
        )
        
        assert result["status"] == "fallback"


# ============== 集成测试 ==============

class TestToolOptimizationIntegration:
    """工具优化集成测试"""
    
    def test_full_workflow(self):
        """测试完整工作流"""
        # 1. 创建工具
        tools = create_test_tools()
        tools_dict = {t.name: t for t in tools}
        
        # 2. 创建上下文管理器
        manager = ToolContextManager(tools_dict, max_tokens=1500)
        
        # 3. 检索和压缩
        result = manager.select_tools(
            "我需要查询供应商信息并创建采购订单",
            top_k=10,
            strategy=RetrievalStrategy.HYBRID,
        )
        
        # 验证结果
        assert len(result.selected_tools) > 0
        assert result.total_tokens <= 1500
        assert result.compression_stats["compression_ratio"] < 1.0
        
        # 验证检索相关性
        tool_names = [t.name for t in result.selected_tools]
        assert "query_supplier" in tool_names or "create_order" in tool_names
    
    @pytest.mark.asyncio
    async def test_healing_integration(self):
        """测试自愈集成"""
        tools = create_test_tools()
        tools_dict = {t.name: t for t in tools}
        
        manager = ToolContextManager(tools_dict)
        healer = ToolHealer(max_retries=2)
        
        # 模拟执行器
        call_count = 0
        async def executor(call, context):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                from opspilot.utils.exceptions import ToolTimeoutError
                raise ToolTimeoutError("Timeout")
            return {"data": "success"}
        
        result = await healer.execute_with_healing(
            {"name": "query_supplier", "parameters": {"name": "test"}},
            executor,
        )
        
        assert result["data"] == "success"
        assert call_count == 2


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

