"""
统一追踪模块

整合 OpenTelemetry、LangSmith 和 AgentScope Studio 的追踪能力。
"""

from __future__ import annotations

import functools
import logging
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TypeVar, ParamSpec

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


@dataclass
class SpanContext:
    """Span 上下文"""
    span_id: str
    trace_id: str
    parent_id: Optional[str] = None
    name: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "UNSET"
    
    def add_event(self, name: str, attributes: Optional[Dict] = None) -> None:
        """添加事件"""
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        })
    
    def set_attribute(self, key: str, value: Any) -> None:
        """设置属性"""
        self.attributes[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": (self.end_time - self.start_time) * 1000 if self.end_time else None,
            "attributes": self.attributes,
            "events": self.events,
            "status": self.status,
        }


class TracingManager:
    """
    统一追踪管理器
    
    整合多种追踪后端。
    
    示例:
        >>> tracing = TracingManager()
        >>> 
        >>> with tracing.span("process_query") as span:
        ...     span.set_attribute("query", query)
        ...     result = await process(query)
        ...     span.add_event("processing_complete")
    """
    
    def __init__(
        self,
        service_name: str = "opspilot",
        enable_otel: bool = True,
        enable_langsmith: bool = True,
    ):
        self.service_name = service_name
        self.enable_otel = enable_otel
        self.enable_langsmith = enable_langsmith
        
        self._spans: Dict[str, SpanContext] = {}
        self._current_span: Optional[SpanContext] = None
        
        # OpenTelemetry
        self._otel_tracer = None
        if enable_otel:
            self._init_otel()
    
    def _init_otel(self) -> None:
        """初始化 OpenTelemetry"""
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import SimpleSpanProcessor
            from opentelemetry.sdk.resources import Resource
            
            resource = Resource.create({"service.name": self.service_name})
            provider = TracerProvider(resource=resource)
            
            # 控制台输出
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter
            processor = SimpleSpanProcessor(ConsoleSpanExporter())
            provider.add_span_processor(processor)
            
            trace.set_tracer_provider(provider)
            self._otel_tracer = trace.get_tracer(self.service_name)
            
        except ImportError:
            logger.warning("OpenTelemetry not installed")
    
    def start_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        parent: Optional[str] = None,
    ) -> SpanContext:
        """开始一个 Span"""
        span = SpanContext(
            span_id=str(uuid.uuid4())[:16],
            trace_id=self._current_span.trace_id if self._current_span else str(uuid.uuid4()),
            parent_id=parent or (self._current_span.span_id if self._current_span else None),
            name=name,
            attributes=attributes or {},
        )
        
        self._spans[span.span_id] = span
        self._current_span = span
        
        return span
    
    def end_span(
        self,
        span: SpanContext,
        status: str = "OK",
    ) -> None:
        """结束 Span"""
        span.end_time = time.time()
        span.status = status
        
        # 恢复父 Span
        if span.parent_id and span.parent_id in self._spans:
            self._current_span = self._spans[span.parent_id]
        else:
            self._current_span = None
    
    @contextmanager
    def span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """
        Span 上下文管理器
        
        示例:
            >>> with tracing.span("process") as span:
            ...     span.set_attribute("key", "value")
        """
        s = self.start_span(name, attributes)
        try:
            yield s
            self.end_span(s, "OK")
        except Exception as e:
            s.set_attribute("error", str(e))
            self.end_span(s, "ERROR")
            raise
    
    def get_trace(self, trace_id: str) -> List[SpanContext]:
        """获取 Trace 的所有 Span"""
        return [s for s in self._spans.values() if s.trace_id == trace_id]
    
    def get_span(self, span_id: str) -> Optional[SpanContext]:
        """获取 Span"""
        return self._spans.get(span_id)
    
    def clear(self) -> None:
        """清除所有 Span"""
        self._spans.clear()
        self._current_span = None


# ============================================================================
# 全局追踪器
# ============================================================================

_tracing: Optional[TracingManager] = None


def get_tracing() -> TracingManager:
    """获取全局追踪器"""
    global _tracing
    if _tracing is None:
        _tracing = TracingManager()
    return _tracing


# ============================================================================
# 装饰器
# ============================================================================

def traced(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    追踪装饰器
    
    示例:
        >>> @traced("process_query")
        ... async def process_query(query: str):
        ...     return await llm.invoke(query)
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        span_name = name or func.__name__
        
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            tracing = get_tracing()
            with tracing.span(span_name, attributes) as span:
                span.set_attribute("function", func.__name__)
                result = await func(*args, **kwargs)
                return result
        
        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            tracing = get_tracing()
            with tracing.span(span_name, attributes) as span:
                span.set_attribute("function", func.__name__)
                result = func(*args, **kwargs)
                return result
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def trace_agent(agent_name: str):
    """
    Agent 追踪装饰器
    
    示例:
        >>> @trace_agent("intent_agent")
        ... class IntentAgent(BaseAgent):
        ...     pass
    """
    return traced(name=f"agent.{agent_name}")


def trace_tool(tool_name: str):
    """
    工具追踪装饰器
    
    示例:
        >>> @trace_tool("query_database")
        ... async def query_database(sql: str):
        ...     return await execute(sql)
    """
    return traced(
        name=f"tool.{tool_name}",
        attributes={"tool.name": tool_name},
    )
