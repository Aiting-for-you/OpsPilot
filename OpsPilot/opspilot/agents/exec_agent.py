"""
执行 Agent

职责：
- 执行审核通过的计划
- 调用工具
- 处理执行结果
- 记录执行轨迹
"""
from typing import Optional, Dict, Any, List

from opspilot.agents.base import (
    BaseAgent,
    AgentConfig,
    AgentRole,
    AgentContext,
    AgentOutput,
    BaseLLMClient,
)
from opspilot.core.state_machine import State
from opspilot.tools.base import ToolRouter, ToolContext, ToolResult


class ExecAgent(BaseAgent):
    """
    执行 Agent

    负责执行审核通过的计划，调用工具并处理结果
    """

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        tool_router: Optional[ToolRouter] = None
    ):
        config = AgentConfig(
            name="ExecAgent",
            role=AgentRole.EXECUTION,
            description="执行Agent，负责调用工具执行具体操作",
            temperature=0.3,
        )
        super().__init__(config, llm_client)
        self._tool_router = tool_router

    def set_tool_router(self, router: ToolRouter) -> None:
        """设置工具路由器"""
        self._tool_router = router

    async def _execute(self, context: AgentContext) -> AgentOutput:
        """执行计划"""
        # 获取计划
        plan = context.metadata.get("plan", {})
        steps = plan.get("steps", [])

        if not steps:
            return AgentOutput(
                success=False,
                error="没有可执行的步骤"
            )

        # 检查工具路由器
        if not self._tool_router:
            return AgentOutput(
                success=False,
                error="工具路由器未配置"
            )

        # 执行步骤
        execution_results = []
        all_success = True

        for step in steps:
            result = await self._execute_step(
                step=step,
                task_id=context.task_id,
                previous_results=execution_results
            )
            execution_results.append(result)

            if not result.get("success", False):
                all_success = False
                break

        # 确定下一个状态
        if all_success:
            next_state = State.VERIFYING
        else:
            next_state = State.RETRY

        return AgentOutput(
            success=all_success,
            result={
                "execution_results": execution_results,
                "total_steps": len(steps),
                "completed_steps": len([r for r in execution_results if r.get("success")])
            },
            next_state=next_state,
            tools_to_call=[],  # 已执行完成
            reasoning=f"执行了 {len(execution_results)}/{len(steps)} 个步骤"
        )

    async def _execute_step(
        self,
        step: Dict[str, Any],
        task_id: str,
        previous_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        执行单个步骤

        Args:
            step: 步骤定义
            task_id: 任务ID
            previous_results: 之前步骤的结果

        Returns:
            Dict[str, Any]: 执行结果
        """
        tool_name = step.get("tool")
        params = step.get("params", {})

        # 参数替换（使用之前结果中的数据）
        params = self._resolve_params(params, previous_results)

        # 创建工具上下文
        tool_context = ToolContext(task_id=task_id)

        try:
            # 调用工具
            result: ToolResult = await self._tool_router.call_tool_with_retry(
                tool_name=tool_name,
                params=params,
                context=tool_context
            )

            return {
                "step_id": step.get("step_id"),
                "tool": tool_name,
                "params": params,
                "success": result.is_success(),
                "data": result.data,
                "error": result.error,
                "latency_ms": result.latency_ms,
                "fallback_mode": result.fallback_mode.value if result.fallback_mode else None
            }

        except Exception as e:
            return {
                "step_id": step.get("step_id"),
                "tool": tool_name,
                "params": params,
                "success": False,
                "error": str(e)
            }

    def _resolve_params(
        self,
        params: Dict[str, Any],
        previous_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        解析参数中的引用

        支持格式：${step_N.field} 引用之前步骤的结果
        """
        import re

        resolved = {}
        pattern = r"\$\{step_(\d+)\.(\w+)\}"

        for key, value in params.items():
            if isinstance(value, str):
                match = re.search(pattern, value)
                if match:
                    step_num = int(match.group(1))
                    field = match.group(2)

                    # 查找对应步骤的结果
                    for result in previous_results:
                        if result.get("step_id") == step_num:
                            data = result.get("data", {})
                            resolved[key] = data.get(field, value)
                            break
                    else:
                        resolved[key] = value
                else:
                    resolved[key] = value
            else:
                resolved[key] = value

        return resolved

    def get_system_prompt(self, context: AgentContext) -> str:
        """获取系统提示"""
        return """你是一个专业的执行助手。
你的任务是按照计划调用工具执行具体操作。
你需要：
1. 按顺序执行每个步骤
2. 正确传递参数
3. 处理执行结果
4. 记录执行轨迹

如果执行失败，请分析原因并报告。"""


class MockExecAgent(ExecAgent):
    """
    Mock 执行 Agent

    不实际调用工具，返回模拟结果
    """

    async def _execute(self, context: AgentContext) -> AgentOutput:
        """执行计划（Mock）"""
        plan = context.metadata.get("plan", {})
        steps = plan.get("steps", [])

        execution_results = []

        for step in steps:
            # 模拟执行结果
            result = await self._mock_execute_step(step, context.task_id)
            execution_results.append(result)

        return AgentOutput(
            success=True,
            result={
                "execution_results": execution_results,
                "total_steps": len(steps),
                "completed_steps": len(steps)
            },
            next_state=State.VERIFYING,
            reasoning=f"Mock 执行完成 {len(steps)} 个步骤"
        )

    async def _mock_execute_step(
        self,
        step: Dict[str, Any],
        task_id: str
    ) -> Dict[str, Any]:
        """模拟执行步骤"""
        tool_name = step.get("tool", "unknown")

        # 根据工具类型返回模拟数据
        mock_data = {
            "query_supplier": {
                "suppliers": [
                    {"id": "SUP001", "name": "测试供应商", "rating": 4.8}
                ],
                "total": 1
            },
            "query_inventory": {
                "sku": "SKU001",
                "quantity": 100,
                "warehouse": "深圳仓"
            },
            "create_order": {
                "order_id": f"ORD{task_id[:8]}",
                "status": "created",
                "need_approval": True
            },
            "query_order": {
                "order_id": "ORD123456",
                "status": "pending",
                "total_amount": 5000
            },
            "check_compliance": {
                "is_compliant": True,
                "violations": [],
                "warnings": []
            },
            "query_policy": {
                "policies": [
                    {"id": "POL001", "title": "测试政策"}
                ],
                "total": 1
            }
        }

        return {
            "step_id": step.get("step_id"),
            "tool": tool_name,
            "params": step.get("params", {}),
            "success": True,
            "data": mock_data.get(tool_name, {"result": "mock"}),
            "error": None,
            "latency_ms": 100
        }

