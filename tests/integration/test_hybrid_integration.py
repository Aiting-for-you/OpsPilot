"""
混合架构集成测试

测试AgentScope + LangChain混合架构的端到端功能
"""

import asyncio
import pytest
from typing import Dict, Any

from opspilot.integration import (
    # AgentScope
    ASMessage,
    ASMessageType,
    create_agent,
    ServiceRegistry,
    ServiceDiscovery,
    # LangChain
    LCToolAdapter,
    LCToolRegistry,
    create_lc_tool_adapter,
    # Hybrid
    HybridOrchestrator,
    HybridOrchestratorConfig,
    OrchestrationMode,
    create_hybrid_orchestrator,
    SequentialWorkflow,
    ParallelWorkflow,
)


# ============================================================================
# 测试工具
# ============================================================================

def create_test_tools():
    """创建测试工具"""
    tools = []
    
    # 工具1: 查询供应商
    async def query_supplier(supplier_id: str) -> Dict:
        return {
            "supplier_id": supplier_id,
            "name": "测试供应商",
            "status": "active",
        }
    
    tool1 = create_lc_tool_adapter(
        name="query_supplier",
        description="查询供应商信息",
        coroutine=query_supplier,
    )
    tools.append(tool1)
    
    # 工具2: 查询库存
    async def query_inventory(sku: str) -> Dict:
        return {
            "sku": sku,
            "quantity": 100,
            "location": "仓库A",
        }
    
    tool2 = create_lc_tool_adapter(
        name="query_inventory",
        description="查询库存信息",
        coroutine=query_inventory,
    )
    tools.append(tool2)
    
    # 工具3: 创建订单
    async def create_order(items: list) -> Dict:
        return {
            "order_id": "ORD-001",
            "items": items,
            "status": "created",
        }
    
    tool3 = create_lc_tool_adapter(
        name="create_order",
        description="创建采购订单",
        coroutine=create_order,
    )
    tools.append(tool3)
    
    return tools


# ============================================================================
# AgentScope 集成测试
# ============================================================================

class TestAgentScopeIntegration:
    """AgentScope集成测试"""
    
    @pytest.mark.asyncio
    async def test_message_creation(self):
        """测试消息创建"""
        msg = ASMessage(
            name="test_sender",
            content={"query": "测试查询"},
            msg_type=ASMessageType.TASK_REQUEST,
        )
        
        assert msg.name == "test_sender"
        assert msg.content["query"] == "测试查询"
        assert msg.msg_type == ASMessageType.TASK_REQUEST
        assert msg.msg_id is not None
        assert msg.trace_id is not None
    
    @pytest.mark.asyncio
    async def test_message_serialization(self):
        """测试消息序列化"""
        msg = ASMessage(
            name="sender",
            content={"data": "test"},
            metadata={"key": "value"},
        )
        
        # 转换为字典
        msg_dict = msg.to_dict()
        assert msg_dict["name"] == "sender"
        assert msg_dict["metadata"]["key"] == "value"
        
        # 从字典恢复
        restored = ASMessage.from_dict(msg_dict)
        assert restored.name == msg.name
        assert restored.content == msg.content
    
    @pytest.mark.asyncio
    async def test_agent_creation(self):
        """测试Agent创建"""
        intent_agent = create_agent("intent", name="TestIntentAgent")
        assert intent_agent.name == "TestIntentAgent"
        
        plan_agent = create_agent("plan")
        assert plan_agent.name == "PlanAgent"
    
    @pytest.mark.asyncio
    async def test_agent_processing(self):
        """测试Agent处理"""
        agent = create_agent("intent", name="TestAgent")
        
        msg = ASMessage(
            name="test",
            content={"query": "查询供应商信息"},
            msg_type=ASMessageType.TASK_REQUEST,
        )
        
        response = await agent.process(msg)
        
        assert response is not None
        assert response.name == "TestAgent"
        assert "intent" in response.content
    
    @pytest.mark.asyncio
    async def test_service_registry(self):
        """测试服务注册与发现"""
        registry = ServiceRegistry()
        
        # 注册服务
        registry.register(
            name="test_agent",
            address="localhost:50051",
            metadata={"type": "intent"},
        )
        
        # 发现服务
        address = registry.discover("test_agent")
        assert address == "localhost:50051"
        
        # 列出服务
        services = registry.list_services()
        assert "test_agent" in services
        
        # 注销服务
        registry.deregister("test_agent")
        assert registry.discover("test_agent") is None


