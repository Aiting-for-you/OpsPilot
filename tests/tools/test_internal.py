"""
内部工具模块单元测试
"""
import pytest

from opspilot.tools.base import ToolContext, ToolStatus
from opspilot.tools.internal import InternalToolsServer


class TestInternalToolsServer:
    """内部工具服务器测试"""

    @pytest.fixture
    def server(self):
        return InternalToolsServer()

    @pytest.fixture
    def context(self):
        return ToolContext(task_id="test-task")

    def test_server_info(self, server):
        """测试服务器信息"""
        assert server.name == "internal-tools"

    def test_registered_tools(self, server):
        """测试注册的工具"""
        schemas = server.get_all_schemas()
        tool_names = [s.name for s in schemas]

        assert "format_currency" in tool_names
        assert "calculate_total" in tool_names
        assert "calculate_date" in tool_names
        assert "format_json" in tool_names
        assert "validate_data" in tool_names
        assert "merge_data" in tool_names

    @pytest.mark.asyncio
    async def test_format_currency_cny(self, server, context):
        """测试格式化人民币"""
        result = await server.execute_tool(
            "format_currency",
            {"amount": 12345.67, "currency": "CNY"},
            context
        )

        assert result.is_success()
        assert "¥" in result.data["formatted"]
        assert result.data["chinese"] != ""

    @pytest.mark.asyncio
    async def test_format_currency_usd(self, server, context):
        """测试格式化美元"""
        result = await server.execute_tool(
            "format_currency",
            {"amount": 100.50, "currency": "USD"},
            context
        )

        assert result.is_success()
        assert "$" in result.data["formatted"]

    @pytest.mark.asyncio
    async def test_calculate_total(self, server, context):
        """测试计算总价"""
        result = await server.execute_tool(
            "calculate_total",
            {
                "items": [
                    {"price": 10.0, "quantity": 2},
                    {"price": 5.0, "quantity": 3}
                ],
                "discount": 0.9
            },
            context
        )

        assert result.is_success()
        assert result.data["subtotal"] == 35.0
        assert result.data["total"] == 31.5
        assert result.data["discount_amount"] == 3.5

    @pytest.mark.asyncio
    async def test_calculate_total_no_discount(self, server, context):
        """测试计算总价无折扣"""
        result = await server.execute_tool(
            "calculate_total",
            {
                "items": [
                    {"price": 100.0, "quantity": 1}
                ]
            },
            context
        )

        assert result.is_success()
        assert result.data["subtotal"] == 100.0
        assert result.data["total"] == 100.0

    @pytest.mark.asyncio
    async def test_calculate_date_future(self, server, context):
        """测试计算未来日期"""
        result = await server.execute_tool(
            "calculate_date",
            {
                "base_date": "2024-01-01",
                "days_offset": 7
            },
            context
        )

        assert result.is_success()
        assert result.data["result_date"] == "2024-01-08"

    @pytest.mark.asyncio
    async def test_calculate_date_past(self, server, context):
        """测试计算过去日期"""
        result = await server.execute_tool(
            "calculate_date",
            {
                "base_date": "2024-01-10",
                "days_offset": -5
            },
            context
        )

        assert result.is_success()
        assert result.data["result_date"] == "2024-01-05"

    @pytest.mark.asyncio
    async def test_format_json_object(self, server, context):
        """测试格式化 JSON 对象"""
        result = await server.execute_tool(
            "format_json",
            {"data": {"key": "value", "number": 123}},
            context
        )

        assert result.is_success()
        assert "key" in result.data["formatted"]

    @pytest.mark.asyncio
    async def test_format_json_string(self, server, context):
        """测试格式化 JSON 字符串"""
        result = await server.execute_tool(
            "format_json",
            {"data": '{"name": "test", "value": 1}'},
            context
        )

        assert result.is_success()
        assert result.data["data"]["name"] == "test"

    @pytest.mark.asyncio
    async def test_format_json_invalid(self, server, context):
        """测试格式化无效 JSON"""
        result = await server.execute_tool(
            "format_json",
            {"data": "not a json"},
            context
        )

        assert result.status == ToolStatus.ERROR
        assert result.error_code == "PARSE_ERROR"

    @pytest.mark.asyncio
    async def test_validate_data_email(self, server, context):
        """测试验证邮箱"""
        result = await server.execute_tool(
            "validate_data",
            {"data": "test@example.com", "validation_type": "email"},
            context
        )

        assert result.is_success()
        assert result.data["is_valid"] is True

    @pytest.mark.asyncio
    async def test_validate_data_phone(self, server, context):
        """测试验证手机号"""
        result = await server.execute_tool(
            "validate_data",
            {"data": "13812345678", "validation_type": "phone"},
            context
        )

        assert result.is_success()
        assert result.data["is_valid"] is True

    @pytest.mark.asyncio
    async def test_validate_data_invalid(self, server, context):
        """测试验证失败"""
        result = await server.execute_tool(
            "validate_data",
            {"data": "invalid-email", "validation_type": "email"},
            context
        )

        assert result.is_success()
        assert result.data["is_valid"] is False

    @pytest.mark.asyncio
    async def test_validate_data_unsupported_type(self, server, context):
        """测试不支持的验证类型"""
        result = await server.execute_tool(
            "validate_data",
            {"data": "test", "validation_type": "unsupported"},
            context
        )

        assert result.status == ToolStatus.ERROR

    @pytest.mark.asyncio
    async def test_merge_data_override(self, server, context):
        """测试合并数据覆盖模式"""
        result = await server.execute_tool(
            "merge_data",
            {
                "sources": [
                    {"a": 1, "b": 2},
                    {"b": 3, "c": 4}
                ],
                "merge_strategy": "override"
            },
            context
        )

        assert result.is_success()
        assert result.data["merged"]["b"] == 3

    @pytest.mark.asyncio
    async def test_merge_data_keep_first(self, server, context):
        """测试合并数据保留首个模式"""
        result = await server.execute_tool(
            "merge_data",
            {
                "sources": [
                    {"a": 1, "b": 2},
                    {"b": 3, "c": 4}
                ],
                "merge_strategy": "keep_first"
            },
            context
        )

        assert result.is_success()
        assert result.data["merged"]["b"] == 2

    @pytest.mark.asyncio
    async def test_health_check(self, server):
        """测试健康检查"""
        result = await server.health_check()
        assert result is True


class TestNumberToChinese:
    """数字转中文测试"""

    @pytest.fixture
    def server(self):
        return InternalToolsServer()

    def test_zero(self, server):
        """测试零"""
        result = server._number_to_chinese(0)
        assert result == "零元整"

    def test_simple_number(self, server):
        """测试简单数字"""
        result = server._number_to_chinese(100)
        assert "壹" in result
        assert "元" in result

    def test_decimal(self, server):
        """测试带小数"""
        result = server._number_to_chinese(123.45)
        assert "元" in result
        assert "角" in result or "分" in result

