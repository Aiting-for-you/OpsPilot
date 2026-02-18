"""
定价模块API

提供定价博弈协商的REST API接口
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

from opspilot.pricing.agents import PricingOrchestrator
from opspilot.reliability.token_tracker import TokenTracker


# ==================== 请求模型 ====================

class PricingNegotiateRequest(BaseModel):
    """定价协商请求"""
    product_id: str = Field(..., description="产品ID")
    market_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="市场上下文"
    )
    constraints: Optional[Dict[str, Any]] = Field(
        default=None,
        description="约束条件（成本底线、价格上限等）"
    )


class PricingHistoryRequest(BaseModel):
    """定价历史查询请求"""
    product_id: Optional[str] = Field(None, description="产品ID筛选")
    limit: int = Field(20, description="返回数量限制")


# ==================== 响应模型 ====================

class PricingNegotiateResponse(BaseModel):
    """定价协商响应"""
    trace_id: str = Field(..., description="追踪ID")
    product_id: str = Field(..., description="产品ID")
    final_price: float = Field(..., description="最终定价")
    confidence: float = Field(..., description="置信度")
    arbitration_method: str = Field(..., description="仲裁方法")
    agent_votes: Dict[str, Any] = Field(..., description="Agent投票详情")
    negotiation_summary: str = Field(..., description="博弈摘要")
    processing_time_ms: float = Field(..., description="处理时长（毫秒）")
    tokens_used: int = Field(..., description="Token消耗")
    timestamp: str = Field(..., description="时间戳")


class PricingHistoryResponse(BaseModel):
    """定价历史响应"""
    history: List[Dict[str, Any]] = Field(..., description="历史记录")
    total: int = Field(..., description="总数量")


class AgentStatusResponse(BaseModel):
    """Agent状态响应"""
    agents: Dict[str, Any] = Field(..., description="Agent状态")


# ==================== API处理函数 ====================

class PricingAPI:
    """定价API处理器"""
    
    def __init__(self):
        # 初始化博弈协调器（复用TokenTracker）
        self.token_tracker = TokenTracker()
        self.orchestrator = PricingOrchestrator(self.token_tracker)
    
    async def negotiate(self, request: PricingNegotiateRequest) -> PricingNegotiateResponse:
        """
        启动定价博弈协商
        
        Args:
            request: 定价协商请求
        
        Returns:
            定价协商响应
        """
        result = await self.orchestrator.negotiate_price(
            product_id=request.product_id,
            market_context=request.market_context,
            constraints=request.constraints
        )
        
        return PricingNegotiateResponse(**result)
    
    async def get_history(self, request: PricingHistoryRequest) -> PricingHistoryResponse:
        """
        查询定价历史
        
        Args:
            request: 历史查询请求
        
        Returns:
            历史记录响应
        """
        history = self.orchestrator.get_negotiation_history(limit=request.limit)
        
        # 按product_id筛选
        if request.product_id:
            history = [
                h for h in history
                if h.get("product_id") == request.product_id
            ]
        
        return PricingHistoryResponse(
            history=history,
            total=len(history)
        )
    
    async def get_agent_status(self) -> AgentStatusResponse:
        """
        获取Agent状态
        
        Returns:
            Agent状态响应
        """
        return AgentStatusResponse(
            agents={
                "CostAgent": {
                    "status": "ready",
                    "weight": 0.30,
                    "description": "成本分析Agent",
                },
                "MarketAgent": {
                    "status": "ready",
                    "weight": 0.40,
                    "description": "市场竞争Agent",
                },
                "ProfitAgent": {
                    "status": "ready",
                    "weight": 0.30,
                    "description": "利润优化Agent",
                },
                "PricingOrchestrator": {
                    "status": "ready",
                    "negotiations_completed": len(self.orchestrator.negotiation_history),
                    "description": "博弈协调器",
                }
            }
        )


# 全局实例
pricing_api = PricingAPI()
