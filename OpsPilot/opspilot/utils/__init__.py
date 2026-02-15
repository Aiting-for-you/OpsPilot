"""
工具函数模块

包含:
- exceptions: 自定义异常类
- config: 配置加载器
- logger: 日志系统
- validators: 校验器（待实现）
"""

from opspilot.utils.exceptions import (
    opspilotError,
    ConfigError,
    ConfigFileNotFoundError,
    ConfigValidationError,
    StateMachineError,
    InvalidTransitionError,
    StatePersistenceError,
    MaxRetryExceededError,
    AgentError,
    AgentTimeoutError,
    AgentExecutionError,
    PromptLoadError,
    ToolError,
    ToolNotFoundError,
    ToolExecutionError,
    MCPConnectionError,
    MemoryError,
    MemoryConnectionError,
    MemoryQueryError,
)

from opspilot.utils.config import (
    Settings,
    AppConfig,
    StateMachineConfig,
    MemoryConfig,
    LLMConfig,
    MCPConfig,
    APIConfig,
    get_config,
    init_config,
    reload_config,
    get_config_path,
)

from opspilot.utils.logger import (
    get_logger,
    init_logging,
    get_trace_id,
    set_trace_id,
    clear_trace_id,
    log_context,
)

__all__ = [
    # 异常
    "opspilotError",
    "ConfigError",
    "ConfigFileNotFoundError",
    "ConfigValidationError",
    "StateMachineError",
    "InvalidTransitionError",
    "StatePersistenceError",
    "MaxRetryExceededError",
    "AgentError",
    "AgentTimeoutError",
    "AgentExecutionError",
    "PromptLoadError",
    "ToolError",
    "ToolNotFoundError",
    "ToolExecutionError",
    "MCPConnectionError",
    "MemoryError",
    "MemoryConnectionError",
    "MemoryQueryError",
    # 配置
    "Settings",
    "AppConfig",
    "StateMachineConfig",
    "MemoryConfig",
    "LLMConfig",
    "MCPConfig",
    "APIConfig",
    "get_config",
    "init_config",
    "reload_config",
    "get_config_path",
    # 日志
    "get_logger",
    "init_logging",
    "get_trace_id",
    "set_trace_id",
    "clear_trace_id",
    "log_context",
]

