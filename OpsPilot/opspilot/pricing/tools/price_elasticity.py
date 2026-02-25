"""
价格弹性分析工具

职责：
- 计算价格弹性系数
- 预测价格变化对销量的影响
- 优化定价策略
"""
from typing import Dict, Any
import asyncio
from datetime import datetime

from opspilot.tools.base import (
    BaseToolServer,
    ToolSchema,
    ToolResult,
    ToolContext,
)


# Mock价格弹性数据
MOCK_ELASTICITY = {
    "PROD001": {
        "elasticity": -1.2,
        "interpretation": "弹性较大",
        "price_range": {"min": 80.0, "max": 120.0},
        "optimal_price": 95.0,
        "sensitivity": "高",
    },
}


class PriceElasticityTool(BaseToolServer):
    """
    价格弹性分析工具
    
    分析价格变动对需求的影响
    """
    
    def __init__(self):
        super().__init__(
            name="price-elasticity",
            description="价格弹性分析：计算弹性系数、预测销量变化、优化定价"
        )
        self._register_tools()
    
    def _register_tools(self):
        """注册工具"""
        
        @self.register_tool(ToolSchema(
            name="calculate_elasticity",
            description="计算价格弹性系数",
            input_schema={
                "type": "object",
                "required": ["product_id"],
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "产品ID"
                    }
                }
            }
        ))
        async def calculate_elasticity_tool(
            params: Dict[str, Any],
            context: ToolContext
        ) -> ToolResult:
            product_id = params.get("product_id", "")
            
            # 模拟延迟
            await asyncio.sleep(0.1)
            
            # 查询Mock数据
            elasticity_data = MOCK_ELASTICITY.get(product_id)
            
            if not elasticity_data:
                # 生成默认数据
                elasticity_data = {
                    "elasticity": -1.0,
                    "interpretation": "单位弹性",
                    "price_range": {"min": 80.0, "max": 120.0},
                    "optimal_price": 100.0,
                    "sensitivity": "中等",
                }
            
            return ToolResult.success({
                "product_id": product_id,
                **elasticity_data,
                "timestamp": datetime.now().isoformat(),
            })
        
        @self.register_tool(ToolSchema(
            name="predict_demand_change",
            description="预测价格变化对需求的影响",
            input_schema={
                "type": "object",
                "required": ["product_id", "price_change"],
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "产品ID"
                    },
                    "price_change": {
                        "type": "number",
                        "description": "价格变化百分比（如10表示涨价10%）"
                    },
                    "base_sales": {
                        "type": "integer",
                        "description": "基准销量",
                        "default": 1000
                    }
                }
            }
        ))
        async def predict_demand_change_tool(
            params: Dict[str, Any],
            context: ToolContext
        ) -> ToolResult:
            product_id = params.get("product_id", "")
            price_change_pct = params.get("price_change", 0) / 100
            base_sales = params.get("base_sales", 1000)
            
            # 模拟延迟
            await asyncio.sleep(0.1)
            
            # 获取弹性系数
            elasticity_data = MOCK_ELASTICITY.get(product_id, {"elasticity": -1.0})
            elasticity = elasticity_data["elasticity"]
            
            # 计算需求变化
            demand_change_pct = price_change_pct * elasticity
            new_sales = int(base_sales * (1 + demand_change_pct))
            
            # 计算收入变化
            price_factor = 1 + price_change_pct
            old_revenue = base_sales * 100  # 假设原价100元
            new_revenue = new_sales * (100 * price_factor)
            revenue_change_pct = (new_revenue - old_revenue) / old_revenue * 100
            
            return ToolResult.success({
                "product_id": product_id,
                "price_change_pct": price_change_pct * 100,
                "elasticity": elasticity,
                "demand_change_pct": demand_change_pct * 100,
                "base_sales": base_sales,
                "predicted_sales": new_sales,
                "revenue_change": {
                    "old_revenue": old_revenue,
                    "new_revenue": new_revenue,
                    "change_pct": round(revenue_change_pct, 2),
                },
                "recommendation": self._generate_recommendation(
                    price_change_pct,
                    demand_change_pct,
                    revenue_change_pct
                ),
                "timestamp": datetime.now().isoformat(),
            })
    
    def _generate_recommendation(
        self,
        price_change: float,
        demand_change: float,
        revenue_change: float
    ) -> str:
        """生成定价建议"""
        if price_change > 0:
            if revenue_change > 0:
                return "涨价可增加收入，建议实施"
            else:
                return "涨价将减少收入，不建议实施"
        else:
            if revenue_change > 0:
                return "降价可增加收入，建议促销"
            else:
                return "降价将减少收入，不建议降价"
    
    async def health_check(self) -> bool:
        """健康检查"""
        return True


# 便捷函数
def create_price_elasticity_tool() -> PriceElasticityTool:
    """创建价格弹性分析工具"""
    return PriceElasticityTool()
