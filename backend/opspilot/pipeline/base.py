"""
Pipeline 基础组件

定义 Pipeline 的核心抽象和数据结构。
"""

from __future__ import annotations

import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class PipelineStatus(str, Enum):
    """Pipeline 状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PipelineContext:
    """
    Pipeline 执行上下文
    
    在 Pipeline 执行过程中传递和累积数据。
    """
    pipeline_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: PipelineStatus = PipelineStatus.PENDING
    
    # 输入输出
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    
    # 步骤结果
    step_results: Dict[str, Any] = field(default_factory=dict)
    
    # 元数据
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    current_step: str = ""
    
    # 错误
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    # 用户定义的共享数据
    shared: Dict[str, Any] = field(default_factory=dict)
    
    def set_result(self, step_name: str, result: Any) -> None:
        """设置步骤结果"""
        self.step_results[step_name] = result
    
    def get_result(self, step_name: str, default: Any = None) -> Any:
        """获取步骤结果"""
        return self.step_results.get(step_name, default)
    
    def add_error(self, step: str, error: str) -> None:
        """添加错误"""
        self.errors.append({
            "step": step,
            "error": error,
            "time": time.time(),
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "pipeline_id": self.pipeline_id,
            "trace_id": self.trace_id,
            "status": self.status.value,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "step_results": self.step_results,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": (self.end_time - self.start_time) * 1000 if self.end_time else None,
            "current_step": self.current_step,
            "errors": self.errors,
        }


@dataclass
class PipelineResult:
    """Pipeline 执行结果"""
    success: bool
    output: Any
    context: PipelineContext
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "context": self.context.to_dict(),
        }


class PipelineStep:
    """
    Pipeline 步骤
    
    封装单个执行单元。
    """
    
    def __init__(
        self,
        name: str,
        action: Callable[[PipelineContext], Any],
        timeout: float = 60.0,
        retry: int = 0,
    ):
        self.name = name
        self.action = action
        self.timeout = timeout
        self.retry = retry
    
    async def execute(self, context: PipelineContext) -> Any:
        """执行步骤"""
        context.current_step = self.name
        
        for attempt in range(self.retry + 1):
            try:
                import asyncio
                
                # 检查是否是协程函数
                import inspect
                if inspect.iscoroutinefunction(self.action):
                    result = await asyncio.wait_for(
                        self.action(context),
                        timeout=self.timeout,
                    )
                else:
                    result = self.action(context)
                
                return result
                
            except asyncio.TimeoutError:
                error_msg = f"Step {self.name} timed out after {self.timeout}s"
                logger.warning(error_msg)
                context.add_error(self.name, error_msg)
                
                if attempt == self.retry:
                    raise
                await asyncio.sleep(1)
                
            except Exception as e:
                error_msg = f"Step {self.name} failed: {e}"
                logger.error(error_msg)
                context.add_error(self.name, error_msg)
                
                if attempt == self.retry:
                    raise
                await asyncio.sleep(1)
        
        raise RuntimeError(f"Step {self.name} failed after {self.retry} retries")


class PipelineBase(ABC):
    """
    Pipeline 基类
    
    所有 Pipeline 类型的抽象基类。
    """
    
    def __init__(self, name: str = ""):
        self.name = name or self.__class__.__name__
        self._pre_hooks: List[Callable] = []
        self._post_hooks: List[Callable] = []
    
    def add_pre_hook(self, hook: Callable[[PipelineContext], None]) -> None:
        """添加前置钩子"""
        self._pre_hooks.append(hook)
    
    def add_post_hook(self, hook: Callable[[PipelineContext], None]) -> None:
        """添加后置钩子"""
        self._post_hooks.append(hook)
    
    async def _run_pre_hooks(self, context: PipelineContext) -> None:
        """执行前置钩子"""
        for hook in self._pre_hooks:
            try:
                import inspect
                if inspect.iscoroutinefunction(hook):
                    await hook(context)
                else:
                    hook(context)
            except Exception as e:
                logger.warning(f"Pre-hook failed: {e}")
    
    async def _run_post_hooks(self, context: PipelineContext) -> None:
        """执行后置钩子"""
        for hook in self._post_hooks:
            try:
                import inspect
                if inspect.iscoroutinefunction(hook):
                    await hook(context)
                else:
                    hook(context)
            except Exception as e:
                logger.warning(f"Post-hook failed: {e}")
    
    @abstractmethod
    async def execute(self, context: PipelineContext) -> PipelineResult:
        """执行 Pipeline（抽象方法）"""
        pass
    
    async def run(
        self,
        input_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> PipelineResult:
        """
        运行 Pipeline
        
        Args:
            input_data: 输入数据
            **kwargs: 其他参数
        
        Returns:
            PipelineResult: 执行结果
        """
        # 创建上下文
        context = PipelineContext(
            input_data=input_data or {},
            status=PipelineStatus.RUNNING,
        )
        
        # 添加 kwargs 到输入
        context.input_data.update(kwargs)
        
        try:
            # 执行前置钩子
            await self._run_pre_hooks(context)
            
            # 执行 Pipeline
            result = await self.execute(context)
            
            # 更新上下文
            context.status = PipelineStatus.COMPLETED
            context.end_time = time.time()
            
            # 执行后置钩子
            await self._run_post_hooks(context)
            
            return result
            
        except Exception as e:
            context.status = PipelineStatus.FAILED
            context.end_time = time.time()
            context.add_error(self.name, str(e))
            
            return PipelineResult(
                success=False,
                output=None,
                context=context,
                error=str(e),
            )
    
    def __or__(self, other: "PipelineBase") -> "SequentialPipeline":
        """
        支持 | 操作符进行 Pipeline 组合
        
        Example:
            pipeline = step1 | step2 | step3
        """
        from opspilot.pipeline.sequential import SequentialPipeline
        return SequentialPipeline([self, other])
