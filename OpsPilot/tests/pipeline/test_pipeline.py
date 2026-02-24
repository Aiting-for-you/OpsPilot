"""
Pipeline 模块测试

测试 PipelineContext, PipelineStep, SequentialPipeline 等
"""

import pytest
import asyncio
from typing import Any

from opspilot.pipeline.base import (
    PipelineStatus,
    PipelineContext,
    PipelineResult,
    PipelineStep,
    PipelineBase,
)
from opspilot.pipeline.sequential import (
    SequentialPipeline,
    sequential_pipeline,
)


class TestPipelineStatus:
    """测试 PipelineStatus 枚举"""

    def test_status_values(self):
        """测试状态值"""
        assert PipelineStatus.PENDING.value == "pending"
        assert PipelineStatus.RUNNING.value == "running"
        assert PipelineStatus.COMPLETED.value == "completed"
        assert PipelineStatus.FAILED.value == "failed"
        assert PipelineStatus.CANCELLED.value == "cancelled"


class TestPipelineContext:
    """测试 PipelineContext"""

    def test_create_context(self):
        """测试创建上下文"""
        context = PipelineContext()
        
        assert context.pipeline_id is not None
        assert context.trace_id is not None
        assert context.status == PipelineStatus.PENDING

    def test_set_and_get_result(self):
        """测试设置和获取结果"""
        context = PipelineContext()
        
        context.set_result("step1", {"data": "value"})
        
        result = context.get_result("step1")
        
        assert result == {"data": "value"}

    def test_get_result_default(self):
        """测试获取默认值"""
        context = PipelineContext()
        
        result = context.get_result("nonexistent", "default")
        
        assert result == "default"

    def test_add_error(self):
        """测试添加错误"""
        context = PipelineContext()
        
        context.add_error("step1", "Error message")
        
        assert len(context.errors) == 1
        assert context.errors[0]["step"] == "step1"

    def test_to_dict(self):
        """测试转换为字典"""
        context = PipelineContext()
        context.set_result("step1", "result")
        
        data = context.to_dict()
        
        assert "pipeline_id" in data
        assert "trace_id" in data
        assert "status" in data
        assert data["status"] == "pending"

    def test_context_with_input_data(self):
        """测试带输入数据的上下文"""
        context = PipelineContext(
            input_data={"query": "test query", "user_id": "user-001"}
        )
        
        assert context.input_data["query"] == "test query"

    def test_shared_data(self):
        """测试共享数据"""
        context = PipelineContext()
        
        context.shared["cache"] = {"key": "value"}
        
        assert context.shared["cache"]["key"] == "value"


class TestPipelineResult:
    """测试 PipelineResult"""

    def test_create_result(self):
        """测试创建结果"""
        context = PipelineContext()
        
        result = PipelineResult(
            success=True,
            output={"result": "success"},
            context=context,
        )
        
        assert result.success is True
        assert result.output == {"result": "success"}
        assert result.error is None

    def test_result_with_error(self):
        """测试带错误的结果"""
        context = PipelineContext()
        
        result = PipelineResult(
            success=False,
            output=None,
            context=context,
            error="Something went wrong",
        )
        
        assert result.success is False
        assert result.error == "Something went wrong"

    def test_result_to_dict(self):
        """测试结果转字典"""
        context = PipelineContext()
        
        result = PipelineResult(
            success=True,
            output="output",
            context=context,
        )
        
        data = result.to_dict()
        
        assert data["success"] is True
        assert data["output"] == "output"
        assert "context" in data


class TestPipelineStep:
    """测试 PipelineStep"""

    @pytest.mark.asyncio
    async def test_create_step(self):
        """测试创建步骤"""
        def action(ctx):
            return "step result"
        
        step = PipelineStep(
            name="test_step",
            action=action,
            timeout=30.0,
            retry=0,
        )
        
        context = PipelineContext()
        result = await step.execute(context)
        
        assert result == "step result"

    @pytest.mark.asyncio
    async def test_step_with_context(self):
        """测试步骤使用上下文"""
        def action(ctx):
            ctx.set_result("inner", "value")
            return ctx.input_data.get("query")
        
        step = PipelineStep(name="step_with_ctx", action=action)
        
        context = PipelineContext(input_data={"query": "test"})
        result = await step.execute(context)
        
        assert result == "test"
        assert context.get_result("inner") == "value"

    @pytest.mark.asyncio
    async def test_async_step(self):
        """测试异步步骤"""
        async def async_action(ctx):
            await asyncio.sleep(0.01)
            return "async result"
        
        step = PipelineStep(name="async_step", action=async_action)
        
        context = PipelineContext()
        result = await step.execute(context)
        
        assert result == "async result"

    @pytest.mark.asyncio
    async def test_step_retry(self):
        """测试步骤重试"""
        attempt_count = 0
        
        def flaky_action(ctx):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ValueError("Temporary error")
            return "success after retry"
        
        step = PipelineStep(
            name="flaky_step",
            action=flaky_action,
            retry=2,
        )
        
        context = PipelineContext()
        result = await step.execute(context)
        
        assert result == "success after retry"
        assert attempt_count == 3


