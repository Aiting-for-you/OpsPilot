"""
集成模块

包含:
- agentscope_integration: AgentScope核心集成（分布式调度）
- langchain_integration: LangChain工具集成（工具调用+RAG）
- hybrid_orchestrator: 混合编排器（融合两者优势）
"""

from opspilot.integration.agentscope_integration import (
    # 消息系统
    ASMessage,
    ASMessageType,
    MessageAdapter,
    # Agent基类
    ASAgentBase,
    ASIntentAgent,
    ASPlanAgent,
    ASExecAgent,
    ASVerifyAgent,
    # 分布式支持
    DistributedAgentConfig,
    AgentServer,
    AgentClient,
    # 服务发现
    ServiceRegistry,
    ServiceDiscovery,
    # 工厂函数
    create_agent,
    create_distributed_agent,
    start_agent_server,
    connect_agent,
)

from opspilot.integration.langchain_integration import (
    # 工具适配
    LCToolAdapter,
    LCToolRegistry,
    MCPToolWrapper,
    # RAG适配
    LCRetrieverAdapter,
    LCMemoryAdapter,
    LCVectorStoreAdapter,
    # 链式调用
    LCChainExecutor,
    # 工厂函数
    create_lc_tool_adapter,
    create_lc_retriever,
)

from opspilot.integration.hybrid_orchestrator import (
    # 混合编排
    HybridOrchestratorConfig,
    HybridOrchestrator,
    OrchestrationMode,
    # 协作模式
    SequentialWorkflow,
    ParallelWorkflow,
    ConditionalWorkflow,
    # 工厂函数
    create_hybrid_orchestrator,
)

__all__ = [
    # AgentScope集成
    "ASMessage",
    "ASMessageType",
    "MessageAdapter",
    "ASAgentBase",
    "ASIntentAgent",
    "ASPlanAgent",
    "ASExecAgent",
    "ASVerifyAgent",
    "DistributedAgentConfig",
    "AgentServer",
    "AgentClient",
    "ServiceRegistry",
    "ServiceDiscovery",
    "create_agent",
    "create_distributed_agent",
    "start_agent_server",
    "connect_agent",
    # LangChain集成
    "LCToolAdapter",
    "LCToolRegistry",
    "MCPToolWrapper",
    "LCRetrieverAdapter",
    "LCMemoryAdapter",
    "LCVectorStoreAdapter",
    "LCChainExecutor",
    "create_lc_tool_adapter",
    "create_lc_retriever",
    # 混合编排
    "HybridOrchestratorConfig",
    "HybridOrchestrator",
    "OrchestrationMode",
    "SequentialWorkflow",
    "ParallelWorkflow",
    "ConditionalWorkflow",
    "create_hybrid_orchestrator",
]

