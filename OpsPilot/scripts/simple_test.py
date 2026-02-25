"""简单测试 MCP Server 数据库版本"""
import asyncio
import sys

sys.path.insert(0, 'e:/AIagentCode/ShowWorkProject/OpsPilot')

async def main():
    # 测试数据库连接
    print("=== 测试数据库连接 ===")
    from opspilot.db.connection import get_database_pool
    
    pool = await get_database_pool()
    result = await pool.fetchval('SELECT COUNT(*) FROM suppliers')
    print(f"供应商数量: {result}")
    
    # 测试 MCP Server
    print("\n=== 测试 ERP Server ===")
    from opspilot.tools.mcp_db import ERPServerDB
    from opspilot.tools.base import ToolContext
    
    server = ERPServerDB()
    context = ToolContext(task_id='test')
    
    # 健康检查
    health = await server.health_check()
    print(f"健康检查: {'OK' if health else 'FAIL'}")
    
    # 查询供应商
    result = await server.execute_tool('query_supplier', {'limit': 3}, context)
    print(f"查询状态: {result.status.value}")
    if result.is_success():
        print(f"返回数量: {result.data['total']}")
        for s in result.data['suppliers']:
            print(f"  - {s['supplier_id']}: {s['name']}")
    else:
        print(f"错误: {result.error}")
    
    # 查询库存
    print("\n=== 测试库存查询 ===")
    result = await server.execute_tool('query_inventory', {'sku': 'SKU0001'}, context)
    print(f"查询状态: {result.status.value}")
    if result.is_success():
        print(f"产品: {result.data.get('product_name')}")
        print(f"总库存: {result.data.get('total_quantity')}")
    else:
        print(f"错误: {result.error}")
    
    # 关闭连接
    from opspilot.db.connection import close_database_pool
    await close_database_pool()
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(main())
