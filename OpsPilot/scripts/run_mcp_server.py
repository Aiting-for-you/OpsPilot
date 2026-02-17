#!/usr/bin/env python
"""
MCP Server 启动脚本

启动指定的 MCP Server

用法：
    python scripts/run_mcp_server.py erp
    python scripts/run_mcp_server.py compliance
    python scripts/run_mcp_server.py erp --mode sse --port 8001
"""
import argparse
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser(description="启动 MCP Server")
    parser.add_argument(
        "server",
        choices=["erp", "compliance", "all"],
        help="要启动的 Server 名称",
    )
    parser.add_argument(
        "--mode",
        choices=["stdio", "sse"],
        default="stdio",
        help="运行模式：stdio 或 sse",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="SSE 模式的端口号",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="SSE 模式的主机地址",
    )

    args = parser.parse_args()

    if args.server == "erp":
        print(f"Starting ERP MCP Server ({args.mode} mode)...")
        from opspilot.mcp.servers.erp_server import ERPMCPServer
        server = ERPMCPServer()
        if args.mode == "sse":
            server.run(mode="sse", host=args.host, port=args.port)
        else:
            server.run(mode="stdio")

    elif args.server == "compliance":
        print(f"Starting Compliance MCP Server ({args.mode} mode)...")
        from opspilot.mcp.servers.compliance_server import ComplianceMCPServer
        server = ComplianceMCPServer()
        if args.mode == "sse":
            server.run(mode="sse", host=args.host, port=args.port)
        else:
            server.run(mode="stdio")

    elif args.server == "all":
        print("Starting all MCP Servers...")
        print("Note: Running multiple servers requires separate processes.")
        print("\nRun each server in a separate terminal:")
        print("  Terminal 1: python scripts/run_mcp_server.py erp")
        print("  Terminal 2: python scripts/run_mcp_server.py compliance")
        sys.exit(1)


if __name__ == "__main__":
    main()
