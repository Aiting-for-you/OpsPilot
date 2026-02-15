"""
日志系统单元测试
"""
import pytest
import logging
import json
from io import StringIO

from opspilot.utils.logger import (
    get_logger,
    init_logging,
    get_trace_id,
    set_trace_id,
    clear_trace_id,
    log_context,
    StructuredFormatter,
    ConsoleFormatter,
)


class TestTraceId:
    """Trace ID 测试"""

    def test_set_and_get_trace_id(self):
        """测试设置和获取 trace_id"""
        clear_trace_id()
        trace_id = set_trace_id("test123")
        assert trace_id == "test123"
        assert get_trace_id() == "test123"

    def test_auto_generate_trace_id(self):
        """测试自动生成 trace_id"""
        clear_trace_id()
        trace_id = set_trace_id()
        assert trace_id is not None
        assert len(trace_id) == 8

    def test_clear_trace_id(self):
        """测试清除 trace_id"""
        set_trace_id("test123")
        clear_trace_id()
        assert get_trace_id() is None


class TestFormatters:
    """日志格式化器测试"""

    def test_structured_formatter(self):
        """测试结构化格式化器"""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="opspilot.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="测试消息",
            args=(),
            exc_info=None
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert data["level"] == "INFO"
        assert data["logger"] == "opspilot.test"
        assert data["message"] == "测试消息"
        assert "timestamp" in data

    def test_structured_formatter_with_trace_id(self):
        """测试带 trace_id 的结构化格式化器"""
        set_trace_id("trace123")
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="opspilot.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="测试消息",
            args=(),
            exc_info=None
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert data["trace_id"] == "trace123"
        clear_trace_id()

    def test_console_formatter(self):
        """测试控制台格式化器"""
        formatter = ConsoleFormatter()
        record = logging.LogRecord(
            name="opspilot.core.state_machine",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="测试消息",
            args=(),
            exc_info=None
        )

        output = formatter.format(record)

        assert "INFO" in output
        assert "core.state_machine" in output
        assert "测试消息" in output


class TestLogManager:
    """日志管理器测试"""

    def test_init_logging(self):
        """测试初始化日志系统"""
        manager = init_logging(
            level=logging.DEBUG,
            console=True,
            force_reload=True
        )
        assert manager is not None

    def test_get_logger(self):
        """测试获取 logger"""
        logger = get_logger("test.module")
        assert logger is not None
        assert logger.name == "opspilot.test.module"

    def test_get_logger_caching(self):
        """测试 logger 缓存"""
        logger1 = get_logger("cached.module")
        logger2 = get_logger("cached.module")
        # lru_cache 应该返回同一个实例
        assert logger1 is logger2

    def test_logger_log_levels(self):
        """测试日志级别"""
        init_logging(level=logging.DEBUG, force_reload=True)
        logger = get_logger("level.test")

        assert logger.isEnabledFor(logging.DEBUG)
        assert logger.isEnabledFor(logging.INFO)
        assert logger.isEnabledFor(logging.WARNING)


class TestLogContext:
    """日志上下文测试"""

    def test_log_context_creation(self):
        """测试日志上下文创建"""
        ctx = log_context(user_id=123, action="test")
        assert ctx == {"user_id": 123, "action": "test"}

    def test_log_context_empty(self):
        """测试空日志上下文"""
        ctx = log_context()
        assert ctx == {}

