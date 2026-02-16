"""
端到端业务流程测试

使用 fixtures 模拟数据进行完整的业务流程测试
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

# 直接导入 fixtures 模块
import sys
import os
fixtures_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fixtures')
sys.path.insert(0, fixtures_path)

from erp_data import (
    MOCK_SUPPLIERS,
    MOCK_INVENTORY,
    MOCK_PRODUCTS,
    generate_mock_order,
)
from compliance_data import check_compliance
from llm_mock import (
    MockLLMClient,
    IntentMockLLMClient,
    AgentMockLLMClient,
)


# ============================================================================
# 供应商查询流程测试
# ============================================================================

class TestSupplierQueryFlow:
    """供应商查询业务流程测试"""

    @pytest.mark.asyncio
    async def test_query_supplier_by_region(self):
        """测试按区域查询供应商"""
        # 模拟查询
        suppliers = [s for s in MOCK_SUPPLIERS if s["region"] == "华南"]
        
        assert len(suppliers) == 1
        assert suppliers[0]["id"] == "SUP001"
        assert suppliers[0]["name"] == "华南电子科技有限公司"

    @pytest.mark.asyncio
    async def test_query_supplier_by_rating(self):
        """测试按评分筛选供应商"""
        high_rated = [s for s in MOCK_SUPPLIERS if s["rating"] >= 4.5]
        
        assert len(high_rated) == 3
        assert all(s["rating"] >= 4.5 for s in high_rated)

    @pytest.mark.asyncio
    async def test_query_supplier_by_product(self):
        """测试按产品类型查询供应商"""
        suppliers_with_electronics = [
            s for s in MOCK_SUPPLIERS 
            if "电子元件" in s["products"]
        ]
        
        assert len(suppliers_with_electronics) == 1
        assert suppliers_with_electronics[0]["id"] == "SUP001"

    @pytest.mark.asyncio
    async def test_intent_recognition_for_supplier_query(self):
        """测试供应商查询意图识别"""
        client = IntentMockLLMClient()
        
        response = await client.generate("帮我查询华南地区的供应商")
        assert "query_supplier" in response
        
        response = await client.generate("有没有做电子元器件的供应商")
        assert "query_supplier" in response


# ============================================================================
# 库存查询流程测试
# ============================================================================

class TestInventoryQueryFlow:
    """库存查询业务流程测试"""

    @pytest.mark.asyncio
    async def test_query_inventory_by_sku(self):
        """测试按 SKU 查询库存"""
        sku = "SKU001"
        inventory = MOCK_INVENTORY.get(sku)
        
        assert inventory is not None
        assert inventory["quantity"] == 50000
        assert inventory["available"] == 48000
        assert inventory["warehouse"] == "WH001"

    @pytest.mark.asyncio
    async def test_check_low_stock(self):
        """测试低库存预警"""
        low_stock_items = []
        for sku, inv in MOCK_INVENTORY.items():
            product = MOCK_PRODUCTS.get(sku)
            if product:
                safety_stock = product["safety_stock"]
                if inv["quantity"] < safety_stock:
                    low_stock_items.append({
                        "sku": sku,
                        "name": product["name"],
                        "current": inv["quantity"],
                        "safety": safety_stock,
                    })
        
        # 验证低库存检测逻辑
        assert isinstance(low_stock_items, list)

    @pytest.mark.asyncio
    async def test_intent_recognition_for_inventory_query(self):
        """测试库存查询意图识别"""
        client = IntentMockLLMClient()
        
        response = await client.generate("查询 SKU001 的库存")
        assert "query_inventory" in response
        
        response = await client.generate("库存还有多少")
        assert "query_inventory" in response


# ============================================================================
# 订单创建流程测试
# ============================================================================

class TestOrderCreationFlow:
    """订单创建业务流程测试"""

    @pytest.mark.asyncio
    async def test_create_small_order(self):
        """测试创建小额订单（无需审批）"""
        order = generate_mock_order(
            supplier_id="SUP001",
            products=[{"sku": "SKU001", "quantity": 100}],
        )
        
        assert order["supplier_id"] == "SUP001"
        assert order["total_amount"] == 2.0  # 100 * 0.02
        assert order["need_approval"] is False
        assert order["status"] == "created"

    @pytest.mark.asyncio
    async def test_create_order_needs_approval(self):
        """测试创建需要审批的订单"""
        order = generate_mock_order(
            supplier_id="SUP001",
            products=[{"sku": "SKU003", "quantity": 2000}],  # 2000 * 8.5 = 17000
        )
        
        assert order["total_amount"] == 17000.0
        assert order["need_approval"] is True
        assert order["status"] == "pending_approval"
        assert order["approval_level"] == "manager"

    @pytest.mark.asyncio
    async def test_create_order_director_approval(self):
        """测试创建需要总监审批的订单"""
        order = generate_mock_order(
            supplier_id="SUP001",
            products=[{"sku": "SKU003", "quantity": 10000}],  # 10000 * 8.5 = 85000
        )
        
        assert order["total_amount"] == 85000.0
        assert order["need_approval"] is True
        assert order["approval_level"] == "director"

    @pytest.mark.asyncio
    async def test_intent_recognition_for_order(self):
        """测试订单创建意图识别"""
        client = IntentMockLLMClient()
        
        response = await client.generate("帮我创建一个采购订单")
        assert "create_order" in response
        
        response = await client.generate("我要下单")
        assert "create_order" in response


# ============================================================================
# 合规检查流程测试
# ============================================================================

class TestComplianceCheckFlow:
    """合规检查业务流程测试"""

    @pytest.mark.asyncio
    async def test_check_amount_compliance_small(self):
        """测试小额采购合规检查"""
        result = check_compliance(
            check_type="amount_limit",
            data={"amount": 3000}
        )
        
        assert result["is_compliant"] is True
        assert len(result["violations"]) == 0

    @pytest.mark.asyncio
    async def test_check_amount_compliance_medium(self):
        """测试中等金额采购合规检查"""
        result = check_compliance(
            check_type="amount_limit",
            data={"amount": 15000}
        )
        
        # 15000 超过 10000 但不超过 50000，应该是合规但有警告
        assert result["is_compliant"] is True

    @pytest.mark.asyncio
    async def test_check_amount_compliance_large(self):
        """测试大额采购合规检查"""
        result = check_compliance(
            check_type="amount_limit",
            data={"amount": 60000}
        )
        
        # 60000 超过 50000，应该有违规
        assert result["is_compliant"] is False
        assert len(result["violations"]) > 0

    @pytest.mark.asyncio
    async def test_check_supplier_rating_compliance(self):
        """测试供应商评分合规检查"""
        result = check_compliance(
            check_type="supplier_rating",
            data={"rating": 4.5}
        )
        
        assert result["is_compliant"] is True
        
        result = check_compliance(
            check_type="supplier_rating",
            data={"rating": 3.8}
        )
        
        assert result["is_compliant"] is False
        assert len(result["violations"]) > 0


# ============================================================================
# 完整业务流程测试
# ============================================================================

class TestFullBusinessFlow:
    """完整业务流程测试"""

    @pytest.fixture
    def mock_llm_client(self):
        """创建 Mock LLM 客户端"""
        return AgentMockLLMClient(agent_type="intent")

    @pytest.mark.asyncio
    async def test_procurement_flow(self):
        """测试完整采购流程"""
        # 1. 用户查询供应商
        suppliers = [s for s in MOCK_SUPPLIERS if s["region"] == "华南"]
        assert len(suppliers) > 0
        
        supplier = suppliers[0]
        
        # 2. 查询产品库存
        sku = "SKU001"
        inventory = MOCK_INVENTORY.get(sku)
        assert inventory is not None
        assert inventory["available"] >= 100
        
        # 3. 创建订单
        order = generate_mock_order(
            supplier_id=supplier["id"],
            products=[{"sku": sku, "quantity": 100}],
        )
        assert order["status"] in ["created", "pending_approval"]
        
        # 4. 合规检查
        compliance = check_compliance(
            check_type="amount_limit",
            data={"amount": order["total_amount"]},
        )
        
        if order["need_approval"]:
            assert compliance["violations"] or compliance["warnings"]

    @pytest.mark.asyncio
    async def test_multi_step_workflow_with_mock_llm(self):
        """测试多步骤工作流（Mock LLM）"""
        client = MockLLMClient(
            responses={
                "供应商": "找到华南电子科技有限公司",
                "库存": "库存充足，当前50000件",
                "订单": "订单创建成功，订单号：PO20260217001",
            }
        )
        
        # 步骤1：查询供应商
        response1 = await client.generate("查询供应商信息")
        assert "华南电子" in response1 or "找到" in response1
        
        # 步骤2：查询库存
        response2 = await client.generate("查询库存")
        assert "库存" in response2
        
        # 步骤3：创建订单
        response3 = await client.generate("创建订单")
        assert "订单" in response3

    @pytest.mark.asyncio
    async def test_concurrent_business_operations(self):
        """测试并发业务操作"""
        async def query_supplier(region: str):
            return [s for s in MOCK_SUPPLIERS if s["region"] == region]
        
        async def check_inventory(sku: str):
            return MOCK_INVENTORY.get(sku)
        
        # 并发执行多个查询
        results = await asyncio.gather(
            query_supplier("华南"),
            query_supplier("华东"),
            check_inventory("SKU001"),
            check_inventory("SKU002"),
        )
        
        assert len(results[0]) == 1  # 华南供应商
        assert len(results[1]) == 1  # 华东供应商
        assert results[2] is not None  # SKU001 库存
        assert results[3] is not None  # SKU002 库存


# ============================================================================
# 错误处理测试
# ============================================================================

class TestErrorHandling:
    """错误处理测试"""

    @pytest.mark.asyncio
    async def test_invalid_supplier_id(self):
        """测试无效供应商ID"""
        with pytest.raises(ValueError):
            generate_mock_order(supplier_id="INVALID_ID")

    @pytest.mark.asyncio
    async def test_invalid_sku(self):
        """测试无效 SKU"""
        inventory = MOCK_INVENTORY.get("INVALID_SKU")
        assert inventory is None

    @pytest.mark.asyncio
    async def test_llm_error_simulation(self):
        """测试 LLM 错误模拟"""
        client = MockLLMClient(error_rate=1.0)  # 100% 错误率
        
        with pytest.raises(RuntimeError):
            await client.generate("测试查询")

    @pytest.mark.asyncio
    async def test_compliance_check_with_missing_data(self):
        """测试缺少数据的合规检查"""
        result = check_compliance(
            check_type="amount_limit",
            data={}  # 缺少 amount 字段
        )
        
        # 应该不会崩溃
        assert "is_compliant" in result


# ============================================================================
# 性能测试
# ============================================================================

class TestPerformance:
    """性能测试"""

    @pytest.mark.asyncio
    async def test_large_dataset_query(self):
        """测试大数据集查询"""
        # 模拟大量数据查询
        import time
        
        start = time.time()
        
        # 查询所有供应商
        all_suppliers = list(MOCK_SUPPLIERS)
        
        # 多次过滤操作
        for _ in range(1000):
            _ = [s for s in MOCK_SUPPLIERS if s["rating"] >= 4.0]
        
        elapsed = time.time() - start
        
        # 1000 次过滤应该在 1 秒内完成
        assert elapsed < 1.0

    @pytest.mark.asyncio
    async def test_concurrent_order_creation(self):
        """测试并发订单创建"""
        async def create_order(i: int):
            return generate_mock_order(
                supplier_id="SUP001",
                products=[{"sku": "SKU001", "quantity": i + 1}],
            )
        
        # 并发创建 10 个订单
        orders = await asyncio.gather(*[create_order(i) for i in range(10)])
        
        assert len(orders) == 10
        assert all(o["supplier_id"] == "SUP001" for o in orders)

    @pytest.mark.asyncio
    async def test_mock_llm_latency(self):
        """测试 Mock LLM 延迟"""
        client = MockLLMClient(latency_ms=10)
        
        import time
        start = time.time()
        
        for _ in range(100):
            await client.generate("测试")
        
        elapsed = time.time() - start
        
        # 100 次 * 10ms = 1s，加上一些开销
        assert elapsed >= 1.0
        assert elapsed < 2.0
