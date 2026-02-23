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

from opspilot.pricing.agents.cost_agent import CostAgent
from opspilot.pricing.agents.market_agent import MarketAgent
from opspilot.pricing.agents.profit_agent import ProfitAgent
from opspilot.pricing.agents.pricing_orchestrator import PricingOrchestrator


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
        product = {
            "product_id": "SKU-001",
            "name": "测试产品",
            "cost": 100.0,
            "category": "electronics",
        }
        
        result = await agent.execute(product)
        
        assert result is not None
        assert "suggested_price" in result
        assert result["suggested_price"] >= product["cost"]
    
    @pytest.mark.asyncio
    async def test_cost_with_margin(self, agent):
        """测试带毛利的价格计算"""
        product = {
            "product_id": "SKU-002",
            "name": "测试产品",
            "cost": 50.0,
            "target_margin": 0.3,  # 30% 毛利
        }
        
        result = await agent.execute(product)
        
        assert result is not None
        # 价格应该 >= 成本 * (1 + 毛利率)
        min_price = product["cost"] * (1 + product["target_margin"])
        assert result["suggested_price"] >= min_price


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
        product = {
            "product_id": "SKU-001",
            "name": "测试产品",
            "category": "electronics",
        }
        
        result = await agent.execute(product)
        
        assert result is not None
        assert "suggested_price" in result
        assert "market_analysis" in result or "competitor_prices" in result
    
    @pytest.mark.asyncio
    async def test_competitor_analysis(self, agent):
        """测试竞品分析"""
        product = {
            "product_id": "SKU-002",
            "name": "测试产品",
            "competitors": [
                {"name": "竞品A", "price": 150.0},
                {"name": "竞品B", "price": 160.0},
            ],
        }
        
        result = await agent.execute(product)
        
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
        product = {
            "product_id": "SKU-001",
            "name": "测试产品",
            "cost": 100.0,
            "current_price": 150.0,
            "demand_elasticity": -1.5,  # 价格弹性
        }
        
        result = await agent.execute(product)
        
        assert result is not None
        assert "suggested_price" in result
        assert "expected_profit" in result or "profit_margin" in result
    
    @pytest.mark.asyncio
    async def test_maximize_profit(self, agent):
        """测试利润最大化"""
        product = {
            "product_id": "SKU-002",
            "name": "测试产品",
            "cost": 80.0,
            "price_range": {"min": 100, "max": 200},
        }
        
        result = await agent.execute(product)
        
        assert result is not None
        suggested = result["suggested_price"]
        assert suggested >= product["price_range"]["min"]
        assert suggested <= product["price_range"]["max"]


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
        product = {
            "product_id": "SKU-001",
            "name": "测试产品",
            "cost": 100.0,
        }
        
        result = await orchestrator.negotiate(product)
        
        assert result is not None
        assert "final_price" in result
        assert "confidence" in result
        assert "agent_votes" in result
    
    @pytest.mark.asyncio
    async def test_agent_votes_structure(self, orchestrator):
        """测试 Agent 投票结构"""
        product = {
            "product_id": "SKU-002",
            "name": "测试产品",
            "cost": 80.0,
        }
        
        result = await orchestrator.negotiate(product)
        
        votes = result["agent_votes"]
        
        assert "cost_agent" in votes
        assert "market_agent" in votes
        assert "profit_agent" in votes
    
    @pytest.mark.asyncio
    async def test_weighted_voting(self, orchestrator):
        """测试加权投票"""
        product = {
            "product_id": "SKU-003",
            "name": "测试产品",
            "cost": 120.0,
        }
        
        result = await orchestrator.negotiate(product)
        
        # 最终价格应该在各 Agent 建议价格的合理范围内
        final_price = result["final_price"]
        votes = result["agent_votes"]
        
        prices = [v["suggested_price"] for v in votes.values()]
        min_price = min(prices)
        max_price = max(prices)
        
        # 允许一定的偏差
        assert final_price >= min_price * 0.8
        assert final_price <= max_price * 1.2
    
    @pytest.mark.asyncio
    async def test_confidence_calculation(self, orchestrator):
        """测试置信度计算"""
        product = {
            "product_id": "SKU-004",
            "name": "测试产品",
            "cost": 100.0,
        }
        
        result = await orchestrator.negotiate(product)
        
        confidence = result["confidence"]
        
        assert 0 <= confidence <= 1
    
    @pytest.mark.asyncio
    async def test_multiple_products(self, orchestrator):
        """测试多产品定价"""
        products = [
            {"product_id": "SKU-001", "name": "产品1", "cost": 50.0},
            {"product_id": "SKU-002", "name": "产品2", "cost": 80.0},
            {"product_id": "SKU-003", "name": "产品3", "cost": 120.0},
        ]
        
        results = []
        for product in products:
            result = await orchestrator.negotiate(product)
            results.append(result)
        
        assert len(results) == 3
        for result in results:
            assert "final_price" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
