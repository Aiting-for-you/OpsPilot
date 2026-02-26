"""
核心模块

包含:
- state_machine: 状态机（状态定义、转换控制、行为约束）
- context: 上下文管理（任务上下文、状态机上下文）
- events: 事件系统（事件定义、事件总线）
- orchestrator: 编排器（多Agent协作）
- sop_executor: SOP执行器（标准操作流程）
- llm_config: LLM配置管理（多模型支持、API Key管理）
"""

from opspilot.core.state_machine import (
    State,
    StateConfig,
    StateTransition,
    StateMachine,
    STATE_CONFIGS,
    ALLOWED_TRANSITIONS,
)

from opspilot.core.context import (
    StateMachineContext,
    TaskContext,
    ContextManager,
)

from opspilot.core.events import (
    EventType,
    BaseEvent,
    StateChangedEvent,
    TaskCreatedEvent,
    TaskCompletedEvent,
    TaskFailedEvent,
    AgentStartedEvent,
    AgentCompletedEvent,
    ToolCalledEvent,
    ToolResultEvent,
    ErrorEvent,
    EventBus,
    get_event_bus,
    subscribe,
    publish,
)

from opspilot.core.orchestrator import Orchestrator

from opspilot.core.sop_executor import (
    SOPStepType,
    SOPStep,
    SOPDefinition,
    SOPExecutor,
    SOPExecutionResult,
    create_order_sop,
    query_supplier_sop,
)

from opspilot.core.llm_config import (
    LLMProvider,
    ProviderConfig,
    LLMConfigManager,
    get_llm_config_manager,
    get_llm_client_config,
    fetch_available_models,
    batch_add_custom_models,
)

__all__ = [
    # 状态机
    "State",
    "StateConfig",
    "StateTransition",
    "StateMachine",
    "STATE_CONFIGS",
    "ALLOWED_TRANSITIONS",
    # 上下文
    "StateMachineContext",
    "TaskContext",
    "ContextManager",
    # 事件
    "EventType",
    "BaseEvent",
    "StateChangedEvent",
    "TaskCreatedEvent",
    "TaskCompletedEvent",
    "TaskFailedEvent",
    "AgentStartedEvent",
    "AgentCompletedEvent",
    "ToolCalledEvent",
    "ToolResultEvent",
    "ErrorEvent",
    "EventBus",
    "get_event_bus",
    "subscribe",
    "publish",
    # 编排器
    "Orchestrator",
    # SOP执行器
    "SOPStepType",
    "SOPStep",
    "SOPDefinition",
    "SOPExecutor",
    "SOPExecutionResult",
    "create_order_sop",
    "query_supplier_sop",
    # LLM 配置
    "LLMProvider",
    "ProviderConfig",
    "LLMConfigManager",
    "get_llm_config_manager",
    "get_llm_client_config",
    "fetch_available_models",
    "batch_add_custom_models",
]

