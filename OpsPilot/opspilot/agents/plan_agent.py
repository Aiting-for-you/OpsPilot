"""
规划 Agent

职责：
- 根据意图制定执行计划
- 分解任务为子任务
- 确定所需工具
- 输出执行路径
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
from opspilot.agents.intent_agent import IntentType
from opspilot.core.state_machine import State


class PlanAgent(BaseAgent):
    """
    规划 Agent

    负责根据识别的意图制定执行计划
    """

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        config = AgentConfig(
            name="PlanAgent",
            role=AgentRole.PLANNING,
            description="规划Agent，负责根据意图制定执行计划，分解任务步骤",
            temperature=0.5,
        )
        super().__init__(config, llm_client)

    async def _execute(self, context: AgentContext) -> AgentOutput:
        """执行规划"""
        # 从上下文获取意图
        intent = context.metadata.get("intent", {})
        intent_type = intent.get("intent_type", "unknown")

        # 构建规划提示
        prompt = self._build_plan_prompt(
            user_input=context.user_input,
            intent=intent,
            knowledge_context=context.knowledge_context
        )

        # 调用 LLM
        response = await self.llm.generate_json(prompt)

        # 解析响应
        plan = self._parse_response(response)

        return AgentOutput(
            success=True,
            result=plan,
            next_state=State.AUDITING,
            reasoning=f"制定了 {len(plan.get('steps', []))} 个执行步骤"
        )

    def _build_plan_prompt(
        self,
        user_input: str,
        intent: Dict[str, Any],
        knowledge_context: str
    ) -> str:
        """构建规划提示"""
        entities_str = ", ".join(
            f"{k}: {v}" for k, v in intent.get("entities", {}).items() if v
        )

        return f"""请根据以下信息制定执行计划。

用户输入：{user_input}
识别意图：{intent.get('intent_type', 'unknown')}
提取实体：{entities_str or '无'}
用户意图摘要：{intent.get('summary', '')}

{knowledge_context}

请以 JSON 格式返回执行计划：
{{
    "plan_summary": "计划摘要",
    "steps": [
        {{
            "step_id": 1,
            "action": "动作描述",
            "tool": "工具名称（如 query_supplier, create_order 等）",
            "params": {{}},
            "expected_output": "预期输出"
        }}
    ],
    "required_approvals": ["需要审批的项"],
    "risks": ["潜在风险"],
    "estimated_time": "预计耗时（秒）"
}}

仅返回 JSON，不要有其他内容。"""

    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析 LLM 响应"""
        return {
            "plan_summary": response.get("plan_summary", ""),
            "steps": response.get("steps", []),
            "required_approvals": response.get("required_approvals", []),
            "risks": response.get("risks", []),
            "estimated_time": response.get("estimated_time", "未知"),
        }

    def get_system_prompt(self, context: AgentContext) -> str:
        """获取系统提示"""
        return """你是一个专业的任务规划助手。
你的任务是根据用户的意图制定详细的执行计划。
你需要：
1. 理解用户的业务意图
2. 确定需要调用的工具和参数
3. 识别需要审批的环节
4. 评估潜在风险
5. 给出合理的执行顺序

可用的工具包括：
- query_supplier: 查询供应商
- create_order: 创建订单
- query_inventory: 查询库存
- query_order: 查询订单
- update_order_status: 更新订单状态
- check_compliance: 合规检查
- query_policy: 查询政策

请确保计划清晰、可执行。"""


class MockPlanAgent(PlanAgent):
    """
    Mock 规划 Agent

    使用预设规则而非 LLM
    """

    # 预设的计划模板
    PLAN_TEMPLATES = {
        IntentType.QUERY_SUPPLIER.value: {
            "plan_summary": "查询供应商信息",
            "steps": [
                {
                    "step_id": 1,
                    "action": "查询供应商信息",
                    "tool": "query_supplier",
                    "params": {"region": "{region}"},
                    "expected_output": "供应商列表"
                }
            ],
            "required_approvals": [],
            "risks": [],
            "estimated_time": "5秒"
        },
        IntentType.CREATE_ORDER.value: {
            "plan_summary": "创建采购订单",
            "steps": [
                {
                    "step_id": 1,
                    "action": "查询供应商",
                    "tool": "query_supplier",
                    "params": {},
                    "expected_output": "供应商信息"
                },
                {
                    "step_id": 2,
                    "action": "检查库存",
                    "tool": "query_inventory",
                    "params": {},
                    "expected_output": "库存信息"
                },
                {
                    "step_id": 3,
                    "action": "创建订单",
                    "tool": "create_order",
                    "params": {},
                    "expected_output": "订单号"
                }
            ],
            "required_approvals": ["订单金额超过10000元需审批"],
            "risks": ["库存不足", "供应商不可用"],
            "estimated_time": "30秒"
        },
        IntentType.QUERY_INVENTORY.value: {
            "plan_summary": "查询产品库存",
            "steps": [
                {
                    "step_id": 1,
                    "action": "查询库存",
                    "tool": "query_inventory",
                    "params": {},
                    "expected_output": "库存信息"
                }
            ],
            "required_approvals": [],
            "risks": [],
            "estimated_time": "5秒"
        },
        IntentType.QUERY_ORDER.value: {
            "plan_summary": "查询订单状态",
            "steps": [
                {
                    "step_id": 1,
                    "action": "查询订单",
                    "tool": "query_order",
                    "params": {},
                    "expected_output": "订单详情"
                }
            ],
            "required_approvals": [],
            "risks": [],
            "estimated_time": "5秒"
        },
        IntentType.CHECK_COMPLIANCE.value: {
            "plan_summary": "合规检查",
            "steps": [
                {
                    "step_id": 1,
                    "action": "执行合规检查",
                    "tool": "check_compliance",
                    "params": {},
                    "expected_output": "合规检查结果"
                }
            ],
            "required_approvals": [],
            "risks": ["可能需要人工审核"],
            "estimated_time": "10秒"
        },
        IntentType.QUERY_POLICY.value: {
            "plan_summary": "查询政策规定",
            "steps": [
                {
                    "step_id": 1,
                    "action": "查询政策",
                    "tool": "query_policy",
                    "params": {},
                    "expected_output": "政策内容"
                }
            ],
            "required_approvals": [],
            "risks": [],
            "estimated_time": "5秒"
        },
    }

    async def _execute(self, context: AgentContext) -> AgentOutput:
        """执行规划（模板匹配）"""
        intent = context.metadata.get("intent", {})
        intent_type = intent.get("intent_type", IntentType.UNKNOWN.value)
        entities = intent.get("entities", {})

        # 获取计划模板
        plan = self.PLAN_TEMPLATES.get(intent_type, {
            "plan_summary": "未知意图，无法制定计划",
            "steps": [],
            "required_approvals": [],
            "risks": ["无法识别用户意图"],
            "estimated_time": "未知"
        }).copy()

        # 填充实体参数
        for step in plan.get("steps", []):
            params = step.get("params", {})
            for key, value in entities.items():
                if key in params:
                    params[key] = value
            step["params"] = params

        return AgentOutput(
            success=True,
            result=plan,
            next_state=State.AUDITING,
            reasoning=f"根据意图 {intent_type} 选择预设计划模板"
        )

