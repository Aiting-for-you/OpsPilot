"""
测试 MCP Server 数据库版本

验证：
1. 数据库连接
2. 工具注册
3. 工具调用
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from opspilot.tools.mcp_db import (
    ERPServerDB,
    ComplianceServerDB,
    LogisticsServerDB,
    EcommerceServerDB,
    create_db_router,
)
from opspilot.tools.base import ToolContext
from opspilot.db.connection import get_database_pool, close_database_pool


async def test_database_connection():
    """测试数据库连接"""
    print("\n=== 测试数据库连接 ===")
    
    try:
        pool = await get_database_pool()
        result = await pool.fetchval("SELECT COUNT(*) FROM suppliers")
        print(f"✅ 数据库连接成功")
        print(f"   供应商数量: {result}")
        
        result = await pool.fetchval("SELECT COUNT(*) FROM products")
        print(f"   产品数量: {result}")
        
        result = await pool.fetchval("SELECT COUNT(*) FROM orders")
        print(f"   订单数量: {result}")
        
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


async def test_erp_server():
    """测试 ERP Server"""
    print("\n=== 测试 ERP Server (数据库版本) ===")
    
    server = ERPServerDB()
    context = ToolContext(task_id="test-001", user_id="test_user")
    
    # 测试健康检查
    health = await server.health_check()
    print(f"健康检查: {'✅' if health else '❌'}")
    
    # 测试查询供应商
    print("\n--- query_supplier ---")
    result = await server.execute_tool("query_supplier", {"region": "华南", "limit": 5}, context)
    if result.is_success():
        print(f"✅ 查询成功，返回 {result.data['total']} 条记录")
        for s in result.data["suppliers"][:3]:
            print(f"   - {s['supplier_id']}: {s['name']} (评分: {s['rating']})")
    else:
        print(f"❌ 查询失败: {result.error}")
    
    # 测试查询产品
    print("\n--- query_product ---")
    result = await server.execute_tool("query_product", {"sku": "SKU0001"}, context)
    if result.is_success():
        print(f"✅ 查询成功")
        print(f"   产品: {result.data.get('name', 'N/A')}")
        print(f"   类别: {result.data.get('category', 'N/A')}")
    else:
        print(f"❌ 查询失败: {result.error}")
    
    # 测试查询库存
    print("\n--- query_inventory ---")
    result = await server.execute_tool("query_inventory", {"sku": "SKU0001"}, context)
    if result.is_success():
        print(f"✅ 查询成功")
        print(f"   总库存: {result.data.get('total_quantity', 0)}")
        print(f"   可用: {result.data.get('total_available', 0)}")
    else:
        print(f"❌ 查询失败: {result.error}")
    
    # 测试查询低库存
    print("\n--- query_low_stock ---")
    result = await server.execute_tool("query_low_stock", {"threshold_ratio": 0.5}, context)
    if result.is_success():
        print(f"✅ 查询成功，发现 {result.data['total']} 个低库存产品")
        for item in result.data["low_stock_items"][:3]:
            print(f"   - {item['sku']}: {item['name']} (当前: {item['current_quantity']}, 安全库存: {item['safety_stock']})")
    else:
        print(f"❌ 查询失败: {result.error}")
    
    # 测试查询汇率
    print("\n--- query_exchange_rate ---")
    result = await server.execute_tool("query_exchange_rate", {"from_currency": "USD", "to_currency": "CNY"}, context)
    if result.is_success():
        print(f"✅ 查询成功")
        print(f"   {result.data['from_currency']}/{result.data['to_currency']}: {result.data['rate']}")
    else:
        print(f"❌ 查询失败: {result.error}")


async def test_compliance_server():
    """测试合规 Server"""
    print("\n=== 测试 Compliance Server (数据库版本) ===")
    
    server = ComplianceServerDB()
    context = ToolContext(task_id="test-002")
    
    # 测试查询政策
    print("\n--- query_policy ---")
    result = await server.execute_tool("query_policy", {"category": "采购限额"}, context)
    if result.is_success():
        print(f"✅ 查询成功，返回 {result.data['total']} 条政策")
        for p in result.data["policies"][:2]:
            print(f"   - {p['title']}")
    else:
        print(f"❌ 查询失败: {result.error}")
    
    # 测试合规检查
    print("\n--- check_compliance (amount_limit) ---")
    result = await server.execute_tool("check_compliance", {
        "check_type": "amount_limit",
        "data": {"amount": 30000}
    }, context)
    if result.is_success():
        print(f"✅ 检查完成")
        print(f"   合规: {result.data['is_compliant']}")
        print(f"   违规: {len(result.data['violations'])} 项")
        print(f"   警告: {len(result.data['warnings'])} 项")
    else:
        print(f"❌ 检查失败: {result.error}")


async def test_logistics_server():
    """测试物流 Server"""
    print("\n=== 测试 Logistics Server (数据库版本) ===")
    
    server = LogisticsServerDB()
    context = ToolContext(task_id="test-003")
    
    # 测试查询物流
    print("\n--- query_logistics ---")
    # 先获取一个订单ID
    pool = await get_database_pool()
    order_id = await pool.fetchval("SELECT order_id FROM orders LIMIT 1")
    
    if order_id:
        result = await server.execute_tool("query_logistics", {"order_id": order_id}, context)
        if result.is_success():
            print(f"✅ 查询成功")
            print(f"   运单号: {result.data.get('tracking_no', 'N/A')}")
            print(f"   承运商: {result.data.get('carrier', 'N/A')}")
            print(f"   状态: {result.data.get('status', 'N/A')}")
        else:
            print(f"❌ 查询失败: {result.error}")
    else:
        print("⚠️ 没有订单数据，跳过测试")
    
    # 测试查询报关问题
    print("\n--- query_customs_issues ---")
    result = await server.execute_tool("query_customs_issues", {}, context)
    if result.is_success():
        print(f"✅ 查询成功，发现 {result.data['total']} 个问题报关单")
    else:
        print(f"❌ 查询失败: {result.error}")


async def test_ecommerce_server():
    """测试电商 Server"""
    print("\n=== 测试 Ecommerce Server (数据库版本) ===")
    
    server = EcommerceServerDB()
    context = ToolContext(task_id="test-004")
    
    # 测试查询平台订单
    print("\n--- query_platform_orders ---")
    result = await server.execute_tool("query_platform_orders", {"platform": "Amazon", "limit": 5}, context)
    if result.is_success():
        print(f"✅ 查询成功，返回 {result.data['total']} 条订单")
    else:
        print(f"❌ 查询失败: {result.error}")
    
    # 测试查询待发货
    print("\n--- query_pending_shipments ---")
    result = await server.execute_tool("query_pending_shipments", {}, context)
    if result.is_success():
        print(f"✅ 查询成功，待发货订单: {result.data['total']} 条")
    else:
        print(f"❌ 查询失败: {result.error}")


async def test_router():
    """测试路由器"""
    print("\n=== 测试 ToolRouter ===")
    
    router = create_db_router()
    context = ToolContext(task_id="test-router")
    
    # 获取所有工具
    schemas = router.get_all_schemas()
    print(f"已注册工具数量: {len(schemas)}")
    
    # 列出所有工具
    print("\n已注册工具列表:")
    for schema in schemas[:10]:  # 只显示前10个
        print(f"   - {schema.name}: {schema.description[:40]}...")
    
    # 测试健康检查
    print("\n健康检查:")
    health = await router.health_check_all()
    for name, status in health.items():
        print(f"   - {name}: {'✅' if status else '❌'}")
    
    # 通过路由器调用工具
    print("\n通过路由器调用工具:")
    result = await router.call_tool("query_supplier", {"limit": 3}, context)
    if result.is_success():
        print(f"✅ 路由调用成功，返回 {result.data['total']} 条记录")
    else:
        print(f"❌ 路由调用失败: {result.error}")


async def main():
    """主测试函数"""
    print("=" * 60)
    print("MCP Server 数据库版本测试")
    print("=" * 60)
    
    try:
        # 测试数据库连接
        db_ok = await test_database_connection()
        if not db_ok:
            print("\n❌ 数据库连接失败，无法继续测试")
            return
        
        # 测试各个 Server
        await test_erp_server()
        await test_compliance_server()
        await test_logistics_server()
        await test_ecommerce_server()
        
        # 测试路由器
        await test_router()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 关闭数据库连接
        await close_database_pool()


if __name__ == "__main__":
    asyncio.run(main())
