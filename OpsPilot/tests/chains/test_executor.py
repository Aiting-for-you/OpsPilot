"""
链式执行器单元测试
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from opspilot.chains.executor import (
    ChainResult,
    RAGChain,
    ToolChain,
    DecisionChain,
    OpsChainExecutor,
    create_rag_chain,
    create_tool_chain,
    create_decision_chain,
    LANGCHAIN_AVAILABLE,
)


class TestChainResult:
    """链执行结果测试"""

    def test_success_result(self):
        """测试成功结果"""
        result = ChainResult(
            success=True,
            output="执行成功",
            metadata={"key": "value"},
        )
        
        assert result.success is True
        assert result.output == "执行成功"
        assert result.error is None
        assert result.metadata == {"key": "value"}

    def test_error_result(self):
        """测试错误结果"""
        result = ChainResult(
            success=False,
            output=None,
            error="执行失败",
        )
        
        assert result.success is False
        assert result.output is None
        assert result.error == "执行失败"

    def test_default_metadata(self):
        """测试默认 metadata"""
        result = ChainResult(success=True, output="test")
        
        assert result.metadata == {}


@pytest.mark.skipif(not LANGCHAIN_AVAILABLE, reason="LangChain 未安装")
class TestRAGChain:
    """RAG 检索链测试"""

    @pytest.fixture
    def mock_retriever(self):
        """Mock 检索器"""
        retriever = MagicMock()
        retriever.invoke = MagicMock(return_value=[
            MagicMock(page_content="文档1内容"),
            MagicMock(page_content="文档2内容"),
        ])
        return retriever

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM"""
        llm = MagicMock()
        llm.invoke = MagicMock(return_value=MagicMock(content="LLM 响应"))
        return llm

    def test_init_without_langchain(self):
        """测试未安装 LangChain 时的初始化"""
        with patch('opspilot.chains.executor.LANGCHAIN_AVAILABLE', False):
            with pytest.raises(ImportError, match="LangChain 未安装"):
                RAGChain(retriever=None, llm=None)

    def test_format_docs(self):
        """测试格式化文档"""
        docs = [
            MagicMock(page_content="文档1"),
            MagicMock(page_content="文档2"),
        ]
        
        result = RAGChain._format_docs(docs)
        
        assert "文档1" in result
        assert "文档2" in result

    @pytest.mark.asyncio
    async def test_ainvoke(self, mock_retriever, mock_llm):
        """测试异步执行"""
        chain = RAGChain(retriever=mock_retriever, llm=mock_llm)
        
        # Mock chain invoke
        chain._chain.ainvoke = AsyncMock(return_value="RAG 响应")
        
        result = await chain.ainvoke("测试查询")
        
        assert result.success is True
        assert result.output == "RAG 响应"

    @pytest.mark.asyncio
    async def test_ainvoke_error(self, mock_retriever, mock_llm):
        """测试异步执行错误"""
        chain = RAGChain(retriever=mock_retriever, llm=mock_llm)
        
        chain._chain.ainvoke = AsyncMock(side_effect=Exception("执行错误"))
        
        result = await chain.ainvoke("测试查询")
        
        assert result.success is False
        assert "执行错误" in result.error

    def test_invoke(self, mock_retriever, mock_llm):
        """测试同步执行"""
        chain = RAGChain(retriever=mock_retriever, llm=mock_llm)
        
        chain._chain.invoke = MagicMock(return_value="RAG 响应")
        
        result = chain.invoke("测试查询")
        
        assert result.success is True


