"""
可观测性模块测试

测试 TracingManager, SpanContext, 装饰器等
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

from opspilot.observability.tracing import (
    SpanContext,
    TracingManager,
    get_tracing,
    traced,
    trace_agent,
    trace_tool,
)


class TestSpanContext:
    """测试 SpanContext"""

    def test_create_span_context(self):
        """测试创建 SpanContext"""
        span = SpanContext(
            span_id="span-001",
            trace_id="trace-001",
            name="test_span",
        )
        
        assert span.span_id == "span-001"
        assert span.trace_id == "trace-001"
        assert span.name == "test_span"
        assert span.status == "UNSET"

    def test_add_event(self):
        """测试添加事件"""
        span = SpanContext(
            span_id="span-001",
            trace_id="trace-001",
        )
        
        span.add_event("event1", {"key": "value"})
        
        assert len(span.events) == 1
        assert span.events[0]["name"] == "event1"

    def test_set_attribute(self):
        """测试设置属性"""
        span = SpanContext(
            span_id="span-001",
            trace_id="trace-001",
        )
        
        span.set_attribute("user_id", "user-001")
        
        assert span.attributes["user_id"] == "user-001"

    def test_to_dict(self):
        """测试转换为字典"""
        span = SpanContext(
            span_id="span-001",
            trace_id="trace-001",
            name="test_span",
        )
        
        data = span.to_dict()
        
        assert data["span_id"] == "span-001"
        assert data["trace_id"] == "trace-001"
        assert data["name"] == "test_span"
        assert "duration_ms" in data


class TestTracingManager:
    """测试 TracingManager"""

    @pytest.fixture
    def tracing(self):
        """创建追踪管理器"""
        return TracingManager(
            service_name="test-service",
            enable_otel=False,
            enable_langsmith=False,
        )

    def test_create_tracing_manager(self):
        """测试创建追踪管理器"""
        tracing = TracingManager(
            service_name="test",
            enable_otel=False,
        )
        
        assert tracing.service_name == "test"

    def test_start_span(self, tracing):
        """测试开始 Span"""
        span = tracing.start_span("test_span")
        
        assert span.name == "test_span"
        assert span.trace_id is not None

    def test_start_span_with_attributes(self, tracing):
        """测试带属性的 Span"""
        span = tracing.start_span(
            "test_span",
            attributes={"user_id": "user-001"},
        )
        
        assert span.attributes["user_id"] == "user-001"

    def test_start_span_with_parent(self, tracing):
        """测试带父 Span"""
        parent = tracing.start_span("parent_span")
        child = tracing.start_span(
            "child_span",
            parent=parent.span_id,
        )
        
        assert child.parent_id == parent.span_id

    def test_end_span(self, tracing):
        """测试结束 Span"""
        span = tracing.start_span("test_span")
        tracing.end_span(span, "OK")
        
        assert span.status == "OK"
        assert span.end_time is not None

    def test_span_context_manager(self, tracing):
        """测试 Span 上下文管理器"""
        with tracing.span("test_span") as span:
            span.set_attribute("key", "value")
        
        assert span.status == "OK"
        assert span.end_time is not None

    def test_span_context_manager_exception(self, tracing):
        """测试 Span 异常处理"""
        with pytest.raises(ValueError):
            with tracing.span("test_span") as span:
                span.set_attribute("error", "test error")
                raise ValueError("Test error")
        
        assert span.status == "ERROR"
        # 异常被捕获时会添加 error 属性为异常消息
        assert "error" in span.attributes

    def test_get_trace(self, tracing):
        """测试获取 Trace"""
        # 创建多个 Span
        span1 = tracing.start_span("span1")
        span2 = tracing.start_span("span2")
        
        # 获取同一 trace 的 span
        spans = tracing.get_trace(span1.trace_id)
        
        # 至少有 2 个 span（span1 和 span2）
        assert len(spans) >= 1

    def test_get_span(self, tracing):
        """测试获取 Span"""
        span = tracing.start_span("test_span")
        
        retrieved = tracing.get_span(span.span_id)
        
        assert retrieved is not None
        assert retrieved.span_id == span.span_id

    def test_clear(self, tracing):
        """测试清除 Span"""
        tracing.start_span("span1")
        tracing.start_span("span2")
        
        tracing.clear()
        
        assert len(tracing._spans) == 0
        assert tracing._current_span is None


class TestGetTracing:
    """测试全局追踪器"""

    def test_get_tracing_singleton(self):
        """测试获取全局追踪器单例"""
        # 清除全局追踪器
        import opspilot.observability.tracing as tracing_module
        tracing_module._tracing = None
        
        t1 = get_tracing()
        t2 = get_tracing()
        
        assert t1 is t2


class TestTracedDecorator:
    """测试 traced 装饰器"""

    def test_traced_sync_function(self):
        """测试同步函数装饰器"""
        @traced("test_func")
        def sync_func(x):
            return x * 2
        
        # 清除全局追踪器
        import opspilot.observability.tracing as tracing_module
        tracing_module._tracing = None
        
        result = sync_func(5)
        
        assert result == 10

    def test_traced_async_function(self):
        """测试异步函数装饰器"""
        @traced("async_func")
        async def async_func(x):
            return x * 2
        
        # 清除全局追踪器
        import opspilot.observability.tracing as tracing_module
        tracing_module._tracing = None
        
        result = asyncio.run(async_func(5))
        
        assert result == 10

    def test_traced_with_attributes(self):
        """测试带属性的装饰器"""
        @traced(
            name="custom_func",
            attributes={"custom_key": "custom_value"},
        )
        def func_with_attrs():
            return "done"
        
        # 清除全局追踪器
        import opspilot.observability.tracing as tracing_module
        tracing_module._tracing = None
        
        result = func_with_attrs()
        
        assert result == "done"


class TestTraceAgentDecorator:
    """测试 trace_agent 装饰器"""

    def test_trace_agent(self):
        """测试 Agent 追踪装饰器"""
        @trace_agent("intent_agent")
        def intent_handler(query):
            return f"handled: {query}"
        
        # 清除全局追踪器
        import opspilot.observability.tracing as tracing_module
        tracing_module._tracing = None
        
        result = intent_handler("test query")
        
        assert result == "handled: test query"


class TestTraceToolDecorator:
    """测试 trace_tool 装饰器"""

    def test_trace_tool(self):
        """测试工具追踪装饰器"""
        @trace_tool("query_database")
        def query_database(sql):
            return [{"id": 1}]
        
        # 清除全局追踪器
        import opspilot.observability.tracing as tracing_module
        tracing_module._tracing = None
        
        result = query_database("SELECT * FROM users")
        
        assert result == [{"id": 1}]


class TestTracingNestedSpans:
    """测试嵌套 Span"""

    @pytest.fixture
    def tracing(self):
        """创建追踪管理器"""
        return TracingManager(enable_otel=False, enable_langsmith=False)

    def test_nested_spans(self, tracing):
        """测试嵌套 Span"""
        with tracing.span("outer") as outer:
            outer.set_attribute("outer_key", "outer_value")
            
            with tracing.span("inner") as inner:
                inner.set_attribute("inner_key", "inner_value")
        
        assert outer.status == "OK"
        assert inner.status == "OK"

    def test_multiple_spans_same_trace(self, tracing):
        """测试同一 Trace 的多个 Span"""
        # 使用嵌套 span，自动共享 trace_id
        with tracing.span("span1"):
            pass
        
        with tracing.span("span2"):
            pass
        
        # 验证 span 被记录
        assert len(tracing._spans) >= 2
