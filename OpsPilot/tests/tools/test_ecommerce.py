"""
跨境电商 MCP 工具测试

测试 EcommerceMockServer 的所有工具
"""
import pytest
import asyncio

from opspilot.tools.ecommerce import EcommerceMockServer, create_ecommerce_server
from opspilot.tools.base import ToolContext


@pytest.fixture
def ecommerce_server():
    """创建电商 Mock Server"""
    return create_ecommerce_server(latency_ms=10)


@pytest.fixture
def context():
    """创建工具上下文"""
    return ToolContext(task_id="test-task-001", user_id="test-user")


class TestExchangeRateTools:
    """汇率工具测试"""

    @pytest.mark.asyncio
    async def test_get_exchange_rate_usd_cny(self, ecommerce_server, context):
        """测试获取 USD/CNY 汇率"""
        result = await ecommerce_server.execute_tool(
            "get_exchange_rate",
            {"from_currency": "USD", "to_currency": "CNY"},
            context,
        )
        
        assert result.is_success()
        assert result.data["from_currency"] == "USD"
        assert result.data["to_currency"] == "CNY"
        assert result.data["rate"] > 0

    @pytest.mark.asyncio
    async def test_get_exchange_rate_unsupported(self, ecommerce_server, context):
        """测试不支持的货币对"""
        result = await ecommerce_server.execute_tool(
            "get_exchange_rate",
            {"from_currency": "XXX", "to_currency": "YYY"},
            context,
        )
        
        assert not result.is_success()
        assert result.error_code == "UNSUPPORTED_CURRENCY_PAIR"

    @pytest.mark.asyncio
    async def test_convert_currency(self, ecommerce_server, context):
        """测试货币换算"""
        result = await ecommerce_server.execute_tool(
            "convert_currency",
            {"amount": 100, "from_currency": "USD", "to_currency": "CNY"},
            context,
        )
        
        assert result.is_success()
        assert result.data["original_amount"] == 100
        assert result.data["original_currency"] == "USD"
        assert result.data["converted_currency"] == "CNY"
        assert result.data["converted_amount"] > 0

    @pytest.mark.asyncio
    async def test_list_exchange_rates(self, ecommerce_server, context):
        """测试获取汇率列表"""
        result = await ecommerce_server.execute_tool(
            "list_exchange_rates",
            {},
            context,
        )
        
        assert result.is_success()
        assert result.data["total"] > 0
        assert len(result.data["rates"]) == result.data["total"]


class TestLogisticsTools:
    """物流工具测试"""

    @pytest.mark.asyncio
    async def test_track_logistics_exists(self, ecommerce_server, context):
        """测试查询存在的物流"""
        result = await ecommerce_server.execute_tool(
            "track_logistics",
            {"tracking_no": "SF1234567890123"},
            context,
        )
        
        assert result.is_success()
        assert result.data["tracking_no"] == "SF1234567890123"
        assert result.data["status"] == "in_transit"
        assert len(result.data["timeline"]) > 0

    @pytest.mark.asyncio
    async def test_track_logistics_not_exists(self, ecommerce_server, context):
        """测试查询不存在的物流"""
        result = await ecommerce_server.execute_tool(
            "track_logistics",
            {"tracking_no": "NOT_EXISTS"},
            context,
        )
        
        assert not result.is_success()
        assert result.error_code == "TRACKING_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_list_logistics_by_status_delayed(self, ecommerce_server, context):
        """测试按状态查询延迟物流"""
        result = await ecommerce_server.execute_tool(
            "list_logistics_by_status",
            {"status": "delayed"},
            context,
        )
        
        assert result.is_success()
        assert result.data["status"] == "delayed"
        # 应该有一个延迟的物流
        assert len(result.data["items"]) > 0

    @pytest.mark.asyncio
    async def test_get_delayed_shipments(self, ecommerce_server, context):
        """测试获取问题物流"""
        result = await ecommerce_server.execute_tool(
            "get_delayed_shipments",
            {},
            context,
        )
        
        assert result.is_success()
        assert "delayed" in result.data
        assert "customs_hold" in result.data


