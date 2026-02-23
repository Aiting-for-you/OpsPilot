"""
工具自愈机制 - Tool Self-Healing

多层容错和自动恢复机制，提升工具调用的稳定性。

核心功能：
1. 错误诊断与分类
2. 多层容错策略
3. 自动修复与恢复
4. 降级与补偿
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union

from opspilot.tools.base import ToolSchema, ToolResult, ToolContext
from opspilot.utils.exceptions import ToolError, ToolTimeoutError, ToolValidationError


class ErrorType(Enum):
    """错误类型"""
    # LLM层错误
    LLM_OUTPUT_INVALID = "llm_output_invalid"      # LLM输出无效
    LLM_OUTPUT_INCOMPLETE = "llm_output_incomplete"  # LLM输出不完整
    LLM_FORMAT_ERROR = "llm_format_error"          # 格式错误
    
    # 参数错误
    PARAM_MISSING = "param_missing"                # 缺少参数
    PARAM_TYPE_ERROR = "param_type_error"          # 参数类型错误
    PARAM_VALUE_INVALID = "param_value_invalid"    # 参数值无效
    PARAM_VALIDATION_FAILED = "param_validation_failed"  # 参数校验失败
    
    # 网络错误
    NETWORK_TIMEOUT = "network_timeout"            # 网络超时
    NETWORK_ERROR = "network_error"                # 网络错误
    SERVICE_UNAVAILABLE = "service_unavailable"    # 服务不可用
    
    # 服务错误
    SERVICE_ERROR = "service_error"                # 服务内部错误
    PERMISSION_DENIED = "permission_denied"        # 权限不足
    RATE_LIMITED = "rate_limited"                  # 限流
    RESOURCE_NOT_FOUND = "resource_not_found"      # 资源不存在
    
    # 业务错误
    BUSINESS_RULE_VIOLATION = "business_rule_violation"  # 业务规则违反
    DATA_CONFLICT = "data_conflict"                # 数据冲突
    OPERATION_FAILED = "operation_failed"          # 操作失败
    
    # 未知错误
    UNKNOWN = "unknown"


class RecoveryStrategy(Enum):
    """恢复策略"""
    RETRY = "retry"                    # 重试
    RETRY_WITH_BACKOFF = "retry_with_backoff"  # 指数退避重试
    AUTO_FIX = "auto_fix"              # 自动修复参数
    FALLBACK = "fallback"              # 降级方案
    DEGRADATION = "degradation"        # 服务降级
    ALTERNATE_TOOL = "alternate_tool"  # 替代工具
    MANUAL_INTERVENTION = "manual_intervention"  # 人工介入
    ABORT = "abort"                    # 终止


@dataclass
class ErrorDiagnosis:
    """错误诊断结果"""
    error_type: ErrorType
    error_message: str
    is_recoverable: bool
    suggested_strategy: RecoveryStrategy
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.error_type.value,
            "error_message": self.error_message,
            "is_recoverable": self.is_recoverable,
            "suggested_strategy": self.suggested_strategy.value,
            "details": self.details,
        }


@dataclass
class RecoveryContext:
    """恢复上下文"""
    original_call: Dict[str, Any]       # 原始调用
    retry_count: int = 0                # 重试次数
    last_error: Optional[Exception] = None  # 最后一次错误
    recovery_history: List[Dict[str, Any]] = field(default_factory=list)  # 恢复历史
    start_time: float = field(default_factory=time.time)
    
    def add_recovery_attempt(
        self,
        strategy: RecoveryStrategy,
        result: str,
        details: Optional[Dict] = None,
    ) -> None:
        """记录恢复尝试"""
        self.recovery_history.append({
            "strategy": strategy.value,
            "result": result,
            "details": details or {},
            "timestamp": time.time(),
        })


class ErrorDiagnoser:
    """错误诊断器"""
    
    # 错误模式匹配
    ERROR_PATTERNS = {
        ErrorType.PARAM_MISSING: [
            r"missing.*parameter",
            r"required.*field",
            r"缺少.*参数",
            r"必填.*字段",
        ],
        ErrorType.PARAM_TYPE_ERROR: [
            r"type.*error",
            r"invalid.*type",
            r"类型.*错误",
            r"无效.*类型",
        ],
        ErrorType.PARAM_VALUE_INVALID: [
            r"invalid.*value",
            r"value.*invalid",
            r"值.*无效",
            r"无效.*值",
        ],
        ErrorType.NETWORK_TIMEOUT: [
            r"timeout",
            r"timed out",
            r"超时",
        ],
        ErrorType.NETWORK_ERROR: [
            r"connection.*error",
            r"network.*error",
            r"连接.*错误",
            r"网络.*错误",
        ],
        ErrorType.SERVICE_UNAVAILABLE: [
            r"service.*unavailable",
            r"503",
            r"服务.*不可用",
        ],
        ErrorType.PERMISSION_DENIED: [
            r"permission.*denied",
            r"403",
            r"权限.*不足",
            r"无权.*访问",
        ],
        ErrorType.RATE_LIMITED: [
            r"rate.*limit",
            r"429",
            r"限流",
            r"请求.*频繁",
        ],
        ErrorType.RESOURCE_NOT_FOUND: [
            r"not found",
            r"404",
            r"未找到",
            r"不存在",
        ],
    }
    
    @classmethod
    def diagnose(cls, error: Exception, context: Optional[Dict] = None) -> ErrorDiagnosis:
        """
        诊断错误
        
        Args:
            error: 异常对象
            context: 额外上下文
        
        Returns:
            错误诊断结果
        """
        error_message = str(error).lower()
        context = context or {}
        
        # 检查特定异常类型
        if isinstance(error, ToolTimeoutError):
            return ErrorDiagnosis(
                error_type=ErrorType.NETWORK_TIMEOUT,
                error_message=str(error),
                is_recoverable=True,
                suggested_strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
                details={"timeout": context.get("timeout")},
            )
        
        if isinstance(error, ToolValidationError):
            return ErrorDiagnosis(
                error_type=ErrorType.PARAM_VALIDATION_FAILED,
                error_message=str(error),
                is_recoverable=True,
                suggested_strategy=RecoveryStrategy.AUTO_FIX,
                details={"validation_errors": context.get("validation_errors", [])},
            )
        
        # 模式匹配
        for error_type, patterns in cls.ERROR_PATTERNS.items():
            for pattern in patterns:
                import re
                if re.search(pattern, error_message, re.IGNORECASE):
                    return cls._create_diagnosis(error_type, str(error))
        
        # 默认：未知错误
        return ErrorDiagnosis(
            error_type=ErrorType.UNKNOWN,
            error_message=str(error),
            is_recoverable=False,
            suggested_strategy=RecoveryStrategy.ABORT,
        )
    
    @classmethod
    def _create_diagnosis(cls, error_type: ErrorType, message: str) -> ErrorDiagnosis:
        """创建诊断结果"""
        recoverable_strategies = {
            ErrorType.PARAM_MISSING: (True, RecoveryStrategy.AUTO_FIX),
            ErrorType.PARAM_TYPE_ERROR: (True, RecoveryStrategy.AUTO_FIX),
            ErrorType.PARAM_VALUE_INVALID: (True, RecoveryStrategy.AUTO_FIX),
            ErrorType.PARAM_VALIDATION_FAILED: (True, RecoveryStrategy.AUTO_FIX),
            ErrorType.NETWORK_TIMEOUT: (True, RecoveryStrategy.RETRY_WITH_BACKOFF),
            ErrorType.NETWORK_ERROR: (True, RecoveryStrategy.RETRY_WITH_BACKOFF),
            ErrorType.SERVICE_UNAVAILABLE: (True, RecoveryStrategy.FALLBACK),
            ErrorType.PERMISSION_DENIED: (True, RecoveryStrategy.DEGRADATION),
            ErrorType.RATE_LIMITED: (True, RecoveryStrategy.RETRY_WITH_BACKOFF),
            ErrorType.RESOURCE_NOT_FOUND: (True, RecoveryStrategy.DEGRADATION),
            ErrorType.BUSINESS_RULE_VIOLATION: (True, RecoveryStrategy.AUTO_FIX),
            ErrorType.DATA_CONFLICT: (True, RecoveryStrategy.FALLBACK),
            ErrorType.OPERATION_FAILED: (True, RecoveryStrategy.RETRY),
            ErrorType.LLM_OUTPUT_INVALID: (True, RecoveryStrategy.RETRY),
            ErrorType.LLM_OUTPUT_INCOMPLETE: (True, RecoveryStrategy.RETRY),
            ErrorType.LLM_FORMAT_ERROR: (True, RecoveryStrategy.AUTO_FIX),
            ErrorType.SERVICE_ERROR: (True, RecoveryStrategy.FALLBACK),
            ErrorType.UNKNOWN: (False, RecoveryStrategy.ABORT),
        }
        
        is_recoverable, strategy = recoverable_strategies.get(
            error_type, (False, RecoveryStrategy.ABORT)
        )
        
        return ErrorDiagnosis(
            error_type=error_type,
            error_message=message,
            is_recoverable=is_recoverable,
            suggested_strategy=strategy,
        )


class ToolHealer:
    """
    工具自愈器
    
    实现多层容错和自动恢复。
    
    示例:
        >>> healer = ToolHealer()
        >>> result = await healer.execute_with_healing(tool_call, executor)
    """
    
    # 默认配置
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BACKOFF_BASE = 1.0  # 秒
    DEFAULT_BACKOFF_MAX = 30.0  # 秒
    
    def __init__(
        self,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base: float = DEFAULT_BACKOFF_BASE,
        backoff_max: float = DEFAULT_BACKOFF_MAX,
        fallback_handler: Optional[Callable] = None,
        degradation_handler: Optional[Callable] = None,
    ):
        """
        初始化自愈器
        
        Args:
            max_retries: 最大重试次数
            backoff_base: 退避基数
            backoff_max: 最大退避时间
            fallback_handler: 降级处理函数
            degradation_handler: 服务降级处理函数
        """
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_max = backoff_max
        self.fallback_handler = fallback_handler
        self.degradation_handler = degradation_handler
        
        # 自动修复器注册
        self._auto_fixers: Dict[ErrorType, Callable] = {}
        self._register_default_fixers()
    
    def _register_default_fixers(self) -> None:
        """注册默认的自动修复器"""
        self._auto_fixers[ErrorType.PARAM_MISSING] = self._fix_missing_param
        self._auto_fixers[ErrorType.PARAM_TYPE_ERROR] = self._fix_type_error
        self._auto_fixers[ErrorType.PARAM_VALUE_INVALID] = self._fix_invalid_value
    
    def register_fixer(
        self,
        error_type: ErrorType,
        fixer: Callable,
    ) -> None:
        """注册自定义修复器"""
        self._auto_fixers[error_type] = fixer
    
    async def execute_with_healing(
        self,
        tool_call: Dict[str, Any],
        executor: Callable,
        context: Optional[ToolContext] = None,
    ) -> ToolResult:
        """
        带自愈机制的执行
        
        Args:
            tool_call: 工具调用参数
            executor: 执行函数
            context: 执行上下文
        
        Returns:
            执行结果
        """
        recovery_ctx = RecoveryContext(original_call=tool_call.copy())
        
        while True:
            try:
                # 尝试执行
                result = await executor(tool_call, context)
                return result
            
            except Exception as e:
                # 诊断错误
                diagnosis = ErrorDiagnoser.diagnose(e, {"tool_call": tool_call})
                recovery_ctx.last_error = e
                
                # 检查是否可恢复
                if not diagnosis.is_recoverable:
                    raise ToolUnrecoverableError(diagnosis) from e
                
                # 检查重试次数
                if recovery_ctx.retry_count >= self.max_retries:
                    # 尝试降级
                    handler = self.degradation_handler or self.fallback_handler
                    if handler:
                        result = await handler(tool_call, diagnosis)
                        return result
                    raise ToolMaxRetriesExceededError(
                        recovery_ctx.retry_count, diagnosis
                    ) from e
                
                # 选择并执行恢复策略
                strategy = self._select_strategy(diagnosis, recovery_ctx)
                recovery_ctx.add_recovery_attempt(
                    strategy, "started", {"diagnosis": diagnosis.to_dict()}
                )
                
                try:
                    tool_call = await self._execute_strategy(
                        strategy, tool_call, diagnosis, recovery_ctx
                    )
                    recovery_ctx.retry_count += 1
                    recovery_ctx.add_recovery_attempt(strategy, "completed")
                
                except Exception as recovery_error:
                    recovery_ctx.add_recovery_attempt(
                        strategy, "failed", {"error": str(recovery_error)}
                    )
                    # 恢复失败，尝试下一个策略
                    continue
    
    def _select_strategy(
        self,
        diagnosis: ErrorDiagnosis,
        recovery_ctx: RecoveryContext,
    ) -> RecoveryStrategy:
        """选择恢复策略"""
        base_strategy = diagnosis.suggested_strategy
        
        # 根据重试次数调整策略
        if recovery_ctx.retry_count >= self.max_retries - 1:
            if base_strategy in [RecoveryStrategy.RETRY, RecoveryStrategy.RETRY_WITH_BACKOFF]:
                return RecoveryStrategy.FALLBACK
        
        return base_strategy
    
    async def _execute_strategy(
        self,
        strategy: RecoveryStrategy,
        tool_call: Dict[str, Any],
        diagnosis: ErrorDiagnosis,
        recovery_ctx: RecoveryContext,
    ) -> Dict[str, Any]:
        """执行恢复策略"""
        if strategy == RecoveryStrategy.RETRY:
            # 立即重试
            return tool_call
        
        elif strategy == RecoveryStrategy.RETRY_WITH_BACKOFF:
            # 指数退避重试
            backoff = min(
                self.backoff_base * (2 ** recovery_ctx.retry_count),
                self.backoff_max,
            )
            await asyncio.sleep(backoff)
            return tool_call
        
        elif strategy == RecoveryStrategy.AUTO_FIX:
            # 自动修复
            return await self._auto_fix(tool_call, diagnosis)
        
        elif strategy == RecoveryStrategy.FALLBACK:
            # 降级方案
            if self.fallback_handler:
                return await self.fallback_handler(tool_call, diagnosis)
            return tool_call
        
        elif strategy == RecoveryStrategy.DEGRADATION:
            # 服务降级
            if self.degradation_handler:
                return await self.degradation_handler(tool_call, diagnosis)
            return tool_call
        
        else:
            raise ToolUnrecoverableError(diagnosis)
    
    async def _auto_fix(
        self,
        tool_call: Dict[str, Any],
        diagnosis: ErrorDiagnosis,
    ) -> Dict[str, Any]:
        """自动修复"""
        fixer = self._auto_fixers.get(diagnosis.error_type)
        if fixer:
            return await fixer(tool_call, diagnosis)
        return tool_call
    
    async def _fix_missing_param(
        self,
        tool_call: Dict[str, Any],
        diagnosis: ErrorDiagnosis,
    ) -> Dict[str, Any]:
        """修复缺少参数"""
        # 尝试使用默认值
        params = tool_call.get("parameters", {})
        
        # 从诊断详情中获取缺少的参数名
        missing_params = diagnosis.details.get("missing_params", [])
        for param in missing_params:
            # 尝试设置默认值
            if param not in params:
                params[param] = None  # 或从上下文推断
        
        tool_call["parameters"] = params
        return tool_call
    
    async def _fix_type_error(
        self,
        tool_call: Dict[str, Any],
        diagnosis: ErrorDiagnosis,
    ) -> Dict[str, Any]:
        """修复类型错误"""
        params = tool_call.get("parameters", {})
        
        # 从诊断详情中获取类型错误信息
        type_errors = diagnosis.details.get("type_errors", [])
        for error in type_errors:
            param_name = error.get("param")
            expected_type = error.get("expected")
            
            if param_name and param_name in params:
                # 尝试类型转换
                try:
                    if expected_type == "number":
                        params[param_name] = float(params[param_name])
                    elif expected_type == "integer":
                        params[param_name] = int(params[param_name])
                    elif expected_type == "string":
                        params[param_name] = str(params[param_name])
                    elif expected_type == "boolean":
                        params[param_name] = bool(params[param_name])
                except (ValueError, TypeError):
                    pass  # 转换失败，保持原值
        
        tool_call["parameters"] = params
        return tool_call
    
    async def _fix_invalid_value(
        self,
        tool_call: Dict[str, Any],
        diagnosis: ErrorDiagnosis,
    ) -> Dict[str, Any]:
        """修复无效值"""
        params = tool_call.get("parameters", {})
        
        # 从诊断详情中获取无效值信息
        invalid_values = diagnosis.details.get("invalid_values", [])
        for error in invalid_values:
            param_name = error.get("param")
            invalid_value = params.get(param_name)
            
            # 尝试修正值
            if param_name and param_name in params:
                # 简单的值修正逻辑
                if isinstance(invalid_value, str):
                    # 尝试去除空格
                    params[param_name] = invalid_value.strip()
        
        tool_call["parameters"] = params
        return tool_call


class ToolUnrecoverableError(ToolError):
    """工具不可恢复错误"""
    
    def __init__(self, diagnosis: ErrorDiagnosis):
        self.diagnosis = diagnosis
        super().__init__(
            f"Tool call unrecoverable: {diagnosis.error_type.value} - {diagnosis.error_message}"
        )


class ToolMaxRetriesExceededError(ToolError):
    """超过最大重试次数错误"""
    
    def __init__(self, retries: int, diagnosis: ErrorDiagnosis):
        self.retries = retries
        self.diagnosis = diagnosis
        super().__init__(
            f"Max retries ({retries}) exceeded: {diagnosis.error_type.value}"
        )


# 便捷函数
def create_healer(
    max_retries: int = 3,
    fallback_handler: Optional[Callable] = None,
) -> ToolHealer:
    """创建自愈器的便捷函数"""
    return ToolHealer(
        max_retries=max_retries,
        fallback_handler=fallback_handler,
    )