@pytest.mark.skipif(not LANGCHAIN_AVAILABLE, reason="LangChain 未安装")
class TestToolChain:
    """工具调用链测试"""

    @pytest.fixture
    def mock_tools(self):
        """Mock 工具列表"""
        tool1 = MagicMock()
        tool1.name = "query_supplier"
        tool1.description = "查询供应商"
        tool1.ainvoke = AsyncMock(return_value="供应商信息")
        
        tool2 = MagicMock()
        tool2.name = "query_inventory"
        tool2.description = "查询库存"
        tool2.ainvoke = AsyncMock(return_value="库存信息")
        
        return [tool1, tool2]

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM"""
        llm = MagicMock()
        llm.invoke = MagicMock(return_value=MagicMock(content="工具名称：query_supplier"))
        return llm

    def test_format_tools(self, mock_tools, mock_llm):
        """测试格式化工具列表"""
        chain = ToolChain(tools=mock_tools, llm=mock_llm)
        
        formatted = chain._format_tools()
        
        assert "query_supplier" in formatted
        assert "查询供应商" in formatted
        assert "query_inventory" in formatted

    def test_parse_tool_name(self, mock_tools, mock_llm):
        """测试解析工具名称"""
        chain = ToolChain(tools=mock_tools, llm=mock_llm)
        
        # 测试中文格式
        result = chain._parse_tool_name("根据分析，工具名称：query_supplier 是最合适的")
        assert result == "query_supplier"
        
        # 测试英文格式
        result = chain._parse_tool_name("tool_name: query_inventory")
        assert result == "query_inventory"
        
        # 测试无匹配
        result = chain._parse_tool_name("没有工具名称")
        assert result is None

    @pytest.mark.asyncio
    async def test_ainvoke(self, mock_tools, mock_llm):
        """测试异步执行"""
        chain = ToolChain(tools=mock_tools, llm=mock_llm)
        
        chain._selection_chain.ainvoke = AsyncMock(return_value="工具名称：query_supplier")
        
        result = await chain.ainvoke("查询华南地区的供应商")
        
        assert result.success is True
        assert result.metadata["tool_name"] == "query_supplier"

    @pytest.mark.asyncio
    async def test_ainvoke_no_tool(self, mock_tools, mock_llm):
        """测试异步执行（无匹配工具）"""
        chain = ToolChain(tools=mock_tools, llm=mock_llm)
        
        chain._selection_chain.ainvoke = AsyncMock(return_value="没有合适的工具")
        
        result = await chain.ainvoke("不明确的请求")
        
        assert result.success is False
        assert "无法确定" in result.error


@pytest.mark.skipif(not LANGCHAIN_AVAILABLE, reason="LangChain 未安装")
class TestDecisionChain:
    """决策验证链测试"""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM"""
        llm = MagicMock()
        llm.invoke = MagicMock(return_value=MagicMock(content="验证通过"))
        return llm

    @pytest.mark.asyncio
    async def test_ainvoke(self, mock_llm):
        """测试异步执行"""
        chain = DecisionChain(llm=mock_llm)
        
        chain._chain.ainvoke = AsyncMock(return_value="验证通过：结果符合预期")
        
        result = await chain.ainvoke(
            task="查询库存",
            result="库存充足，共1000件",
        )
        
        assert result.success is True
        assert "验证通过" in result.output

    @pytest.mark.asyncio
    async def test_ainvoke_error(self, mock_llm):
        """测试异步执行错误"""
        chain = DecisionChain(llm=mock_llm)
        
        chain._chain.ainvoke = AsyncMock(side_effect=Exception("验证失败"))
        
        result = await chain.ainvoke(task="测试", result="结果")
        
        assert result.success is False
        assert "验证失败" in result.error


