"""
工具基类模块

职责：
- 定义工具基础抽象
- 工具注册机制
- 工具执行结果封装
- 工具路由器
"""
from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable, Awaitable, TypeVar, Generic
from dataclasses import dataclass, field
import asyncio
import time
import jsonschema
from functools import wraps

from opspilot.utils.exceptions import (
    ToolNotFoundError,
    ToolExecutionError,
    ToolTimeoutError,
    ToolValidationError,
    MCPConnectionError,
)


class ToolStatus(str, Enum):
    """工具执行状态"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


class FallbackMode(str, Enum):
    """降级模式"""
    NONE = "none"
    GUI_MODE = "gui_mode"
    MANUAL = "manual"


@dataclass
class ToolSchema:
    """
    工具 Schema 定义

    定义工具的元信息，用于：
    - LLM 理解工具功能
    - 参数校验
    - 文档生成
    """
    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Optional[Dict[str, Any]] = None
    timeout_seconds: int = 30
    retryable: bool = True  # 是否可重试

    @property
    def parameters(self) -> Dict[str, Any]:
        """parameters属性，兼容input_schema"""
        return self.input_schema

    @parameters.setter
    def parameters(self, value: Dict[str, Any]):
        """设置parameters"""
        self.input_schema = value

    @property
    def timeout(self) -> int:
        """timeout属性，兼容timeout_seconds"""
        return self.timeout_seconds

    @timeout.setter
    def timeout(self, value: int):
        """设置timeout"""
        self.timeout_seconds = value

    def to_mcp_format(self) -> Dict[str, Any]:
        """转换为 MCP 协议格式"""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }

    def validate_input(self, params: Dict[str, Any]) -> bool:
        """验证输入参数"""
        if not self.input_schema:
            return True
        try:
            jsonschema.validate(params, self.input_schema)
            return True
        except jsonschema.ValidationError:
            return False


@dataclass
class ToolResult:
    """
    工具执行结果

    封装工具执行的返回数据，包含：
    - 执行状态
    - 返回数据/错误信息
    - 降级建议
    - 执行耗时
    """
    status: ToolStatus
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    retry_suggested: bool = False
    fallback_mode: FallbackMode = FallbackMode.NONE
    latency_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(cls, data: Dict[str, Any], latency_ms: int = 0) -> "ToolResult":
        """创建成功结果"""
        return cls(
            status=ToolStatus.SUCCESS,
            data=data,
            latency_ms=latency_ms
        )

    @classmethod
    def error(
        cls,
        error: str,
        error_code: str,
        retry_suggested: bool = False,
        fallback_mode: FallbackMode = FallbackMode.NONE
    ) -> "ToolResult":
        """创建错误结果"""
        return cls(
            status=ToolStatus.ERROR,
            error=error,
            error_code=error_code,
            retry_suggested=retry_suggested,
            fallback_mode=fallback_mode
        )

    @classmethod
    def timeout(cls, latency_ms: int = 0) -> "ToolResult":
        """创建超时结果"""
        return cls(
            status=ToolStatus.TIMEOUT,
            error="工具执行超时",
            error_code="TIMEOUT",
            retry_suggested=True,
            fallback_mode=FallbackMode.GUI_MODE,
            latency_ms=latency_ms
        )

    def is_success(self) -> bool:
        """是否成功"""
        return self.status == ToolStatus.SUCCESS

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "error_code": self.error_code,
            "retry_suggested": self.retry_suggested,
            "fallback_mode": self.fallback_mode.value,
            "latency_ms": self.latency_ms,
            "metadata": self.metadata,
        }


@dataclass
class ToolContext:
    """工具执行上下文"""
    task_id: str
    state: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# 工具函数类型
ToolFunc = Callable[[Dict[str, Any], ToolContext], Awaitable[ToolResult]]


class BaseToolServer(ABC):
    """
    工具服务器抽象基类

    所有 MCP Server 的基类，提供：
    - 工具注册机制
    - 工具执行框架
    - Schema 管理
    """

    def __init__(self, name: str, description: str = ""):
        """
        初始化工具服务器

        Args:
            name: 服务器名称
            description: 服务器描述
        """
        self.name = name
        self.description = description
        self._tools: Dict[str, ToolSchema] = {}
        self._handlers: Dict[str, ToolFunc] = {}
        self._initialized = False

    def register_tool(self, schema: ToolSchema) -> Callable[[ToolFunc], ToolFunc]:
        """
        工具注册装饰器

        Args:
            schema: 工具 Schema

        Returns:
            装饰器函数
        """
        def decorator(func: ToolFunc) -> ToolFunc:
            @wraps(func)
            async def wrapper(params: Dict[str, Any], context: ToolContext) -> ToolResult:
                return await func(params, context)

            self._tools[schema.name] = schema
            self._handlers[schema.name] = wrapper
            return wrapper

        return decorator

    def add_tool(self, schema: ToolSchema, handler: ToolFunc) -> None:
        """
        直接添加工具（非装饰器方式）

        Args:
            schema: 工具 Schema
            handler: 工具处理函数
        """
        self._tools[schema.name] = schema
        self._handlers[schema.name] = handler

    def get_tool_schema(self, tool_name: str) -> Optional[ToolSchema]:
        """获取工具 Schema"""
        return self._tools.get(tool_name)

    def get_all_schemas(self) -> List[ToolSchema]:
        """获取所有工具 Schema"""
        return list(self._tools.values())

    def has_tool(self, tool_name: str) -> bool:
        """检查工具是否存在"""
        return tool_name in self._tools

    async def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: ToolContext,
        raise_on_error: bool = False
    ) -> ToolResult:
        """
        执行工具

        Args:
            tool_name: 工具名称
            params: 工具参数
            context: 执行上下文
            raise_on_error: 是否在错误时抛出异常（默认返回 ToolResult.error）

        Returns:
            ToolResult: 执行结果

        Raises:
            ToolNotFoundError: 工具不存在
            ToolValidationError: 参数校验失败
            ToolTimeoutError: 工具执行超时
            ToolExecutionError: 工具执行失败
        """
        # 检查工具是否存在
        if tool_name not in self._tools:
            if raise_on_error:
                raise ToolNotFoundError(tool_name)
            return ToolResult.error(
                error=f"工具不存在: {tool_name}",
                error_code="TOOL_NOT_FOUND"
            )

        schema = self._tools[tool_name]
        handler = self._handlers[tool_name]

        # 参数校验
        if not schema.validate_input(params):
            if raise_on_error:
                raise ToolValidationError(
                    tool_name=tool_name,
                    reason="参数校验失败",
                    params=params
                )
            return ToolResult.error(
                error="参数校验失败",
                error_code="INVALID_PARAMS"
            )

        # 执行工具（带超时）
        start_time = time.time()
        try:
            result = await asyncio.wait_for(
                handler(params, context),
                timeout=schema.timeout_seconds
            )
            result.latency_ms = int((time.time() - start_time) * 1000)
            return result

        except asyncio.TimeoutError:
            latency_ms = int((time.time() - start_time) * 1000)
            if raise_on_error:
                raise ToolTimeoutError(tool_name, schema.timeout_seconds)
            return ToolResult.timeout(latency_ms)

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            if raise_on_error:
                raise ToolExecutionError(
                    tool_name=tool_name,
                    reason=str(e),
                    params=params
                )
            return ToolResult.error(
                error=str(e),
                error_code="EXECUTION_ERROR",
                retry_suggested=schema.retryable,
                latency_ms=latency_ms
            )

    @abstractmethod
    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 服务是否健康
        """
        pass

    async def initialize(self) -> None:
        """初始化服务器（子类可重写）"""
        self._initialized = True

    async def shutdown(self) -> None:
        """关闭服务器（子类可重写）"""
        self._initialized = False


