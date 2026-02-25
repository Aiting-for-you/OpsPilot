"""
意图识别 Agent

职责：
- 解析用户输入
- 识别用户意图
- 提取关键实体
- 输出结构化意图
"""
from typing import Optional, Dict, Any, List
from enum import Enum

from opspilot.agents.base import (
    BaseAgent,
    AgentConfig,
    AgentRole,
    AgentContext,
    AgentOutput,
    BaseLLMClient,
)
from opspilot.core.state_machine import State


class IntentType(str, Enum):
    """意图类型"""
    CREATE_ORDER = "create_order"           # 创建订单
    QUERY_SUPPLIER = "query_supplier"       # 查询供应商
    QUERY_INVENTORY = "query_inventory"     # 查询库存
    QUERY_ORDER = "query_order"             # 查询订单
    UPDATE_ORDER = "update_order"           # 更新订单
    CHECK_COMPLIANCE = "check_compliance"   # 合规检查
    QUERY_POLICY = "query_policy"           # 查询政策
    UNKNOWN = "unknown"                     # 未知意图


class IntentAgent(BaseAgent):
    """
    意图识别 Agent

    负责理解用户输入，识别意图并提取实体
    """

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        config = AgentConfig(
            name="IntentAgent",
            role=AgentRole.INTENT,
            description="意图识别Agent，负责理解用户输入，识别意图并提取关键实体",
            temperature=0.3,  # 低温度，更确定的输出
        )
        super().__init__(config, llm_client)

    async def _execute(self, context: AgentContext) -> AgentOutput:
        """执行意图识别"""
        user_input = context.user_input

        if not user_input:
            return AgentOutput(
                success=False,
                error="用户输入为空"
            )

        # 构建提示
        prompt = self._build_intent_prompt(user_input)

        # 调用 LLM
        response = await self.llm.generate_json(prompt)

        # 解析响应
        intent = self._parse_response(response)

        return AgentOutput(
            success=True,
            result=intent,
            next_state=State.PLANNING,
            reasoning=f"识别到意图: {intent.get('intent_type', 'unknown')}"
        )

    def _build_intent_prompt(self, user_input: str) -> str:
        """构建意图识别提示"""
        return f"""请分析以下用户输入，识别用户意图并提取关键实体。

用户输入：{user_input}

请以 JSON 格式返回以下信息：
{{
    "intent_type": "意图类型（create_order/query_supplier/query_inventory/query_order/update_order/check_compliance/query_policy/unknown）",
    "confidence": 0.0-1.0 的置信度,
    "entities": {{
        "supplier_name": "供应商名称（如有）",
        "product_name": "产品名称（如有）",
        "region": "区域（如有）",
        "order_id": "订单号（如有）",
        "amount": "金额（如有）"
    }},
    "summary": "用户意图的简要描述"
}}

仅返回 JSON，不要有其他内容。"""

    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析 LLM 响应"""
        # 确保必要字段存在
        intent = {
            "intent_type": response.get("intent_type", IntentType.UNKNOWN.value),
            "confidence": response.get("confidence", 0.5),
            "entities": response.get("entities", {}),
            "summary": response.get("summary", ""),
        }

        # 验证意图类型
        try:
            IntentType(intent["intent_type"])
        except ValueError:
            intent["intent_type"] = IntentType.UNKNOWN.value
            intent["confidence"] = 0.0

        return intent

    def get_system_prompt(self, context: AgentContext) -> str:
        """获取系统提示"""
        return """你是一个专业的意图识别助手。
你的任务是分析用户的自然语言输入，识别其业务意图并提取关键实体。
你需要准确识别以下意图类型：
- create_order: 创建采购订单
- query_supplier: 查询供应商信息
- query_inventory: 查询产品库存
- query_order: 查询订单状态
- update_order: 更新订单（如审批、取消等）
- check_compliance: 合规检查
- query_policy: 查询政策规定

请始终保持客观、准确，如果无法确定意图，请返回 unknown。"""


class MockIntentAgent(IntentAgent):
    """
    Mock 意图识别 Agent

    用于测试，使用规则匹配而非 LLM
    """

    async def _execute(self, context: AgentContext) -> AgentOutput:
        """执行意图识别（规则匹配）"""
        user_input = context.user_input.lower()

        # 简单的规则匹配
        intent_type = IntentType.UNKNOWN
        entities = {}

        if any(kw in user_input for kw in ["创建订单", "下单", "采购"]):
            intent_type = IntentType.CREATE_ORDER
        elif any(kw in user_input for kw in ["查询供应商", "找供应商", "供应商"]):
            intent_type = IntentType.QUERY_SUPPLIER
            # 提取区域
            for region in ["华南", "华东", "华北", "西南", "西北"]:
                if region in user_input:
                    entities["region"] = region
        elif any(kw in user_input for kw in ["库存", "存货"]):
            intent_type = IntentType.QUERY_INVENTORY
        elif any(kw in user_input for kw in ["订单状态", "订单查询", "订单"]):
            intent_type = IntentType.QUERY_ORDER
        elif any(kw in user_input for kw in ["审批", "通过", "拒绝"]):
            intent_type = IntentType.UPDATE_ORDER
        elif any(kw in user_input for kw in ["合规", "是否符合"]):
            intent_type = IntentType.CHECK_COMPLIANCE
        elif any(kw in user_input for kw in ["政策", "规定", "规则"]):
            intent_type = IntentType.QUERY_POLICY

        result = {
            "intent_type": intent_type.value,
            "confidence": 0.9 if intent_type != IntentType.UNKNOWN else 0.3,
            "entities": entities,
            "summary": f"识别为{intent_type.value}意图"
        }

        return AgentOutput(
            success=True,
            result=result,
            next_state=State.PLANNING,
            reasoning=f"通过关键词匹配识别意图: {intent_type.value}"
        )