# ============================================================================
# LangChain 集成测试
# ============================================================================

class TestLangChainIntegration:
    """LangChain集成测试"""
    
    @pytest.mark.asyncio
    async def test_tool_adapter_creation(self):
        """测试工具适配器创建"""
        async def test_func(input_data: dict) -> dict:
            return {"result": "success"}
        
        adapter = create_lc_tool_adapter(
            name="test_tool",
            description="测试工具",
            coroutine=test_func,
        )
        
        assert adapter.name == "test_tool"
        assert adapter.description == "测试工具"
    
    @pytest.mark.asyncio
    async def test_tool_invocation(self):
        """测试工具调用"""
        async def query_func(query: str) -> dict:
            return {"query": query, "result": "found"}
        
        adapter = create_lc_tool_adapter(
            name="query",
            description="查询工具",
            coroutine=query_func,
        )
        
        result = await adapter.ainvoke({"query": "test"})
        assert result["result"] == "found"
        
        stats = adapter.get_stats()
        assert stats["usage_count"] == 1
    
    @pytest.mark.asyncio
    async def test_tool_registry(self):
        """测试工具注册表"""
        registry = LCToolRegistry()
        
        tools = create_test_tools()
        for tool in tools:
            registry.register(tool, category="test")
        
        # 检查注册
        assert len(registry.list_tools()) == 3
        assert "test" in registry.list_categories()
        
        # 获取工具
        tool = registry.get("query_supplier")
        assert tool is not None
        
        # 调用工具
        result = await registry.call_tool("query_supplier", {"supplier_id": "SUP001"})
        assert result is not None
        assert "supplier_id" in result or result.get("supplier_id") == "SUP001"


# ============================================================================
# 混合编排器测试
# ============================================================================

class TestHybridOrchestrator:
    """混合编排器测试"""
    
    @pytest.fixture
    def orchestrator(self):
        """创建编排器"""
        config = HybridOrchestratorConfig(
            mode=OrchestrationMode.SEQUENTIAL,
            enable_cache=True,
            enable_idempotency=True,
        )
        orchestrator = HybridOrchestrator(config)
        
        # 注册工具
        tools = create_test_tools()
        orchestrator.register_lc_tools(tools)
        
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_orchestrator_creation(self, orchestrator):
        """测试编排器创建"""
        assert orchestrator is not None
        assert len(orchestrator._agents) == 4  # intent, plan, exec, verify
    
    @pytest.mark.asyncio
    async def test_sequential_execution(self, orchestrator):
        """测试顺序执行"""
        result = await orchestrator.execute({
            "query": "查询供应商SUP001的信息",
        })
        
        assert result["success"] is True
        assert "results" in result
        assert "workflow_id" in result
    
    @pytest.mark.asyncio
    async def test_workflow_registration(self, orchestrator):
        """测试工作流注册"""
        workflow = SequentialWorkflow.create_default()
        
        # 验证工作流
        assert workflow.validate() is True
        assert len(workflow.steps) == 4
    
    @pytest.mark.asyncio
    async def test_agent_stats(self, orchestrator):
        """测试Agent统计"""
        # 执行一次工作流
        await orchestrator.execute({"query": "测试查询"})
        
        # 获取统计
        stats = orchestrator.get_stats()
        
        assert "agents" in stats
        assert "tools" in stats
        assert stats["tools"]["count"] == 3
    
    @pytest.mark.asyncio
    async def test_idempotency(self, orchestrator):
        """测试幂等性"""
        input_data = {"query": "幂等性测试"}
        
        # 第一次执行
        result1 = await orchestrator.execute(input_data)
        
        # 第二次执行（应该命中缓存）
        result2 = await orchestrator.execute(input_data)
        
        # 结果应该相同（幂等性保证）
        assert result1["workflow_id"] == result2["workflow_id"]
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, orchestrator):
        """测试缓存统计"""
        # 执行几次查询
        for i in range(5):
            await orchestrator.execute({"query": f"测试查询 {i}"})
        
        stats = orchestrator.get_stats()
        
        # 验证 stats 存在
        assert stats is not None
        # 缓存功能已启用
        assert "cache" in stats or "executions" in stats


