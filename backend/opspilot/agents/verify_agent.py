"""
验证 Agent

职责：
- 验证执行结果
- 检查结果完整性
- 生成执行报告
- 决定是否需要重试
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


class VerifyAgent(BaseAgent):
    """
    验证 Agent

    负责验证执行结果，生成执行报告
    """

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        config = AgentConfig(
            name="VerifyAgent",
            role=AgentRole.VERIFICATION,
            description="验证Agent，负责检查执行结果并生成报告",
            temperature=0.2,
        )
        super().__init__(config, llm_client)

    async def _execute(self, context: AgentContext) -> AgentOutput:
        """执行验证"""
        # 获取执行结果
        execution_results = context.metadata.get("execution_results", [])
        plan = context.metadata.get("plan", {})
        intent = context.metadata.get("intent", {})

        if not execution_results:
            return AgentOutput(
                success=False,
                error="没有执行结果可验证"
            )

        # 构建验证提示
        prompt = self._build_verify_prompt(
            intent=intent,
            plan=plan,
            results=execution_results
        )

        # 调用 LLM
        response = await self.llm.generate_json(prompt)

        # 解析响应
        verification = self._parse_response(response)

        # 确定下一个状态
        if verification.get("passed", False):
            next_state = State.SUCCESS
        else:
            next_state = State.RETRY

        return AgentOutput(
            success=verification.get("passed", False),
            result=verification,
            next_state=next_state,
            reasoning=verification.get("reason", "")
        )

    def _build_verify_prompt(
        self,
        intent: Dict[str, Any],
        plan: Dict[str, Any],
        results: List[Dict[str, Any]]
    ) -> str:
        """构建验证提示"""
        results_str = "\n".join([
            f"步骤 {r.get('step_id')}: {r.get('tool')} -> "
            f"{'成功' if r.get('success') else '失败'}"
            for r in results
        ])

        return f"""请验证以下执行结果是否满足用户意图。

用户意图：{intent.get('intent_type', 'unknown')}
意图摘要：{intent.get('summary', '')}

执行计划：
{plan.get('plan_summary', '')}

执行结果：
{results_str}

请以 JSON 格式返回验证结果：
{{
    "passed": true/false,
    "reason": "验证通过/失败的原因",
    "checklist": [
        {{
            "item": "检查项",
            "passed": true/false,
            "detail": "详情"
        }}
    ],
    "summary": "执行结果摘要",
    "recommendations": ["改进建议"]
}}

仅返回 JSON，不要有其他内容。"""

    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析 LLM 响应"""
        return {
            "passed": response.get("passed", False),
            "reason": response.get("reason", ""),
            "checklist": response.get("checklist", []),
            "summary": response.get("summary", ""),
            "recommendations": response.get("recommendations", []),
        }

    def get_system_prompt(self, context: AgentContext) -> str:
        """获取系统提示"""
        return """你是一个专业的验证助手。
你的任务是检查执行结果是否满足用户的原始意图。
你需要：
1. 检查所有步骤是否成功执行
2. 验证结果数据是否完整
3. 确认是否满足用户意图
4. 给出改进建议（如有）

请保持客观、严谨。"""


class MockVerifyAgent(VerifyAgent):
    """
    Mock 验证 Agent

    使用简单规则验证结果
    """

    async def _execute(self, context: AgentContext) -> AgentOutput:
        """执行验证（Mock）"""
        execution_results = context.metadata.get("execution_results", [])

        # 简单检查：所有步骤是否成功
        all_success = all(r.get("success", False) for r in execution_results)

        checklist = [
            {
                "item": "所有步骤执行成功",
                "passed": all_success,
                "detail": f"{sum(1 for r in execution_results if r.get('success'))}/{len(execution_results)} 步骤成功"
            },
            {
                "item": "返回数据有效",
                "passed": any(r.get("data") for r in execution_results),
                "detail": "检查是否有返回数据"
            }
        ]

        verification = {
            "passed": all_success,
            "reason": "所有步骤执行成功" if all_success else "部分步骤执行失败",
            "checklist": checklist,
            "summary": f"执行了 {len(execution_results)} 个步骤，"
                       f"成功 {sum(1 for r in execution_results if r.get('success'))} 个",
            "recommendations": [] if all_success else ["建议检查失败的步骤并重试"]
        }

        next_state = State.SUCCESS if all_success else State.RETRY

        return AgentOutput(
            success=all_success,
            result=verification,
            next_state=next_state,
            reasoning=verification["reason"]
        )

    def generate_report(
        self,
        context: AgentContext,
        verification: Dict[str, Any]
    ) -> str:
        """
        生成执行报告

        Args:
            context: 执行上下文
            verification: 验证结果

        Returns:
            str: 报告文本
        """
        intent = context.metadata.get("intent", {})
        plan = context.metadata.get("plan", {})
        execution_results = context.metadata.get("execution_results", [])

        lines = [
            "=== 执行报告 ===",
            "",
            f"任务ID: {context.task_id}",
            f"用户意图: {intent.get('intent_type', 'unknown')}",
            f"执行状态: {'成功' if verification.get('passed') else '失败'}",
            "",
            "--- 执行步骤 ---",
        ]

        for i, result in enumerate(execution_results, 1):
            status = "✓" if result.get("success") else "✗"
            lines.append(f"{i}. [{status}] {result.get('tool', 'unknown')}")

        lines.extend([
            "",
            "--- 验证结果 ---",
        ])

        for item in verification.get("checklist", []):
            status = "✓" if item.get("passed") else "✗"
            lines.append(f"[{status}] {item.get('item')}: {item.get('detail')}")

        if verification.get("recommendations"):
            lines.extend([
                "",
                "--- 改进建议 ---",
            ])
            for rec in verification.get("recommendations", []):
                lines.append(f"- {rec}")

        return "\n".join(lines)