class TestSequentialPipeline:
    """测试 SequentialPipeline"""

    @pytest.mark.asyncio
    async def test_create_pipeline(self):
        """测试创建管道"""
        def step1(ctx):
            return "step1_output"
        
        def step2(ctx):
            return "step2_output"
        
        pipeline = SequentialPipeline([step1, step2])
        
        assert pipeline.name == "SequentialPipeline"
        assert len(pipeline._steps) == 2

    @pytest.mark.asyncio
    async def test_execute_pipeline(self):
        """测试执行管道"""
        def step1(ctx):
            return "result1"
        
        def step2(ctx):
            return "result2"
        
        pipeline = SequentialPipeline([step1, step2])
        
        result = await pipeline.run({"input": "test"})
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_pipeline_passes_output(self):
        """测试管道传递输出"""
        def step1(ctx):
            return {"value": 100}
        
        def step2(ctx):
            prev = ctx.get_result("step1")
            return prev["value"] * 2
        
        pipeline = SequentialPipeline([step1, step2])
        
        result = await pipeline.run({})
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_pipeline_with_failure(self):
        """测试管道失败"""
        def failing_step(ctx):
            raise ValueError("Step failed")
        
        pipeline = SequentialPipeline([failing_step])
        
        result = await pipeline.run({})
        
        assert result.success is False
        assert "Step failed" in result.error

    @pytest.mark.asyncio
    async def test_pipeline_context_status(self):
        """测试上下文状态更新"""
        def step1(ctx):
            return "done"
        
        pipeline = SequentialPipeline([step1])
        
        result = await pipeline.run({})
        
        assert result.context.status == PipelineStatus.COMPLETED
        assert result.context.end_time is not None

    @pytest.mark.asyncio
    async def test_pipeline_step_results(self):
        """测试步骤结果存储"""
        def step1(ctx):
            return "result1"
        
        def step2(ctx):
            return "result2"
        
        pipeline = SequentialPipeline([step1, step2])
        
        result = await pipeline.run({})
        
        assert result.context.get_result("step1") == "result1"
        assert result.context.get_result("step2") == "result2"

    @pytest.mark.asyncio
    async def test_add_step(self):
        """测试添加步骤"""
        pipeline = SequentialPipeline([])
        
        def step1(ctx):
            return "step1"
        
        pipeline.add_step(step1)
        
        assert len(pipeline._steps) == 1

    @pytest.mark.asyncio
    async def test_pipeline_with_async_steps(self):
        """测试异步步骤"""
        async def async_step1(ctx):
            return "async1"
        
        async def async_step2(ctx):
            return "async2"
        
        pipeline = SequentialPipeline([async_step1, async_step2])
        
        result = await pipeline.run({})
        
        assert result.success is True


class TestSequentialPipelineOperator:
    """测试管道操作符"""

    @pytest.mark.asyncio
    async def test_pipeline_or_operator(self):
        """测试 | 操作符 - SequentialPipeline 之间的组合"""
        # 创建两个 Pipeline
        pipeline1 = SequentialPipeline([
            PipelineStep(name="step1", action=lambda ctx: "s1")
        ])
        pipeline2 = SequentialPipeline([
            PipelineStep(name="step2", action=lambda ctx: "s2")
        ])
        
        combined = pipeline1 | pipeline2
        
        assert isinstance(combined, SequentialPipeline)
        
        result = await combined.run({})
        assert result.success is True


class TestPipelineHooks:
    """测试 Pipeline 钩子"""

    @pytest.mark.asyncio
    async def test_pre_hook(self):
        """测试前置钩子"""
        hook_called = []
        
        def pre_hook(ctx):
            hook_called.append("pre")
        
        def step1(ctx):
            return "done"
        
        pipeline = SequentialPipeline([step1])
        pipeline.add_pre_hook(pre_hook)
        
        await pipeline.run({})
        
        assert "pre" in hook_called

    @pytest.mark.asyncio
    async def test_post_hook(self):
        """测试后置钩子"""
        hook_called = []
        
        def post_hook(ctx):
            hook_called.append("post")
        
        def step1(ctx):
            return "done"
        
        pipeline = SequentialPipeline([step1])
        pipeline.add_post_hook(post_hook)
        
        await pipeline.run({})
        
        assert "post" in hook_called

    @pytest.mark.asyncio
    async def test_async_hook(self):
        """测试异步钩子"""
        hook_called = []
        
        async def async_hook(ctx):
            await asyncio.sleep(0.01)
            hook_called.append("async")
        
        def step1(ctx):
            return "done"
        
        pipeline = SequentialPipeline([step1])
        pipeline.add_pre_hook(async_hook)
        
        await pipeline.run({})
        
        assert "async" in hook_called


class TestSequentialPipelineFunction:
    """测试便捷函数"""

    @pytest.mark.asyncio
    async def test_sequential_pipeline_function(self):
        """测试 sequential_pipeline 函数"""
        def step1(ctx):
            return "r1"
        
        def step2(ctx):
            return "r2"
        
        pipeline = sequential_pipeline(step1, step2)
        
        assert isinstance(pipeline, SequentialPipeline)
        
        result = await pipeline.run({})
        assert result.success is True