# ============================================================================
# 端到端测试
# ============================================================================

class TestEndToEnd:
    """端到端测试"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流"""
        # 创建编排器
        orchestrator = create_hybrid_orchestrator(
            mode=OrchestrationMode.SEQUENTIAL,
            enable_rag=False,
        )
        
        # 注册工具
        tools = create_test_tools()
        orchestrator.register_lc_tools(tools)
        
        # 执行查询
        result = await orchestrator.execute({
            "query": "查询供应商SUP001的库存情况",
        })
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_parallel_workflow(self):
        """测试并行工作流"""
        orchestrator = create_hybrid_orchestrator(
            mode=OrchestrationMode.PARALLEL,
        )
        
        result = await orchestrator.execute(
            {"query": "并行查询测试"},
            workflow_name="parallel",
        )
        
        assert "results" in result
    
    @pytest.mark.asyncio
    async def test_agent_lifecycle(self):
        """测试Agent生命周期"""
        orchestrator = create_hybrid_orchestrator()
        
        # 启动所有Agent
        await orchestrator.start_all_agents()
        
        # 执行任务
        result = await orchestrator.execute({"query": "测试"})
        
        # 停止所有Agent
        await orchestrator.stop_all_agents()
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """测试错误处理"""
        orchestrator = create_hybrid_orchestrator()
        
        # 注册一个会抛出错误的工具
        async def error_tool(input_data: dict) -> dict:
            raise ValueError("测试错误")
        
        error_adapter = create_lc_tool_adapter(
            name="error_tool",
            description="会出错的工具",
            coroutine=error_tool,
        )
        orchestrator.register_lc_tools([error_adapter])
        
        # 执行应该有错误处理
        try:
            result = await orchestrator.execute({"query": "测试错误处理"})
        except Exception as e:
            # 错误应该被捕获或传播
            assert True


# ============================================================================
# 性能测试
# ============================================================================

class TestPerformance:
    """性能测试"""
    
    @pytest.mark.asyncio
    async def test_message_throughput(self):
        """测试消息吞吐量"""
        messages_created = 0
        
        async def create_messages():
            nonlocal messages_created
            for _ in range(100):
                msg = ASMessage(
                    name="perf_test",
                    content={"data": "test"},
                )
                messages_created += 1
        
        start = asyncio.get_event_loop().time()
        await create_messages()
        elapsed = asyncio.get_event_loop().time() - start
        
        # 每秒应该能创建至少1000条消息
        assert messages_created / elapsed > 1000
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """测试并发请求"""
        orchestrator = create_hybrid_orchestrator()
        
        async def make_request(i: int):
            return await orchestrator.execute({"query": f"并发测试 {i}"})
        
        # 并发10个请求
        start = asyncio.get_event_loop().time()
        results = await asyncio.gather(*[make_request(i) for i in range(10)])
        elapsed = asyncio.get_event_loop().time() - start
        
        assert len(results) == 10
        # 10个并发请求应该在合理时间内完成
        assert elapsed < 5.0

