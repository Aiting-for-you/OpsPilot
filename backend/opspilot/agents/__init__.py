"""
Agent 模块

按文档要求，使用 AgentScope 负责多智能体调度：
- MsgHub 消息中心
- FSM 状态机
- Agent 编排
- 博弈协调

包含:
- base: Agent 基类和 LLM 客户端接口
- agentscope_adapter: AgentScope 适配器（新增）
- intent_agent: 意图识别 Agent
- plan_agent: 规划 Agent
- exec_agent: 执行 Agent
- verify_agent: 验证 Agent
- msg_hub: 消息中心（优化保留）
- actor: Actor模式（优化保留）
- collaboration: 多智能体协作（优化保留）
"""

from opspilot.agents.base import (
    AgentRole,
    AgentConfig,
    AgentContext,
    AgentOutput,
    BaseLLMClient,
    MockLLMClient,
    BaseAgent,
    AgentRegistry,
)

# AgentScope 适配 - 按文档要求
try:
    from opspilot.agents.agentscope_adapter import (
        AgentScopeAdapter,
        AgentScopeConfig,
        OpsAgentBase,
        IntentAgent as ASIntentAgent,
        PlanAgent as ASPlanAgent,
        ExecAgent as ASExecAgent,
        VerifyAgent as ASVerifyAgent,
        is_agentscope_available,
        create_agentscope_message,
        AGENTSCOPE_AVAILABLE,
    )
except ImportError:
    AGENTSCOPE_AVAILABLE = False
    AgentScopeAdapter = None
    AgentScopeConfig = None
    OpsAgentBase = None
    ASIntentAgent = None
    ASPlanAgent = None
    ASExecAgent = None
    ASVerifyAgent = None
    is_agentscope_available = lambda: False
    create_agentscope_message = None

from opspilot.agents.intent_agent import (
    IntentType,
    IntentAgent,
    MockIntentAgent,
)

from opspilot.agents.plan_agent import (
    PlanAgent,
    MockPlanAgent,
)

from opspilot.agents.exec_agent import (
    ExecAgent,
    MockExecAgent,
)

from opspilot.agents.verify_agent import (
    VerifyAgent,
    MockVerifyAgent,
)

# 消息中心和协作（优化保留）
from opspilot.agents.msg_hub import (
    MessageType,
    AgentMessage,
    MessageSubscriber,
    MessageHub,
    create_message,
    get_message_hub,
    subscribe,
    publish,
    broadcast,
)

from opspilot.agents.actor import (
    ActorState,
    ActorStats,
    BaseActor,
    IntentActor,
    PlanActor,
    ExecActor,
    VerifyActor,
    ActorRegistry,
    create_actor,
)

from opspilot.agents.collaboration import (
    CollaborationMode,
    CollaborationContext,
    CollaborationResult,
    SequentialCollaboration,
    ParallelCollaboration,
    ConditionalCollaboration,
    PipelineCollaboration,
    CollaborationOrchestrator,
    create_orchestrator,
    run_collaboration,
)

__all__ = [
    # 基础
    "AgentRole",
    "AgentConfig",
    "AgentContext",
    "AgentOutput",
    "BaseLLMClient",
    "MockLLMClient",
    "BaseAgent",
    "AgentRegistry",
    # AgentScope 适配
    "AgentScopeAdapter",
    "AgentScopeConfig",
    "OpsAgentBase",
    "ASIntentAgent",
    "ASPlanAgent",
    "ASExecAgent",
    "ASVerifyAgent",
    "is_agentscope_available",
    "create_agentscope_message",
    "AGENTSCOPE_AVAILABLE",
    # 意图识别
    "IntentType",
    "IntentAgent",
    "MockIntentAgent",
    # 规划
    "PlanAgent",
    "MockPlanAgent",
    # 执行
    "ExecAgent",
    "MockExecAgent",
    # 验证
    "VerifyAgent",
    "MockVerifyAgent",
    # 消息中心
    "MessageType",
    "AgentMessage",
    "MessageSubscriber",
    "MessageHub",
    "create_message",
    "get_message_hub",
    "subscribe",
    "publish",
    "broadcast",
    # Actor模式
    "ActorState",
    "ActorStats",
    "BaseActor",
    "IntentActor",
    "PlanActor",
    "ExecActor",
    "VerifyActor",
    "ActorRegistry",
    "create_actor",
    # 协作模式
    "CollaborationMode",
    "CollaborationContext",
    "CollaborationResult",
    "SequentialCollaboration",
    "ParallelCollaboration",
    "ConditionalCollaboration",
    "PipelineCollaboration",
    "CollaborationOrchestrator",
    "create_orchestrator",
    "run_collaboration",
]

