"""
Agent 基础模块单元测试
"""
import pytest
import asyncio

from opspilot.agents.base import (
    AgentRole,
    AgentConfig,
    AgentContext,
    AgentOutput,
    MockLLMClient,
    AgentRegistry,
    BaseAgent,
)
from opspilot.core.state_machine import State
from opspilot.utils.exceptions import (
    AgentTimeoutError,
    AgentExecutionError,
)


class TestAgentRole:
    """Agent 角色枚举测试"""

    def test_all_roles_defined(self):
        """测试所有角色已定义"""
        assert AgentRole.INTENT.value == "intent"
        assert AgentRole.PLANNING.value == "planning"
        assert AgentRole.EXECUTION.value == "execution"
        assert AgentRole.VERIFICATION.value == "verification"


class TestAgentConfig:
    """Agent 配置测试"""

    def test_create_config(self):
        """测试创建配置"""
        config = AgentConfig(
            name="TestAgent",
            role=AgentRole.INTENT,
            description="测试Agent"
        )

        assert config.name == "TestAgent"
        assert config.role == AgentRole.INTENT
        assert config.temperature == 0.7
        assert config.max_tokens == 4096

    def test_config_defaults(self):
        """测试配置默认值"""
        config = AgentConfig(
            name="Test",
            role=AgentRole.INTENT
        )

        assert config.model == "default"
        assert config.timeout == 60


class TestAgentContext:
    """Agent 上下文测试"""

    def test_create_context(self):
        """测试创建上下文"""
        context = AgentContext(
            task_id="task-123",
            state=State.INIT,
            user_input="测试输入"
        )

        assert context.task_id == "task-123"
        assert context.state == State.INIT
        assert context.user_input == "测试输入"

    def test_context_with_history(self):
        """测试带历史的上下文"""
        context = AgentContext(
            task_id="task-123",
            state=State.PLANNING,
            history=[
                {"role": "user", "content": "之前的问题"},
                {"role": "assistant", "content": "之前的回答"}
            ]
        )

        assert len(context.history) == 2


class TestAgentOutput:
    """Agent 输出测试"""

    def test_success_output(self):
        """测试成功输出"""
        output = AgentOutput(
            success=True,
            result={"intent": "test"},
            next_state=State.PLANNING,
            reasoning="识别成功"
        )

        assert output.success is True
        assert output.result["intent"] == "test"
        assert output.next_state == State.PLANNING

    def test_failure_output(self):
        """测试失败输出"""
        output = AgentOutput(
            success=False,
            error="执行失败"
        )

        assert output.success is False
        assert output.error == "执行失败"

    def test_to_dict(self):
        """测试转换为字典"""
        output = AgentOutput(
            success=True,
            result={"key": "value"},
            next_state=State.SUCCESS
        )
        data = output.to_dict()

        assert data["success"] is True
        assert data["result"] == {"key": "value"}
        assert data["next_state"] == "SUCCESS"


class TestMockLLMClient:
    """Mock LLM 客户端测试"""

    @pytest.fixture
    def client(self):
        return MockLLMClient()

    @pytest.mark.asyncio
    async def test_generate_default_response(self, client):
        """测试默认响应"""
        response = await client.generate("测试提示")

        assert "Mock" in response

    @pytest.mark.asyncio
    async def test_generate_with_preset(self, client):
        """测试预设响应"""
        client.set_response("测试", "这是预设的测试响应")

        response = await client.generate("这是一个测试问题")

        assert response == "这是预设的测试响应"

    @pytest.mark.asyncio
    async def test_generate_json_default(self, client):
        """测试默认 JSON 响应"""
        response = await client.generate_json("测试")

        assert response["status"] == "mock"

    @pytest.mark.asyncio
    async def test_generate_json_with_preset(self, client):
        """测试预设 JSON 响应"""
        client.set_json_response("意图", {
            "intent_type": "create_order",
            "confidence": 0.9
        })

        response = await client.generate_json("识别意图")

        assert response["intent_type"] == "create_order"
        assert response["confidence"] == 0.9