class ToolRouter:
    """
    工具路由器

    职责：
    - 管理多个 ToolServer
    - 根据工具名路由到对应 Server
    - 提供统一调用接口
    - 重试机制
    """

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """
        初始化工具路由器

        Args:
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self._servers: Dict[str, BaseToolServer] = {}
        self._tool_to_server: Dict[str, str] = {}  # tool_name -> server_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def register_server(self, server: BaseToolServer) -> None:
        """
        注册工具服务器

        Args:
            server: 工具服务器实例
        """
        self._servers[server.name] = server

        # 建立工具名到服务器的映射
        for schema in server.get_all_schemas():
            self._tool_to_server[schema.name] = server.name

    def unregister_server(self, server_name: str) -> None:
        """注销工具服务器"""
        if server_name in self._servers:
            server = self._servers[server_name]
            # 移除工具映射
            for schema in server.get_all_schemas():
                self._tool_to_server.pop(schema.name, None)
            # 移除服务器
            del self._servers[server_name]

    def get_server(self, tool_name: str) -> Optional[BaseToolServer]:
        """根据工具名获取服务器"""
        server_name = self._tool_to_server.get(tool_name)
        return self._servers.get(server_name) if server_name else None

    def has_tool(self, tool_name: str) -> bool:
        """检查工具是否存在"""
        return tool_name in self._tool_to_server

    def get_tool_schema(self, tool_name: str) -> Optional[ToolSchema]:
        """获取工具 Schema"""
        server = self.get_server(tool_name)
        return server.get_tool_schema(tool_name) if server else None

    def get_all_schemas(self) -> List[ToolSchema]:
        """获取所有工具 Schema"""
        schemas = []
        for server in self._servers.values():
            schemas.extend(server.get_all_schemas())
        return schemas

    async def call_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: ToolContext,
        raise_on_error: bool = False
    ) -> ToolResult:
        """
        单次工具调用

        Args:
            tool_name: 工具名称
            params: 工具参数
            context: 执行上下文
            raise_on_error: 是否在错误时抛出异常

        Returns:
            ToolResult: 执行结果

        Raises:
            ToolNotFoundError: 工具不存在
            ToolValidationError: 参数校验失败
            ToolTimeoutError: 工具执行超时
            ToolExecutionError: 工具执行失败
        """
        server = self.get_server(tool_name)

        if not server:
            if raise_on_error:
                raise ToolNotFoundError(tool_name)
            return ToolResult.error(
                error=f"工具不存在: {tool_name}",
                error_code="TOOL_NOT_FOUND"
            )

        return await server.execute_tool(tool_name, params, context, raise_on_error)

    async def call_tool_with_retry(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: ToolContext,
        max_retries: Optional[int] = None,
        raise_on_error: bool = False
    ) -> ToolResult:
        """
        带重试的工具调用

        Args:
            tool_name: 工具名称
            params: 工具参数
            context: 执行上下文
            max_retries: 最大重试次数（None 使用默认值）
            raise_on_error: 是否在错误时抛出异常

        Returns:
            ToolResult: 执行结果

        Raises:
            ToolNotFoundError: 工具不存在
            ToolValidationError: 参数校验失败
            ToolTimeoutError: 工具执行超时（重试后仍失败）
            ToolExecutionError: 工具执行失败（重试后仍失败）
        """
        retries = max_retries if max_retries is not None else self.max_retries
        last_result = None
        last_error = None

        for attempt in range(retries + 1):
            try:
                result = await self.call_tool(tool_name, params, context, raise_on_error=False)
                last_result = result

                # 成功直接返回
                if result.is_success():
                    return result

                # 不可重试的错误直接返回
                if not result.retry_suggested:
                    return result

            except (ToolNotFoundError, ToolValidationError) as e:
                # 这些错误不应该重试
                if raise_on_error:
                    raise
                return ToolResult.error(
                    error=str(e),
                    error_code=e.code,
                    retry_suggested=False
                )
            except (ToolTimeoutError, ToolExecutionError) as e:
                last_error = e
                last_result = ToolResult.error(
                    error=str(e),
                    error_code=e.code,
                    retry_suggested=True
                )

            # 最后一次尝试不等待
            if attempt < retries:
                await asyncio.sleep(self.retry_delay * (attempt + 1))

        # 重试后仍失败
        if raise_on_error and last_error:
            raise last_error

        return last_result

    async def health_check_all(self) -> Dict[str, bool]:
        """检查所有服务器健康状态"""
        results = {}
        for name, server in self._servers.items():
            try:
                results[name] = await server.health_check()
            except Exception:
                results[name] = False
        return results

    async def initialize_all(self) -> None:
        """初始化所有服务器"""
        for server in self._servers.values():
            await server.initialize()

    async def shutdown_all(self) -> None:
        """关闭所有服务器"""
        for server in self._servers.values():
            await server.shutdown()

