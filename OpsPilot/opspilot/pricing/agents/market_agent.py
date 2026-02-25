"""
市场竞争Agent

职责：
- 分析竞品定价策略
- 监控市场趋势
- 提供竞争性定价建议
"""
from typing import Optional, Dict, Any, List
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


class MarketAgent(BaseAgent):
    """
    市场竞争Agent

    基于市场竞品数据，提供竞争性定价建议
    """

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        tool_router: Optional[ToolRouter] = None
    ):
        config = AgentConfig(
            name="MarketAgent",
            role=AgentRole.EXECUTION,
            description="市场竞争Agent，分析竞品定价并提供竞争性建议",
            temperature=0.5,  # 稍高温度，考虑市场不确定性
        )
        super().__init__(config, llm_client)
        self._tool_router = tool_router

    def set_tool_router(self, router: ToolRouter) -> None:
        """设置工具路由器"""
        self._tool_router = router

    async def _execute(self, context: AgentContext) -> AgentOutput:
        """执行市场竞争分析"""
        product_id = context.metadata.get("product_id")
        
        if not product_id:
            return AgentOutput(
                success=False,
                error="缺少产品ID"
            )

        # 1. 查询竞品数据（新增工具）
        competitors = await self._query_competitors(product_id)
        
        # 2. 分析市场趋势（新增工具）
        market_trend = await self._analyze_market_trend(product_id)
        
        # 3. 计算建议价格
        suggested_price = self._calculate_market_price(competitors, market_trend)
        
        # 4. 生成推理说明
        reasoning = self._generate_reasoning(competitors, market_trend, suggested_price)

        return AgentOutput(
            success=True,
            result={
                "agent": "MarketAgent",
                "product_id": product_id,
                "suggested_price": suggested_price,
                "confidence": 0.75,  # 市场数据不确定性较高
                "reasoning": reasoning,
                "competitor_analysis": competitors,
                "market_trend": market_trend,
            },
            reasoning=reasoning
        )

    async def _query_competitors(self, product_id: str) -> List[Dict[str, Any]]:
        """查询竞品数据"""
        # Mock数据（实际应调用competitor_monitor工具）
        await asyncio.sleep(0.15)
        
        return [
            {
                "competitor": "竞品A",
                "price": 98.0,
                "market_share": 0.35,
                "rating": 4.5,
            },
            {
                "competitor": "竞品B",
                "price": 105.0,
                "market_share": 0.25,
                "rating": 4.3,
            },
            {
                "competitor": "竞品C",
                "price": 92.0,
                "market_share": 0.20,
                "rating": 4.2,
            },
        ]

    async def _analyze_market_trend(self, product_id: str) -> Dict[str, Any]:
        """分析市场趋势"""
        # Mock数据
        await asyncio.sleep(0.1)
        
        return {
            "trend": "上升",  # 上升/下降/稳定
            "demand_change": 0.15,  # 需求增长15%
            "seasonality": "旺季",
            "avg_market_price": 98.3,
        }

    def _calculate_market_price(
        self,
        competitors: List[Dict[str, Any]],
        market_trend: Dict[str, Any]
    ) -> float:
        """基于市场计算建议价格"""
        # 加权平均竞品价格
        total_share = sum(c["market_share"] for c in competitors)
        weighted_price = sum(
            c["price"] * c["market_share"] for c in competitors
        ) / total_share if total_share > 0 else 98.0
        
        # 根据市场趋势调整
        if market_trend["trend"] == "上升":
            # 需求上升，可适当提价
            adjustment = 1.02
        elif market_trend["trend"] == "下降":
            # 需求下降，需降价促销
            adjustment = 0.98
        else:
            adjustment = 1.0
        
        # 略低于加权平均价以获取市场份额
        suggested_price = weighted_price * 0.95 * adjustment
        
        return round(suggested_price, 2)

    def _generate_reasoning(
        self,
        competitors: List[Dict[str, Any]],
        market_trend: Dict[str, Any],
        suggested_price: float
    ) -> str:
        """生成推理说明"""
        avg_price = sum(c["price"] for c in competitors) / len(competitors)
        
        comp_info = "、".join([
            f"{c['competitor']}{c['price']}元" for c in competitors
        ])
        
        return (
            f"市场分析：竞品价格分别为{comp_info}，"
            f"平均价格{avg_price:.1f}元。市场趋势{market_trend['trend']}，"
            f"需求增长{market_trend['demand_change']*100:.0f}%。"
            f"建议定价{suggested_price}元，略低于市场均价以获取份额。"
        )
