"""
追踪模块单元测试
"""
import pytest
import time

from opspilot.runtime.tracing import (
    Tracer,
    LLMTracer,
    AgentTracer,
    ToolTracer,
    TraceSpan,
    get_tracer,
    get_llm_tracer,
    get_agent_tracer,
    get_tool_tracer,
    traced,
    OTEL_AVAILABLE,
)


class TestTraceSpan:
    """追踪 Span 测试"""

    def test_create_span(self):
        """测试创建 Span"""
        span = TraceSpan(
            span_id="span-123",
            trace_id="trace-456",
            name="test_span",
            start_time=time.time(),
        )
        
        assert span.span_id == "span-123"
        assert span.trace_id == "trace-456"
        assert span.name == "test_span"
        assert span.status == "UNSET"
        assert span.end_time is None

    def test_end_span(self):
        """测试结束 Span"""
        span = TraceSpan(
            span_id="span-123",
            trace_id="trace-456",
            name="test_span",
            start_time=time.time() - 0.1,
        )
        
        span.end_time = time.time()
        span.duration_ms = (span.end_time - span.start_time) * 1000
        span.status = "OK"
        
        assert span.end_time is not None
        assert span.duration_ms > 0
        assert span.status == "OK"

    def test_to_dict(self):
        """测试转换为字典"""
        span = TraceSpan(
            span_id="span-123",
            trace_id="trace-456",
            name="test_span",
            start_time=1000.0,
            end_time=1001.0,
            duration_ms=1000.0,
            attributes={"key": "value"},
            events=[{"name": "event1"}],
            status="OK",
        )
        
        data = span.to_dict()
        
        assert data["span_id"] == "span-123"
        assert data["trace_id"] == "trace-456"
        assert data["duration_ms"] == 1000.0
        assert data["attributes"] == {"key": "value"}
        assert data["status"] == "OK"


class TestTracer:
    """追踪器测试"""

    @pytest.fixture
    def tracer(self):
        return Tracer(service_name="test-service")

    def test_initial_state(self, tracer):
        """测试初始状态"""
        assert tracer.service_name == "test-service"
        assert len(tracer._spans) == 0

    def test_available(self, tracer):
        """测试可用性检查"""
        # 结果取决于是否安装了 OpenTelemetry
        assert isinstance(tracer.available, bool)

    def test_start_span(self, tracer):
        """测试开始 Span"""
        span_id = tracer.start_span(
            name="test_span",
            attributes={"key": "value"},
        )
        
        assert span_id is not None
        assert span_id in tracer._spans
        
        span = tracer._spans[span_id]
        assert span.name == "test_span"
        assert span.attributes["key"] == "value"

    def test_end_span(self, tracer):
        """测试结束 Span"""
        span_id = tracer.start_span("test_span")
        result = tracer.end_span(span_id, "OK", {"extra": "attr"})
        
        assert result is not None
        assert result.status == "OK"
        assert result.end_time is not None
        assert result.duration_ms > 0
        assert result.attributes["extra"] == "attr"

    def test_end_nonexistent_span(self, tracer):
        """测试结束不存在的 Span"""
        result = tracer.end_span("nonexistent")
        assert result is None

    def test_add_event(self, tracer):
        """测试添加事件"""
        span_id = tracer.start_span("test_span")
        tracer.add_event(span_id, "test_event", {"event_key": "event_value"})
        
        span = tracer._spans[span_id]
        assert len(span.events) == 1
        assert span.events[0]["name"] == "test_event"

    def test_get_span(self, tracer):
        """测试获取 Span"""
        span_id = tracer.start_span("test_span")
        
        span = tracer.get_span(span_id)
        assert span is not None
        assert span.name == "test_span"
        
        # 不存在的 Span
        span = tracer.get_span("nonexistent")
        assert span is None

    def test_get_trace(self, tracer):
        """测试获取 Trace 的所有 Span"""
        # 创建多个 Span（模拟同一 trace）
        span1 = tracer.start_span("span1")
        tracer._spans[span1].trace_id = "trace-123"
        
        span2 = tracer.start_span("span2")
        tracer._spans[span2].trace_id = "trace-123"
        
        span3 = tracer.start_span("span3")
        tracer._spans[span3].trace_id = "trace-456"
        
        spans = tracer.get_trace("trace-123")
        assert len(spans) == 2

    def test_clear_spans(self, tracer):
        """测试清理 Span"""
        tracer.start_span("span1")
        tracer.start_span("span2")
        
        assert len(tracer._spans) == 2
        
        tracer.clear_spans()
        assert len(tracer._spans) == 0

    def test_span_context_manager(self, tracer):
        """测试 Span 上下文管理器"""
        with tracer.span("test_span", {"key": "value"}) as span_id:
            assert span_id in tracer._spans
            span = tracer._spans[span_id]
            assert span.name == "test_span"
        
        # 退出后 Span 应该已结束
        span = tracer._spans[span_id]
        assert span.status == "OK"
        assert span.end_time is not None

    def test_span_context_manager_error(self, tracer):
        """测试 Span 上下文管理器（错误情况）"""
        with pytest.raises(ValueError):
            with tracer.span("test_span") as span_id:
                raise ValueError("测试错误")
        
        # Span 应该记录了错误
        span = tracer._spans[span_id]
        assert span.status == "ERROR"
        assert "error" in span.attributes

    def test_traced_decorator_async(self, tracer):
        """测试追踪装饰器（异步函数）"""
        @tracer.traced("custom_name", {"extra": "attr"})
        async def async_function():
            await asyncio.sleep(0.01)
            return "result"
        
        import asyncio
        result = asyncio.run(async_function())
        
        assert result == "result"
        # 应该创建了一个 Span
        assert len(tracer._spans) == 1

    def test_traced_decorator_sync(self, tracer):
        """测试追踪装饰器（同步函数）"""
        @tracer.traced()
        def sync_function():
            return "result"
        
        result = sync_function()
        
        assert result == "result"
        assert len(tracer._spans) == 1


