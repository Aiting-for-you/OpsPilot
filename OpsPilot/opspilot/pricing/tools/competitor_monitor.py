"""
竞品监控工具

职责：
- 查询竞品定价
- 分析市场趋势
- 提供竞争情报
"""
from typing import Dict, Any, List
import asyncio
from datetime import datetime

from opspilot.tools.base import (
    BaseToolServer,
    ToolSchema,
    ToolResult,
    ToolContext,
)


# Mock竞品数据
MOCK_COMPETITORS = {
    "PROD001": [
        {
            "competitor_id": "COMP001",
            "competitor_name": "竞品A",
            "price": 98.0,
            "market_share": 0.35,
            "rating": 4.5,
            "review_count": 1250,
            "last_updated": "2026-02-18",
        },
        {
            "competitor_id": "COMP002",
            "competitor_name": "竞品B",
            "price": 105.0,
            "market_share": 0.25,
            "rating": 4.3,
            "review_count": 980,
            "last_updated": "2026-02-18",
        },
        {
            "competitor_id": "COMP003",
            "competitor_name": "竞品C",
            "price": 92.0,
            "market_share": 0.20,
            "rating": 4.2,
            "review_count": 750,
            "last_updated": "2026-02-18",
        },
    ],
}


class CompetitorMonitorTool(BaseToolServer):
    """
    竞品监控工具
    
    提供竞品定价和市场分析
    """
    
    def __init__(self):
        super().__init__(
            name="competitor-monitor",
            description="竞品监控工具：定价分析、市场趋势、竞争情报"
        )
        self._register_tools()
    
    def _register_tools(self):
        """注册工具"""
        
        @self.register_tool(ToolSchema(
            name="query_competitors",
            description="查询产品竞品信息",
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
        async def query_competitors_tool(
            params: Dict[str, Any],
            context: ToolContext
        ) -> ToolResult:
            product_id = params.get("product_id", "")
            
            # 模拟延迟
            await asyncio.sleep(0.1)
            
            # 查询Mock数据
            competitors = MOCK_COMPETITORS.get(product_id, [])
            
            if not competitors:
                return ToolResult.error(
                    error=f"未找到产品{product_id}的竞品信息",
                    error_code="COMPETITORS_NOT_FOUND"
                )
            
            # 分析统计
            prices = [c["price"] for c in competitors]
            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)
            
            return ToolResult.success({
                "product_id": product_id,
                "competitors": competitors,
                "analysis": {
                    "total_competitors": len(competitors),
                    "avg_price": round(avg_price, 2),
                    "min_price": min_price,
                    "max_price": max_price,
                    "price_range": max_price - min_price,
                },
                "timestamp": datetime.now().isoformat(),
            })
        
        @self.register_tool(ToolSchema(
            name="analyze_market_trend",
            description="分析市场趋势",
            input_schema={
                "type": "object",
                "required": ["product_id"],
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "产品ID"
                    },
                    "days": {
                        "type": "integer",
                        "description": "分析天数",
                        "default": 30
                    }
                }
            }
        ))
        async def analyze_market_trend_tool(
            params: Dict[str, Any],
            context: ToolContext
        ) -> ToolResult:
            product_id = params.get("product_id", "")
            days = params.get("days", 30)
            
            # 模拟延迟
            await asyncio.sleep(0.12)
            
            # Mock趋势数据
            trend_data = {
                "product_id": product_id,
                "trend": "上升",
                "demand_change": 0.15,
                "price_trend": "稳定",
                "seasonality": "旺季",
                "market_size": 50000,
                "growth_rate": 0.08,
                "competition_level": "激烈",
                "insights": [
                    "市场需求持续增长",
                    "竞品价格战激烈",
                    "用户更关注性价比",
                ],
                "period_days": days,
                "timestamp": datetime.now().isoformat(),
            }
            
            return ToolResult.success(trend_data)
    
    async def health_check(self) -> bool:
        """健康检查"""
        return True


# 便捷函数
def create_competitor_monitor() -> CompetitorMonitorTool:
    """创建竞品监控工具"""
    return CompetitorMonitorTool()
