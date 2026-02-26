"""
组合 Pipeline

支持 Pipeline 的组合和构建器模式。
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional, Union

from opspilot.pipeline.base import (
    PipelineBase,
    PipelineContext,
    PipelineResult,
    PipelineStep,
)

from opspilot.pipeline.sequential import SequentialPipeline
from opspilot.pipeline.conditional import IfElsePipeline, SwitchPipeline
from opspilot.pipeline.loop import ForLoopPipeline, WhileLoopPipeline

logger = logging.getLogger(__name__)


class CompositePipeline(PipelineBase):
    """
    组合 Pipeline
    
    将多个 Pipeline 组合成复杂的执行流程。
    
    示例:
        >>> pipeline = CompositePipeline()
        >>> pipeline.add_sequential([step1, step2, step3])
        >>> pipeline.add_if_else(condition, on_true, on_false)
        >>> pipeline.add_for_loop(items_func, loop_body)
        >>> 
        >>> result = await pipeline.run({"query": "..."})
    """
    
    def __init__(self, name: str = ""):
        super().__init__(name or "CompositePipeline")
        self._pipelines: List[PipelineBase] = []
    
    def add_sequential(
        self,
        steps: List[Union[PipelineStep, PipelineBase, Callable]],
    ) -> "CompositePipeline":
        """添加顺序 Pipeline"""
        pipeline = SequentialPipeline(steps)
        self._pipelines.append(pipeline)
        return self
    
    def add_if_else(
        self,
        condition: Callable[[PipelineContext], bool],
        on_true: Union[PipelineStep, PipelineBase, Callable],
        on_false: Union[PipelineStep, PipelineBase, Callable],
    ) -> "CompositePipeline":
        """添加 If-Else Pipeline"""
        pipeline = IfElsePipeline(condition, on_true, on_false)
        self._pipelines.append(pipeline)
        return self
    
    def add_switch(
        self,
        route_func: Callable[[PipelineContext], str],
        routes: Dict[str, Union[PipelineStep, PipelineBase, Callable]],
        default: Optional[Union[PipelineStep, PipelineBase, Callable]] = None,
    ) -> "CompositePipeline":
        """添加 Switch Pipeline"""
        pipeline = SwitchPipeline(route_func, routes, default)
        self._pipelines.append(pipeline)
        return self
    
    def add_for_loop(
        self,
        items_func: Callable[[PipelineContext], List[Any]],
        loop_body: Union[PipelineStep, PipelineBase, Callable],
        max_iterations: int = 100,
        parallel: bool = False,
    ) -> "CompositePipeline":
        """添加 For 循环 Pipeline"""
        pipeline = ForLoopPipeline(
            items_func=items_func,
            loop_body=loop_body,
            max_iterations=max_iterations,
            parallel=parallel,
        )
        self._pipelines.append(pipeline)
        return self
    
    def add_while_loop(
        self,
        condition: Callable[[PipelineContext], bool],
        loop_body: Union[PipelineStep, PipelineBase, Callable],
        max_iterations: int = 10,
        sleep_between: float = 0,
    ) -> "CompositePipeline":
        """添加 While 循环 Pipeline"""
        pipeline = WhileLoopPipeline(
            condition=condition,
            loop_body=loop_body,
            max_iterations=max_iterations,
            sleep_between=sleep_between,
        )
        self._pipelines.append(pipeline)
        return self
    
    async def execute(self, context: PipelineContext) -> PipelineResult:
        """执行组合 Pipeline"""
        output = context.input_data
        
        for i, pipeline in enumerate(self._pipelines):
            context.current_step = f"sub_pipeline_{i}"
            
            try:
                result = await pipeline.execute(context)
                
                if not result.success:
                    return result
                
                output = result.output
                context.step_results[f"sub_pipeline_{i}"] = output
                
            except Exception as e:
                logger.error(f"Sub-pipeline {i} failed: {e}")
                context.add_error(f"sub_pipeline_{i}", str(e))
                
                return PipelineResult(
                    success=False,
                    output=None,
                    context=context,
                    error=f"Sub-pipeline {i} failed: {e}",
                )
        
        context.output_data = output if isinstance(output, dict) else {"result": output}
        
        return PipelineResult(
            success=True,
            output=output,
            context=context,
        )


class PipelineBuilder:
    """
    Pipeline 构建器
    
    使用流畅接口构建复杂的 Pipeline。
    
    示例:
        >>> pipeline = (
        ...     PipelineBuilder()
        ...     .start_with(intent_step)
        ...     .then(plan_step)
        ...     .branch_if(
        ...         condition=is_complex,
        ...         on_true=complex_flow,
        ...         on_false=simple_flow,
        ...     )
        ...     .then(verify_step)
        ...     .build()
        ... )
    """
    
    def __init__(self):
        self._steps: List[Union[PipelineStep, PipelineBase, Callable]] = []
        self._name: str = "BuiltPipeline"
    
    def start_with(
        self,
        step: Union[PipelineStep, PipelineBase, Callable],
    ) -> "PipelineBuilder":
        """设置起始步骤"""
        self._steps.append(step)
        return self
    
    def then(
        self,
        step: Union[PipelineStep, PipelineBase, Callable],
    ) -> "PipelineBuilder":
        """添加下一步"""
        self._steps.append(step)
        return self
    
    def branch_if(
        self,
        condition: Callable[[PipelineContext], bool],
        on_true: Union[PipelineStep, PipelineBase, Callable],
        on_false: Union[PipelineStep, PipelineBase, Callable],
    ) -> "PipelineBuilder":
        """添加条件分支"""
        pipeline = IfElsePipeline(condition, on_true, on_false)
        self._steps.append(pipeline)
        return self
    
    def switch(
        self,
        route_func: Callable[[PipelineContext], str],
        routes: Dict[str, Union[PipelineStep, PipelineBase, Callable]],
        default: Optional[Union[PipelineStep, PipelineBase, Callable]] = None,
    ) -> "PipelineBuilder":
        """添加多路选择"""
        pipeline = SwitchPipeline(route_func, routes, default)
        self._steps.append(pipeline)
        return self
    
    def for_each(
        self,
        items_func: Callable[[PipelineContext], List[Any]],
        loop_body: Union[PipelineStep, PipelineBase, Callable],
        parallel: bool = False,
    ) -> "PipelineBuilder":
        """添加循环"""
        pipeline = ForLoopPipeline(
            items_func=items_func,
            loop_body=loop_body,
            parallel=parallel,
        )
        self._steps.append(pipeline)
        return self
    
    def while_do(
        self,
        condition: Callable[[PipelineContext], bool],
        loop_body: Union[PipelineStep, PipelineBase, Callable],
        max_iterations: int = 10,
    ) -> "PipelineBuilder":
        """添加 While 循环"""
        pipeline = WhileLoopPipeline(
            condition=condition,
            loop_body=loop_body,
            max_iterations=max_iterations,
        )
        self._steps.append(pipeline)
        return self
    
    def name(self, name: str) -> "PipelineBuilder":
        """设置 Pipeline 名称"""
        self._name = name
        return self
    
    def build(self) -> SequentialPipeline:
        """构建 Pipeline"""
        return SequentialPipeline(self._steps, self._name)
