"""
Pipeline 工作流模块

整合 AgentScope Pipeline 特性，提供声明式工作流编排。

特性：
- SequentialPipeline: 顺序执行
- IfElsePipeline: 条件分支
- SwitchPipeline: 多路选择
- ForLoopPipeline: 循环执行
- WhileLoopPipeline: 条件循环
"""

from opspilot.pipeline.base import (
    PipelineBase,
    PipelineContext,
    PipelineResult,
    PipelineStatus,
)

from opspilot.pipeline.sequential import (
    SequentialPipeline,
    sequential_pipeline,
)

from opspilot.pipeline.conditional import (
    IfElsePipeline,
    SwitchPipeline,
    ConditionalPipeline,
)

from opspilot.pipeline.loop import (
    ForLoopPipeline,
    WhileLoopPipeline,
)

from opspilot.pipeline.composite import (
    CompositePipeline,
    PipelineBuilder,
)

__all__ = [
    # 基础
    "PipelineBase",
    "PipelineContext",
    "PipelineResult",
    "PipelineStatus",
    # 顺序
    "SequentialPipeline",
    "sequential_pipeline",
    # 条件
    "IfElsePipeline",
    "SwitchPipeline",
    "ConditionalPipeline",
    # 循环
    "ForLoopPipeline",
    "WhileLoopPipeline",
    # 组合
    "CompositePipeline",
    "PipelineBuilder",
]
