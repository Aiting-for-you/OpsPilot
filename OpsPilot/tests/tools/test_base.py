"""
工具基类模块单元测试
"""
import pytest
import asyncio

from opspilot.tools.base import (
    ToolStatus,
    FallbackMode,
    ToolSchema,
    ToolResult,
    ToolContext,
    BaseToolServer,
    ToolRouter,
)


class TestToolSchema:
    """工具 Schema 测试"""

    def test_create_schema(self):
        """测试创建 Schema"""
        schema = ToolSchema(
            name="test_tool",
            description="测试工具",
            input_schema={
                "type": "object",
                "properties": {"param": {"type": "string"}}
            }
        )
        assert schema.name == "test_tool"
        assert schema.timeout_seconds == 30

    def test_to_mcp_format(self):
        """测试转换为 MCP 格式"""
        schema = ToolSchema(
            name="test_tool",
            description="测试工具",
            input_schema={"type": "object"}
        )
        mcp_format = schema.to_mcp_format()

        assert mcp_format["name"] == "test_tool"
        assert "inputSchema" in mcp_format

    def test_validate_input_success(self):
        """测试输入验证成功"""
        schema = ToolSchema(
            name="test_tool",
            description="测试工具",
            input_schema={
                "type": "object",
                "required": ["name"],
                "properties": {"name": {"type": "string"}}
            }
        )

        assert schema.validate_input({"name": "test"}) is True

    def test_validate_input_failure(self):
        """测试输入验证失败"""
        schema = ToolSchema(
            name="test_tool",
            description="测试工具",
            input_schema={
                "type": "object",
                "required": ["name"],
                "properties": {"name": {"type": "string"}}
            }
        )

        # 缺少必需参数
        assert schema.validate_input({}) is False


class TestToolResult:
    """工具执行结果测试"""

    def test_success_result(self):
        """测试成功结果"""
        result = ToolResult.success({"data": "test"}, latency_ms=100)

        assert result.status == ToolStatus.SUCCESS
        assert result.data == {"data": "test"}
        assert result.latency_ms == 100
        assert result.is_success() is True

    def test_error_result(self):
        """测试错误结果"""
        result = ToolResult.error(
            error="执行失败",
            error_code="EXECUTION_ERROR",
            retry_suggested=True,
            fallback_mode=FallbackMode.GUI_MODE
        )

        assert result.status == ToolStatus.ERROR
        assert result.error == "执行失败"
        assert result.retry_suggested is True
        assert result.fallback_mode == FallbackMode.GUI_MODE

    def test_timeout_result(self):
        """测试超时结果"""
        result = ToolResult.timeout(latency_ms=30000)

        assert result.status == ToolStatus.TIMEOUT
        assert result.retry_suggested is True
        assert result.fallback_mode == FallbackMode.GUI_MODE

    def test_to_dict(self):
        """测试转换为字典"""
        result = ToolResult.success({"data": "test"})
        data = result.to_dict()

        assert data["status"] == "success"
        assert data["data"] == {"data": "test"}


class TestToolContext:
    """工具执行上下文测试"""

    def test_create_context(self):
        """测试创建上下文"""
        context = ToolContext(
            task_id="task-123",
            state="EXECUTING",
            user_id="user-001"
        )

        assert context.task_id == "task-123"
        assert context.state == "EXECUTING"


class MockToolServer(BaseToolServer):
    """Mock 工具服务器"""

    def __init__(self):
        super().__init__("mock-server", "Mock 测试服务器")
        self._register_tools()

    def _register_tools(self):
        @self.register_tool(ToolSchema(
            name="echo",
            description="返回输入内容",
            input_schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                }
            }
        ))
        async def echo(params: dict, context: ToolContext) -> ToolResult:
            return ToolResult.success({"echo": params.get("message", "")})

        @self.register_tool(ToolSchema(
            name="slow_tool",
            description="慢工具",
            input_schema={"type": "object"},
            timeout_seconds=1
        ))
        async def slow_tool(params: dict, context: ToolContext) -> ToolResult:
            await asyncio.sleep(2)
            return ToolResult.success({"done": True})

        @self.register_tool(ToolSchema(
            name="error_tool",
            description="错误工具",
            input_schema={"type": "object"}
        ))
        async def error_tool(params: dict, context: ToolContext) -> ToolResult:
            raise Exception("工具执行出错")

    async def health_check(self) -> bool:
        return True


