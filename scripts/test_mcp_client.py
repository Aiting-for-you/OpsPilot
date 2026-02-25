#!/usr/bin/env python
"""
MCP 实现测试脚本

测试 MCP Server 和 Client 的基本功能
"""
import asyncio
import sys
import os
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_server_directly():
    """直接测试 Server（不通过 MCP 协议）"""
    print("=" * 60)
    print("测试 1: 直接调用 Server 方法")
    print("=" * 60)

    from opspilot.mcp.servers.erp_server import ERPMCPServer
    from opspilot.mcp.servers.compliance_server import ComplianceMCPServer

    # 测试 ERP Server
    print("\n--- ERP Server ---")
    erp_server = ERPMCPServer()

    # 查看注册的工具
    tools = erp_server.get_tools()
    print(f"已注册 {len(tools)} 个工具:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:50]}...")

    # 直接调用工具处理器
    print("\n测试调用 query_supplier:")
    for handler_name, handler in erp_server._handlers.items():
        if handler_name == "query_supplier":
            result = await handler({"region": "华南", "limit": 3})
            print(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}...")
            break

    # 测试 Compliance Server
    print("\n--- Compliance Server ---")
    compliance_server = ComplianceMCPServer()

    tools = compliance_server.get_tools()
    print(f"已注册 {len(tools)} 个工具:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:50]}...")

    print("\n测试调用 query_policy:")
    for handler_name, handler in compliance_server._handlers.items():
        if handler_name == "query_policy":
            result = await handler({"keywords": "采购", "limit": 3})
            print(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}...")
            break


async def test_mcp_protocol():
    """测试 MCP 协议通信"""
    print("\n" + "=" * 60)
    print("测试 2: MCP 协议通信（Client -> Server）")
    print("=" * 60)

    from opspilot.mcp.client import MCPClientManager, ServerConfig

    manager = MCPClientManager()

    # 配置 Server
    manager.add_server(ServerConfig(
        name="erp",
        command=sys.executable,
        args=["-m", "opspilot.mcp.servers.erp_server"],
    ))

    print("\n尝试连接 ERP Server...")
    try:
        async with manager.connect("erp") as client:
            print(f"✓ 已连接到 {client.server_name}")

            # 列出工具
            tools = await client.list_tools()
            print(f"\n可用工具 ({len(tools)} 个):")
            for tool in tools:
                print(f"  - {tool.name}")

            # 调用工具
            print("\n调用 query_supplier...")
            result = await client.call_tool("query_supplier", {"region": "华南", "limit": 3})
            print(f"结果类型: {type(result)}")
            if isinstance(result, dict):
                print(f"供应商数量: {result.get('total', 0)}")
                if result.get('suppliers'):
                    for s in result['suppliers'][:3]:
                        print(f"  - {s['supplier_id']}: {s['name']}")
            else:
                print(f"结果: {str(result)[:500]}")

            # 调用健康检查
            print("\n调用 health_check...")
            health = await client.call_tool("health_check", {})
            print(f"健康状态: {health}")

        print("\n✓ MCP 协议测试通过!")

    except Exception as e:
        print(f"✗ MCP 协议测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_router():
    """测试 MCPRouter"""
    print("\n" + "=" * 60)
    print("测试 3: MCPRouter 统一接口")
    print("=" * 60)

    from opspilot.mcp.client import MCPRouter

    router = MCPRouter()
    router.add_server_config(
        name="erp",
        command=sys.executable,
        args=["-m", "opspilot.mcp.servers.erp_server"],
    )

    print("\n启动 Router...")
    try:
        await router.start()
        print("✓ Router 已启动")

        # 列出工具
        tools = router.list_tools()
        print(f"\n可用工具 ({len(tools)} 个):")
        for tool in tools:
            print(f"  - {tool.name} ({tool.server_name})")

        # 调用工具
        print("\n调用 query_supplier...")
        result = await router.call_tool("query_supplier", {"limit": 2})
        if isinstance(result, dict):
            print(f"供应商数量: {result.get('total', 0)}")

        await router.stop()
        print("\n✓ Router 测试通过!")

    except Exception as e:
        print(f"✗ Router 测试失败: {e}")
        import traceback
        traceback.print_exc()
        await router.stop()


async def main():
    print("\n" + "=" * 60)
    print("OpsPilot MCP 实现测试")
    print("=" * 60)

    # 测试 1: 直接调用
    await test_server_directly()

    # 测试 2: MCP 协议
    await test_mcp_protocol()

    # 测试 3: Router
    # await test_router()  # 可选，需要更长时间

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
