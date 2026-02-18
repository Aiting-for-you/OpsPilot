"""
成本分析Agent

职责：
- 分析产品成本（生产成本、运营成本、物流成本）
- 确保定价覆盖成本+合理毛利
- 提供成本底线建议
"""
from typing import Optional, Dict, Any
import asyncio

from opspilot.agents.base import (
    BaseAgent,
    AgentConfig,
    AgentRole,
    AgentContext,
    AgentOutput,
    BaseLLMClient,
)
from opspilot.tools.base import ToolRouter, ToolContext


class CostAgent(BaseAgent):
    """
    成本分析Agent

    基于成本数据，确保定价合理覆盖成本
    """

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        tool_router: Optional[ToolRouter] = None
    ):
        config = AgentConfig(
            name="CostAgent",
            role=AgentRole.EXECUTION,
            description="成本分析Agent，确保定价覆盖成本+合理毛利",
            temperature=0.3,
        )
        super().__init__(config, llm_client)
        self._tool_router = tool_router

    def set_tool_router(self, router: ToolRouter) -> None:
        """设置工具路由器"""
        self._tool_router = router

    async def _execute(self, context: AgentContext) -> AgentOutput:
        """执行成本分析"""
        product_id = context.metadata.get("product_id")
        
        if not product_id:
            return AgentOutput(
                success=False,
                error="缺少产品ID"
            )

        # 1. 查询成本数据（复用database工具）
        cost_data = await self._query_cost_data(product_id)
        
        if not cost_data:
            return AgentOutput(
                success=False,
                error="无法获取成本数据"
            )

        # 2. 计算建议价格
        suggested_price = self._calculate_cost_based_price(cost_data)
        
        # 3. 生成推理说明
        reasoning = self._generate_reasoning(cost_data, suggested_price)

        return AgentOutput(
            success=True,
            result={
                "agent": "CostAgent",
                "product_id": product_id,
                "suggested_price": suggested_price,
                "confidence": 0.85,
                "reasoning": reasoning,
                "cost_breakdown": cost_data,
            },
            reasoning=reasoning
        )

    async def _query_cost_data(self, product_id: str) -> Optional[Dict[str, Any]]:
        """查询成本数据"""
        # Mock数据（实际应调用database工具）
        await asyncio.sleep(0.1)  # 模拟延迟
        
        return {
            "product_id": product_id,
            "production_cost": 45.0,      # 生产成本
            "operation_cost": 8.0,        # 运营成本
            "logistics_cost": 5.0,        # 物流成本
            "marketing_cost": 6.0,        # 营销成本
            "total_cost": 64.0,           # 总成本
            "currency": "CNY",
        }

    def _calculate_cost_based_price(self, cost_data: Dict[str, Any]) -> float:
        """基于成本计算建议价格"""
        total_cost = cost_data["total_cost"]
        
        # 目标毛利率：30%
        target_margin = 0.30
        
        # 建议价格 = 总成本 / (1 - 毛利率)
        suggested_price = total_cost / (1 - target_margin)
        
        return round(suggested_price, 2)

    def _generate_reasoning(
        self,
        cost_data: Dict[str, Any],
        suggested_price: float
    ) -> str:
        """生成推理说明"""
        total_cost = cost_data["total_cost"]
        margin = (suggested_price - total_cost) / suggested_price * 100
        
        return (
            f"成本分析：产品总成本为{total_cost}元"
            f"（生产{cost_data['production_cost']} + 运营{cost_data['operation_cost']}"
            f" + 物流{cost_data['logistics_cost']} + 营销{cost_data['marketing_cost']}）。"
            f"建议定价{suggested_price}元，毛利率约{margin:.1f}%，符合30%目标毛利。"
        )
