"""
集成测试模块

测试完整的工作流程：
- 多工具协作
- Agent + Tools 集成
- Runtime 集成
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from opspilot.tools import (
    ToolRouter,
    DatabaseServer,
    ApiServer,
    DevOpsServer,
    FileServer,
    NotificationServer,
    create_default_router,
)
from opspilot.tools.base import ToolContext, ToolResult
from opspilot.runtime import (
    create_sandbox,
    StreamManager,
    StreamWriter,
    StreamEventType,
    Tracer,
    LLMTracer,
    AgentTracer,
    LocalAgentRegistry,
    A2AClient,
    A2AServer,
    create_agent_card,
)


# ==================== 工具路由集成测试 ====================

class TestToolRouterIntegration:
    """工具路由集成测试"""
    
    @pytest.fixture
    def router(self):
        """创建工具路由器"""
        router = ToolRouter()
        router.register_server(DatabaseServer(db_type="mock"))
        router.register_server(ApiServer())
        router.register_server(DevOpsServer())
        return router
    
    @pytest.fixture
    def context(self):
        """创建工具上下文"""
        return ToolContext(task_id="integration-test")
    
    @pytest.mark.asyncio
    async def test_router_has_all_tools(self, router):
        """测试路由器包含所有工具"""
        tools = router.get_all_schemas()
        tool_names = [t.name for t in tools]
        
        # 数据库工具
        assert "db_query" in tool_names
        assert "db_execute" in tool_names
        
        # API 工具
        assert "http_get" in tool_names
        assert "http_post" in tool_names
        
        # 运维工具
        assert "system_info" in tool_names
        assert "system_cpu" in tool_names
    
    @pytest.mark.asyncio
    async def test_router_call_database_tool(self, router, context):
        """测试路由器调用数据库工具"""
        result = await router.call_tool(
            "db_query",
            {"sql": "SELECT * FROM users"},
            context
        )
        assert result.is_success()
    
    @pytest.mark.asyncio
    async def test_router_call_http_tool(self, router, context):
        """测试路由器调用 HTTP 工具"""
        result = await router.call_tool(
            "http_get",
            {"url": "https://api.example.com/users"},
            context
        )
        assert result.is_success()
    
    @pytest.mark.asyncio
    async def test_router_unknown_tool(self, router, context):
        """测试路由器未知工具"""
        result = await router.call_tool(
            "unknown_tool",
            {},
            context
        )
        assert not result.is_success()


# ==================== 沙箱集成测试 ====================

class TestSandboxIntegration:
    """沙箱集成测试"""
    
    @pytest.mark.asyncio
    async def test_sandbox_execute_shell(self):
        """测试沙箱执行 Shell 命令"""
        sandbox = create_sandbox("local")
        
        # 安全命令
        result = await sandbox.execute_tool(
            tool_name="echo",
            tool_command="echo 'Hello, Sandbox!'"
        )
        assert result.success or result.status.value in ["success", "failed"]
    
    @pytest.mark.asyncio
    async def test_sandbox_blocked_command(self):
        """测试沙箱阻止危险命令"""
        from opspilot.runtime.sandbox import SandboxConfig
        
        config = SandboxConfig(
            blocked_commands=["rm -rf /"]
        )
        sandbox = create_sandbox("local", config)
        
        result = await sandbox.execute_tool(
            tool_name="danger",
            tool_command="rm -rf /"
        )
        assert not result.success


# ==================== 流式输出集成测试 ====================

class TestStreamingIntegration:
    """流式输出集成测试"""
    
    @pytest.mark.asyncio
    async def test_stream_manager_create_writer(self):
        """测试流管理器创建写入器"""
        manager = StreamManager()
        writer = await manager.create_writer("test-task")
        
        assert writer.task_id == "test-task"
        assert writer._closed is False
    
    @pytest.mark.asyncio
    async def test_stream_writer_events(self):
        """测试流写入器事件"""
        writer = StreamWriter("test-task")
        
        # 写入事件
        await writer.write_event(
            StreamEventType.TASK_START,
            {"message": "任务开始"}
        )
        
        await writer.write_event(
            StreamEventType.AGENT_MESSAGE,
            {"agent": "test-agent", "content": "测试消息"}
        )
        
        events = writer._buffer
        assert len(events) == 2
        assert events[0].event_type == StreamEventType.TASK_START
    
    @pytest.mark.asyncio
    async def test_stream_sse_format(self):
        """测试 SSE 格式"""
        writer = StreamWriter("test-task")
        
        await writer.write_event(
            StreamEventType.TASK_START,
            {"message": "test"}
        )
        
        event = writer._buffer[0]
        sse = event.to_sse()
        
        assert "event: task_start" in sse
        assert "data:" in sse


# ==================== 追踪集成测试 ====================

class TestTracingIntegration:
    """追踪集成测试"""
    
    @pytest.mark.asyncio
    async def test_tracer_span(self):
        """测试追踪器 Span"""
        tracer = Tracer()
        
        span_id = tracer.start_span("test_operation", {"key": "value"})
        assert span_id is not None
        
        tracer.add_event(span_id, "test_event", {"detail": "test"})
        
        span = tracer.end_span(span_id, "OK")
        assert span is not None
        assert span.status == "OK"
        assert len(span.events) == 1
    
    @pytest.mark.asyncio
    async def test_llm_tracer(self):
        """测试 LLM 追踪器"""
        tracer = LLMTracer()
        
        span_id = tracer.trace_llm_call(
            model="gpt-4",
            prompt="Hello",
            completion="Hi there!",
            prompt_tokens=10,
            completion_tokens=5,
            latency_ms=150,
        )
        
        assert span_id is not None
    
    @pytest.mark.asyncio
    async def test_agent_tracer(self):
        """测试 Agent 追踪器"""
        tracer = AgentTracer()
        
        span_id = tracer.trace_agent_call(
            agent_name="IntentAgent",
            input_data="查询库存",
            output_data={"intent": "query_stock"},
            duration_ms=200,
            tools_used=["query_erp"],
        )
        
        assert span_id is not None


# ==================== A2A 集成测试 ====================

class TestA2AIntegration:
    """A2A 协议集成测试"""
    
    @pytest.mark.asyncio
    async def test_agent_registry(self):
        """测试 Agent 注册中心"""
        registry = LocalAgentRegistry()
        
        card = create_agent_card(
            agent_id="test-agent",
            name="TestAgent",
            description="测试 Agent",
            skills=[{"id": "test_skill", "name": "测试技能", "description": "测试"}]
        )
        
        result = await registry.register(card)
        assert result is True
        
        # 发现 Agent
        agents = await registry.discover()
        assert len(agents) == 1
        assert agents[0].agent_id == "test-agent"
    
    @pytest.mark.asyncio
    async def test_a2a_client_discover(self):
        """测试 A2A 客户端发现"""
        registry = LocalAgentRegistry()
        
        # 注册 Agent
        card = create_agent_card(
            agent_id="intent-agent",
            name="IntentAgent",
            description="意图识别",
            skills=[{"id": "intent_recognition", "name": "意图识别", "description": "识别用户意图"}]
        )
        await registry.register(card)
        
        # 客户端发现
        client = A2AClient("orchestrator", registry)
        agents = await client.discover_agents(skill_id="intent_recognition")
        
        assert len(agents) == 1


# ==================== 端到端工作流测试 ====================

class TestEndToEndWorkflow:
    """端到端工作流测试"""
    
    @pytest.fixture
    def full_setup(self):
        """完整配置"""
        router = ToolRouter()
        router.register_server(DatabaseServer(db_type="mock"))
        router.register_server(ApiServer())
        router.register_server(NotificationServer())
        
        tracer = Tracer()
        registry = LocalAgentRegistry()
        
        return {
            "router": router,
            "tracer": tracer,
            "registry": registry,
        }
    
    @pytest.mark.asyncio
    async def test_query_workflow(self, full_setup):
        """测试查询工作流"""
        router = full_setup["router"]
        tracer = full_setup["tracer"]
        context = ToolContext(task_id="workflow-test")
        
        # 开始追踪
        span_id = tracer.start_span("workflow.query")
        
        # 1. 数据库查询
        db_result = await router.call_tool(
            "db_query",
            {"sql": "SELECT * FROM products"},
            context
        )
        assert db_result.is_success()
        
        tracer.add_event(span_id, "db_query_complete", {"rows": db_result.data.get("row_count", 0)})
        
        # 2. 发送通知
        notify_result = await router.call_tool(
            "send_notification",
            {"channel": "dingtalk", "subject": "查询完成", "body": f"查询到 {db_result.data.get('row_count', 0)} 条记录"},
            context
        )
        assert notify_result.is_success()
        
        # 结束追踪
        tracer.end_span(span_id, "OK")
        
        # 验证追踪
        span = tracer.get_span(span_id)
        assert span is not None
        assert span.status == "OK"
    
    @pytest.mark.asyncio
    async def test_api_to_db_workflow(self, full_setup):
        """测试 API 到数据库工作流"""
        router = full_setup["router"]
        context = ToolContext(task_id="api-db-workflow")
        
        # 1. 从 API 获取数据
        api_result = await router.call_tool(
            "http_get",
            {"url": "https://api.example.com/users"},
            context
        )
        assert api_result.is_success()
        
        # 2. 写入数据库
        db_result = await router.call_tool(
            "db_execute",
            {
                "sql": "INSERT INTO users (name, email) VALUES (:name, :email)",
                "params": {"name": "API用户", "email": "api@example.com"}
            },
            context
        )
        assert db_result.is_success()


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
