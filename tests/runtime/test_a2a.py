"""
A2A 协议模块单元测试
"""
import pytest
import asyncio
import time

from opspilot.runtime.a2a import (
    AgentStatus,
    MessageType,
    AgentSkill,
    AgentCard,
    A2AMessage,
    AgentRegistry,
    LocalAgentRegistry,
    A2AClient,
    A2AServer,
    create_agent_card,
    get_registry,
)


class TestAgentSkill:
    """Agent 技能测试"""

    def test_create_skill(self):
        """测试创建技能"""
        skill = AgentSkill(
            id="query_supplier",
            name="查询供应商",
            description="根据条件查询供应商信息",
            tags=["erp", "供应商"],
        )
        
        assert skill.id == "query_supplier"
        assert skill.name == "查询供应商"
        assert "erp" in skill.tags

    def test_to_dict(self):
        """测试转换为字典"""
        skill = AgentSkill(
            id="skill-1",
            name="技能",
            description="描述",
            input_schema={"type": "object"},
            tags=["tag1"],
        )
        
        data = skill.to_dict()
        
        assert data["id"] == "skill-1"
        assert data["input_schema"] == {"type": "object"}

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "id": "skill-1",
            "name": "技能",
            "description": "描述",
            "input_schema": {"type": "object"},
            "tags": ["tag1"],
        }
        
        skill = AgentSkill.from_dict(data)
        
        assert skill.id == "skill-1"
        assert skill.input_schema == {"type": "object"}


class TestAgentCard:
    """Agent 名片测试"""

    @pytest.fixture
    def card(self):
        return AgentCard(
            agent_id="agent-001",
            name="IntentAgent",
            description="意图识别 Agent",
            skills=[
                AgentSkill(id="intent_recognition", name="意图识别", description="识别用户意图"),
            ],
            endpoints={"http": "http://localhost:8001"},
        )

    def test_create_card(self, card):
        """测试创建名片"""
        assert card.agent_id == "agent-001"
        assert card.name == "IntentAgent"
        assert len(card.skills) == 1
        assert card.status == AgentStatus.ONLINE

    def test_to_dict(self, card):
        """测试转换为字典"""
        data = card.to_dict()
        
        assert data["agent_id"] == "agent-001"
        assert data["name"] == "IntentAgent"
        assert len(data["skills"]) == 1
        assert data["status"] == "online"

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "agent_id": "agent-002",
            "name": "PlanningAgent",
            "description": "规划 Agent",
            "skills": [
                {"id": "planning", "name": "规划", "description": "制定执行计划"},
            ],
            "endpoints": {},
            "status": "online",
        }
        
        card = AgentCard.from_dict(data)
        
        assert card.agent_id == "agent-002"
        assert len(card.skills) == 1
        assert card.status == AgentStatus.ONLINE


class TestA2AMessage:
    """A2A 消息测试"""

    def test_create_message(self):
        """测试创建消息"""
        message = A2AMessage(
            sender_id="agent-001",
            receiver_id="agent-002",
            message_type=MessageType.REQUEST,
            skill_id="query_supplier",
            content={"region": "华南"},
        )
        
        assert message.sender_id == "agent-001"
        assert message.receiver_id == "agent-002"
        assert message.message_type == MessageType.REQUEST
        assert message.content == {"region": "华南"}
        assert message.message_id is not None

    def test_to_dict(self):
        """测试转换为字典"""
        message = A2AMessage(
            message_id="msg-123",
            sender_id="agent-001",
            receiver_id="agent-002",
            message_type=MessageType.RESPONSE,
            content={"result": "success"},
        )
        
        data = message.to_dict()
        
        assert data["message_id"] == "msg-123"
        assert data["message_type"] == "response"

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "message_id": "msg-123",
            "sender_id": "agent-001",
            "receiver_id": "agent-002",
            "message_type": "request",
            "skill_id": "query_supplier",
            "content": {"region": "华南"},
        }
        
        message = A2AMessage.from_dict(data)
        
        assert message.message_id == "msg-123"
        assert message.message_type == MessageType.REQUEST

    def test_create_response(self):
        """测试创建响应消息"""
        request = A2AMessage(
            message_id="msg-123",
            sender_id="agent-001",
            receiver_id="agent-002",
            message_type=MessageType.REQUEST,
            skill_id="query_supplier",
            content={"region": "华南"},
        )
        
        response = request.create_response(
            content={"suppliers": ["SUP001"]},
            sender_id="agent-002",
        )
        
        assert response.sender_id == "agent-002"
        assert response.receiver_id == "agent-001"
        assert response.message_type == MessageType.RESPONSE
        assert response.skill_id == "query_supplier"