class TestLLMTracer:
    """LLM 追踪器测试"""

    @pytest.fixture
    def tracer(self):
        return LLMTracer()

    def test_trace_llm_call(self, tracer):
        """测试追踪 LLM 调用"""
        span_id = tracer.trace_llm_call(
            model="gpt-4",
            prompt="Hello",
            completion="World",
            prompt_tokens=10,
            completion_tokens=5,
            latency_ms=100.5,
        )
        
        assert span_id is not None
        
        span = tracer.get_span(span_id)
        assert span is not None
        assert "llm.call.gpt-4" in span.name
        assert span.attributes["llm.model"] == "gpt-4"
        assert span.attributes["llm.total_tokens"] == 15
        assert len(span.events) == 2  # prompt + completion


class TestAgentTracer:
    """Agent 追踪器测试"""

    @pytest.fixture
    def tracer(self):
        return AgentTracer()

    def test_trace_agent_call(self, tracer):
        """测试追踪 Agent 调用"""
        span_id = tracer.trace_agent_call(
            agent_name="IntentAgent",
            input_data="查询供应商",
            output_data={"intent": "query_supplier"},
            duration_ms=50.5,
            tools_used=["query_supplier"],
        )
        
        assert span_id is not None
        
        span = tracer.get_span(span_id)
        assert span is not None
        assert "agent.call.IntentAgent" in span.name
        assert span.attributes["agent.name"] == "IntentAgent"
        assert span.attributes["agent.tools_used"] == ["query_supplier"]


class TestToolTracer:
    """工具追踪器测试"""

    @pytest.fixture
    def tracer(self):
        return ToolTracer()

    def test_trace_tool_call(self, tracer):
        """测试追踪工具调用"""
        span_id = tracer.trace_tool_call(
            tool_name="query_supplier",
            params={"region": "华南"},
            result={"suppliers": []},
            duration_ms=20.5,
            success=True,
        )
        
        assert span_id is not None
        
        span = tracer.get_span(span_id)
        assert span is not None
        assert "tool.call.query_supplier" in span.name
        assert span.attributes["tool.success"] is True

    def test_trace_tool_call_error(self, tracer):
        """测试追踪工具调用（错误）"""
        span_id = tracer.trace_tool_call(
            tool_name="error_tool",
            params={},
            result=None,
            duration_ms=10.0,
            success=False,
        )
        
        span = tracer.get_span(span_id)
        assert span.status == "ERROR"


class TestGlobalTracers:
    """全局追踪器测试"""

    def test_get_tracer(self):
        """测试获取全局追踪器"""
        tracer1 = get_tracer()
        tracer2 = get_tracer()
        
        assert tracer1 is tracer2

    def test_get_llm_tracer(self):
        """测试获取 LLM 追踪器"""
        tracer1 = get_llm_tracer()
        tracer2 = get_llm_tracer()
        
        assert tracer1 is tracer2

    def test_get_agent_tracer(self):
        """测试获取 Agent 追踪器"""
        tracer1 = get_agent_tracer()
        tracer2 = get_agent_tracer()
        
        assert tracer1 is tracer2

    def test_get_tool_tracer(self):
        """测试获取工具追踪器"""
        tracer1 = get_tool_tracer()
        tracer2 = get_tool_tracer()
        
        assert tracer1 is tracer2


class TestTracedDecorator:
    """追踪装饰器测试"""

    @pytest.mark.asyncio
    async def test_traced_decorator(self):
        """测试 traced 装饰器"""
        @traced("custom_operation")
        async def operation():
            return "done"
        
        result = await operation()
        
        assert result == "done"
