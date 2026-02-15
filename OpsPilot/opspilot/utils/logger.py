"""
日志系统

职责：
- 统一日志格式
- 支持多输出（控制台、文件）
- 支持结构化日志（JSON）
- 支持请求追踪（trace_id）

使用方式：
    from opspilot.utils.logger import get_logger

    logger = get_logger(__name__)
    logger.info("消息", extra={"key": "value"})
"""
import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from functools import lru_cache
from contextvars import ContextVar
import uuid


# ==================== 上下文变量 ====================

# 请求追踪 ID
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


def get_trace_id() -> Optional[str]:
    """获取当前请求的 trace_id"""
    return trace_id_var.get()


def set_trace_id(trace_id: Optional[str] = None) -> str:
    """设置 trace_id，不传则自动生成"""
    if trace_id is None:
        trace_id = str(uuid.uuid4())[:8]
    trace_id_var.set(trace_id)
    return trace_id


def clear_trace_id() -> None:
    """清除 trace_id"""
    trace_id_var.set(None)


# ==================== 日志格式化器 ====================

class StructuredFormatter(logging.Formatter):
    """
    结构化日志格式化器

    输出格式：
    {
        "timestamp": "2024-01-01T12:00:00",
        "level": "INFO",
        "logger": "opspilot.core.state_machine",
        "message": "状态转换",
        "trace_id": "abc123",
        "extra": {...}
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": get_trace_id(),
        }

        # 添加额外字段
        if hasattr(record, "extra") and record.extra:
            log_data["extra"] = record.extra

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """
    控制台日志格式化器

    输出格式：
    2024-01-01 12:00:00 | INFO     | opspilot.core | [abc123] 状态转换
    """

    COLORS = {
        "DEBUG": "\033[36m",     # 青色
        "INFO": "\033[32m",      # 绿色
        "WARNING": "\033[33m",   # 黄色
        "ERROR": "\033[31m",     # 红色
        "CRITICAL": "\033[35m",  # 紫色
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        # 时间
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 日志级别（带颜色）
        level = record.levelname
        color = self.COLORS.get(level, "")
        colored_level = f"{color}{level:8}{self.RESET}" if color else f"{level:8}"

        # 模块名（简化）
        module = record.name
        if module.startswith("opspilot."):
            module = module[7:]  # 移除 "opspilot." 前缀
        module = module[:20].ljust(20)

        # trace_id
        trace = get_trace_id()
        trace_str = f"[{trace}] " if trace else ""

        # 消息
        message = record.getMessage()

        # 组装
        base = f"{timestamp} | {colored_level} | {module} | {trace_str}{message}"

        # 异常信息
        if record.exc_info:
            base += f"\n{self.formatException(record.exc_info)}"

        return base


# ==================== 日志处理器 ====================

def create_console_handler(level: int = logging.INFO) -> logging.Handler:
    """创建控制台处理器"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(ConsoleFormatter())
    return handler


def create_file_handler(
    filepath: str,
    level: int = logging.DEBUG,
    structured: bool = False
) -> logging.Handler:
    """创建文件处理器"""
    # 确保目录存在
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.FileHandler(filepath, encoding="utf-8")
    handler.setLevel(level)

    if structured:
        handler.setFormatter(StructuredFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        ))

    return handler


# ==================== 日志管理器 ====================

class LogManager:
    """
    日志管理器

    职责：
    - 管理全局日志配置
    - 创建 logger 实例
    - 控制日志级别
    """

    DEFAULT_LOG_DIR = Path("logs")
    DEFAULT_LOG_FILE = "opspilot.log"

    def __init__(
        self,
        level: int = logging.INFO,
        log_dir: Optional[str] = None,
        log_file: Optional[str] = None,
        console: bool = True,
        structured_file: bool = True
    ):
        self.level = level
        self.log_dir = Path(log_dir) if log_dir else self.DEFAULT_LOG_DIR
        self.log_file = log_file or self.DEFAULT_LOG_FILE
        self.console = console
        self.structured_file = structured_file
        self._initialized = False

    def setup(self) -> None:
        """初始化日志系统"""
        if self._initialized:
            return

        # 配置根 logger
        root_logger = logging.getLogger("opspilot")
        root_logger.setLevel(self.level)

        # 清除现有处理器
        root_logger.handlers.clear()

        # 添加控制台处理器
        if self.console:
            root_logger.addHandler(create_console_handler(self.level))

        # 添加文件处理器
        if self.log_file:
            log_path = self.log_dir / self.log_file
            root_logger.addHandler(
                create_file_handler(
                    str(log_path),
                    level=logging.DEBUG,
                    structured=self.structured_file
                )
            )

        # 防止日志向上传播
        root_logger.propagate = False

        self._initialized = True

    def get_logger(self, name: str) -> logging.Logger:
        """获取 logger 实例"""
        if not self._initialized:
            self.setup()

        # 确保名称以 opspilot 开头
        if not name.startswith("opspilot."):
            name = f"opspilot.{name}"

        return logging.getLogger(name)


# ==================== 全局日志访问 ====================

_log_manager: Optional[LogManager] = None


def init_logging(
    level: int = logging.INFO,
    log_dir: Optional[str] = None,
    log_file: Optional[str] = None,
    console: bool = True,
    structured_file: bool = True,
    force_reload: bool = False
) -> LogManager:
    """
    初始化日志系统

    Args:
        level: 日志级别
        log_dir: 日志目录
        log_file: 日志文件名
        console: 是否输出到控制台
        structured_file: 文件日志是否使用结构化格式
        force_reload: 是否强制重新初始化

    Returns:
        LogManager: 日志管理器实例
    """
    global _log_manager

    if _log_manager is not None and not force_reload:
        return _log_manager

    _log_manager = LogManager(
        level=level,
        log_dir=log_dir,
        log_file=log_file,
        console=console,
        structured_file=structured_file
    )
    _log_manager.setup()

    return _log_manager


@lru_cache(maxsize=128)
def get_logger(name: str) -> logging.Logger:
    """
    获取 logger 实例

    首次调用时自动初始化

    Args:
        name: 模块名称（通常传 __name__）

    Returns:
        logging.Logger: logger 实例
    """
    global _log_manager

    if _log_manager is None:
        _log_manager = init_logging()

    return _log_manager.get_logger(name)


# ==================== 便捷日志函数 ====================

def log_context(**kwargs: Any) -> Dict[str, Any]:
    """
    创建日志上下文

    使用方式：
        logger.info("消息", extra={"extra": log_context(user_id=123)})
    """
    return kwargs

