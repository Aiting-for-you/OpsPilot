"""
SOP 执行器模块

职责：
- 执行标准操作流程
- 支持分支和条件判断
- 支持并行执行
"""
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio

from opspilot.core.state_machine import State
from opspilot.core.events import EventBus, TaskCreatedEvent
from opspilot.tools.base import ToolRouter, ToolContext, ToolResult


class SOPStepType(str, Enum):
    """SOP 步骤类型"""
    SEQUENTIAL = "sequential"   # 顺序执行
    PARALLEL = "parallel"       # 并行执行
    CONDITIONAL = "conditional" # 条件分支
    LOOP = "loop"               # 循环
    TOOL = "tool"               # 工具调用


@dataclass
class SOPStep:
    """SOP 步骤定义"""
    id: str
    name: str
    step_type: SOPStepType
    description: str = ""
    tool_name: Optional[str] = None
    tool_params: Optional[Dict[str, Any]] = None
    condition: Optional[str] = None  # 条件表达式
    branches: Optional[Dict[str, "SOPStep"]] = None  # 条件分支
    sub_steps: Optional[List["SOPStep"]] = None  # 子步骤
    on_success: Optional[str] = None  # 成功后的动作
    on_failure: Optional[str] = None  # 失败后的动作
    timeout: int = 30
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "id": self.id,
            "name": self.name,
            "step_type": self.step_type.value,
            "description": self.description,
        }
        if self.tool_name:
            result["tool_name"] = self.tool_name
        if self.tool_params:
            result["tool_params"] = self.tool_params
        return result


@dataclass
class SOPExecutionResult:
    """SOP 执行结果"""
    step_id: str
    success: bool
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


class SOPDefinition:
    """
    SOP 定义

    标准操作流程的定义类
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        version: str = "1.0"
    ):
        self.name = name
        self.description = description
        self.version = version
        self.steps: List[SOPStep] = []
        self.variables: Dict[str, Any] = {}

    def add_step(self, step: SOPStep) -> "SOPDefinition":
        """添加步骤"""
        self.steps.append(step)
        return self

    def set_variable(self, name: str, value: Any) -> "SOPDefinition":
        """设置变量"""
        self.variables[name] = value
        return self

    def get_step(self, step_id: str) -> Optional[SOPStep]:
        """获取步骤"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "steps": [s.to_dict() for s in self.steps],
            "variables": self.variables,
        }


