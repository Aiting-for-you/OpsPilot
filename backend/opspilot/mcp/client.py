"""
MCP Client 管理器

提供：
- MCPClientManager：连接和管理多个 MCP Server
- MCPRouter：统一工具调用接口
- 与 LangChain/AgentScope 的集成适配器
"""
import asyncio
import json
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@dataclass
class ServerConfig:
    """Server 配置"""
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)


@dataclass
class ToolInfo:
    """工具信息"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str


class MCPClientManager:
    """
    MCP Client 管理器

    管理 MCP Server 连接，提供工具调用接口

    使用示例：
    ```python
    manager = MCPClientManager()

    # 添加 Server 配置
    manager.add_server(ServerConfig(
        name="erp",
        command="python",
        args=["-m", "opspilot.mcp.servers.erp_server"],
    ))

    # 连接并使用
    async with manager.connect("erp") as client:
        tools = await client.list_tools()
        result = await client.call_tool("query_supplier", {"region": "华南"})
    ```
    """

    def __init__(self):
        self._servers: Dict[str, ServerConfig] = {}
        self._sessions: Dict[str, ClientSession] = {}
        self._tools: Dict[str, ToolInfo] = {}  # tool_name -> ToolInfo

    def add_server(self, config: ServerConfig) -> None:
        """添加 Server 配置"""
        self._servers[config.name] = config

    def add_server_simple(self, name: str, command: str, args: List[str] = None) -> None:
        """简化方式添加 Server"""
        self.add_server(ServerConfig(
            name=name,
            command=command,
            args=args or [],
        ))

    def remove_server(self, name: str) -> None:
        """移除 Server 配置"""
        self._servers.pop(name, None)

    def get_server_config(self, name: str) -> Optional[ServerConfig]:
        """获取 Server 配置"""
        return self._servers.get(name)

    def list_servers(self) -> List[str]:
        """列出所有已配置的 Server"""
        return list(self._servers.keys())

    @asynccontextmanager
    async def connect(self, server_name: str):
        """
        连接指定 Server

        Args:
            server_name: Server 名称

        Yields:
            ConnectedClient: 已连接的客户端
        """
        config = self._servers.get(server_name)
        if not config:
            raise ValueError(f"Server not found: {server_name}")

        server_params = StdioServerParameters(
            command=config.command,
            args=config.args,
            env=config.env or None,
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # 初始化连接
                await session.initialize()

                # 创建已连接客户端
                client = ConnectedClient(server_name, session)

                # 注册工具
                tools = await session.list_tools()
                for tool in tools.tools:
                    self._tools[tool.name] = ToolInfo(
                        name=tool.name,
                        description=tool.description,
                        input_schema=tool.inputSchema,
                        server_name=server_name,
                    )

                yield client

    async def connect_all(self) -> Dict[str, bool]:
        """
        连接所有已配置的 Server

        Returns:
            Dict[str, bool]: Server 名称 -> 连接结果
        """
        results = {}
        for name in self._servers:
            try:
                async with self.connect(name):
                    results[name] = True
            except Exception as e:
                print(f"Failed to connect {name}: {e}")
                results[name] = False
        return results

    def get_tool(self, tool_name: str) -> Optional[ToolInfo]:
        """获取工具信息"""
        return self._tools.get(tool_name)

    def list_tools(self) -> List[ToolInfo]:
        """列出所有已发现的工具"""
        return list(self._tools.values())


class ConnectedClient:
    """已连接的 MCP Client"""

    def __init__(self, server_name: str, session: ClientSession):
        self.server_name = server_name
        self._session = session

    async def list_tools(self) -> List[ToolInfo]:
        """列出 Server 提供的所有工具"""
        result = await self._session.list_tools()
        return [
            ToolInfo(
                name=tool.name,
                description=tool.description,
                input_schema=tool.inputSchema,
                server_name=self.server_name,
            )
            for tool in result.tools
        ]

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any] = None,
    ) -> Any:
        """
        调用工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            Any: 工具返回结果
        """
        result = await self._session.call_tool(tool_name, arguments or {})

        # 解析返回内容
        if result.content:
            # 取第一个内容块
            content = result.content[0]
            if hasattr(content, 'text'):
                try:
                    return json.loads(content.text)
                except json.JSONDecodeError:
                    return content.text
            return content

        return None

    async def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具的输入 Schema"""
        tools = await self.list_tools()
        for tool in tools:
            if tool.name == tool_name:
                return tool.input_schema
        return None