@pytest.mark.skipif(not LANGCHAIN_AVAILABLE, reason="LangChain 未安装")
class TestOpsChainExecutor:
    """链执行器测试"""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM"""
        return MagicMock()

    @pytest.fixture
    def mock_retriever(self):
        """Mock 检索器"""
        retriever = MagicMock()
        return retriever

    @pytest.fixture
    def mock_tools(self):
        """Mock 工具"""
        tool = MagicMock()
        tool.name = "test_tool"
        tool.description = "测试工具"
        return [tool]

    def test_init(self, mock_llm):
        """测试初始化"""
        executor = OpsChainExecutor(llm=mock_llm)
        
        assert executor._llm == mock_llm
        assert executor._retriever is None
        assert len(executor._tools) == 0

    def test_set_retriever(self, mock_llm, mock_retriever):
        """测试设置检索器"""
        executor = OpsChainExecutor(llm=mock_llm)
        executor.set_retriever(mock_retriever)
        
        assert executor._retriever == mock_retriever
        assert executor._rag_chain is not None

    def test_register_tools(self, mock_llm, mock_tools):
        """测试注册工具"""
        executor = OpsChainExecutor(llm=mock_llm)
        executor.register_tools(mock_tools)
        
        assert len(executor._tools) == 1
        assert executor._tool_chain is not None

    def test_add_tool(self, mock_llm, mock_tools):
        """测试添加工具"""
        executor = OpsChainExecutor(llm=mock_llm)
        executor.register_tools([])
        
        new_tool = MagicMock()
        new_tool.name = "new_tool"
        new_tool.description = "新工具"
        
        executor.add_tool(new_tool)
        
        assert len(executor._tools) == 1

    @pytest.mark.asyncio
    async def test_execute_rag_no_retriever(self, mock_llm):
        """测试执行 RAG（无检索器）"""
        executor = OpsChainExecutor(llm=mock_llm)
        
        result = await executor.execute_rag("测试查询")
        
        assert result.success is False
        assert "未设置检索器" in result.error

    @pytest.mark.asyncio
    async def test_execute_tool_no_tools(self, mock_llm):
        """测试执行工具（无工具）"""
        executor = OpsChainExecutor(llm=mock_llm)
        
        result = await executor.execute_tool("测试查询")
        
        assert result.success is False
        assert "未注册工具" in result.error

    @pytest.mark.asyncio
    async def test_execute_full_flow(self, mock_llm, mock_retriever, mock_tools):
        """测试执行完整流程"""
        executor = OpsChainExecutor(llm=mock_llm)
        executor.set_retriever(mock_retriever)
        executor.register_tools(mock_tools)
        
        # Mock 各个链的执行
        executor._rag_chain.ainvoke = AsyncMock(
            return_value=ChainResult(success=True, output="RAG 结果")
        )
        executor._tool_chain.ainvoke = AsyncMock(
            return_value=ChainResult(success=True, output="工具结果")
        )
        executor._decision_chain = DecisionChain(mock_llm)
        executor._decision_chain._chain.ainvoke = AsyncMock(
            return_value="验证通过"
        )
        
        result = await executor.execute(
            query="测试查询",
            use_rag=True,
            use_tools=True,
            verify=True,
        )
        
        assert result["query"] == "测试查询"
        assert result["rag_result"] == "RAG 结果"
        assert result["tool_result"] == "工具结果"


class TestConvenienceFunctions:
    """便捷函数测试"""

    @pytest.mark.skipif(not LANGCHAIN_AVAILABLE, reason="LangChain 未安装")
    def test_create_rag_chain(self):
        """测试创建 RAG 链"""
        mock_retriever = MagicMock()
        mock_llm = MagicMock()
        
        with patch.object(RAGChain, '__init__', return_value=None):
            chain = create_rag_chain(mock_retriever, mock_llm)
            assert chain is not None

    @pytest.mark.skipif(not LANGCHAIN_AVAILABLE, reason="LangChain 未安装")
    def test_create_tool_chain(self):
        """测试创建工具链"""
        mock_tools = [MagicMock()]
        mock_llm = MagicMock()
        
        with patch.object(ToolChain, '__init__', return_value=None):
            chain = create_tool_chain(mock_tools, mock_llm)
            assert chain is not None

    @pytest.mark.skipif(not LANGCHAIN_AVAILABLE, reason="LangChain 未安装")
    def test_create_decision_chain(self):
        """测试创建决策链"""
        mock_llm = MagicMock()
        
        with patch.object(DecisionChain, '__init__', return_value=None):
            chain = create_decision_chain(mock_llm)
            assert chain is not None
