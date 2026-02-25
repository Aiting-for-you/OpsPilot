"""
AgentScope集成测试

测试消息中心、Actor模式和协作模式。
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch

from opspilot.agents.msg_hub import (
    MessageType,
    AgentMessage,
    MessageSubscriber,
    MessageHub,
    create_message,
    get_message_hub,
)
from opspilot.agents.actor import (
    ActorState,
    ActorStats,
    BaseActor,
    IntentActor,
    PlanActor,
    ExecActor,
    VerifyActor,
    ActorRegistry,
    create_actor,
)
from opspilot.agents.collaboration import (
    CollaborationMode,
    CollaborationContext,
    CollaborationResult,
    SequentialCollaboration,
    ParallelCollaboration,
    ConditionalCollaboration,
    PipelineCollaboration,
    CollaborationOrchestrator,
    create_orchestrator,
    run_collaboration,
)
from opspilot.agents.base import AgentRole, AgentConfig


# ============== 消息中心测试 ==============

class TestAgentMessage:
    """测试Agent消息"""
    
    def test_create_message(self):
        """测试创建消息"""
        msg = AgentMessage(
            name="test_agent",
            content={"data": "value"},
        )
        
        assert msg.name == "test_agent"
        assert msg.content == {"data": "value"}
        assert msg.message_id is not None
        assert msg.timestamp > 0
    
    def test_message_serialization(self):
        """测试消息序列化"""
        msg = AgentMessage(
            name="test",
            content="hello",
            msg_type=MessageType.AGENT_MESSAGE,
            sender="agent1",
            receiver="agent2",
        )
        
        data = msg.to_dict()
        assert data["name"] == "test"
        assert data["sender"] == "agent1"
        
        restored = AgentMessage.from_dict(data)
        assert restored.name == msg.name
        assert restored.sender == msg.sender
    
    def test_message_reply(self):
        """测试消息回复"""
        original = AgentMessage(
            name="agent1",
            content="question",
            sender="agent1",
            trace_id="trace123",
        )
        
        reply = original.reply("answer", sender="agent2")
        
        assert reply.sender == "agent2"
        assert reply.receiver == "agent1"
        assert reply.reply_to == original.message_id
        assert reply.trace_id == original.trace_id


class TestMessageHub:
    """测试消息中心"""
    
    @pytest.fixture
    def hub(self):
        """创建消息中心"""
        hub = MessageHub()
        hub._subscribers.clear()
        hub._history.clear()
        return hub
    
    def test_subscribe(self, hub):
        """测试订阅"""
        hub.subscribe("agent1")
        
        assert "agent1" in hub._subscribers
    
    def test_unsubscribe(self, hub):
        """测试取消订阅"""
        hub.subscribe("agent1")
        hub.unsubscribe("agent1")
        
        assert "agent1" not in hub._subscribers
    
    def test_publish_broadcast(self, hub):
        """测试广播发布"""
        received = []
        
        def handler(msg):
            received.append(msg)
        
        hub.subscribe("agent1", handler)
        hub.subscribe("agent2", handler)
        
        msg = AgentMessage(
            name="test",
            content="broadcast",
            msg_type=MessageType.AGENT_BROADCAST,
        )
        
        count = hub.publish(msg)
        
        assert count == 2
        assert len(received) == 2
    
    def test_send_to_specific_receiver(self, hub):
        """测试发送给特定接收者"""
        received_agent1 = []
        received_agent2 = []
        
        hub.subscribe("agent1", lambda m: received_agent1.append(m))
        hub.subscribe("agent2", lambda m: received_agent2.append(m))
        
        msg = AgentMessage(
            name="test",
            content="private",
            receiver="agent1",
        )
        
        success = hub.send_to(msg, "agent1")
        
        assert success
        assert len(received_agent1) == 1
        assert len(received_agent2) == 0
    
    def test_message_history(self, hub):
        """测试消息历史"""
        hub.enable_history = True
        
        msg = AgentMessage(name="test", content="msg1")
        hub.publish(msg)
        
        history = hub.get_history()
        
        assert len(history) == 1
    
    def test_singleton(self):
        """测试单例模式"""
        hub1 = get_message_hub()
        hub2 = get_message_hub()
        
        assert hub1 is hub2


# ============== Actor模式测试 ==============

class TestBaseActor:
    """测试Actor基类"""
    
    @pytest.fixture
    def actor(self):
        """创建测试Actor"""
        class TestActor(BaseActor):
            async def handle_message(self, msg: AgentMessage):
                return msg.reply(f"processed: {msg.content}", self.name)
        
        return TestActor(
            name="test_actor",
            role=AgentRole.EXECUTION,
        )
    
    def test_actor_initialization(self, actor):
        """测试Actor初始化"""
        assert actor.name == "test_actor"
        assert actor.state == ActorState.IDLE
        assert actor.stats.messages_received == 0
    
    @pytest.mark.asyncio
    async def test_actor_send_message(self, actor):
        """测试Actor发送消息"""
        hub = get_message_hub()
        hub._subscribers.clear()
        hub.subscribe("receiver")
        
        msg = AgentMessage(
            name=actor.name,
            content="test",
            receiver="receiver",
        )
        
        success = await actor.send(msg, "receiver")
        
        assert success
        assert actor.stats.messages_sent == 1
    
    @pytest.mark.asyncio
    async def test_actor_handle_message(self, actor):
        """测试Actor处理消息"""
        msg = AgentMessage(
            name="sender",
            content="hello",
        )
        
        response = await actor.handle_message(msg)
        
        assert response is not None
        assert "processed" in response.content


class TestIntentActor:
    """测试意图识别Actor"""
    
    @pytest.fixture
    def actor(self):
        return IntentActor()
    
    @pytest.mark.asyncio
    async def test_classify_order_create(self, actor):
        """测试识别创建订单意图"""
        msg = AgentMessage(
            name="user",
            content={"query": "我要创建一个采购订单"},
        )
        
        response = await actor.handle_message(msg)
        
        assert response is not None
        assert response.content["intent"] == "order_create"
    
    @pytest.mark.asyncio
    async def test_classify_query(self, actor):
        """测试识别查询意图"""
        msg = AgentMessage(
            name="user",
            content={"query": "查询供应商信息"},
        )
        
        response = await actor.handle_message(msg)
        
        assert response is not None
        assert response.content["intent"] == "query"


class TestPlanActor:
    """测试规划Actor"""
    
    @pytest.fixture
    def actor(self):
        return PlanActor()
    
    @pytest.mark.asyncio
    async def test_generate_plan(self, actor):
        """测试生成计划"""
        msg = AgentMessage(
            name="intent_agent",
            content={"intent": "order_create", "query": "test"},
        )
        
        response = await actor.handle_message(msg)
        
        assert response is not None
        assert "plan" in response.content
        assert len(response.content["plan"]) > 0


class TestExecActor:
    """测试执行Actor"""
    
    @pytest.fixture
    def actor(self):
        return ExecActor()
    
    @pytest.mark.asyncio
    async def test_execute_plan(self, actor):
        """测试执行计划"""
        msg = AgentMessage(
            name="plan_agent",
            content={
                "plan": [
                    {"step": 1, "action": "query"},
                    {"step": 2, "action": "process"},
                ]
            },
        )
        
        response = await actor.handle_message(msg)
        
        assert response is not None
        assert "results" in response.content


class TestActorRegistry:
    """测试Actor注册表"""
    
    def setup_method(self):
        ActorRegistry._actors.clear()
    
    def test_register(self):
        """测试注册"""
        actor = create_actor(AgentRole.INTENT)
        ActorRegistry.register(actor)
        
        assert actor.name in ActorRegistry._actors
    
    def test_unregister(self):
        """测试注销"""
        actor = create_actor(AgentRole.INTENT)
        ActorRegistry.register(actor)
        ActorRegistry.unregister(actor.name)
        
        assert actor.name not in ActorRegistry._actors
    
    def test_get_stats(self):
        """测试获取统计"""
        actor = create_actor(AgentRole.INTENT)
        ActorRegistry.register(actor)
        
        stats = ActorRegistry.get_stats()
        
        assert actor.name in stats


# ============== 协作模式测试 ==============

class TestSequentialCollaboration:
    """测试顺序协作"""
    
    @pytest.fixture
    def collaboration(self):
        actors = {
            "intent": IntentActor(),
            "plan": PlanActor(),
            "exec": ExecActor(),
            "verify": VerifyActor(),
        }
        return SequentialCollaboration(actors)
    
    @pytest.mark.asyncio
    async def test_sequential_execution(self, collaboration):
        """测试顺序执行"""
        context = CollaborationContext(
            task_id="test001",
            query="创建采购订单",
            mode=CollaborationMode.SEQUENTIAL,
        )
        
        result = await collaboration.execute(context)
        
        assert isinstance(result, CollaborationResult)
        assert result.elapsed_time > 0


class TestParallelCollaboration:
    """测试并行协作"""
    
    @pytest.fixture
    def collaboration(self):
        actors = {
            "exec1": ExecActor(name="exec1"),
            "exec2": ExecActor(name="exec2"),
        }
        return ParallelCollaboration(actors)
    
    @pytest.mark.asyncio
    async def test_parallel_execution(self, collaboration):
        """测试并行执行"""
        context = CollaborationContext(
            task_id="test002",
            query="并行执行多个任务",
            mode=CollaborationMode.PARALLEL,
        )
        
        result = await collaboration.execute(context)
        
        assert isinstance(result, CollaborationResult)
        # 并行执行应该比顺序快
        assert result.elapsed_time >= 0


class TestConditionalCollaboration:
    """测试条件分支协作"""
    
    @pytest.fixture
    def collaboration(self):
        actors = {
            "intent": IntentActor(),
            "plan": PlanActor(),
            "exec": ExecActor(),
        }
        return ConditionalCollaboration(actors)
    
    @pytest.mark.asyncio
    async def test_conditional_execution(self, collaboration):
        """测试条件分支执行"""
        context = CollaborationContext(
            task_id="test003",
            query="查询供应商信息",
            mode=CollaborationMode.CONDITIONAL,
        )
        
        result = await collaboration.execute(context)
        
        assert isinstance(result, CollaborationResult)


class TestCollaborationOrchestrator:
    """测试协作编排器"""
    
    @pytest.fixture
    def orchestrator(self):
        return create_orchestrator(
            actor_configs=[
                {"role": AgentRole.INTENT},
                {"role": AgentRole.PLANNING},
                {"role": AgentRole.EXECUTION},
                {"role": AgentRole.VERIFICATION},
            ]
        )
    
    @pytest.mark.asyncio
    async def test_execute_sequential(self, orchestrator):
        """测试顺序执行"""
        result = await orchestrator.execute(
            query="创建采购订单",
            mode=CollaborationMode.SEQUENTIAL,
        )
        
        assert isinstance(result, CollaborationResult)
    
    @pytest.mark.asyncio
    async def test_execute_default_mode(self, orchestrator):
        """测试默认模式执行"""
        result = await orchestrator.execute(
            query="查询供应商",
        )
        
        assert isinstance(result, CollaborationResult)
    
    def test_select_mode(self, orchestrator):
        """测试模式选择"""
        mode1 = orchestrator.select_mode("同时执行多个任务")
        assert mode1 == CollaborationMode.PARALLEL
        
        mode2 = orchestrator.select_mode("创建订单")
        assert mode2 == CollaborationMode.SEQUENTIAL


# ============== 集成测试 ==============

class TestMultiAgentIntegration:
    """多智能体集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流"""
        # 1. 创建编排器
        orchestrator = create_orchestrator(
            actor_configs=[
                {"role": AgentRole.INTENT},
                {"role": AgentRole.PLANNING},
                {"role": AgentRole.EXECUTION},
                {"role": AgentRole.VERIFICATION},
            ]
        )
        
        # 2. 执行任务
        result = await orchestrator.execute(
            query="我要创建一个采购订单，供应商是ABC公司",
            mode=CollaborationMode.SEQUENTIAL,
        )
        
        # 3. 验证结果
        assert isinstance(result, CollaborationResult)
        assert result.context.task_id is not None
        assert len(result.agent_outputs) > 0
    
    @pytest.mark.asyncio
    async def test_message_flow(self):
        """测试消息流"""
        hub = get_message_hub()
        hub.clear_history()
        
        # 创建Actor
        intent_actor = IntentActor()
        plan_actor = PlanActor()
        
        # 发送消息
        msg = create_message(
            name="user",
            content={"query": "创建订单"},
            msg_type=MessageType.TASK_REQUEST,
        )
        
        response = await intent_actor.handle_message(msg)
        
        assert response is not None
        
        # 继续处理
        plan_response = await plan_actor.handle_message(response)
        
        assert plan_response is not None


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