class TestPlatformOrderTools:
    """平台订单工具测试"""

    @pytest.mark.asyncio
    async def test_get_platform_order_exists(self, ecommerce_server, context):
        """测试查询存在的订单"""
        result = await ecommerce_server.execute_tool(
            "get_platform_order",
            {"order_id": "AMZ-2026021002"},
            context,
        )
        
        assert result.is_success()
        assert result.data["order_id"] == "AMZ-2026021002"
        assert result.data["platform"] == "amazon"

    @pytest.mark.asyncio
    async def test_get_platform_order_not_exists(self, ecommerce_server, context):
        """测试查询不存在的订单"""
        result = await ecommerce_server.execute_tool(
            "get_platform_order",
            {"order_id": "NOT_EXISTS"},
            context,
        )
        
        assert not result.is_success()
        assert result.error_code == "ORDER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_list_platform_orders_by_platform(self, ecommerce_server, context):
        """测试按平台查询订单"""
        result = await ecommerce_server.execute_tool(
            "list_platform_orders",
            {"platform": "amazon"},
            context,
        )
        
        assert result.is_success()
        assert result.data["filters"]["platform"] == "amazon"
        # 所有订单应该是亚马逊的
        for order in result.data["orders"]:
            assert order["platform"] == "amazon"

    @pytest.mark.asyncio
    async def test_sync_platform_orders(self, ecommerce_server, context):
        """测试同步平台订单"""
        result = await ecommerce_server.execute_tool(
            "sync_platform_orders",
            {"platform": "amazon", "days": 7},
            context,
        )
        
        assert result.is_success()
        assert result.data["platform"] == "amazon"
        assert result.data["total_orders"] > 0

    @pytest.mark.asyncio
    async def test_get_pending_shipments(self, ecommerce_server, context):
        """测试获取待发货订单"""
        result = await ecommerce_server.execute_tool(
            "get_pending_shipments",
            {},
            context,
        )
        
        assert result.is_success()
        assert "pending_shipment" in result.data
        assert "pending_payment" in result.data


class TestCustomsTools:
    """报关工具测试"""

    @pytest.mark.asyncio
    async def test_get_customs_by_declaration_no(self, ecommerce_server, context):
        """测试按报关单号查询"""
        result = await ecommerce_server.execute_tool(
            "get_customs_declaration",
            {"declaration_no": "CUS2026021501"},
            context,
        )
        
        assert result.is_success()
        assert result.data["declaration_no"] == "CUS2026021501"
        assert result.data["status"] == "cleared"

    @pytest.mark.asyncio
    async def test_get_customs_by_order_id(self, ecommerce_server, context):
        """测试按订单号查询报关单"""
        result = await ecommerce_server.execute_tool(
            "get_customs_declaration",
            {"order_id": "AMZ-2026021002"},
            context,
        )
        
        assert result.is_success()
        assert result.data["order_id"] == "AMZ-2026021002"

    @pytest.mark.asyncio
    async def test_list_customs_by_status(self, ecommerce_server, context):
        """测试按状态查询报关单"""
        result = await ecommerce_server.execute_tool(
            "list_customs_by_status",
            {"status": "pending_docs"},
            context,
        )
        
        assert result.is_success()
        assert result.data["status"] == "pending_docs"

    @pytest.mark.asyncio
    async def test_get_customs_issues(self, ecommerce_server, context):
        """测试获取问题报关单"""
        result = await ecommerce_server.execute_tool(
            "get_customs_issues",
            {},
            context,
        )
        
        assert result.is_success()
        assert "pending_documents" in result.data


class TestSummaryTools:
    """统计工具测试"""

    @pytest.mark.asyncio
    async def test_get_ecommerce_summary(self, ecommerce_server, context):
        """测试获取汇总统计"""
        result = await ecommerce_server.execute_tool(
            "get_ecommerce_summary",
            {},
            context,
        )
        
        assert result.is_success()
        assert "orders" in result.data
        assert "logistics" in result.data
        assert "customs" in result.data
        assert "exchange_rates" in result.data
        
        # 验证订单统计
        assert result.data["orders"]["total"] > 0
        assert result.data["orders"]["total_amount_usd"] > 0


class TestServerHealth:
    """服务器健康检查测试"""

    @pytest.mark.asyncio
    async def test_health_check(self, ecommerce_server):
        """测试健康检查"""
        result = await ecommerce_server.health_check()
        assert result is True

    def test_server_name(self, ecommerce_server):
        """测试服务器名称"""
        assert ecommerce_server.name == "ecommerce-tools"

    def test_server_has_tools(self, ecommerce_server):
        """测试服务器注册了工具"""
        schemas = ecommerce_server.get_all_schemas()
        assert len(schemas) > 0
        
        # 检查关键工具存在
        tool_names = [s.name for s in schemas]
        assert "get_exchange_rate" in tool_names
        assert "track_logistics" in tool_names
        assert "get_platform_order" in tool_names
        assert "get_customs_declaration" in tool_names
