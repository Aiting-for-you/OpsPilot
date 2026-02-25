"""
OpenTelemetry 追踪模块

基于 AgentScope Studio 的可视化追踪能力。
提供完整的链路追踪、性能监控和调试支持。

特性：
- LLM 调用追踪（Token 使用、耗时）
- Agent 调用链追踪
- 工具执行追踪
- 自定义 Span
"""

from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, ParamSpec

# OpenTelemetry imports
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.trace import Status, StatusCode, Span
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    from opentelemetry.context import Context
    
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None
    Span = None


P = ParamSpec("P")
T = TypeVar("T")


@dataclass
class TraceSpan:
    """追踪 Span 数据"""
    span_id: str
    trace_id: str
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "UNSET"
    parent_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "attributes": self.attributes,
            "events": self.events,
            "status": self.status,
            "parent_id": self.parent_id,
        }


class Tracer:
    """
    追踪器
    
    提供统一的追踪接口。
    """
    
    def __init__(self, service_name: str = "opspilot"):
        self.service_name = service_name
        self._tracer = None
        self._spans: Dict[str, TraceSpan] = {}
        
        if OTEL_AVAILABLE:
            self._init_opentelemetry()
    
    def _init_opentelemetry(self):
        """初始化 OpenTelemetry"""
        resource = Resource.create({"service.name": self.service_name})
        provider = TracerProvider(resource=resource)
        
        # 默认使用控制台输出，生产环境可替换为 OTLP
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter
        processor = SimpleSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(processor)
        
        trace.set_tracer_provider(provider)
        self._tracer = trace.get_tracer(self.service_name)
    
    @property
    def available(self) -> bool:
        """追踪器是否可用"""
        return OTEL_AVAILABLE and self._tracer is not None
    
    def start_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        parent: Optional[str] = None,
    ) -> str:
        """
        开始一个 Span
        
        Args:
            name: Span 名称
            attributes: 属性
            parent: 父 Span ID
        
        Returns:
            str: Span ID
        """
        span_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())
        
        span = TraceSpan(
            span_id=span_id,
            trace_id=trace_id,
            name=name,
            start_time=time.time(),
            attributes=attributes or {},
            parent_id=parent,
        )
        
        self._spans[span_id] = span
        
        if self.available and self._tracer:
            otel_span = self._tracer.start_span(name)
            otel_span.set_attribute("span_id", span_id)
            otel_span.set_attribute("trace_id", trace_id)
            if attributes:
                for key, value in attributes.items():
                    otel_span.set_attribute(key, str(value))
            # 存储 OTEL span 引用
            span.attributes["_otel_span"] = otel_span
        
        return span_id
    
    def end_span(
        self,
        span_id: str,
        status: str = "OK",
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Optional[TraceSpan]:
        """
        结束 Span
        
        Args:
            span_id: Span ID
            status: 状态
            attributes: 额外属性
        
        Returns:
            TraceSpan: 完成的 Span
        """
        span = self._spans.get(span_id)
        if not span:
            return None
        
        span.end_time = time.time()
        span.duration_ms = (span.end_time - span.start_time) * 1000
        span.status = status
        
        if attributes:
            span.attributes.update(attributes)
        
        if self.available:
            otel_span = span.attributes.pop("_otel_span", None)
            if otel_span:
                otel_span.set_status(Status(StatusCode.OK if status == "OK" else StatusCode.ERROR))
                otel_span.end()
        
        return span
    
    def add_event(
        self,
        span_id: str,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        添加事件到 Span
        
        Args:
            span_id: Span ID
            name: 事件名称
            attributes: 事件属性
        """
        span = self._spans.get(span_id)
        if span:
            event = {
                "name": name,
                "timestamp": time.time(),
                "attributes": attributes or {},
            }
            span.events.append(event)
            
            if self.available:
                otel_span = span.attributes.get("_otel_span")
                if otel_span:
                    otel_span.add_event(name, attributes or {})
    
    def get_span(self, span_id: str) -> Optional[TraceSpan]:
        """获取 Span"""
        return self._spans.get(span_id)
    
    def get_trace(self, trace_id: str) -> List[TraceSpan]:
        """
        获取 Trace 的所有 Span
        
        Args:
            trace_id: Trace ID
        
        Returns:
            List[TraceSpan]: Span 列表
        """
        return [s for s in self._spans.values() if s.trace_id == trace_id]
    
    def clear_spans(self, trace_id: Optional[str] = None) -> None:
        """
        清理 Span
        
        Args:
            trace_id: 指定 Trace ID，为空则清理全部
        """
        if trace_id:
            self._spans = {
                k: v for k, v in self._spans.items()
                if v.trace_id != trace_id
            }
        else:
            self._spans.clear()
    
    @contextmanager
    def span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """
        Span 上下文管理器
        
        Args:
            name: Span 名称
            attributes: 属性
        
        Yields:
            str: Span ID
        """
        span_id = self.start_span(name, attributes)
        try:
            yield span_id
            self.end_span(span_id, "OK")
        except Exception as e:
            self.end_span(span_id, "ERROR", {"error": str(e)})
            raise
    
    def traced(
        self,
        name: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Callable[[Callable[P, T]], Callable[P, T]]:
        """
        追踪装饰器
        
        Args:
            name: Span 名称（默认使用函数名）
            attributes: 属性
        
        Returns:
            装饰器
        """
        def decorator(func: Callable[P, T]) -> Callable[P, T]:
            span_name = name or func.__name__
            
            @wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                with self.span(span_name, attributes) as span_id:
                    result = await func(*args, **kwargs)
                    self.add_event(span_id, "function_complete")
                    return result
            
            @wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                with self.span(span_name, attributes) as span_id:
                    result = func(*args, **kwargs)
                    self.add_event(span_id, "function_complete")
                    return result
            
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        
        return decorator


class LLMTracer(Tracer):
    """
    LLM 调用追踪器
    
    专门追踪 LLM 调用，记录 Token 使用和耗时。
    """
    
    def trace_llm_call(
        self,
        model: str,
        prompt: str,
        completion: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        追踪 LLM 调用
        
        Args:
            model: 模型名称
            prompt: 提示词
            completion: 补全内容
            prompt_tokens: 提示词 Token 数
            completion_tokens: 补全 Token 数
            latency_ms: 延迟（毫秒）
            metadata: 元数据
        
        Returns:
            str: Span ID
        """
        attributes = {
            "llm.model": model,
            "llm.prompt_tokens": prompt_tokens,
            "llm.completion_tokens": completion_tokens,
            "llm.total_tokens": prompt_tokens + completion_tokens,
            "llm.latency_ms": latency_ms,
        }
        
        if metadata:
            attributes.update(metadata)
        
        span_id = self.start_span(f"llm.call.{model}", attributes)
        
        self.add_event(span_id, "llm.prompt", {"content": prompt[:500]})
        self.add_event(span_id, "llm.completion", {"content": completion[:500]})
        
        return self.end_span(span_id, "OK")


class AgentTracer(Tracer):
    """
    Agent 调用追踪器
    
    追踪 Agent 执行链路。
    """
    
    def trace_agent_call(
        self,
        agent_name: str,
        input_data: Any,
        output_data: Any,
        duration_ms: float,
        tools_used: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        追踪 Agent 调用
        
        Args:
            agent_name: Agent 名称
            input_data: 输入数据
            output_data: 输出数据
            duration_ms: 执行时长（毫秒）
            tools_used: 使用的工具列表
            metadata: 元数据
        
        Returns:
            str: Span ID
        """
        attributes = {
            "agent.name": agent_name,
            "agent.duration_ms": duration_ms,
            "agent.tools_used": tools_used or [],
        }
        
        if metadata:
            attributes.update(metadata)
        
        span_id = self.start_span(f"agent.call.{agent_name}", attributes)
        
        self.add_event(span_id, "agent.input", {"data": str(input_data)[:500]})
        self.add_event(span_id, "agent.output", {"data": str(output_data)[:500]})
        
        return self.end_span(span_id, "OK")


class ToolTracer(Tracer):
    """
    工具调用追踪器
    
    追踪工具执行。
    """
    
    def trace_tool_call(
        self,
        tool_name: str,
        params: Dict[str, Any],
        result: Any,
        duration_ms: float,
        success: bool = True,
        fallback_mode: Optional[str] = None,
    ) -> str:
        """
        追踪工具调用
        
        Args:
            tool_name: 工具名称
            params: 参数
            result: 结果
            duration_ms: 执行时长（毫秒）
            success: 是否成功
            fallback_mode: 降级模式
        
        Returns:
            str: Span ID
        """
        attributes = {
            "tool.name": tool_name,
            "tool.duration_ms": duration_ms,
            "tool.success": success,
        }
        
        if fallback_mode:
            attributes["tool.fallback_mode"] = fallback_mode
        
        span_id = self.start_span(f"tool.call.{tool_name}", attributes)
        
        self.add_event(span_id, "tool.params", {"params": params})
        self.add_event(span_id, "tool.result", {"result": str(result)[:500]})
        
        return self.end_span(span_id, "OK" if success else "ERROR")


# 全局追踪器
_tracer: Optional[Tracer] = None
_llm_tracer: Optional[LLMTracer] = None
_agent_tracer: Optional[AgentTracer] = None
_tool_tracer: Optional[ToolTracer] = None


def get_tracer() -> Tracer:
    """获取全局追踪器"""
    global _tracer
    if _tracer is None:
        _tracer = Tracer()
    return _tracer


def get_llm_tracer() -> LLMTracer:
    """获取 LLM 追踪器"""
    global _llm_tracer
    if _llm_tracer is None:
        _llm_tracer = LLMTracer()
    return _llm_tracer


def get_agent_tracer() -> AgentTracer:
    """获取 Agent 追踪器"""
    global _agent_tracer
    if _agent_tracer is None:
        _agent_tracer = AgentTracer()
    return _agent_tracer


def get_tool_tracer() -> ToolTracer:
    """获取工具追踪器"""
    global _tool_tracer
    if _tool_tracer is None:
        _tool_tracer = ToolTracer()
    return _tool_tracer


# 便捷装饰器
def traced(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
) -> Callable:
    """追踪装饰器"""
    return get_tracer().traced(name, attributes)
