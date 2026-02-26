"""
利润优化Agent

职责：
- 分析价格弹性
- 预测销量
- 最大化利润
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


class ProfitAgent(BaseAgent):
    """
    利润优化Agent

    基于价格弹性和销量预测，最大化利润
    """

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        tool_router: Optional[ToolRouter] = None
    ):
        config = AgentConfig(
            name="ProfitAgent",
            role=AgentRole.EXECUTION,
            description="利润优化Agent，基于价格弹性分析最大化利润",
            temperature=0.4,
        )
        super().__init__(config, llm_client)
        self._tool_router = tool_router

    def set_tool_router(self, router: ToolRouter) -> None:
        """设置工具路由器"""
        self._tool_router = router

    async def _execute(self, context: AgentContext) -> AgentOutput:
        """执行利润优化分析"""
        product_id = context.metadata.get("product_id")
        cost_data = context.metadata.get("cost_data", {})
        
        if not product_id:
            return AgentOutput(
                success=False,
                error="缺少产品ID"
            )

        # 1. 查询价格弹性（新增工具）
        elasticity = await self._query_price_elasticity(product_id)
        
        # 2. 预测销量（新增工具）
        sales_forecast = await self._forecast_sales(product_id)
        
        # 3. 计算最优价格
        optimal_price = self._optimize_profit(
            elasticity,
            sales_forecast,
            cost_data.get("total_cost", 64.0)
        )
        
        # 4. 生成推理说明
        reasoning = self._generate_reasoning(
            elasticity,
            sales_forecast,
            optimal_price
        )

        return AgentOutput(
            success=True,
            result={
                "agent": "ProfitAgent",
                "product_id": product_id,
                "suggested_price": optimal_price["price"],
                "confidence": 0.80,
                "reasoning": reasoning,
                "profit_analysis": {
                    "expected_profit": optimal_price["profit"],
                    "expected_sales": optimal_price["sales"],
                    "profit_margin": optimal_price["margin"],
                },
                "elasticity": elasticity,
                "forecast": sales_forecast,
            },
            reasoning=reasoning
        )

    async def _query_price_elasticity(self, product_id: str) -> Dict[str, Any]:
        """查询价格弹性"""
        # Mock数据
        await asyncio.sleep(0.12)
        
        return {
            "elasticity": -1.2,  # 需求价格弹性系数（负数表示价格上升需求下降）
            "interpretation": "弹性较大",  # 价格变动对销量影响明显
            "price_range": {
                "min": 80.0,
                "max": 120.0,
            },
        }

    async def _forecast_sales(self, product_id: str) -> Dict[str, Any]:
        """预测销量"""
        # Mock数据
        await asyncio.sleep(0.1)
        
        return {
            "base_sales": 1000,  # 基准销量
            "growth_rate": 0.10,  # 增长率
            "seasonality_factor": 1.2,  # 季节性因子
        }

    def _optimize_profit(
        self,
        elasticity: Dict[str, Any],
        sales_forecast: Dict[str, Any],
        unit_cost: float
    ) -> Dict[str, Any]:
        """优化利润计算最优价格"""
        elasticity_coef = elasticity["elasticity"]
        base_sales = sales_forecast["base_sales"]
        seasonality = sales_forecast["seasonality_factor"]
        
        # 简化的利润最大化模型
        # 利润 = (价格 - 成本) * 销量
        # 销量 = 基准销量 * (价格变化影响)
        
        best_profit = 0
        best_price = unit_cost * 1.3  # 初始价格
        
        # 在价格区间内搜索最优价格
        for price in range(80, 121, 5):
            price_float = float(price)
            
            # 计算销量（基于价格弹性）
            price_change = (price_float - 100) / 100  # 相对基准价格的变化
            quantity_change = price_change * elasticity_coef
            quantity = int(base_sales * (1 + quantity_change) * seasonality)
            
            # 计算利润
            profit = (price_float - unit_cost) * quantity
            
            if profit > best_profit:
                best_profit = profit
                best_price = price_float
                best_quantity = quantity
        
        # 计算毛利率
        margin = (best_price - unit_cost) / best_price * 100
        
        return {
            "price": best_price,
            "profit": best_profit,
            "sales": best_quantity,
            "margin": round(margin, 1),
        }

    def _generate_reasoning(
        self,
        elasticity: Dict[str, Any],
        sales_forecast: Dict[str, Any],
        optimal_price: Dict[str, Any]
    ) -> str:
        """生成推理说明"""
        return (
            f"利润优化：价格弹性系数{elasticity['elasticity']:.1f}，"
            f"{elasticity['interpretation']}。基准销量{sales_forecast['base_sales']}件，"
            f"季节性因子{sales_forecast['seasonality_factor']:.1f}。"
            f"建议定价{optimal_price['price']}元，预计销量{optimal_price['sales']}件，"
            f"利润{optimal_price['profit']:.0f}元，毛利率{optimal_price['margin']:.1f}%。"
        )
