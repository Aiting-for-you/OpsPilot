"""
MCP Server 实现

各个业务领域的 MCP Server 实现
"""
from opspilot.mcp.servers.erp_server import ERPMCPServer
from opspilot.mcp.servers.compliance_server import ComplianceMCPServer

__all__ = [
    "ERPMCPServer",
    "ComplianceMCPServer",
]
