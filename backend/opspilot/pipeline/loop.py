"""
循环 Pipeline

支持 For 循环和 While 循环。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, List, Union

from opspilot.pipeline.base import (
    PipelineBase,
    PipelineContext,
    PipelineResult,
    PipelineStep,
)

logger = logging.getLogger(__name__)


class ForLoopPipeline(PipelineBase):
    """
    For 循环 Pipeline
    
    对列表中的每个元素执行相同的 Pipeline。
    
    示例:
        >>> def get_items(ctx):
        ...     return ctx.input_data.get("items", [])
        >>> 
        >>> pipeline = ForLoopPipeline(
        ...     items_func=get_items,
        ...     loop_body=process_item_step,
        ...     max_iterations=100,
        ... )
    """
    
    def __init__(
        self,
        items_func: Callable[[PipelineContext], List[Any]],
        loop_body: Union[PipelineStep, PipelineBase, Callable],
        max_iterations: int = 100,
        parallel: bool = False,
        name: str = "",
    ):
        super().__init__(name or "ForLoopPipeline")
        self._items_func = items_func
        self._loop_body = loop_body
        self._max_iterations = max_iterations
        self._parallel = parallel
    
    async def execute(self, context: PipelineContext) -> PipelineResult:
        """执行 For 循环 Pipeline"""
        import inspect
        
        try:
            # 获取要遍历的列表
            if inspect.iscoroutinefunction(self._items_func):
                items = await self._items_func(context)
            else:
                items = self._items_func(context)
            
            if not items:
                logger.debug("No items to iterate")
                return PipelineResult(
                    success=True,
                    output=[],
                    context=context,
                )
            
            # 限制迭代次数
            items = items[:self._max_iterations]
            
            results = []
            
            if self._parallel:
                # 并行执行
                tasks = [
                    self._execute_body(item, i, context)
                    for i, item in enumerate(items)
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 处理异常
                final_results = []
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        context.add_error(f"item_{i}", str(result))
                        final_results.append({"error": str(result), "success": False})
                    else:
                        final_results.append(result)
                results = final_results
                
            else:
                # 顺序执行
                for i, item in enumerate(items):
                    context.current_step = f"item_{i}"
                    
                    result = await self._execute_body(item, i, context)
                    results.append(result)
                    
                    context.set_result(f"item_{i}", result)
            
            return PipelineResult(
                success=True,
                output=results,
                context=context,
            )
            
        except Exception as e:
            logger.error(f"ForLoopPipeline failed: {e}")
            context.add_error(self.name, str(e))
            
            return PipelineResult(
                success=False,
                output=None,
                context=context,
                error=str(e),
            )
    
    async def _execute_body(
        self,
        item: Any,
        index: int,
        context: PipelineContext,
    ) -> Any:
        """执行循环体"""
        # 创建子上下文
        sub_context = PipelineContext(
            pipeline_id=f"{context.pipeline_id}_item_{index}",
            trace_id=context.trace_id,
            input_data={"item": item, "index": index, **context.input_data},
            shared=context.shared,
        )
        
        if isinstance(self._loop_body, PipelineStep):
            return await self._loop_body.execute(sub_context)
        
        elif isinstance(self._loop_body, PipelineBase):
            result = await self._loop_body.execute(sub_context)
            return result.output
        
        elif callable(self._loop_body):
            import inspect
            if inspect.iscoroutinefunction(self._loop_body):
                return await self._loop_body(sub_context)
            else:
                return self._loop_body(sub_context)
        
        else:
            raise ValueError(f"Invalid loop body type: {type(self._loop_body)}")


class WhileLoopPipeline(PipelineBase):
    """
    While 循环 Pipeline
    
    只要条件为真就持续执行。
    
    示例:
        >>> def should_continue(ctx):
        ...     return ctx.shared.get("attempts", 0) < 5
        >>> 
        >>> pipeline = WhileLoopPipeline(
        ...     condition=should_continue,
        ...     loop_body=retry_step,
        ...     max_iterations=10,
        ... )
    """
    
    def __init__(
        self,
        condition: Callable[[PipelineContext], bool],
        loop_body: Union[PipelineStep, PipelineBase, Callable],
        max_iterations: int = 10,
        sleep_between: float = 0,
        name: str = "",
    ):
        super().__init__(name or "WhileLoopPipeline")
        self._condition = condition
        self._loop_body = loop_body
        self._max_iterations = max_iterations
        self._sleep_between = sleep_between
    
    async def execute(self, context: PipelineContext) -> PipelineResult:
        """执行 While 循环 Pipeline"""
        import inspect
        
        try:
            iterations = 0
            results = []
            
            while iterations < self._max_iterations:
                # 检查条件
                if inspect.iscoroutinefunction(self._condition):
                    should_continue = await self._condition(context)
                else:
                    should_continue = self._condition(context)
                
                if not should_continue:
                    logger.debug(f"Condition false, stopping after {iterations} iterations")
                    break
                
                # 执行循环体
                context.current_step = f"iteration_{iterations}"
                
                result = await self._execute_body(context)
                results.append(result)
                
                context.set_result(f"iteration_{iterations}", result)
                
                iterations += 1
                
                # 间隔
                if self._sleep_between > 0:
                    await asyncio.sleep(self._sleep_between)
            
            if iterations >= self._max_iterations:
                logger.warning(f"Max iterations ({self._max_iterations}) reached")
            
            return PipelineResult(
                success=True,
                output=results,
                context=context,
            )
            
        except Exception as e:
            logger.error(f"WhileLoopPipeline failed: {e}")
            context.add_error(self.name, str(e))
            
            return PipelineResult(
                success=False,
                output=None,
                context=context,
                error=str(e),
            )
    
    async def _execute_body(self, context: PipelineContext) -> Any:
        """执行循环体"""
        if isinstance(self._loop_body, PipelineStep):
            return await self._loop_body.execute(context)
        
        elif isinstance(self._loop_body, PipelineBase):
            result = await self._loop_body.execute(context)
            return result.output
        
        elif callable(self._loop_body):
            import inspect
            if inspect.iscoroutinefunction(self._loop_body):
                return await self._loop_body(context)
            else:
                return self._loop_body(context)
        
        else:
            raise ValueError(f"Invalid loop body type: {type(self._loop_body)}")
