"""
并行工具执行模块

使用 AgentScope 和 asyncio 实现高效的工具并行调用。

特性：
- 独立工具并行执行
- 结果聚合
- 错误隔离
- 超时控制
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class ToolCall:
    """工具调用定义"""
    tool_name: str
    params: Dict[str, Any]
    call_id: str = ""
    timeout: float = 30.0
    priority: int = 0  # 优先级，数字越小越优先
    
    def __post_init__(self):
        if not self.call_id:
            import uuid
            self.call_id = str(uuid.uuid4())[:8]


@dataclass
class ToolResult:
    """工具执行结果"""
    call_id: str
    tool_name: str
    status: ExecutionStatus
    data: Any = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "call_id": self.call_id,
            "tool_name": self.tool_name,
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "latency_ms": self.latency_ms,
        }


@dataclass
class ParallelExecutionResult:
    """并行执行结果"""
    total_calls: int
    successful: int
    failed: int
    results: List[ToolResult]
    total_latency_ms: float
    parallelism_saved_ms: float  # 并行节省的时间
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_calls": self.total_calls,
            "successful": self.successful,
            "failed": self.failed,
            "success_rate": self.successful / self.total_calls if self.total_calls > 0 else 0,
            "results": [r.to_dict() for r in self.results],
            "total_latency_ms": self.total_latency_ms,
            "parallelism_saved_ms": self.parallelism_saved_ms,
        }


class ParallelToolExecutor:
    """
    并行工具执行器
    
    高效并行执行多个独立的工具调用。
    
    示例:
        >>> executor = ParallelToolExecutor(tool_router)
        >>> 
        >>> calls = [
        ...     ToolCall("query_supplier", {"id": "SUP001"}),
        ...     ToolCall("query_inventory", {"sku": "SKU001"}),
        ...     ToolCall("query_orders", {"status": "pending"}),
        ... ]
        >>> 
        >>> result = await executor.execute_parallel(calls)
        >>> print(f"并行执行 {result.total_calls} 个工具，节省 {result.parallelism_saved_ms}ms")
    """
    
    def __init__(
        self,
        tool_router: Any,
        max_concurrent: int = 10,
        default_timeout: float = 30.0,
    ):
        """
        初始化并行执行器
        
        Args:
            tool_router: 工具路由器（ToolRouter 实例）
            max_concurrent: 最大并发数
            default_timeout: 默认超时时间
        """
        self._tool_router = tool_router
        self._max_concurrent = max_concurrent
        self._default_timeout = default_timeout
        
        # 信号量控制并发
        self._semaphore = asyncio.Semaphore(max_concurrent)
        
        # 统计
        self._stats = {
            "total_executions": 0,
            "total_tools_called": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "timeout_calls": 0,
            "total_time_saved_ms": 0.0,
        }
    
    async def execute_single(
        self,
        call: ToolCall,
        context: Optional[Any] = None,
    ) -> ToolResult:
        """
        执行单个工具调用
        
        Args:
            call: 工具调用定义
            context: 工具上下文
        
        Returns:
            ToolResult: 执行结果
        """
        start_time = time.time()
        
        async with self._semaphore:
            try:
                # 调用工具路由器
                if context:
                    result = await asyncio.wait_for(
                        self._tool_router.call_tool_with_retry(
                            tool_name=call.tool_name,
                            params=call.params,
                            context=context,
                        ),
                        timeout=call.timeout,
                    )
                else:
                    # 无上下文时的简化调用
                    result = await asyncio.wait_for(
                        self._tool_router.call_tool(
                            tool_name=call.tool_name,
                            params=call.params,
                        ),
                        timeout=call.timeout,
                    )
                
                latency_ms = (time.time() - start_time) * 1000
                
                return ToolResult(
                    call_id=call.call_id,
                    tool_name=call.tool_name,
                    status=ExecutionStatus.COMPLETED,
                    data=result.data if hasattr(result, 'data') else result,
                    latency_ms=latency_ms,
                )
                
            except asyncio.TimeoutError:
                latency_ms = (time.time() - start_time) * 1000
                logger.warning(f"Tool {call.tool_name} timed out after {call.timeout}s")
                
                return ToolResult(
                    call_id=call.call_id,
                    tool_name=call.tool_name,
                    status=ExecutionStatus.TIMEOUT,
                    error=f"Timeout after {call.timeout}s",
                    latency_ms=latency_ms,
                )
                
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                logger.error(f"Tool {call.tool_name} failed: {e}")
                
                return ToolResult(
                    call_id=call.call_id,
                    tool_name=call.tool_name,
                    status=ExecutionStatus.FAILED,
                    error=str(e),
                    latency_ms=latency_ms,
                )
    
    async def execute_parallel(
        self,
        calls: List[ToolCall],
        context: Optional[Any] = None,
        fail_fast: bool = False,
    ) -> ParallelExecutionResult:
        """
        并行执行多个工具调用
        
        Args:
            calls: 工具调用列表
            context: 工具上下文
            fail_fast: 是否快速失败（一个失败即停止）
        
        Returns:
            ParallelExecutionResult: 并行执行结果
        """
        if not calls:
            return ParallelExecutionResult(
                total_calls=0,
                successful=0,
                failed=0,
                results=[],
                total_latency_ms=0,
                parallelism_saved_ms=0,
            )
        
        start_time = time.time()
        
        # 创建所有任务
        tasks = [
            self.execute_single(call, context)
            for call in calls
        ]
        
        # 并行执行
        if fail_fast:
            # 快速失败模式
            results = await asyncio.gather(*tasks, return_exceptions=False)
        else:
            # 容错模式：所有任务都执行完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_latency_ms = (time.time() - start_time) * 1000
        
        # 处理结果
        final_results: List[ToolResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # 异常转为 ToolResult
                final_results.append(ToolResult(
                    call_id=calls[i].call_id,
                    tool_name=calls[i].tool_name,
                    status=ExecutionStatus.FAILED,
                    error=str(result),
                ))
            else:
                final_results.append(result)
        
        # 统计
        successful = sum(1 for r in final_results if r.status == ExecutionStatus.COMPLETED)
        failed = sum(1 for r in final_results if r.status in (ExecutionStatus.FAILED, ExecutionStatus.TIMEOUT))
        
        # 计算并行节省的时间
        sequential_time = sum(r.latency_ms for r in final_results)
        parallelism_saved_ms = max(0, sequential_time - total_latency_ms)
        
        # 更新统计
        self._stats["total_executions"] += 1
        self._stats["total_tools_called"] += len(calls)
        self._stats["successful_calls"] += successful
        self._stats["failed_calls"] += failed
        self._stats["timeout_calls"] += sum(1 for r in final_results if r.status == ExecutionStatus.TIMEOUT)
        self._stats["total_time_saved_ms"] += parallelism_saved_ms
        
        return ParallelExecutionResult(
            total_calls=len(calls),
            successful=successful,
            failed=failed,
            results=final_results,
            total_latency_ms=total_latency_ms,
            parallelism_saved_ms=parallelism_saved_ms,
        )
    
    async def execute_batch(
        self,
        calls: List[ToolCall],
        context: Optional[Any] = None,
        batch_size: int = 5,
    ) -> List[ParallelExecutionResult]:
        """
        分批并行执行
        
        将大量调用分成多个批次执行，避免资源耗尽。
        
        Args:
            calls: 工具调用列表
            context: 工具上下文
            batch_size: 每批大小
        
        Returns:
            List[ParallelExecutionResult]: 每批的执行结果
        """
        results = []
        
        for i in range(0, len(calls), batch_size):
            batch = calls[i:i + batch_size]
            result = await self.execute_parallel(batch, context)
            results.append(result)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            "average_time_saved_ms": (
                self._stats["total_time_saved_ms"] / self._stats["total_executions"]
                if self._stats["total_executions"] > 0 else 0
            ),
        }


# ============================================================================
# 便捷函数
# ============================================================================

async def execute_tools_parallel(
    tool_router: Any,
    tool_calls: List[Dict[str, Any]],
    context: Optional[Any] = None,
    max_concurrent: int = 10,
) -> ParallelExecutionResult:
    """
    并行执行多个工具的便捷函数
    
    Args:
        tool_router: 工具路由器
        tool_calls: 工具调用列表，格式：[{"tool": "name", "params": {...}}, ...]
        context: 工具上下文
        max_concurrent: 最大并发数
    
    Returns:
        ParallelExecutionResult
    
    示例:
        >>> results = await execute_tools_parallel(
        ...     tool_router,
        ...     [
        ...         {"tool": "query_supplier", "params": {"id": "SUP001"}},
        ...         {"tool": "query_inventory", "params": {"sku": "SKU001"}},
        ...     ],
        ... )
    """
    calls = [
        ToolCall(
            tool_name=tc["tool"],
            params=tc.get("params", {}),
            timeout=tc.get("timeout", 30.0),
        )
        for tc in tool_calls
    ]
    
    executor = ParallelToolExecutor(tool_router, max_concurrent)
    return await executor.execute_parallel(calls, context)