class SOPExecutor:
    """
    SOP 执行器

    执行标准操作流程
    """

    def __init__(self, tool_router: Optional[ToolRouter] = None):
        """
        初始化

        Args:
            tool_router: 工具路由器
        """
        self._tool_router = tool_router
        self._event_bus = EventBus.get_instance()
        self._execution_context: Dict[str, Any] = {}
        self._results: List[SOPExecutionResult] = []

    def set_tool_router(self, router: ToolRouter) -> None:
        """设置工具路由器"""
        self._tool_router = router

    async def execute(
        self,
        sop: SOPDefinition,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行 SOP

        Args:
            sop: SOP 定义
            context: 执行上下文

        Returns:
            Dict[str, Any]: 执行结果
        """
        # 初始化执行上下文
        self._execution_context = {**sop.variables, **(context or {})}
        self._results = []

        start_time = datetime.now()

        try:
            # 执行所有步骤
            for step in sop.steps:
                result = await self._execute_step(step)
                self._results.append(result)

                if not result.success:
                    # 步骤失败，停止执行
                    break

            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            # 汇总结果
            all_success = all(r.success for r in self._results)

            return {
                "sop_name": sop.name,
                "success": all_success,
                "steps_executed": len(self._results),
                "total_steps": len(sop.steps),
                "duration_ms": duration_ms,
                "results": [r.to_dict() for r in self._results],
                "context": self._execution_context,
            }

        except Exception as e:
            return {
                "sop_name": sop.name,
                "success": False,
                "error": str(e),
                "results": [r.to_dict() for r in self._results],
            }

    async def _execute_step(self, step: SOPStep) -> SOPExecutionResult:
        """
        执行单个步骤

        Args:
            step: 步骤定义

        Returns:
            SOPExecutionResult: 执行结果
        """
        start_time = datetime.now()

        try:
            if step.step_type == SOPStepType.TOOL:
                result = await self._execute_tool_step(step)
            elif step.step_type == SOPStepType.PARALLEL:
                result = await self._execute_parallel_step(step)
            elif step.step_type == SOPStepType.CONDITIONAL:
                result = await self._execute_conditional_step(step)
            elif step.step_type == SOPStepType.LOOP:
                result = await self._execute_loop_step(step)
            else:
                result = await self._execute_sequential_step(step)

            end_time = datetime.now()
            result.start_time = start_time
            result.end_time = end_time
            result.duration_ms = int((end_time - start_time).total_seconds() * 1000)

            return result

        except Exception as e:
            end_time = datetime.now()
            return SOPExecutionResult(
                step_id=step.id,
                success=False,
                error=str(e),
                start_time=start_time,
                end_time=end_time,
                duration_ms=int((end_time - start_time).total_seconds() * 1000)
            )

    async def _execute_tool_step(self, step: SOPStep) -> SOPExecutionResult:
        """执行工具调用步骤"""
        if not self._tool_router:
            return SOPExecutionResult(
                step_id=step.id,
                success=False,
                error="工具路由器未配置"
            )

        # 解析参数（支持变量替换）
        params = self._resolve_params(step.tool_params or {})

        # 创建工具上下文
        tool_context = ToolContext(
            task_id=self._execution_context.get("task_id", "sop-execution")
        )

        # 调用工具
        result: ToolResult = await self._tool_router.call_tool_with_retry(
            tool_name=step.tool_name,
            params=params,
            context=tool_context,
            max_retries=step.retry_count
        )

        # 保存结果到上下文
        self._execution_context[f"step_{step.id}_result"] = result.data

        return SOPExecutionResult(
            step_id=step.id,
            success=result.is_success(),
            output=result.data,
            error=result.error
        )

    async def _execute_sequential_step(self, step: SOPStep) -> SOPExecutionResult:
        """执行顺序步骤"""
        if not step.sub_steps:
            return SOPExecutionResult(step_id=step.id, success=True)

        for sub_step in step.sub_steps:
            result = await self._execute_step(sub_step)
            if not result.success:
                return SOPExecutionResult(
                    step_id=step.id,
                    success=False,
                    error=f"子步骤 {sub_step.id} 执行失败: {result.error}"
                )

        return SOPExecutionResult(step_id=step.id, success=True)

    async def _execute_parallel_step(self, step: SOPStep) -> SOPExecutionResult:
        """执行并行步骤"""
        if not step.sub_steps:
            return SOPExecutionResult(step_id=step.id, success=True)

        # 并行执行所有子步骤
        tasks = [self._execute_step(s) for s in step.sub_steps]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 检查结果
        errors = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append(f"步骤 {step.sub_steps[i].id} 异常: {result}")
            elif not result.success:
                errors.append(f"步骤 {result.step_id} 失败: {result.error}")

        if errors:
            return SOPExecutionResult(
                step_id=step.id,
                success=False,
                error="; ".join(errors)
            )

        return SOPExecutionResult(
            step_id=step.id,
            success=True,
            output={"parallel_results": [r.to_dict() for r in results if not isinstance(r, Exception)]}
        )

    async def _execute_conditional_step(self, step: SOPStep) -> SOPExecutionResult:
        """执行条件分支步骤"""
        if not step.condition or not step.branches:
            return SOPExecutionResult(step_id=step.id, success=True)

        # 评估条件
        branch_key = self._evaluate_condition(step.condition)

        # 执行对应分支
        branch_step = step.branches.get(branch_key) or step.branches.get("default")
        if branch_step:
            return await self._execute_step(branch_step)

        return SOPExecutionResult(step_id=step.id, success=True)

    async def _execute_loop_step(self, step: SOPStep) -> SOPExecutionResult:
        """执行循环步骤"""
        if not step.sub_steps:
            return SOPExecutionResult(step_id=step.id, success=True)

        # 简单实现：循环执行固定次数
        # 实际实现应该支持条件循环
        max_iterations = self._execution_context.get("loop_max", 3)

        for i in range(max_iterations):
            for sub_step in step.sub_steps:
                result = await self._execute_step(sub_step)
                if not result.success:
                    return SOPExecutionResult(
                        step_id=step.id,
                        success=False,
                        error=f"循环第 {i+1} 次，子步骤 {sub_step.id} 失败"
                    )

        return SOPExecutionResult(step_id=step.id, success=True)

    def _resolve_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """解析参数中的变量引用"""
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$"):
                # 变量引用
                var_name = value[1:]
                resolved[key] = self._execution_context.get(var_name, value)
            elif isinstance(value, dict):
                resolved[key] = self._resolve_params(value)
            else:
                resolved[key] = value
        return resolved

    def _evaluate_condition(self, condition: str) -> str:
        """
        评估条件表达式

        简单实现：直接返回变量值或条件结果
        """
        # 支持简单的变量引用
        if condition.startswith("$"):
            var_name = condition[1:]
            return str(self._execution_context.get(var_name, "default"))

        # 默认返回条件本身作为分支键
        return condition


# ==================== 预定义 SOP ====================

def create_order_sop() -> SOPDefinition:
    """创建订单 SOP"""
    sop = SOPDefinition(
        name="create_order",
        description="创建采购订单标准流程",
        version="1.0"
    )

    sop.add_step(SOPStep(
        id="step1",
        name="查询供应商",
        step_type=SOPStepType.TOOL,
        tool_name="query_supplier",
        tool_params={"region": "$region"}
    ))

    sop.add_step(SOPStep(
        id="step2",
        name="检查库存",
        step_type=SOPStepType.TOOL,
        tool_name="query_inventory",
        tool_params={"sku": "$sku"}
    ))

    sop.add_step(SOPStep(
        id="step3",
        name="合规检查",
        step_type=SOPStepType.TOOL,
        tool_name="check_compliance",
        tool_params={
            "check_type": "amount_limit",
            "data": {"amount": "$amount"}
        }
    ))

    sop.add_step(SOPStep(
        id="step4",
        name="创建订单",
        step_type=SOPStepType.TOOL,
        tool_name="create_order",
        tool_params={
            "supplier_id": "$supplier_id",
            "products": "$products"
        }
    ))

    return sop


def query_supplier_sop() -> SOPDefinition:
    """查询供应商 SOP"""
    sop = SOPDefinition(
        name="query_supplier",
        description="查询供应商信息标准流程",
        version="1.0"
    )

    sop.add_step(SOPStep(
        id="step1",
        name="查询供应商",
        step_type=SOPStepType.TOOL,
        tool_name="query_supplier",
        tool_params={"region": "$region", "supplier_name": "$supplier_name"}
    ))

    return sop

