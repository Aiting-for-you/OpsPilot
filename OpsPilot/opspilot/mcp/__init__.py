"""
OpsPilot MCP 模块

提供标准的 MCP (Model Context Protocol) 实现：
- MCP Server：独立进程运行，支持 stdio/SSE 通信
- MCP Client：连接多个 Server，统一工具调用接口
- External MCP Manager：管理外部 MCP Server 连接

与现有 tools/ 模块并存，用户可选择使用：
- tools/：嵌入式工具框架（简单、快速）
- mcp/：标准 MCP 实现（进程隔离、协议标准）
"""

from opspilot.mcp.base import MCPServerBase, ToolDefinition
from opspilot.mcp.client import MCPClientManager, MCPRouter
from opspilot.mcp.external_manager import (
    ExternalMCPManager,
    ServerStatus,
    get_external_mcp_manager,
)

__all__ = [
    # Server
    "MCPServerBase",
    "ToolDefinition",
    # Client
    "MCPClientManager",
    "MCPRouter",
    # External Manager
    "ExternalMCPManager",
    "ServerStatus",
    "get_external_mcp_manager",
]