class TestLocalAgentRegistry:
    """本地 Agent 注册中心测试"""

    @pytest.fixture
    def registry(self):
        return LocalAgentRegistry()

    @pytest.fixture
    def agent_card(self):
        return AgentCard(
            agent_id="agent-001",
            name="TestAgent",
            description="测试 Agent",
            skills=[
                AgentSkill(
                    id="skill-1",
                    name="技能1",
                    description="测试技能",
                    tags=["erp", "查询"],
                ),
            ],
        )

    @pytest.mark.asyncio
    async def test_register(self, registry, agent_card):
        """测试注册 Agent"""
        result = await registry.register(agent_card)
        
        assert result is True
        assert "agent-001" in registry._agents

    @pytest.mark.asyncio
    async def test_unregister(self, registry, agent_card):
        """测试注销 Agent"""
        await registry.register(agent_card)
        result = await registry.unregister("agent-001")
        
        assert result is True
        assert "agent-001" not in registry._agents

    @pytest.mark.asyncio
    async def test_discover_by_skill(self, registry, agent_card):
        """测试按技能发现 Agent"""
        await registry.register(agent_card)
        
        agents = await registry.discover(skill_id="skill-1")
        assert len(agents) == 1
        
        agents = await registry.discover(skill_id="nonexistent")
        assert len(agents) == 0

    @pytest.mark.asyncio
    async def test_discover_by_tags(self, registry, agent_card):
        """测试按标签发现 Agent"""
        await registry.register(agent_card)
        
        agents = await registry.discover(tags=["erp"])
        assert len(agents) == 1
        
        agents = await registry.discover(tags=["nonexistent"])
        assert len(agents) == 0

    @pytest.mark.asyncio
    async def test_get_agent(self, registry, agent_card):
        """测试获取 Agent"""
        await registry.register(agent_card)
        
        card = await registry.get_agent("agent-001")
        assert card is not None
        assert card.name == "TestAgent"
        
        card = await registry.get_agent("nonexistent")
        assert card is None

    @pytest.mark.asyncio
    async def test_heartbeat(self, registry, agent_card):
        """测试心跳"""
        await registry.register(agent_card)
        
        result = await registry.heartbeat("agent-001")
        assert result is True
        
        # 检查心跳时间更新
        assert "agent-001" in registry._heartbeats

    @pytest.mark.asyncio
    async def test_cleanup_stale(self, registry, agent_card):
        """测试清理过期 Agent"""
        await registry.register(agent_card)
        
        # 模拟过期
        registry._heartbeats["agent-001"] = time.time() - 400
        
        cleaned = await registry.cleanup_stale(timeout=300)
        
        assert cleaned == 1
        assert "agent-001" not in registry._agents


class TestA2AClient:
    """A2A 客户端测试"""

    @pytest.fixture
    def registry(self):
        return LocalAgentRegistry()

    @pytest.fixture
    def client(self, registry):
        return A2AClient(agent_id="client-001", registry=registry)

    @pytest.fixture
    def target_agent(self):
        return AgentCard(
            agent_id="agent-001",
            name="TargetAgent",
            description="目标 Agent",
            endpoints={"http": "http://localhost:8001"},
        )

    @pytest.mark.asyncio
    async def test_discover_agents(self, client, registry, target_agent):
        """测试发现 Agent"""
        await registry.register(target_agent)
        
        agents = await client.discover_agents()
        assert len(agents) == 1

    @pytest.mark.asyncio
    async def test_send_message_no_target(self, client):
        """测试发送消息（无目标）"""
        message = A2AMessage(
            sender_id="client-001",
            receiver_id="nonexistent",
            message_type=MessageType.REQUEST,
        )
        
        response = await client.send_message(message)
        assert response is None


class TestA2AServer:
    """A2A 服务端测试"""

    @pytest.fixture
    def registry(self):
        return LocalAgentRegistry()

    @pytest.fixture
    def agent_card(self):
        return AgentCard(
            agent_id="server-001",
            name="ServerAgent",
            description="服务端 Agent",
            skills=[
                AgentSkill(id="test_skill", name="测试技能", description="测试"),
            ],
        )

    @pytest.fixture
    def server(self, registry, agent_card):
        return A2AServer(agent_card, registry)

    @pytest.mark.asyncio
    async def test_start_stop(self, server, registry):
        """测试启动和停止"""
        await server.start()
        assert "server-001" in registry._agents
        
        await server.stop()
        assert "server-001" not in registry._agents

    @pytest.mark.asyncio
    async def test_register_skill_handler(self, server):
        """测试注册技能处理器"""
        async def handler(content):
            return {"processed": True, "input": content}
        
        server.register_skill_handler("test_skill", handler)
        
        assert "test_skill" in server._skill_handlers

    @pytest.mark.asyncio
    async def test_handle_heartbeat(self, server, registry):
        """测试处理心跳消息"""
        await server.start()
        
        message = A2AMessage(
            sender_id="client-001",
            message_type=MessageType.HEARTBEAT,
        )
        
        response = await server.handle_message(message)
        
        assert response is not None
        assert response.message_type == MessageType.RESPONSE
        assert response.content["status"] == "ok"

    @pytest.mark.asyncio
    async def test_handle_skill_request(self, server):
        """测试处理技能请求"""
        async def handler(content):
            return {"result": f"处理了: {content}"}
        
        server.register_skill_handler("test_skill", handler)
        
        message = A2AMessage(
            sender_id="client-001",
            message_type=MessageType.REQUEST,
            skill_id="test_skill",
            content="测试内容",
        )
        
        response = await server.handle_message(message)
        
        assert response is not None
        assert response.message_type == MessageType.RESPONSE
        assert "处理了" in response.content["result"]

    @pytest.mark.asyncio
    async def test_handle_unknown_skill(self, server):
        """测试处理未知技能请求"""
        message = A2AMessage(
            sender_id="client-001",
            message_type=MessageType.REQUEST,
            skill_id="unknown_skill",
        )
        
        response = await server.handle_message(message)
        
        assert response is None


class TestCreateAgentCard:
    """创建 Agent 名片测试"""

    def test_create_agent_card(self):
        """测试创建 Agent 名片"""
        card = create_agent_card(
            agent_id="test-001",
            name="TestAgent",
            description="测试 Agent",
            skills=[
                {"id": "skill-1", "name": "技能", "description": "描述"},
            ],
            endpoints={"http": "http://localhost:8001"},
        )
        
        assert card.agent_id == "test-001"
        assert len(card.skills) == 1
        assert card.endpoints["http"] == "http://localhost:8001"


class TestGetRegistry:
    """获取注册中心测试"""

    def test_get_registry(self):
        """测试获取全局注册中心"""
        registry1 = get_registry()
        registry2 = get_registry()
        
        assert registry1 is registry2
