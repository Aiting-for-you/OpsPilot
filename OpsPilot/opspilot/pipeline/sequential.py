"""
顺序 Pipeline

按顺序依次执行每个步骤。
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional, Union

from opspilot.pipeline.base import (
    PipelineBase,
    PipelineContext,
    PipelineResult,
    PipelineStep,
    PipelineStatus,
)

logger = logging.getLogger(__name__)


class SequentialPipeline(PipelineBase):
    """
    顺序 Pipeline
    
    按顺序依次执行每个步骤，前一个步骤的输出可以作为后一个步骤的输入。
    
    示例:
        >>> pipeline = SequentialPipeline([
        ...     intent_recognition_step,
        ...     planning_step,
        ...     execution_step,
        ...     verification_step,
        ... ])
        >>> 
        >>> result = await pipeline.run({"query": "查询供应商信息"})
    """
    
    def __init__(
        self,
        steps: List[Union[PipelineStep, PipelineBase, Callable]],
        name: str = "",
    ):
        super().__init__(name or "SequentialPipeline")
        self._steps = steps
    
    def add_step(
        self,
        step: Union[PipelineStep, PipelineBase, Callable],
    ) -> "SequentialPipeline":
        """添加步骤"""
        self._steps.append(step)
        return self
    
    async def execute(self, context: PipelineContext) -> PipelineResult:
        """执行顺序 Pipeline"""
        output = context.input_data
        
        for i, step in enumerate(self._steps):
            step_name = self._get_step_name(step, i)
            context.current_step = step_name
            
            try:
                # 执行步骤
                result = await self._execute_step(step, context, output)
                
                # 存储结果
                context.set_result(step_name, result)
                output = result
                
                logger.debug(f"Step {step_name} completed")
                
            except Exception as e:
                logger.error(f"Step {step_name} failed: {e}")
                context.add_error(step_name, str(e))
                
                return PipelineResult(
                    success=False,
                    output=None,
                    context=context,
                    error=f"Step {step_name} failed: {e}",
                )
        
        context.output_data = output if isinstance(output, dict) else {"result": output}
        
        return PipelineResult(
            success=True,
            output=output,
            context=context,
        )
    
    async def _execute_step(
        self,
        step: Union[PipelineStep, PipelineBase, Callable],
        context: PipelineContext,
        input_data: Any,
    ) -> Any:
        """执行单个步骤"""
        if isinstance(step, PipelineStep):
            return await step.execute(context)
        
        elif isinstance(step, PipelineBase):
            result = await step.execute(context)
            return result.output
        
        elif callable(step):
            import inspect
            if inspect.iscoroutinefunction(step):
                return await step(context)
            else:
                return step(context)
        
        else:
            raise ValueError(f"Invalid step type: {type(step)}")
    
    def _get_step_name(
        self,
        step: Union[PipelineStep, PipelineBase, Callable],
        index: int,
    ) -> str:
        """获取步骤名称"""
        if isinstance(step, PipelineStep):
            return step.name
        elif isinstance(step, PipelineBase):
            return step.name
        elif hasattr(step, "__name__"):
            return step.__name__
        else:
            return f"step_{index}"


def sequential_pipeline(
    *steps: Union[PipelineStep, PipelineBase, Callable],
) -> SequentialPipeline:
    """
    创建顺序 Pipeline 的便捷函数
    
    Args:
        *steps: 步骤列表
    
    Returns:
        SequentialPipeline
    
    示例:
        >>> pipeline = sequential_pipeline(
        ...     intent_step,
        ...     plan_step,
        ...     execute_step,
        ... )
    """
    return SequentialPipeline(list(steps))
