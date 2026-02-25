"""
博弈定价系统测试

测试多 Agent 博弈定价功能：
- 成本 Agent
- 市场 Agent
- 利润 Agent
- 博弈协调
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from opspilot.agents.base import AgentContext, AgentOutput, State
from opspilot.pricing.agents.cost_agent import CostAgent
from opspilot.pricing.agents.market_agent import MarketAgent
from opspilot.pricing.agents.profit_agent import ProfitAgent
from opspilot.pricing.agents.pricing_orchestrator import PricingOrchestrator


@pytest.fixture
def agent_context():
    """创建AgentContext实例"""
    return AgentContext(
        task_id="test-task-001",
        state=State.IDLE,
        user_input="测试输入"
    )


class TestCostAgent:
    """成本 Agent 测试"""
    
    @pytest.fixture
    def agent(self):
        """创建 Agent 实例"""
        return CostAgent()
    
    def test_agent_creation(self, agent):
        """测试 Agent 创建"""
        assert agent is not None
        assert agent.name == "CostAgent"
    
    @pytest.mark.asyncio
    async def test_calculate_base_price(self, agent):
        """测试计算基础价格"""
        context = AgentContext(
            task_id="test-task-001",
            state=State.EXECUTING,
            user_input="计算基础价格",
            metadata={
                "product_id": "SKU-001",
                "name": "测试产品",
                "cost": 100.0,
                "category": "electronics",
            }
        )
        
        result = await agent.execute(context)
        
        assert result is not None
        assert result.success is True
        assert "suggested_price" in result.result
        # 价格应该大于0（成本加成后的价格）
        assert result.result["suggested_price"] > 0
    
    @pytest.mark.asyncio
    async def test_cost_with_margin(self, agent):
        """测试带毛利的价格计算"""
        context = AgentContext(
            task_id="test-task-002",
            state=State.EXECUTING,
            user_input="计算带毛利价格",
            metadata={
                "product_id": "SKU-002",
                "name": "测试产品",
                "cost": 50.0,
                "target_margin": 0.3,  # 30% 毛利
            }
        )
        
        result = await agent.execute(context)
        
        assert result is not None
        assert result.success is True
        # 价格应该 >= 成本 * (1 + 毛利率)
        min_price = 50.0 * (1 + 0.3)
        assert result.result["suggested_price"] >= min_price


class TestMarketAgent:
    """市场 Agent 测试"""
    
    @pytest.fixture
    def agent(self):
        """创建 Agent 实例"""
        return MarketAgent()
    
    def test_agent_creation(self, agent):
        """测试 Agent 创建"""
        assert agent is not None
        assert agent.name == "MarketAgent"
    
    @pytest.mark.asyncio
    async def test_analyze_market_price(self, agent):
        """测试分析市场价格"""
        context = AgentContext(
            task_id="test-task-003",
            state=State.EXECUTING,
            user_input="分析市场价格",
            metadata={
                "product_id": "SKU-001",
                "name": "测试产品",
                "category": "electronics",
            }
        )
        
        result = await agent.execute(context)
        
        assert result is not None
        assert result.success is True
        assert "suggested_price" in result.result
    
    @pytest.mark.asyncio
    async def test_competitor_analysis(self, agent):
        """测试竞品分析"""
        context = AgentContext(
            task_id="test-task-004",
            state=State.EXECUTING,
            user_input="分析竞品",
            metadata={
                "product_id": "SKU-002",
                "name": "测试产品",
                "competitors": [
                    {"name": "竞品A", "price": 150.0},
                    {"name": "竞品B", "price": 160.0},
                ],
            }
        )
        
        result = await agent.execute(context)
        
        assert result is not None


class TestProfitAgent:
    """利润 Agent 测试"""
    
    @pytest.fixture
    def agent(self):
        """创建 Agent 实例"""
        return ProfitAgent()
    
    def test_agent_creation(self, agent):
        """测试 Agent 创建"""
        assert agent is not None
        assert agent.name == "ProfitAgent"
    
    @pytest.mark.asyncio
    async def test_optimize_price(self, agent):
        """测试价格优化"""
        context = AgentContext(
            task_id="test-task-005",
            state=State.EXECUTING,
            user_input="优化价格",
            metadata={
                "product_id": "SKU-001",
                "name": "测试产品",
                "cost": 100.0,
                "current_price": 150.0,
                "demand_elasticity": -1.5,  # 价格弹性
            }
        )
        
        result = await agent.execute(context)
        
        assert result is not None
        assert result.success is True
        assert "suggested_price" in result.result
    
    @pytest.mark.asyncio
    async def test_maximize_profit(self, agent):
        """测试利润最大化"""
        context = AgentContext(
            task_id="test-task-006",
            state=State.EXECUTING,
            user_input="最大化利润",
            metadata={
                "product_id": "SKU-002",
                "name": "测试产品",
                "cost": 80.0,
                "price_range": {"min": 100, "max": 200},
            }
        )
        
        result = await agent.execute(context)
        
        assert result is not None
        assert result.success is True


class TestPricingOrchestrator:
    """定价协调器测试"""
    
    @pytest.fixture
    def orchestrator(self):
        """创建协调器实例"""
        return PricingOrchestrator()
    
    def test_orchestrator_creation(self, orchestrator):
        """测试协调器创建"""
        assert orchestrator is not None
        assert orchestrator.cost_agent is not None
        assert orchestrator.market_agent is not None
        assert orchestrator.profit_agent is not None
    
    @pytest.mark.asyncio
    async def test_negotiate_price(self, orchestrator):
        """测试博弈定价"""
        result = await orchestrator.negotiate_price(
            product_id="SKU-001",
            market_context={"category": "electronics"},
            constraints={"min_margin": 0.1}
        )
        
        assert result is not None
        assert "final_price" in result
        assert "confidence" in result
        assert "agent_votes" in result
    
    @pytest.mark.asyncio
    async def test_agent_votes_structure(self, orchestrator):
        """测试 Agent 投票结构"""
        result = await orchestrator.negotiate_price(
            product_id="SKU-002",
            market_context={},
            constraints={}
        )
        
        votes = result["agent_votes"]
        
        # 检查投票结构
        for agent_name in ["CostAgent", "MarketAgent", "ProfitAgent"]:
            if agent_name in votes:
                assert "suggested_price" in votes[agent_name]
    
    @pytest.mark.asyncio
    async def test_weighted_voting(self, orchestrator):
        """测试加权投票"""
        result = await orchestrator.negotiate_price(
            product_id="SKU-003",
            market_context={},
            constraints={}
        )
        
        # 最终价格应该存在于结果中
        assert "final_price" in result
    
    @pytest.mark.asyncio
    async def test_confidence_calculation(self, orchestrator):
        """测试置信度计算"""
        result = await orchestrator.negotiate_price(
            product_id="SKU-004",
            market_context={},
            constraints={}
        )
        
        assert result is not None
        assert "confidence" in result
    
    @pytest.mark.asyncio
    async def test_multiple_products(self, orchestrator):
        """测试多产品定价"""
        product_ids = ["SKU-001", "SKU-002", "SKU-003"]
        
        results = []
        for product_id in product_ids:
            result = await orchestrator.negotiate_price(
                product_id=product_id,
                market_context={},
                constraints={}
            )
            results.append(result)
        
        assert len(results) == 3
        for result in results:
            assert "final_price" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