class MCPRouter:
    """
    MCP 路由器

    统一管理多个 Server 的工具调用，提供类似原 ToolRouter 的接口

    使用示例：
    ```python
    router = MCPRouter()
    router.add_server_config("erp", "python", ["-m", "opspilot.mcp.servers.erp_server"])
    router.add_server_config("compliance", "python", ["-m", "opspilot.mcp.servers.compliance_server"])

    # 启动所有 Server
    await router.start()

    # 调用工具
    result = await router.call_tool("query_supplier", {"region": "华南"})

    # 关闭
    await router.stop()
    ```
    """

    def __init__(self):
        self._manager = MCPClientManager()
        self._sessions: Dict[str, ClientSession] = {}
        self._tool_to_server: Dict[str, str] = {}
        self._started = False

    def add_server_config(
        self,
        name: str,
        command: str,
        args: List[str] = None,
    ) -> None:
        """添加 Server 配置"""
        self._manager.add_server_simple(name, command, args)

    async def start(self) -> None:
        """启动所有 Server 并建立连接"""
        if self._started:
            return

        for name in self._manager.list_servers():
            config = self._manager.get_server_config(name)
            server_params = StdioServerParameters(
                command=config.command,
                args=config.args,
                env=config.env or None,
            )

            # 创建连接
            client_context = stdio_client(server_params)
            read, write = await client_context.__aenter__()

            session_context = ClientSession(read, write)
            session = await session_context.__aenter__()
            await session.initialize()

            # 保存上下文以便后续清理
            self._sessions[name] = {
                'session': session,
                'client_context': client_context,
                'session_context': session_context,
            }

            # 注册工具
            tools = await session.list_tools()
            for tool in tools.tools:
                self._tool_to_server[tool.name] = name

        self._started = True

    async def stop(self) -> None:
        """停止所有 Server 连接"""
        if not self._started:
            return

        for name, ctx in self._sessions.items():
            try:
                await ctx['session_context'].__aexit__(None, None, None)
                await ctx['client_context'].__aexit__(None, None, None)
            except Exception as e:
                print(f"Error closing {name}: {e}")

        self._sessions.clear()
        self._tool_to_server.clear()
        self._started = False

    def list_tools(self) -> List[ToolInfo]:
        """列出所有可用工具"""
        return self._manager.list_tools()

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具的输入 Schema"""
        tool = self._manager.get_tool(tool_name)
        return tool.input_schema if tool else None

    def has_tool(self, tool_name: str) -> bool:
        """检查工具是否存在"""
        return tool_name in self._tool_to_server

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any] = None,
    ) -> Any:
        """
        调用工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            Any: 工具返回结果
        """
        if not self._started:
            raise RuntimeError("Router not started. Call start() first.")

        server_name = self._tool_to_server.get(tool_name)
        if not server_name:
            raise ValueError(f"Tool not found: {tool_name}")

        session = self._sessions[server_name]['session']
        result = await session.call_tool(tool_name, arguments or {})

        # 解析返回内容
        if result.content:
            content = result.content[0]
            if hasattr(content, 'text'):
                try:
                    return json.loads(content.text)
                except json.JSONDecodeError:
                    return content.text
            return content

        return None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()


# ==================== LangChain 集成 ====================

def create_langchain_adapter(router: MCPRouter):
    """
    创建 LangChain 工具适配器

    将 MCP 工具转换为 LangChain StructuredTool

    Args:
        router: MCPRouter 实例

    Returns:
        List[StructuredTool]: LangChain 工具列表
    """
    try:
        from langchain_core.tools import StructuredTool
    except ImportError:
        raise ImportError("langchain-core not installed. Run: pip install langchain-core")

    tools = []
    for tool_info in router.list_tools():
        # 创建工具函数
        async def tool_func(arguments: dict, _name=tool_info.name):
            return await router.call_tool(_name, arguments)

        # 创建 StructuredTool
        tool = StructuredTool(
            name=tool_info.name,
            description=tool_info.description,
            args_schema=tool_info.input_schema,
            coroutine=tool_func,
        )
        tools.append(tool)

    return tools


# ==================== 便捷函数 ====================

def create_default_router() -> MCPRouter:
    """
    创建默认配置的 MCP Router

    自动配置 ERP 和 Compliance Server
    """
    router = MCPRouter()

    # ERP Server
    router.add_server_config(
        name="erp",
        command="python",
        args=["-m", "opspilot.mcp.servers.erp_server"],
    )

    # Compliance Server
    router.add_server_config(
        name="compliance",
        command="python",
        args=["-m", "opspilot.mcp.servers.compliance_server"],
    )

    return router
