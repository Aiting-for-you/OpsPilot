"""
外部 MCP Server 管理器

职责：
- 管理外部 MCP Server 的连接生命周期
- 提供工具发现和调用代理
- 支持动态添加/删除 Server
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from opspilot.utils.config import MCPServerConfig, get_mcp_config
from opspilot.utils.exceptions import opspilotError


class MCPServerError(opspilotError):
    """MCP Server 相关错误"""
    pass


class ServerStatus(str, Enum):
    """Server 连接状态"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class ServerConnection:
    """Server 连接信息"""
    config: MCPServerConfig
    status: ServerStatus = ServerStatus.DISCONNECTED
    session: Optional[ClientSession] = None
    tools: List[Dict[str, Any]] = field(default_factory=list)
    error_message: str = ""
    connected_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.config.name,
            "command": self.config.command,
            "args": self.config.args,
            "enabled": self.config.enabled,
            "auto_connect": self.config.auto_connect,
            "description": self.config.description,
            "status": self.status.value,
            "tool_count": len(self.tools),
            "error_message": self.error_message,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
        }


class ExternalMCPManager:
    """
    外部 MCP Server 管理器
    
    使用方式：
        manager = ExternalMCPManager()
        
        # 添加并连接 Server
        config = MCPServerConfig(name="filesystem", command="npx", args=[...])
        await manager.add_server(config)
        await manager.connect("filesystem")
        
        # 获取工具
        tools = await manager.list_tools("filesystem")
        
        # 调用工具
        result = await manager.call_tool("read_file", {"path": "/tmp/test.txt"})
    """
    
    def __init__(self):
        self._servers: Dict[str, ServerConnection] = {}
        self._tool_to_server: Dict[str, str] = {}  # tool_name -> server_name
        self._lock = asyncio.Lock()
    
    def list_servers(self) -> List[Dict[str, Any]]:
        """列出所有已配置的 Server"""
        return [conn.to_dict() for conn in self._servers.values()]
    
    def get_server(self, name: str) -> Optional[Dict[str, Any]]:
        """获取单个 Server 信息"""
        if name in self._servers:
            return self._servers[name].to_dict()
        return None
    
    def add_server(self, config: MCPServerConfig) -> Dict[str, Any]:
        """添加新的 Server 配置"""
        if config.name in self._servers:
            raise MCPServerError(f"Server '{config.name}' already exists")
        
        self._servers[config.name] = ServerConnection(config=config)
        return self._servers[config.name].to_dict()
    
    def update_server(self, name: str, config: MCPServerConfig) -> Dict[str, Any]:
        """更新 Server 配置"""
        if name not in self._servers:
            raise MCPServerError(f"Server '{name}' not found")
        
        # 如果改名，需要检查新名称是否已存在
        if config.name != name and config.name in self._servers:
            raise MCPServerError(f"Server '{config.name}' already exists")
        
        old_conn = self._servers.pop(name)
        
        # 如果已连接，先断开
        if old_conn.status == ServerStatus.CONNECTED:
            asyncio.create_task(self.disconnect(name))
        
        # 更新配置
        old_conn.config = config
        old_conn.status = ServerStatus.DISCONNECTED
        old_conn.tools = []
        old_conn.error_message = ""
        
        self._servers[config.name] = old_conn
        return old_conn.to_dict()
    
    def remove_server(self, name: str) -> bool:
        """删除 Server 配置"""
        if name not in self._servers:
            return False
        
        conn = self._servers[name]
        
        # 清理工具映射
        for tool in conn.tools:
            tool_name = tool.get("name", "")
            if tool_name in self._tool_to_server:
                del self._tool_to_server[tool_name]
        
        del self._servers[name]
        return True
    
    async def connect(self, name: str) -> Dict[str, Any]:
        """连接到 Server"""
        if name not in self._servers:
            raise MCPServerError(f"Server '{name}' not found")
        
        conn = self._servers[name]
        
        if conn.status == ServerStatus.CONNECTED:
            return conn.to_dict()
        
        conn.status = ServerStatus.CONNECTING
        conn.error_message = ""
        
        try:
            # 准备环境变量
            env = os.environ.copy()
            env.update(conn.config.env)
            
            # 创建 Server 参数
            server_params = StdioServerParameters(
                command=conn.config.command,
                args=conn.config.args,
                env=env,
            )
            
            # 启动连接
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # 初始化会话
                    await session.initialize()
                    
                    # 获取工具列表
                    tools_result = await session.list_tools()
                    conn.tools = [
                        {
                            "name": tool.name,
                            "description": tool.description or "",
                            "inputSchema": tool.inputSchema,
                        }
                        for tool in tools_result.tools
                    ]
                    
                    # 更新工具映射
                    for tool in conn.tools:
                        self._tool_to_server[tool["name"]] = name
                    
                    # 保存会话
                    conn.session = session
                    conn.status = ServerStatus.CONNECTED
                    conn.connected_at = datetime.now()
                    
                    return conn.to_dict()
                    
        except Exception as e:
            conn.status = ServerStatus.ERROR
            conn.error_message = str(e)
            raise MCPServerError(f"Failed to connect to '{name}': {e}")
    
    async def disconnect(self, name: str) -> Dict[str, Any]:
        """断开 Server 连接"""
        if name not in self._servers:
            raise MCPServerError(f"Server '{name}' not found")
        
        conn = self._servers[name]
        
        if conn.session:
            # MCP session 会在 context 退出时自动关闭
            conn.session = None
        
        # 清理工具映射
        for tool in conn.tools:
            tool_name = tool.get("name", "")
            if tool_name in self._tool_to_server:
                del self._tool_to_server[tool_name]
        
        conn.status = ServerStatus.DISCONNECTED
        conn.tools = []
        conn.connected_at = None
        
        return conn.to_dict()
    
    async def list_tools(self, name: str) -> List[Dict[str, Any]]:
        """获取 Server 提供的工具列表"""
        if name not in self._servers:
            raise MCPServerError(f"Server '{name}' not found")
        
        conn = self._servers[name]
        
        if conn.status != ServerStatus.CONNECTED:
            raise MCPServerError(f"Server '{name}' is not connected")
        
        return conn.tools
    
    def list_all_tools(self) -> List[Dict[str, Any]]:
        """获取所有已连接 Server 的工具列表"""
        all_tools = []
        for conn in self._servers.values():
            if conn.status == ServerStatus.CONNECTED:
                for tool in conn.tools:
                    all_tools.append({
                        **tool,
                        "server": conn.config.name,
                    })
        return all_tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        调用工具（自动路由到对应的 Server）
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        # 查找工具所属的 Server
        server_name = self._tool_to_server.get(tool_name)
        if not server_name:
            raise MCPServerError(f"Tool '{tool_name}' not found in any connected server")
        
        conn = self._servers.get(server_name)
        if not conn or conn.status != ServerStatus.CONNECTED:
            raise MCPServerError(f"Server '{server_name}' is not connected")
        
        if not conn.session:
            raise MCPServerError(f"Server '{server_name}' session is not available")
        
        try:
            result = await conn.session.call_tool(tool_name, arguments)
            
            # 解析结果
            if result.content:
                # 返回文本内容
                text_contents = [
                    c.text for c in result.content 
                    if hasattr(c, 'type') and c.type == 'text' and hasattr(c, 'text')
                ]
                if text_contents:
                    # 尝试解析 JSON
                    combined = "\n".join(text_contents)
                    try:
                        return json.loads(combined)
                    except json.JSONDecodeError:
                        return combined
            
            return {"status": "success", "content": result.content}
            
        except Exception as e:
            raise MCPServerError(f"Tool call failed: {e}")
    
    async def call_tool_on_server(
        self, 
        server_name: str, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> Any:
        """在指定 Server 上调用工具"""
        if server_name not in self._servers:
            raise MCPServerError(f"Server '{server_name}' not found")
        
        conn = self._servers[server_name]
        
        if conn.status != ServerStatus.CONNECTED:
            raise MCPServerError(f"Server '{server_name}' is not connected")
        
        if not conn.session:
            raise MCPServerError(f"Server '{server_name}' session is not available")
        
        try:
            result = await conn.session.call_tool(tool_name, arguments)
            
            if result.content:
                text_contents = [
                    c.text for c in result.content 
                    if hasattr(c, 'type') and c.type == 'text' and hasattr(c, 'text')
                ]
                if text_contents:
                    combined = "\n".join(text_contents)
                    try:
                        return json.loads(combined)
                    except json.JSONDecodeError:
                        return combined
            
            return {"status": "success", "content": result.content}
            
        except Exception as e:
            raise MCPServerError(f"Tool call failed: {e}")
    
    async def auto_connect_enabled(self) -> List[str]:
        """自动连接所有配置了 auto_connect 的 Server"""
        connected = []
        
        for name, conn in self._servers.items():
            if conn.config.enabled and conn.config.auto_connect:
                try:
                    await self.connect(name)
                    connected.append(name)
                except Exception as e:
                    print(f"Failed to auto-connect '{name}': {e}")
        
        return connected
    
    def load_from_config(self) -> int:
        """从配置文件加载 Server 配置"""
        mcp_config = get_mcp_config()
        count = 0
        
        for server_config in mcp_config.servers:
            if isinstance(server_config, dict):
                config = MCPServerConfig(**server_config)
            else:
                config = server_config
            
            if config.name not in self._servers:
                self._servers[config.name] = ServerConnection(config=config)
                count += 1
        
        return count
    
    def save_to_config_dict(self) -> List[Dict[str, Any]]:
        """导出为配置字典（用于保存到 YAML）"""
        return [
            {
                "name": conn.config.name,
                "command": conn.config.command,
                "args": conn.config.args,
                "env": conn.config.env,
                "enabled": conn.config.enabled,
                "auto_connect": conn.config.auto_connect,
                "description": conn.config.description,
            }
            for conn in self._servers.values()
        ]


# 全局管理器实例
_manager: Optional[ExternalMCPManager] = None


def get_external_mcp_manager() -> ExternalMCPManager:
    """获取全局管理器实例"""
    global _manager
    if _manager is None:
        _manager = ExternalMCPManager()
        _manager.load_from_config()
    return _manager