class TestBaseToolServer:
    """工具服务器基类测试"""

    @pytest.fixture
    def server(self):
        return MockToolServer()

    @pytest.mark.asyncio
    async def test_has_tool(self, server):
        """测试工具存在检查"""
        assert server.has_tool("echo") is True
        assert server.has_tool("nonexistent") is False

    def test_get_tool_schema(self, server):
        """测试获取工具 Schema"""
        schema = server.get_tool_schema("echo")
        assert schema.name == "echo"

    def test_get_all_schemas(self, server):
        """测试获取所有 Schema"""
        schemas = server.get_all_schemas()
        assert len(schemas) == 3

    @pytest.mark.asyncio
    async def test_execute_tool_success(self, server):
        """测试执行工具成功"""
        context = ToolContext(task_id="test")
        result = await server.execute_tool("echo", {"message": "hello"}, context)

        assert result.is_success()
        assert result.data == {"echo": "hello"}

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, server):
        """测试执行不存在的工具"""
        context = ToolContext(task_id="test")
        result = await server.execute_tool("nonexistent", {}, context)

        assert result.status == ToolStatus.ERROR
        assert result.error_code == "TOOL_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_execute_tool_invalid_params(self, server):
        """测试执行参数校验失败"""
        # 创建需要必需参数的工具
        schema = ToolSchema(
            name="required_param_tool",
            description="需要必需参数的工具",
            input_schema={
                "type": "object",
                "required": ["required_field"],
                "properties": {
                    "required_field": {"type": "string"}
                }
            }
        )

        @server.register_tool(schema)
        async def required_tool(params: dict, context: ToolContext) -> ToolResult:
            return ToolResult.success({})

        context = ToolContext(task_id="test")
        result = await server.execute_tool("required_param_tool", {}, context)

        assert result.status == ToolStatus.ERROR
        assert result.error_code == "INVALID_PARAMS"

    @pytest.mark.asyncio
    async def test_execute_tool_timeout(self, server):
        """测试执行超时"""
        context = ToolContext(task_id="test")
        result = await server.execute_tool("slow_tool", {}, context)

        assert result.status == ToolStatus.TIMEOUT

    @pytest.mark.asyncio
    async def test_execute_tool_exception(self, server):
        """测试执行异常"""
        context = ToolContext(task_id="test")
        result = await server.execute_tool("error_tool", {}, context)

        assert result.status == ToolStatus.ERROR
        assert "出错" in result.error


class TestToolRouter:
    """工具路由器测试"""

    @pytest.fixture
    def router(self):
        router = ToolRouter()
        router.register_server(MockToolServer())
        return router

    def test_register_server(self, router):
        """测试注册服务器"""
        assert router.has_tool("echo") is True

    def test_get_server(self, router):
        """测试获取服务器"""
        server = router.get_server("echo")
        assert server is not None
        assert server.name == "mock-server"

    def test_get_all_schemas(self, router):
        """测试获取所有 Schema"""
        schemas = router.get_all_schemas()
        assert len(schemas) == 3

    @pytest.mark.asyncio
    async def test_call_tool(self, router):
        """测试调用工具"""
        context = ToolContext(task_id="test")
        result = await router.call_tool("echo", {"message": "test"}, context)

        assert result.is_success()

    @pytest.mark.asyncio
    async def test_call_tool_not_found(self, router):
        """测试调用不存在的工具"""
        context = ToolContext(task_id="test")
        result = await router.call_tool("nonexistent", {}, context)

        assert result.error_code == "TOOL_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_call_tool_with_retry_success(self, router):
        """测试带重试的调用成功"""
        context = ToolContext(task_id="test")
        result = await router.call_tool_with_retry(
            "echo",
            {"message": "test"},
            context,
            max_retries=2
        )

        assert result.is_success()

    @pytest.mark.asyncio
    async def test_unregister_server(self, router):
        """测试注销服务器"""
        router.unregister_server("mock-server")
        assert router.has_tool("echo") is False

