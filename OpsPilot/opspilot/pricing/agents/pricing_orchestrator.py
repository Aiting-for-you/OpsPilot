"""
定价博弈协调器

职责：
- 协调三个定价Agent的博弈协商
- 实现加权投票仲裁机制
- 处理价格冲突与调和
"""
from typing import Dict, Any, List, Optional
import asyncio
import time
from datetime import datetime

from opspilot.pricing.agents.cost_agent import CostAgent
from opspilot.pricing.agents.market_agent import MarketAgent
from opspilot.pricing.agents.profit_agent import ProfitAgent
from opspilot.agents.base import AgentContext
from opspilot.reliability.token_tracker import TokenTracker


class PricingOrchestrator:
    """
    定价博弈协调器
    
    通过多Agent协作博弈，实现智能定价决策
    """
    
    def __init__(self, token_tracker: Optional[TokenTracker] = None):
        """
        初始化博弈协调器
        
        Args:
            token_tracker: Token追踪器（复用）
        """
        # 初始化三个定价Agent
        self.cost_agent = CostAgent()
        self.market_agent = MarketAgent()
        self.profit_agent = ProfitAgent()
        
        # Token追踪（复用现有功能）
        self.token_tracker = token_tracker or TokenTracker()
        
        # Agent权重（可配置）
        self.weights = {
            "CostAgent": 0.30,      # 成本权重
            "MarketAgent": 0.40,    # 市场权重（最重要）
            "ProfitAgent": 0.30,    # 利润权重
        }
        
        # 历史记录
        self.negotiation_history: List[Dict[str, Any]] = []
    
    async def negotiate_price(
        self,
        product_id: str,
        market_context: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        启动定价博弈协商
        
        Args:
            product_id: 产品ID
            market_context: 市场上下文（可选）
            constraints: 约束条件（可选）
        
        Returns:
            定价协商结果
        """
        start_time = time.time()
        trace_id = f"pricing_{product_id}_{int(time.time()*1000)}"
        
        # 1. 并行调用三个Agent（AgentScope消息驱动）
        context = AgentContext(
            task_id=trace_id,
            state=None,
            metadata={
                "product_id": product_id,
                "market_context": market_context or {},
                "constraints": constraints or {},
            }
        )
        
        # AgentScope风格的并行执行
        results = await asyncio.gather(
            self.cost_agent._execute(context),
            self.market_agent._execute(context),
            self.profit_agent._execute(context),
            return_exceptions=True
        )
        
        # 2. 收集Agent投票
        agent_votes = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                agent_votes[f"Agent{i}"] = {
                    "error": str(result),
                    "suggested_price": None,
                }
            else:
                agent_name = result.result.get("agent", f"Agent{i}")
                agent_votes[agent_name] = {
                    "suggested_price": result.result.get("suggested_price"),
                    "confidence": result.result.get("confidence", 0.5),
                    "reasoning": result.reasoning,
                }
        
        # 3. 博弈仲裁
        arbitration = self._arbitrate(agent_votes)
        
        # 4. 记录Token消耗（复用TokenTracker）
        total_tokens = sum(
            result.metadata.get("tokens_used", 0) 
            for result in results 
            if hasattr(result, "metadata")
        )
        
        with self.token_tracker.track(
            agent_name="PricingOrchestrator",
            task_id=trace_id,
            metadata={
                "model": "pricing-model",
                "operation": "pricing_negotiation"
            }
        ):
            pass
        
        # 5. 生成最终结果
        processing_time = time.time() - start_time
        
        result = {
            "trace_id": trace_id,
            "product_id": product_id,
            "final_price": arbitration["price"],
            "confidence": arbitration["confidence"],
            "arbitration_method": arbitration["method"],
            "agent_votes": agent_votes,
            "negotiation_summary": self._generate_summary(agent_votes, arbitration),
            "processing_time_ms": processing_time * 1000,
            "tokens_used": total_tokens,
            "timestamp": datetime.now().isoformat(),
        }
        
        # 保存历史记录
        self.negotiation_history.append(result)
        
        return result
    
    def _arbitrate(self, agent_votes: Dict[str, Any]) -> Dict[str, Any]:
        """
        博弈仲裁
        
        Args:
            agent_votes: Agent投票结果
        
        Returns:
            仲裁结果
        """
        # 提取有效价格
        prices = []
        for agent_name, vote in agent_votes.items():
            price = vote.get("suggested_price")
            if price is not None:
                weight = self.weights.get(agent_name, 0.33)
                confidence = vote.get("confidence", 0.5)
                prices.append({
                    "agent": agent_name,
                    "price": price,
                    "weight": weight,
                    "confidence": confidence,
                    "weighted_score": price * weight * confidence,
                })
        
        if not prices:
            return {
                "price": 0.0,
                "confidence": 0.0,
                "method": "no_valid_votes",
            }
        
        # 方法1: 加权平均
        total_weighted_score = sum(p["weighted_score"] for p in prices)
        total_weight = sum(p["weight"] * p["confidence"] for p in prices)
        
        if total_weight > 0:
            weighted_avg_price = total_weighted_score / total_weight
        else:
            weighted_avg_price = sum(p["price"] for p in prices) / len(prices)
        
        # 方法2: 中位数（降低极端值影响）
        sorted_prices = sorted([p["price"] for p in prices])
        median_price = sorted_prices[len(sorted_prices) // 2]
        
        # 方法3: 选择最接近加权平均的价格（倾向具体建议）
        closest_price = min(
            prices,
            key=lambda p: abs(p["price"] - weighted_avg_price)
        )["price"]
        
        # 综合决策：40%加权平均 + 30%中位数 + 30%最接近价格
        final_price = (
            weighted_avg_price * 0.4 + 
            median_price * 0.3 + 
            closest_price * 0.3
        )
        
        # 计算置信度（基于Agent一致度）
        price_std = (sum((p["price"] - weighted_avg_price)**2 for p in prices) / len(prices)) ** 0.5
        consistency = 1.0 - min(price_std / weighted_avg_price, 1.0)  # 价格一致性
        avg_confidence = sum(p["confidence"] for p in prices) / len(prices)
        
        final_confidence = (consistency * 0.5 + avg_confidence * 0.5)
        
        return {
            "price": round(final_price, 2),
            "confidence": round(final_confidence, 2),
            "method": "weighted_hybrid",
            "weighted_avg": round(weighted_avg_price, 2),
            "median": median_price,
            "closest": closest_price,
        }
    
    def _generate_summary(
        self,
        agent_votes: Dict[str, Any],
        arbitration: Dict[str, Any]
    ) -> str:
        """生成博弈摘要"""
        vote_lines = []
        for agent_name, vote in agent_votes.items():
            price = vote.get("suggested_price", "N/A")
            confidence = vote.get("confidence", 0)
            vote_lines.append(f"{agent_name}: {price}元（置信度{confidence:.0%}）")
        
        votes_str = "；".join(vote_lines)
        
        return (
            f"博弈协商：{votes_str}。"
            f"仲裁方法：加权混合（40%加权平均+30%中位数+30%最接近价格）。"
            f"最终定价{arbitration['price']}元，置信度{arbitration['confidence']:.0%}。"
        )
    
    def get_negotiation_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取博弈历史记录"""
        return self.negotiation_history[-limit:]
    
    def clear_history(self):
        """清空历史记录"""
        self.negotiation_history.clear()
