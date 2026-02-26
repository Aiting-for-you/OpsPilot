"""
条件 Pipeline

支持条件分支和多路选择。
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

logger = logging.getLogger(__name__)


class IfElsePipeline(PipelineBase):
    """
    If-Else Pipeline
    
    根据条件选择执行不同的分支。
    
    示例:
        >>> def is_complex(ctx):
        ...     return ctx.input_data.get("complexity") == "high"
        >>> 
        >>> pipeline = IfElsePipeline(
        ...     condition=is_complex,
        ...     on_true=complex_workflow,
        ...     on_false=simple_workflow,
        ... )
    """
    
    def __init__(
        self,
        condition: Callable[[PipelineContext], bool],
        on_true: Union[PipelineStep, PipelineBase, Callable],
        on_false: Union[PipelineStep, PipelineBase, Callable],
        name: str = "",
    ):
        super().__init__(name or "IfElsePipeline")
        self._condition = condition
        self._on_true = on_true
        self._on_false = on_false
    
    async def execute(self, context: PipelineContext) -> PipelineResult:
        """执行条件 Pipeline"""
        try:
            # 评估条件
            import inspect
            if inspect.iscoroutinefunction(self._condition):
                condition_result = await self._condition(context)
            else:
                condition_result = self._condition(context)
            
            logger.debug(f"Condition evaluated to: {condition_result}")
            
            # 选择分支
            selected_branch = self._on_true if condition_result else self._on_false
            branch_name = "on_true" if condition_result else "on_false"
            
            # 执行选中的分支
            result = await self._execute_branch(selected_branch, context)
            
            context.set_result(branch_name, result)
            
            return PipelineResult(
                success=True,
                output=result,
                context=context,
            )
            
        except Exception as e:
            logger.error(f"IfElsePipeline failed: {e}")
            context.add_error(self.name, str(e))
            
            return PipelineResult(
                success=False,
                output=None,
                context=context,
                error=str(e),
            )
    
    async def _execute_branch(
        self,
        branch: Union[PipelineStep, PipelineBase, Callable],
        context: PipelineContext,
    ) -> Any:
        """执行分支"""
        if isinstance(branch, PipelineStep):
            return await branch.execute(context)
        
        elif isinstance(branch, PipelineBase):
            result = await branch.execute(context)
            return result.output
        
        elif callable(branch):
            import inspect
            if inspect.iscoroutinefunction(branch):
                return await branch(context)
            else:
                return branch(context)
        
        else:
            raise ValueError(f"Invalid branch type: {type(branch)}")


class SwitchPipeline(PipelineBase):
    """
    Switch Pipeline
    
    根据路由函数返回的键值选择执行对应的分支。
    
    示例:
        >>> def route_intent(ctx):
        ...     return ctx.input_data.get("intent", "default")
        >>> 
        >>> pipeline = SwitchPipeline(
        ...     route_func=route_intent,
        ...     routes={
        ...         "query": query_pipeline,
        ...         "order": order_pipeline,
        ...         "alert": alert_pipeline,
        ...         "default": default_pipeline,
        ...     },
        ... )
    """
    
    def __init__(
        self,
        route_func: Callable[[PipelineContext], str],
        routes: Dict[str, Union[PipelineStep, PipelineBase, Callable]],
        default: Optional[Union[PipelineStep, PipelineBase, Callable]] = None,
        name: str = "",
    ):
        super().__init__(name or "SwitchPipeline")
        self._route_func = route_func
        self._routes = routes
        self._default = default
    
    async def execute(self, context: PipelineContext) -> PipelineResult:
        """执行 Switch Pipeline"""
        try:
            # 获取路由键
            import inspect
            if inspect.iscoroutinefunction(self._route_func):
                route_key = await self._route_func(context)
            else:
                route_key = self._route_func(context)
            
            logger.debug(f"Routed to: {route_key}")
            
            # 选择路由
            selected = self._routes.get(route_key, self._default)
            
            if selected is None:
                raise ValueError(f"No route found for key: {route_key}")
            
            # 执行选中的路由
            result = await self._execute_route(selected, context)
            
            context.set_result(f"route_{route_key}", result)
            
            return PipelineResult(
                success=True,
                output=result,
                context=context,
            )
            
        except Exception as e:
            logger.error(f"SwitchPipeline failed: {e}")
            context.add_error(self.name, str(e))
            
            return PipelineResult(
                success=False,
                output=None,
                context=context,
                error=str(e),
            )
    
    async def _execute_route(
        self,
        route: Union[PipelineStep, PipelineBase, Callable],
        context: PipelineContext,
    ) -> Any:
        """执行路由"""
        if isinstance(route, PipelineStep):
            return await route.execute(context)
        
        elif isinstance(route, PipelineBase):
            result = await route.execute(context)
            return result.output
        
        elif callable(route):
            import inspect
            if inspect.iscoroutinefunction(route):
                return await route(context)
            else:
                return route(context)
        
        else:
            raise ValueError(f"Invalid route type: {type(route)}")


class ConditionalPipeline(PipelineBase):
    """
    条件 Pipeline 组合
    
    支持多个条件分支的复杂逻辑。
    
    示例:
        >>> pipeline = ConditionalPipeline(
        ...     branches=[
        ...         (condition1, branch1),
        ...         (condition2, branch2),
        ...         (condition3, branch3),
        ...     ],
        ...     default=default_branch,
        ... )
    """
    
    def __init__(
        self,
        branches: List[tuple],  # List of (condition, branch) tuples
        default: Optional[Union[PipelineStep, PipelineBase, Callable]] = None,
        name: str = "",
    ):
        super().__init__(name or "ConditionalPipeline")
        self._branches = branches
        self._default = default
    
    async def execute(self, context: PipelineContext) -> PipelineResult:
        """执行条件 Pipeline"""
        import inspect
        
        try:
            # 依次检查条件
            for i, (condition, branch) in enumerate(self._branches):
                if inspect.iscoroutinefunction(condition):
                    matches = await condition(context)
                else:
                    matches = condition(context)
                
                if matches:
                    logger.debug(f"Matched branch {i}")
                    
                    result = await self._execute_branch(branch, context)
                    context.set_result(f"branch_{i}", result)
                    
                    return PipelineResult(
                        success=True,
                        output=result,
                        context=context,
                    )
            
            # 没有匹配，执行默认分支
            if self._default:
                result = await self._execute_branch(self._default, context)
                context.set_result("default", result)
                
                return PipelineResult(
                    success=True,
                    output=result,
                    context=context,
                )
            
            # 没有匹配且没有默认分支
            return PipelineResult(
                success=True,
                output=None,
                context=context,
            )
            
        except Exception as e:
            logger.error(f"ConditionalPipeline failed: {e}")
            context.add_error(self.name, str(e))
            
            return PipelineResult(
                success=False,
                output=None,
                context=context,
                error=str(e),
            )
    
    async def _execute_branch(
        self,
        branch: Union[PipelineStep, PipelineBase, Callable],
        context: PipelineContext,
    ) -> Any:
        """执行分支"""
        if isinstance(branch, PipelineStep):
            return await branch.execute(context)
        elif isinstance(branch, PipelineBase):
            result = await branch.execute(context)
            return result.output
        elif callable(branch):
            import inspect
            if inspect.iscoroutinefunction(branch):
                return await branch(context)
            else:
                return branch(context)
        else:
            raise ValueError(f"Invalid branch type: {type(branch)}")
