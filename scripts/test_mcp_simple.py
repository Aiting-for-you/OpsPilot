"""测试 MCP Server 数据库版本"""
import asyncio
import sys

sys.path.insert(0, 'e:/AIagentCode/ShowWorkProject/OpsPilot')

from opspilot.db.connection import get_database_pool, close_database_pool
from opspilot.tools.mcp_db import ERPServerDB
from opspilot.tools.base import ToolContext


async def main():
    # 初始化数据库连接
    pool = await get_database_pool()
    
    # 创建 Server 和 Context
    server = ERPServerDB()
    context = ToolContext(task_id='test', user_id='test_user')
    
    # 健康检查
    print("=== ERP Server 测试 ===")
    health = await server.health_check()
    print(f"健康检查: {'OK' if health else 'FAIL'}")
    
    # 查询供应商
    print("\n--- query_supplier ---")
    result = await server.execute_tool('query_supplier', {'region': '华南', 'limit': 5}, context)
    print(f"状态: {result.status.value}")
    if result.is_success():
        print(f"返回数量: {result.data['total']}")
        for s in result.data['suppliers'][:3]:
            print(f"  - {s['supplier_id']}: {s['name']} (评分: {s['rating']})")
    else:
        print(f"错误: {result.error}")
    
    # 查询库存
    print("\n--- query_inventory ---")
    result = await server.execute_tool('query_inventory', {'sku': 'SKU0001'}, context)
    print(f"状态: {result.status.value}")
    if result.is_success():
        print(f"产品: {result.data.get('product_name')}")
        print(f"总库存: {result.data.get('total_quantity')}")
        print(f"可用: {result.data.get('total_available')}")
    else:
        print(f"错误: {result.error}")
    
    # 查询低库存
    print("\n--- query_low_stock ---")
    result = await server.execute_tool('query_low_stock', {}, context)
    print(f"状态: {result.status.value}")
    if result.is_success():
        print(f"低库存产品: {result.data['total']} 个")
        for item in result.data['low_stock_items'][:3]:
            print(f"  - {item['sku']}: {item['name']} (当前: {item['current_quantity']})")
    else:
        print(f"错误: {result.error}")
    
    # 查询汇率
    print("\n--- query_exchange_rate ---")
    result = await server.execute_tool('query_exchange_rate', {'from_currency': 'USD', 'to_currency': 'CNY'}, context)
    print(f"状态: {result.status.value}")
    if result.is_success():
        print(f"汇率: {result.data['from_currency']}/{result.data['to_currency']} = {result.data['rate']}")
    else:
        print(f"错误: {result.error}")
    
    # 关闭连接
    await close_database_pool()
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    asyncio.run(main())
