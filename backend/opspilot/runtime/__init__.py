"""
OpsPilot Runtime 模块

基于 AgentScope Runtime 的生产级运行时能力。

模块：
- sandbox: 工具沙箱，安全隔离执行
- streaming: SSE 流式输出
- tracing: OpenTelemetry 追踪
- a2a: Agent-to-Agent 协议
"""

from opspilot.runtime.sandbox import (
    BaseSandbox,
    LocalSandbox,
    DockerSandbox,
    ToolSandboxManager,
    SandboxConfig,
    SandboxResult,
    SandboxStatus,
    create_sandbox,
)

from opspilot.runtime.streaming import (
    StreamEventType,
    StreamEvent,
    StreamWriter,
    StreamManager,
    StreamingTaskExecutor,
    get_stream_manager,
    create_task_stream,
)

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
)

from opspilot.runtime.a2a import (
    AgentStatus,
    MessageType,
    AgentSkill,
    AgentCard,
    A2AMessage,
    AgentRegistry,
    LocalAgentRegistry,
    A2AClient,
    A2AServer,
    create_agent_card,
    get_registry,
)

__all__ = [
    # Sandbox
    "BaseSandbox",
    "LocalSandbox",
    "DockerSandbox",
    "ToolSandboxManager",
    "SandboxConfig",
    "SandboxResult",
    "SandboxStatus",
    "create_sandbox",
    # Streaming
    "StreamEventType",
    "StreamEvent",
    "StreamWriter",
    "StreamManager",
    "StreamingTaskExecutor",
    "get_stream_manager",
    "create_task_stream",
    # Tracing
    "Tracer",
    "LLMTracer",
    "AgentTracer",
    "ToolTracer",
    "TraceSpan",
    "get_tracer",
    "get_llm_tracer",
    "get_agent_tracer",
    "get_tool_tracer",
    "traced",
    # A2A
    "AgentStatus",
    "MessageType",
    "AgentSkill",
    "AgentCard",
    "A2AMessage",
    "AgentRegistry",
    "LocalAgentRegistry",
    "A2AClient",
    "A2AServer",
    "create_agent_card",
    "get_registry",
]
