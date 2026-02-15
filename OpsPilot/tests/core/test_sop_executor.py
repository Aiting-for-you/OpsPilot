"""
SOP 执行器模块单元测试
"""
import pytest

from opspilot.core.sop_executor import (
    SOPStepType,
    SOPStep,
    SOPDefinition,
    SOPExecutor,
    SOPExecutionResult,
    create_order_sop,
    query_supplier_sop,
)
from opspilot.tools.mcp import create_default_router


class TestSOPStep:
    """SOP 步骤测试"""

    def test_create_step(self):
        """测试创建步骤"""
        step = SOPStep(
            id="step1",
            name="测试步骤",
            step_type=SOPStepType.TOOL,
            tool_name="query_supplier"
        )

        assert step.id == "step1"
        assert step.step_type == SOPStepType.TOOL
        assert step.timeout == 30

    def test_step_to_dict(self):
        """测试步骤序列化"""
        step = SOPStep(
            id="step1",
            name="测试步骤",
            step_type=SOPStepType.TOOL,
            tool_name="query_supplier",
            tool_params={"region": "华南"}
        )

        data = step.to_dict()

        assert data["id"] == "step1"
        assert data["tool_name"] == "query_supplier"


class TestSOPDefinition:
    """SOP 定义测试"""

    def test_create_sop(self):
        """测试创建 SOP"""
        sop = SOPDefinition(
            name="test_sop",
            description="测试 SOP",
            version="1.0"
        )

        assert sop.name == "test_sop"
        assert len(sop.steps) == 0

    def test_add_step(self):
        """测试添加步骤"""
        sop = SOPDefinition(name="test")
        step = SOPStep(
            id="step1",
            name="步骤1",
            step_type=SOPStepType.TOOL
        )

        sop.add_step(step)

        assert len(sop.steps) == 1
        assert sop.steps[0].id == "step1"

    def test_set_variable(self):
        """测试设置变量"""
        sop = SOPDefinition(name="test")
        sop.set_variable("region", "华南")

        assert sop.variables["region"] == "华南"

    def test_get_step(self):
        """测试获取步骤"""
        sop = SOPDefinition(name="test")
        step = SOPStep(id="step1", name="步骤1", step_type=SOPStepType.TOOL)
        sop.add_step(step)

        found = sop.get_step("step1")
        not_found = sop.get_step("nonexistent")

        assert found is step
        assert not_found is None

    def test_to_dict(self):
        """测试序列化"""
        sop = SOPDefinition(name="test", description="测试")
        sop.add_step(SOPStep(id="s1", name="步骤", step_type=SOPStepType.TOOL))

        data = sop.to_dict()

        assert data["name"] == "test"
        assert len(data["steps"]) == 1


class TestSOPExecutor:
    """SOP 执行器测试"""

    @pytest.fixture
    def executor(self):
        return SOPExecutor()

    @pytest.fixture
    def executor_with_tools(self):
        router = create_default_router()
        executor = SOPExecutor(tool_router=router)
        return executor

    def test_set_tool_router(self, executor):
        """测试设置工具路由器"""
        router = create_default_router()
        executor.set_tool_router(router)

        assert executor._tool_router is router

    @pytest.mark.asyncio
    async def test_execute_simple_sop(self, executor_with_tools):
        """测试执行简单 SOP"""
        sop = SOPDefinition(name="test")
        sop.add_step(SOPStep(
            id="step1",
            name="查询供应商",
            step_type=SOPStepType.TOOL,
            tool_name="query_supplier",
            tool_params={}
        ))

        result = await executor_with_tools.execute(sop)

        assert result["success"] is True
        assert result["sop_name"] == "test"
        assert result["steps_executed"] == 1

    @pytest.mark.asyncio
    async def test_execute_sop_with_variables(self, executor_with_tools):
        """测试带变量的 SOP"""
        sop = SOPDefinition(name="test")
        sop.set_variable("region", "华南")
        sop.add_step(SOPStep(
            id="step1",
            name="查询供应商",
            step_type=SOPStepType.TOOL,
            tool_name="query_supplier",
            tool_params={"region": "$region"}
        ))

        result = await executor_with_tools.execute(sop)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execute_multiple_steps(self, executor_with_tools):
        """测试多步骤 SOP"""
        sop = SOPDefinition(name="multi_step")
        sop.add_step(SOPStep(
            id="step1",
            name="查询供应商",
            step_type=SOPStepType.TOOL,
            tool_name="query_supplier",
            tool_params={}
        ))
        sop.add_step(SOPStep(
            id="step2",
            name="查询库存",
            step_type=SOPStepType.TOOL,
            tool_name="query_inventory",
            tool_params={"sku": "SKU001"}
        ))

        result = await executor_with_tools.execute(sop)

        assert result["success"] is True
        assert result["steps_executed"] == 2

    @pytest.mark.asyncio
    async def test_execute_without_tool_router(self, executor):
        """测试没有工具路由器"""
        sop = SOPDefinition(name="test")
        sop.add_step(SOPStep(
            id="step1",
            name="工具调用",
            step_type=SOPStepType.TOOL,
            tool_name="query_supplier"
        ))

        result = await executor.execute(sop)

        assert result["success"] is False
        assert "工具路由器" in result["results"][0]["error"]

    @pytest.mark.asyncio
    async def test_execute_parallel_steps(self, executor_with_tools):
        """测试并行执行"""
        sop = SOPDefinition(name="parallel_test")
        sop.add_step(SOPStep(
            id="parallel1",
            name="并行查询",
            step_type=SOPStepType.PARALLEL,
            sub_steps=[
                SOPStep(id="p1", name="查询1", step_type=SOPStepType.TOOL,
                       tool_name="query_supplier", tool_params={}),
                SOPStep(id="p2", name="查询2", step_type=SOPStepType.TOOL,
                       tool_name="query_inventory", tool_params={"sku": "SKU001"}),
            ]
        ))

        result = await executor_with_tools.execute(sop)

        assert result["success"] is True


class TestPredefinedSOPs:
    """预定义 SOP 测试"""

    def test_create_order_sop(self):
        """测试创建订单 SOP"""
        sop = create_order_sop()

        assert sop.name == "create_order"
        assert len(sop.steps) == 4

    def test_query_supplier_sop(self):
        """测试查询供应商 SOP"""
        sop = query_supplier_sop()

        assert sop.name == "query_supplier"
        assert len(sop.steps) == 1

    @pytest.mark.asyncio
    async def test_execute_create_order_sop(self):
        """测试执行创建订单 SOP"""
        router = create_default_router()
        executor = SOPExecutor(tool_router=router)
        sop = create_order_sop()

        result = await executor.execute(sop, {
            "region": "华南",
            "sku": "SKU001",
            "amount": 5000,
            "supplier_id": "SUP001",
            "products": [{"sku": "SKU001", "quantity": 10}]
        })

        assert result["success"] is True
        assert result["steps_executed"] == 4


class TestSOPExecutionResult:
    """SOP 执行结果测试"""

    def test_success_result(self):
        """测试成功结果"""
        result = SOPExecutionResult(
            step_id="step1",
            success=True,
            output={"data": "test"}
        )

        data = result.to_dict()

        assert data["success"] is True
        assert data["output"]["data"] == "test"

    def test_failure_result(self):
        """测试失败结果"""
        result = SOPExecutionResult(
            step_id="step1",
            success=False,
            error="执行失败"
        )

        data = result.to_dict()

        assert data["success"] is False
        assert data["error"] == "执行失败"

