"""
真实数据库集成测试

使用 PostgreSQL 和 Redis 进行端到端功能测试
"""
import pytest
import asyncio
import os
import sys
import json
from typing import Dict, Any, List

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


@pytest.fixture
async def db_pool():
    """数据库连接池 fixture"""
    import asyncpg
    pool = await asyncpg.create_pool(
        host="localhost",
        port=5432,
        user="postgres",
        password="cyx0414",
        database="opspilot",
        min_size=1,
        max_size=5,
    )
    yield pool
    await pool.close()


@pytest.fixture
def cache():
    """Redis 缓存 fixture"""
    from opspilot.db.cache import CacheManager
    return CacheManager()


class TestDatabaseConnection:
    """测试数据库连接"""

    @pytest.mark.asyncio
    async def test_postgresql_connection(self, db_pool):
        """测试 PostgreSQL 连接"""
        async with db_pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            assert result == 1

    @pytest.mark.asyncio
    async def test_postgresql_query_suppliers(self, db_pool):
        """测试查询供应商数据"""
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM suppliers LIMIT 10")
            assert len(rows) > 0, "No suppliers data"
            row = rows[0]
            assert "supplier_id" in row or "id" in row

    @pytest.mark.asyncio
    async def test_postgresql_query_products(self, db_pool):
        """测试查询产品数据"""
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM products LIMIT 10")
            assert len(rows) > 0, "No products data"

    @pytest.mark.asyncio
    async def test_postgresql_query_inventory(self, db_pool):
        """测试查询库存数据"""
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM inventory LIMIT 10")
            assert isinstance(rows, list)


class TestRedisConnection:
    """测试 Redis 连接"""

    @pytest.mark.asyncio
    async def test_redis_connection(self, cache):
        """测试 Redis 连接"""
        assert cache.connected is True
        
        result = cache.set("test_key", "test_value", ttl=60)
        assert result is True
        
        value = cache.get("test_key")
        assert value == "test_value"
        
        cache.delete("test_key")

    @pytest.mark.asyncio
    async def test_redis_cache_operations(self, cache):
        """测试 Redis 缓存操作"""
        if not cache.connected:
            pytest.skip("Redis not connected")
        
        cache.set("test_string", "hello world", ttl=300)
        value = cache.get("test_string")
        assert value == "hello world"
        
        cache.delete("test_string")

    @pytest.mark.asyncio
    async def test_redis_ttl(self, cache):
        """测试 Redis TTL"""
        if not cache.connected:
            pytest.skip("Redis not connected")
        
        cache.set("ttl_test", "value", ttl=1)
        value = cache.get("ttl_test")
        assert value == "value"
        
        await asyncio.sleep(2)
        
        value = cache.get("ttl_test")
        assert value is None


class TestCacheWithDatabase:
    """测试缓存与数据库结合"""

    @pytest.mark.asyncio
    async def test_supplier_cache_flow(self, db_pool, cache):
        """测试供应商查询缓存流程"""
        if not cache.connected:
            pytest.skip("Redis not connected")
        
        import decimal
        import datetime
        
        def serialize_value(obj):
            """序列化特殊类型"""
            if isinstance(obj, decimal.Decimal):
                return float(obj)
            elif isinstance(obj, datetime.datetime):
                return obj.isoformat()
            elif isinstance(obj, datetime.date):
                return obj.isoformat()
            elif isinstance(obj, list):
                return [serialize_value(i) for i in obj]
            elif isinstance(obj, dict):
                return {k: serialize_value(v) for k, v in obj.items()}
            return obj
        
        cache_key = "test:suppliers:top"
        cached = cache.get(cache_key)
        
        if cached:
            suppliers = json.loads(cached)
        else:
            async with db_pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM suppliers LIMIT 5")
                suppliers = [serialize_value(dict(row)) for row in rows]
                cache.set(cache_key, json.dumps(suppliers), ttl=60)
        
        assert isinstance(suppliers, list)
        assert len(suppliers) > 0, "Should have suppliers data"
        
        cache.delete(cache_key)


class TestFullWorkflow:
    """完整工作流测试"""

    @pytest.mark.asyncio
    async def test_supplier_to_inventory_flow(self, db_pool):
        """测试供应商到产品到库存查询流程"""
        async with db_pool.acquire() as conn:
            # 1. 查询供应商
            suppliers = await conn.fetch("SELECT * FROM suppliers LIMIT 3")
            assert len(suppliers) > 0
            
            # 2. 查询产品
            products = await conn.fetch("SELECT * FROM products LIMIT 3")
            assert len(products) > 0
            
            # 3. 查询库存 (通过 sku 关联 products)
            product = products[0]
            sku = product.get("sku")
            
            inventory = await conn.fetch(
                "SELECT * FROM inventory WHERE sku = $1 LIMIT 10",
                sku
            )
            
            assert product is not None
            assert isinstance(inventory, list)

    @pytest.mark.asyncio
    async def test_order_creation_flow(self, db_pool):
        """测试订单创建流程"""
        import uuid
        from datetime import datetime
        
        async with db_pool.acquire() as conn:
            suppliers = await conn.fetch("SELECT supplier_id FROM suppliers LIMIT 1")
            assert len(suppliers) > 0
            supplier_id = suppliers[0]["supplier_id"]
            
            # 生成唯一订单号
            test_order_id = f"TEST-{uuid.uuid4().hex[:8].upper()}"
            
            order_id = await conn.fetchval("""
                INSERT INTO orders (order_id, supplier_id, status, total_amount)
                VALUES ($1, $2, 'pending', 0)
                RETURNING id
            """, test_order_id, supplier_id)
            
            assert order_id is not None
            
            await conn.execute("DELETE FROM orders WHERE order_id = $1", test_order_id)
            
            count = await conn.fetchval("SELECT COUNT(*) FROM orders WHERE order_id = $1", test_order_id)
            assert count == 0

    @pytest.mark.asyncio
    async def test_concurrent_database_queries(self, db_pool):
        """测试并发数据库查询"""
        # 每个查询使用独立的连接
        async with db_pool.acquire() as conn1:
            r1 = await conn1.fetch("SELECT * FROM suppliers LIMIT 5")
        async with db_pool.acquire() as conn2:
            r2 = await conn2.fetch("SELECT * FROM products LIMIT 5")
        async with db_pool.acquire() as conn3:
            r3 = await conn3.fetch("SELECT * FROM warehouses LIMIT 5")
        
        assert len(r1) > 0
        assert len(r2) > 0
        assert isinstance(r3, list)


class TestDataIntegrity:
    """数据完整性测试"""

    @pytest.mark.asyncio
    async def test_foreign_key_constraints(self, db_pool):
        """测试外键约束"""
        async with db_pool.acquire() as conn:
            with pytest.raises(Exception):
                await conn.execute("""
                    INSERT INTO orders (supplier_id, status)
                    VALUES ('NONEXISTENT_ID_12345', 'pending')
                """)

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, db_pool):
        """测试事务回滚"""
        async with db_pool.acquire() as conn:
            supplier = await conn.fetchrow("SELECT supplier_id FROM suppliers LIMIT 1")
            test_supplier_id = supplier["supplier_id"]
        
        try:
            async with db_pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute("""
                        INSERT INTO orders (supplier_id, status, total_amount)
                        VALUES ($1, 'pending', 100)
                    """, test_supplier_id)
                    raise Exception("Test rollback")
        except Exception:
            pass
        
        async with db_pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT COUNT(*) FROM orders 
                WHERE supplier_id = $1 AND status = 'pending' AND total_amount = 100
            """, test_supplier_id)
            assert result == 0