class TestAgentRegistry:
    """Agent 注册表测试"""

    @pytest.fixture
    def registry(self):
        reg = AgentRegistry()
        reg.clear()
        return reg

    def test_singleton(self):
        """测试单例模式"""
        reg1 = AgentRegistry()
        reg2 = AgentRegistry()

        assert reg1 is reg2

    def test_register_and_get(self, registry):
        """测试注册和获取"""
        from opspilot.agents.intent_agent import MockIntentAgent

        agent = MockIntentAgent()
        registry.register(agent)

        retrieved = registry.get("IntentAgent")

        assert retrieved is agent

    def test_unregister(self, registry):
        """测试注销"""
        from opspilot.agents.intent_agent import MockIntentAgent

        agent = MockIntentAgent()
        registry.register(agent)
        registry.unregister("IntentAgent")

        retrieved = registry.get("IntentAgent")
        assert retrieved is None

    def test_get_by_role(self, registry):
        """测试按角色获取"""
        from opspilot.agents.intent_agent import MockIntentAgent
        from opspilot.agents.plan_agent import MockPlanAgent

        registry.register(MockIntentAgent())
        registry.register(MockPlanAgent())

        intent_agents = registry.get_by_role(AgentRole.INTENT)

        assert len(intent_agents) == 1

    def test_list_all(self, registry):
        """测试列出所有"""
        from opspilot.agents.intent_agent import MockIntentAgent

        registry.register(MockIntentAgent())

        names = registry.list_all()

        assert "IntentAgent" in names


class TestAgentExceptions:
    """Agent 异常测试 - 测试 raise_on_error 参数"""

    @pytest.fixture
    def slow_agent(self):
        """创建超时 Agent"""
        config = AgentConfig(
            name="SlowAgent",
            role=AgentRole.INTENT,
            description="超时测试 Agent",
            timeout=1  # 1秒超时
        )

        class SlowMockLLMClient(MockLLMClient):
            async def generate(self, prompt, system_prompt=None, temperature=0.7, max_tokens=4096):
                await asyncio.sleep(2)  # 模拟慢响应
                return "slow response"

        agent = BaseAgent.__new__(BaseAgent)
        agent.config = config
        agent._llm = SlowMockLLMClient()
        agent._event_bus = None

        # 手动设置 _event_bus
        from opspilot.core.events import EventBus
        agent._event_bus = EventBus.get_instance()

        return agent

    @pytest.fixture
    def error_agent(self):
        """创建错误 Agent"""
        config = AgentConfig(
            name="ErrorAgent",
            role=AgentRole.INTENT,
            description="错误测试 Agent"
        )

        class ErrorMockLLMClient(MockLLMClient):
            async def generate(self, prompt, system_prompt=None, temperature=0.7, max_tokens=4096):
                raise ValueError("LLM 调用失败")

        agent = BaseAgent.__new__(BaseAgent)
        agent.config = config
        agent._llm = ErrorMockLLMClient()

        from opspilot.core.events import EventBus
        agent._event_bus = EventBus.get_instance()

        return agent

    @pytest.mark.asyncio
    async def test_raise_agent_timeout(self, slow_agent):
        """测试 Agent 超时时抛出异常"""
        context = AgentContext(
            task_id="test-timeout",
            state=State.INIT,
            user_input="测试超时"
        )

        # 创建一个会超时的 _execute 方法
        async def slow_execute(ctx):
            await asyncio.sleep(2)
            return AgentOutput(success=True, result={})

        slow_agent._execute = slow_execute

        with pytest.raises(AgentTimeoutError) as exc_info:
            await slow_agent.execute(context, raise_on_error=True)
        assert slow_agent.name in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raise_agent_execution_error(self, error_agent):
        """测试 Agent 执行失败时抛出异常"""
        context = AgentContext(
            task_id="test-error",
            state=State.INIT,
            user_input="测试错误"
        )

        # 创建一个会抛出异常的 _execute 方法
        async def error_execute(ctx):
            raise ValueError("执行失败")

        error_agent._execute = error_execute

        with pytest.raises(AgentExecutionError) as exc_info:
            await error_agent.execute(context, raise_on_error=True)
        assert error_agent.name in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_no_raise_returns_error_output(self, error_agent):
        """测试不抛出异常时返回错误输出"""
        context = AgentContext(
            task_id="test-no-raise",
            state=State.INIT,
            user_input="测试"
        )

        async def error_execute(ctx):
            raise ValueError("执行失败")

        error_agent._execute = error_execute

        output = await error_agent.execute(context, raise_on_error=False)
        assert output.success is False
        assert "执行失败" in output.error

