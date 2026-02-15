"""
opspilot 自定义异常类

异常层次结构：
    opspilotError (基类)
    ├── ConfigError          配置相关错误
    ├── StateMachineError    状态机相关错误
    │   ├── InvalidTransitionError   非法状态转换
    │   ├── StatePersistenceError    状态持久化错误
    │   └── MaxRetryExceededError    超过最大重试次数
    ├── AgentError           Agent相关错误
    │   ├── AgentTimeoutError        Agent执行超时
    │   ├── AgentExecutionError      Agent执行失败
    │   └── PromptLoadError          提示词加载失败
    ├── ToolError            工具相关错误
    │   ├── ToolNotFoundError        工具不存在
    │   ├── ToolExecutionError       工具执行失败
    │   └── MCPConnectionError       MCP连接错误
    └── MemoryError          记忆相关错误
        ├── MemoryConnectionError    存储连接错误
        └── MemoryQueryError         查询错误
"""
from typing import Optional, Any


class opspilotError(Exception):
    """opspilot 基础异常类"""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[dict] = None
    ):
        self.message = message
        self.code = code or "UNKNOWN_ERROR"
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """转换为字典，用于 API 响应"""
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details
        }

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


# ==================== 配置相关 ====================

class ConfigError(opspilotError):
    """配置相关错误"""
    pass


class ConfigFileNotFoundError(ConfigError):
    """配置文件不存在"""

    def __init__(self, filepath: str):
        super().__init__(
            message=f"配置文件不存在: {filepath}",
            code="CONFIG_FILE_NOT_FOUND",
            details={"filepath": filepath}
        )


class ConfigValidationError(ConfigError):
    """配置验证失败"""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            code="CONFIG_VALIDATION_ERROR",
            details={"field": field} if field else {}
        )


# ==================== 状态机相关 ====================

class StateMachineError(opspilotError):
    """状态机相关错误基类"""
    pass


class InvalidTransitionError(StateMachineError):
    """非法状态转换"""

    def __init__(
        self,
        from_state: str,
        to_state: str,
        allowed_transitions: Optional[list] = None
    ):
        super().__init__(
            message=f"非法状态转换: {from_state} -> {to_state}",
            code="INVALID_STATE_TRANSITION",
            details={
                "from_state": from_state,
                "to_state": to_state,
                "allowed_transitions": allowed_transitions or []
            }
        )


class StatePersistenceError(StateMachineError):
    """状态持久化错误"""

    def __init__(self, message: str, state: Optional[str] = None):
        super().__init__(
            message=message,
            code="STATE_PERSISTENCE_ERROR",
            details={"state": state} if state else {}
        )


class MaxRetryExceededError(StateMachineError):
    """超过最大重试次数"""

    def __init__(self, max_retry: int, current_retry: int):
        super().__init__(
            message=f"超过最大重试次数: {current_retry}/{max_retry}",
            code="MAX_RETRY_EXCEEDED",
            details={
                "max_retry": max_retry,
                "current_retry": current_retry
            }
        )


# ==================== Agent 相关 ====================

class AgentError(opspilotError):
    """Agent 相关错误基类"""
    pass


class AgentTimeoutError(AgentError):
    """Agent 执行超时"""

    def __init__(self, agent_name: str, timeout: float):
        super().__init__(
            message=f"Agent '{agent_name}' 执行超时: {timeout}s",
            code="AGENT_TIMEOUT",
            details={"agent_name": agent_name, "timeout": timeout}
        )


class AgentExecutionError(AgentError):
    """Agent 执行失败"""

    def __init__(self, agent_name: str, reason: str, output: Optional[Any] = None):
        super().__init__(
            message=f"Agent '{agent_name}' 执行失败: {reason}",
            code="AGENT_EXECUTION_ERROR",
            details={
                "agent_name": agent_name,
                "reason": reason,
                "output": output
            }
        )


class PromptLoadError(AgentError):
    """提示词加载失败"""

    def __init__(self, prompt_name: str, reason: str):
        super().__init__(
            message=f"提示词加载失败 '{prompt_name}': {reason}",
            code="PROMPT_LOAD_ERROR",
            details={"prompt_name": prompt_name, "reason": reason}
        )


# ==================== 工具相关 ====================

class ToolError(opspilotError):
    """工具相关错误基类"""
    pass


class ToolNotFoundError(ToolError):
    """工具不存在"""

    def __init__(self, tool_name: str):
        super().__init__(
            message=f"工具不存在: {tool_name}",
            code="TOOL_NOT_FOUND",
            details={"tool_name": tool_name}
        )


class ToolExecutionError(ToolError):
    """工具执行失败"""

    def __init__(self, tool_name: str, reason: str, params: Optional[dict] = None):
        super().__init__(
            message=f"工具 '{tool_name}' 执行失败: {reason}",
            code="TOOL_EXECUTION_ERROR",
            details={
                "tool_name": tool_name,
                "reason": reason,
                "params": params
            }
        )


class MCPConnectionError(ToolError):
    """MCP 连接错误"""

    def __init__(self, server_name: str, reason: str):
        super().__init__(
            message=f"MCP Server '{server_name}' 连接失败: {reason}",
            code="MCP_CONNECTION_ERROR",
            details={"server_name": server_name, "reason": reason}
        )


# ==================== 记忆相关 ====================

class MemoryError(opspilotError):
    """记忆相关错误基类"""
    pass


class MemoryConnectionError(MemoryError):
    """存储连接错误"""

    def __init__(self, storage_type: str, reason: str):
        super().__init__(
            message=f"{storage_type} 连接失败: {reason}",
            code="MEMORY_CONNECTION_ERROR",
            details={"storage_type": storage_type, "reason": reason}
        )


class MemoryQueryError(MemoryError):
    """查询错误"""

    def __init__(self, query: str, reason: str):
        super().__init__(
            message=f"查询失败: {reason}",
            code="MEMORY_QUERY_ERROR",
            details={"query": query, "reason": reason}
        )

