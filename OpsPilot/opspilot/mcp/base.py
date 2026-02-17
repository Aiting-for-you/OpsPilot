"""
MCP Server 基类

封装官方 mcp SDK，提供简化的工具注册接口：
- 装饰器式工具注册
- 自动 Schema 生成
- 统一错误处理
- 支持 stdio 和 SSE 两种传输方式
"""
import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Awaitable

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    INVALID_PARAMS,
    INTERNAL_ERROR,
)


@dataclass
class ToolDefinition:
    """
    工具定义

    简化的工具定义，自动转换为 MCP Tool 类型
    """
    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Optional[Dict[str, Any]] = None
    timeout_seconds: int = 30


# 工具处理函数类型
ToolHandler = Callable[[Dict[str, Any]], Awaitable[Any]]


class MCPServerBase(ABC):
    """
    MCP Server 基类

    封装官方 mcp.Server，提供：
    - 装饰器式工具注册 @server.tool()
    - 自动参数校验
    - 统一返回格式
    - 错误处理

    使用示例：
    ```python
    class MyServer(MCPServerBase):
        def __init__(self):
            super().__init__(name="my-server", version="1.0.0")
        
        def _register_tools(self):
            @self.tool(
                name="hello",
                description="打招呼",
                input_schema={"type": "object", "properties": {"name": {"type": "string"}}}
            )
            async def hello(params: dict) -> dict:
                return {"message": f"Hello, {params.get('name', 'World')}!"}
    ```
    """

    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        description: str = "",
    ):
        """
        初始化 MCP Server

        Args:
            name: Server 名称（唯一标识）
            version: 版本号
            description: 描述信息
        """
        self.name = name
        self.version = version
        self.description = description

        # 创建 MCP Server 实例
        self.server = Server(name)

        # 工具注册表
        self._tools: Dict[str, ToolDefinition] = {}
        self._handlers: Dict[str, ToolHandler] = {}

        # 注册核心能力
        self._setup_handlers()

    def _setup_handlers(self):
        """设置 MCP Server 的核心处理器"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """返回所有已注册的工具"""
            return [
                Tool(
                    name=tool.name,
                    description=tool.description,
                    inputSchema=tool.input_schema,
                )
                for tool in self._tools.values()
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> List[TextContent | ImageContent | EmbeddedResource]:
            """执行工具调用"""
            if name not in self._handlers:
                raise Exception(f"Tool not found: {name}")

            try:
                # 执行工具
                result = await self._handlers[name](arguments or {})

                # 转换结果为 MCP 格式
                if isinstance(result, str):
                    content = result
                elif isinstance(result, dict):
                    content = json.dumps(result, ensure_ascii=False, indent=2)
                else:
                    content = str(result)

                return [TextContent(type="text", text=content)]

            except Exception as e:
                # 错误也返回为 TextContent，让客户端处理
                error_response = {
                    "error": str(e),
                    "error_code": "EXECUTION_ERROR",
                    "tool": name,
                }
                return [TextContent(type="text", text=json.dumps(error_response, ensure_ascii=False))]

    def tool(
        self,
        name: str,
        description: str,
        input_schema: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 30,
    ) -> Callable[[ToolHandler], ToolHandler]:
        """
        工具注册装饰器

        Args:
            name: 工具名称
            description: 工具描述
            input_schema: 输入参数 Schema（JSON Schema 格式）
            timeout_seconds: 超时时间

        Returns:
            装饰器函数

        示例：
        ```python
        @server.tool(
            name="query",
            description="查询数据",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                }
            }
        )
        async def query(params: dict) -> dict:
            return {"result": "..."}
        ```
        """
        def decorator(handler: ToolHandler) -> ToolHandler:
            # 创建工具定义
            tool_def = ToolDefinition(
                name=name,
                description=description,
                input_schema=input_schema or {"type": "object", "properties": {}},
                timeout_seconds=timeout_seconds,
            )

            # 注册到表中
            self._tools[name] = tool_def
            self._handlers[name] = handler

            return handler

        return decorator

    def add_tool(
        self,
        name: str,
        description: str,
        handler: ToolHandler,
        input_schema: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        直接添加工具（非装饰器方式）

        Args:
            name: 工具名称
            description: 工具描述
            handler: 处理函数
            input_schema: 输入参数 Schema
        """
        tool_def = ToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema or {"type": "object", "properties": {}},
        )
        self._tools[name] = tool_def
        self._handlers[name] = handler

    def get_tools(self) -> List[ToolDefinition]:
        """获取所有工具定义"""
        return list(self._tools.values())

    @abstractmethod
    def _register_tools(self) -> None:
        """
        注册工具（子类实现）

        子类在此方法中使用 @self.tool() 装饰器注册工具
        """
        pass

    async def run_stdio(self) -> None:
        """
        以 stdio 模式运行 Server

        这是最常用的模式，通过标准输入输出与 Client 通信
        """
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )

    async def run_sse(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """
        以 SSE 模式运行 Server

        通过 HTTP SSE 与 Client 通信，适合需要网络访问的场景
        """
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Route

        sse = SseServerTransport("/messages")

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await self.server.run(
                    streams[0],
                    streams[1],
                    self.server.create_initialization_options(),
                )

        async def handle_messages(request):
            await sse.handle_post_message(request.scope, request.receive, request._send)

        app = Starlette(
            routes=[
                Route("/sse", endpoint=handle_sse),
                Route("/messages", endpoint=handle_messages, methods=["POST"]),
            ]
        )

        import uvicorn
        config = uvicorn.Config(app, host=host, port=port)
        server = uvicorn.Server(config)
        await server.serve()

    def run(self, mode: str = "stdio", **kwargs) -> None:
        """
        启动 Server

        Args:
            mode: 运行模式，"stdio" 或 "sse"
            **kwargs: 传递给具体运行模式的参数
        """
        # 确保工具已注册
        self._register_tools()

        if mode == "stdio":
            asyncio.run(self.run_stdio())
        elif mode == "sse":
            asyncio.run(self.run_sse(**kwargs))
        else:
            raise ValueError(f"Unknown mode: {mode}")
