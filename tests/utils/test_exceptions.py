"""
异常类单元测试
"""
import pytest

from opspilot.utils.exceptions import (
    opspilotError,
    ConfigFileNotFoundError,
    ConfigValidationError,
    InvalidTransitionError,
    MaxRetryExceededError,
    AgentTimeoutError,
    AgentExecutionError,
    ToolNotFoundError,
    ToolExecutionError,
    MCPConnectionError,
    MemoryConnectionError,
    MemoryQueryError,
)


class TestopspilotError:
    """opspilotError 基类测试"""

    def test_basic_error(self):
        """测试基本错误创建"""
        error = opspilotError("测试错误")
        assert error.message == "测试错误"
        assert error.code == "UNKNOWN_ERROR"
        assert error.details == {}

    def test_error_with_code(self):
        """测试带错误码的错误"""
        error = opspilotError("测试错误", code="TEST_ERROR")
        assert error.code == "TEST_ERROR"

    def test_error_with_details(self):
        """测试带详情的错误"""
        error = opspilotError("测试错误", details={"key": "value"})
        assert error.details == {"key": "value"}

    def test_to_dict(self):
        """测试转换为字典"""
        error = opspilotError("测试错误", code="TEST", details={"a": 1})
        result = error.to_dict()
        assert result == {
            "error": "TEST",
            "message": "测试错误",
            "details": {"a": 1}
        }

    def test_str_representation(self):
        """测试字符串表示"""
        error = opspilotError("测试错误", code="TEST")
        assert str(error) == "[TEST] 测试错误"


class TestConfigErrors:
    """配置相关错误测试"""

    def test_config_file_not_found(self):
        """测试配置文件不存在错误"""
        error = ConfigFileNotFoundError("/path/to/config.yaml")
        assert error.code == "CONFIG_FILE_NOT_FOUND"
        assert "/path/to/config.yaml" in error.message
        assert error.details["filepath"] == "/path/to/config.yaml"

    def test_config_validation_error(self):
        """测试配置验证错误"""
        error = ConfigValidationError("字段验证失败", field="app.name")
        assert error.code == "CONFIG_VALIDATION_ERROR"
        assert error.details["field"] == "app.name"


class TestStateMachineErrors:
    """状态机相关错误测试"""

    def test_invalid_transition(self):
        """测试非法状态转换错误"""
        error = InvalidTransitionError(
            from_state="INIT",
            to_state="EXECUTING",
            allowed_transitions=["PLANNING"]
        )
        assert error.code == "INVALID_STATE_TRANSITION"
        assert "INIT" in error.message
        assert "EXECUTING" in error.message
        assert error.details["from_state"] == "INIT"
        assert error.details["to_state"] == "EXECUTING"
        assert error.details["allowed_transitions"] == ["PLANNING"]

    def test_max_retry_exceeded(self):
        """测试超过最大重试次数错误"""
        error = MaxRetryExceededError(max_retry=3, current_retry=4)
        assert error.code == "MAX_RETRY_EXCEEDED"
        assert error.details["max_retry"] == 3
        assert error.details["current_retry"] == 4


class TestAgentErrors:
    """Agent 相关错误测试"""

    def test_agent_timeout(self):
        """测试 Agent 超时错误"""
        error = AgentTimeoutError(agent_name="ExecAgent", timeout=30.0)
        assert error.code == "AGENT_TIMEOUT"
        assert "ExecAgent" in error.message
        assert error.details["timeout"] == 30.0

    def test_agent_execution_error(self):
        """测试 Agent 执行错误"""
        error = AgentExecutionError(
            agent_name="PlanAgent",
            reason="工具调用失败",
            output={"result": "failed"}
        )
        assert error.code == "AGENT_EXECUTION_ERROR"
        assert error.details["output"] == {"result": "failed"}


class TestToolErrors:
    """工具相关错误测试"""

    def test_tool_not_found(self):
        """测试工具不存在错误"""
        error = ToolNotFoundError("create_order")
        assert error.code == "TOOL_NOT_FOUND"
        assert "create_order" in error.message

    def test_tool_execution_error(self):
        """测试工具执行错误"""
        error = ToolExecutionError(
            tool_name="query_inventory",
            reason="数据库连接失败",
            params={"sku": "123"}
        )
        assert error.code == "TOOL_EXECUTION_ERROR"
        assert error.details["params"] == {"sku": "123"}

    def test_mcp_connection_error(self):
        """测试 MCP 连接错误"""
        error = MCPConnectionError(
            server_name="erp-server",
            reason="连接超时"
        )
        assert error.code == "MCP_CONNECTION_ERROR"
        assert error.details["server_name"] == "erp-server"


class TestMemoryErrors:
    """记忆相关错误测试"""

    def test_memory_connection_error(self):
        """测试存储连接错误"""
        error = MemoryConnectionError(
            storage_type="Redis",
            reason="连接被拒绝"
        )
        assert error.code == "MEMORY_CONNECTION_ERROR"
        assert "Redis" in error.message

    def test_memory_query_error(self):
        """测试查询错误"""
        error = MemoryQueryError(
            query="SELECT * FROM memory",
            reason="语法错误"
        )
        assert error.code == "MEMORY_QUERY_ERROR"
        assert error.details["query"] == "SELECT * FROM memory"

