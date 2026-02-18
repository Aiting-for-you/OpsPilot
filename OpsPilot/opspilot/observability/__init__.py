"""
可观测性模块

整合 AgentScope Studio 和 LangSmith 的可视化追踪能力。

特性：
- AgentScope Studio: 多智能体可视化监控
- LangSmith: LangChain 链路追踪
- 统一的可观测性接口
"""

from opspilot.observability.studio import (
    StudioConfig,
    StudioIntegration,
    get_studio,
    init_studio,
)

from opspilot.observability.langsmith_config import (
    LangSmithConfig,
    LangSmithIntegration,
    get_langsmith,
    init_langsmith,
)

from opspilot.observability.tracing import (
    TracingManager,
    SpanContext,
    traced,
    trace_agent,
    trace_tool,
)

__all__ = [
    # AgentScope Studio
    "StudioConfig",
    "StudioIntegration",
    "get_studio",
    "init_studio",
    # LangSmith
    "LangSmithConfig",
    "LangSmithIntegration",
    "get_langsmith",
    "init_langsmith",
    # 统一追踪
    "TracingManager",
    "SpanContext",
    "traced",
    "trace_agent",
    "trace_tool",
]
