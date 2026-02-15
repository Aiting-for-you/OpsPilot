"""
MCP Server 模块单元测试
"""
import pytest

from opspilot.tools.base import ToolContext, ToolStatus
from opspilot.tools.mcp import (
    ERPServer,
    ComplianceServer,
    MOCK_SUPPLIERS,
    MOCK_INVENTORY,
    MOCK_ORDERS,
)


class TestERPServer:
    """ERP Server 测试"""

    @pytest.fixture
    def server(self):
        return ERPServer()

    @pytest.fixture
    def context(self):
        return ToolContext(task_id="test-task", user_id="test-user")

    def test_server_info(self, server):
        """测试服务器信息"""
        assert server.name == "erp-tools"
        assert "供应商" in server.description

    def test_registered_tools(self, server):
        """测试注册的工具"""
        schemas = server.get_all_schemas()
        tool_names = [s.name for s in schemas]

        assert "query_supplier" in tool_names
        assert "create_order" in tool_names
        assert "query_inventory" in tool_names
        assert "query_order" in tool_names
        assert "update_order_status" in tool_names

    @pytest.mark.asyncio
    async def test_query_supplier_all(self, server, context):
        """测试查询所有供应商"""
        result = await server.execute_tool("query_supplier", {}, context)

        assert result.is_success()
        assert len(result.data["suppliers"]) == len(MOCK_SUPPLIERS)

    @pytest.mark.asyncio
    async def test_query_supplier_by_region(self, server, context):
        """测试按区域查询供应商"""
        result = await server.execute_tool(
            "query_supplier",
            {"region": "华南"},
            context
        )

        assert result.is_success()
        for supplier in result.data["suppliers"]:
            assert supplier["region"] == "华南"

    @pytest.mark.asyncio
    async def test_query_supplier_by_name(self, server, context):
        """测试按名称查询供应商"""
        result = await server.execute_tool(
            "query_supplier",
            {"supplier_name": "电子"},
            context
        )

        assert result.is_success()
        assert len(result.data["suppliers"]) > 0
        for supplier in result.data["suppliers"]:
            assert "电子" in supplier["name"]

    @pytest.mark.asyncio
    async def test_create_order_success(self, server, context):
        """测试创建订单成功"""
        result = await server.execute_tool(
            "create_order",
            {
                "supplier_id": "SUP001",
                "products": [
                    {"sku": "SKU001", "quantity": 100},
                    {"sku": "SKU002", "quantity": 50}
                ]
            },
            context
        )

        assert result.is_success()
        assert "order_id" in result.data
        assert result.data["order_id"].startswith("ORD")

    @pytest.mark.asyncio
    async def test_create_order_need_approval(self, server, context):
        """测试创建需要审批的订单"""
        result = await server.execute_tool(
            "create_order",
            {
                "supplier_id": "SUP001",
                "products": [
                    {"sku": "SKU001", "quantity": 1000}  # 大额订单
                ]
            },
            context
        )

        assert result.is_success()
        assert result.data["need_approval"] is True
        assert result.data["status"] == "pending_approval"

    @pytest.mark.asyncio
    async def test_create_order_supplier_not_found(self, server, context):
        """测试创建订单供应商不存在"""
        result = await server.execute_tool(
            "create_order",
            {
                "supplier_id": "INVALID_SUP",
                "products": [{"sku": "SKU001", "quantity": 10}]
            },
            context
        )

        assert result.status == ToolStatus.ERROR
        assert result.error_code == "SUPPLIER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_query_inventory_success(self, server, context):
        """测试查询库存成功"""
        result = await server.execute_tool(
            "query_inventory",
            {"sku": "SKU001"},
            context
        )

        assert result.is_success()
        assert result.data["sku"] == "SKU001"
        assert "quantity" in result.data

    @pytest.mark.asyncio
    async def test_query_inventory_not_found(self, server, context):
        """测试查询库存产品不存在"""
        result = await server.execute_tool(
            "query_inventory",
            {"sku": "INVALID_SKU"},
            context
        )

        assert result.status == ToolStatus.ERROR
        assert result.error_code == "PRODUCT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_query_order_flow(self, server, context):
        """测试订单查询流程"""
        # 先创建订单
        create_result = await server.execute_tool(
            "create_order",
            {
                "supplier_id": "SUP001",
                "products": [{"sku": "SKU001", "quantity": 10}]
            },
            context
        )
        order_id = create_result.data["order_id"]

        # 查询订单
        query_result = await server.execute_tool(
            "query_order",
            {"order_id": order_id},
            context
        )

        assert query_result.is_success()
        assert query_result.data["order_id"] == order_id

    @pytest.mark.asyncio
    async def test_update_order_status(self, server, context):
        """测试更新订单状态"""
        # 创建订单
        create_result = await server.execute_tool(
            "create_order",
            {
                "supplier_id": "SUP001",
                "products": [{"sku": "SKU001", "quantity": 10}]
            },
            context
        )
        order_id = create_result.data["order_id"]

        # 更新状态
        update_result = await server.execute_tool(
            "update_order_status",
            {
                "order_id": order_id,
                "status": "approved",
                "reason": "审批通过"
            },
            context
        )

        assert update_result.is_success()
        assert update_result.data["new_status"] == "approved"

    @pytest.mark.asyncio
    async def test_health_check(self, server):
        """测试健康检查"""
        result = await server.health_check()
        assert result is True


class TestComplianceServer:
    """合规 Server 测试"""

    @pytest.fixture
    def server(self):
        return ComplianceServer()

    @pytest.fixture
    def context(self):
        return ToolContext(task_id="test-task")

    def test_server_info(self, server):
        """测试服务器信息"""
        assert server.name == "compliance-tools"

    def test_registered_tools(self, server):
        """测试注册的工具"""
        schemas = server.get_all_schemas()
        tool_names = [s.name for s in schemas]

        assert "query_policy" in tool_names
        assert "check_compliance" in tool_names

    @pytest.mark.asyncio
    async def test_query_policy_all(self, server, context):
        """测试查询所有政策"""
        result = await server.execute_tool("query_policy", {}, context)

        assert result.is_success()
        assert len(result.data["policies"]) > 0

    @pytest.mark.asyncio
    async def test_query_policy_by_category(self, server, context):
        """测试按类别查询政策"""
        result = await server.execute_tool(
            "query_policy",
            {"category": "采购限额"},
            context
        )

        assert result.is_success()
        for policy in result.data["policies"]:
            assert "采购限额" in policy["category"]

    @pytest.mark.asyncio
    async def test_check_compliance_amount_limit(self, server, context):
        """测试金额限额合规检查"""
        # 超过限额
        result = await server.execute_tool(
            "check_compliance",
            {
                "check_type": "amount_limit",
                "data": {"amount": 60000}
            },
            context
        )

        assert result.is_success()
        assert result.data["is_compliant"] is False
        assert len(result.data["violations"]) > 0

    @pytest.mark.asyncio
    async def test_check_compliance_supplier_rating(self, server, context):
        """测试供应商评分合规检查"""
        # 评分低于标准
        result = await server.execute_tool(
            "check_compliance",
            {
                "check_type": "supplier_rating",
                "data": {"rating": 3.5}
            },
            context
        )

        assert result.is_success()
        assert result.data["is_compliant"] is False

    @pytest.mark.asyncio
    async def test_health_check(self, server):
        """测试健康检查"""
        result = await server.health_check()
        assert result is True

