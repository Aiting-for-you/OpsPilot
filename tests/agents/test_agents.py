"""
Agent 模块单元测试
"""
import pytest

from opspilot.agents.base import AgentContext, AgentOutput
from opspilot.agents.intent_agent import IntentType, IntentAgent, MockIntentAgent
from opspilot.agents.plan_agent import PlanAgent, MockPlanAgent
from opspilot.agents.exec_agent import ExecAgent, MockExecAgent
from opspilot.agents.verify_agent import VerifyAgent, MockVerifyAgent
from opspilot.core.state_machine import State


class TestIntentAgent:
    """意图识别 Agent 测试"""

    @pytest.fixture
    def agent(self):
        return MockIntentAgent()

    @pytest.fixture
    def context(self):
        return AgentContext(
            task_id="test-task",
            state=State.INIT,
            user_input="帮我查询华南地区的供应商"
        )

    @pytest.mark.asyncio
    async def test_execute(self, agent, context):
        """测试执行"""
        output = await agent.execute(context)

        assert output.success is True
        assert output.result is not None
        assert output.next_state == State.PLANNING

    @pytest.mark.asyncio
    async def test_recognize_query_supplier(self, agent):
        """测试识别查询供应商意图"""
        context = AgentContext(
            task_id="test",
            state=State.INIT,
            user_input="查找华南的供应商"
        )

        output = await agent.execute(context)

        assert output.result["intent_type"] == IntentType.QUERY_SUPPLIER.value
        assert output.result["entities"].get("region") == "华南"

    @pytest.mark.asyncio
    async def test_recognize_create_order(self, agent):
        """测试识别创建订单意图"""
        context = AgentContext(
            task_id="test",
            state=State.INIT,
            user_input="帮我创建一个采购订单"
        )

        output = await agent.execute(context)

        assert output.result["intent_type"] == IntentType.CREATE_ORDER.value

    @pytest.mark.asyncio
    async def test_recognize_unknown(self, agent):
        """测试未知意图"""
        context = AgentContext(
            task_id="test",
            state=State.INIT,
            user_input="今天天气怎么样"
        )

        output = await agent.execute(context)

        assert output.result["intent_type"] == IntentType.UNKNOWN.value
        assert output.result["confidence"] < 0.5


class TestPlanAgent:
    """规划 Agent 测试"""

    @pytest.fixture
    def agent(self):
        return MockPlanAgent()

    @pytest.fixture
    def context(self):
        return AgentContext(
            task_id="test-task",
            state=State.PLANNING,
            user_input="查询华南供应商",
            metadata={
                "intent": {
                    "intent_type": IntentType.QUERY_SUPPLIER.value,
                    "entities": {"region": "华南"},
                    "summary": "查询华南地区供应商"
                }
            }
        )

    @pytest.mark.asyncio
    async def test_execute(self, agent, context):
        """测试执行"""
        output = await agent.execute(context)

        assert output.success is True
        assert output.result is not None
        assert output.next_state == State.AUDITING

    @pytest.mark.asyncio
    async def test_plan_has_steps(self, agent, context):
        """测试计划包含步骤"""
        output = await agent.execute(context)

        assert len(output.result["steps"]) > 0

    @pytest.mark.asyncio
    async def test_plan_for_query_supplier(self, agent):
        """测试查询供应商计划"""
        context = AgentContext(
            task_id="test",
            state=State.PLANNING,
            metadata={
                "intent": {
                    "intent_type": IntentType.QUERY_SUPPLIER.value,
                    "entities": {"region": "华东"}
                }
            }
        )

        output = await agent.execute(context)

        steps = output.result["steps"]
        assert any(s["tool"] == "query_supplier" for s in steps)


class TestExecAgent:
    """执行 Agent 测试"""

    @pytest.fixture
    def agent(self):
        return MockExecAgent()

    @pytest.fixture
    def context(self):
        return AgentContext(
            task_id="test-task",
            state=State.EXECUTING,
            metadata={
                "plan": {
                    "plan_summary": "测试计划",
                    "steps": [
                        {
                            "step_id": 1,
                            "tool": "query_supplier",
                            "params": {"region": "华南"}
                        }
                    ]
                }
            }
        )

    @pytest.mark.asyncio
    async def test_execute(self, agent, context):
        """测试执行"""
        output = await agent.execute(context)

        assert output.success is True
        assert output.next_state == State.VERIFYING

    @pytest.mark.asyncio
    async def test_execution_results(self, agent, context):
        """测试执行结果"""
        output = await agent.execute(context)

        assert "execution_results" in output.result
        assert len(output.result["execution_results"]) > 0

    @pytest.mark.asyncio
    async def test_mock_data_returned(self, agent, context):
        """测试返回 Mock 数据"""
        output = await agent.execute(context)

        result = output.result["execution_results"][0]
        assert result["success"] is True
        assert result["data"] is not None


class TestVerifyAgent:
    """验证 Agent 测试"""

    @pytest.fixture
    def agent(self):
        return MockVerifyAgent()

    @pytest.fixture
    def context(self):
        return AgentContext(
            task_id="test-task",
            state=State.VERIFYING,
            metadata={
                "execution_results": [
                    {
                        "step_id": 1,
                        "tool": "query_supplier",
                        "success": True,
                        "data": {"suppliers": [], "total": 0}
                    }
                ]
            }
        )

    @pytest.mark.asyncio
    async def test_execute(self, agent, context):
        """测试执行"""
        output = await agent.execute(context)

        assert output.success is True
        assert output.next_state == State.SUCCESS

    @pytest.mark.asyncio
    async def test_verification_passed(self, agent, context):
        """测试验证通过"""
        output = await agent.execute(context)

        assert output.result["passed"] is True
        assert len(output.result["checklist"]) > 0

    @pytest.mark.asyncio
    async def test_verification_failed(self, agent):
        """测试验证失败"""
        context = AgentContext(
            task_id="test",
            state=State.VERIFYING,
            metadata={
                "execution_results": [
                    {
                        "step_id": 1,
                        "tool": "query_supplier",
                        "success": False,
                        "error": "执行失败"
                    }
                ]
            }
        )

        output = await agent.execute(context)

        assert output.success is False
        assert output.next_state == State.RETRY

    @pytest.mark.asyncio
    async def test_generate_report(self, agent, context):
        """测试生成报告"""
        output = await agent.execute(context)

        report = agent.generate_report(context, output.result)

        assert "执行报告" in report
        assert "test-task" in report


class TestAgentIntegration:
    """Agent 集成测试"""

    @pytest.mark.asyncio
    async def test_full_flow(self):
        """测试完整流程"""
        # 1. 意图识别
        intent_agent = MockIntentAgent()
        intent_context = AgentContext(
            task_id="integration-test",
            state=State.INIT,
            user_input="查询华南供应商"
        )
        intent_output = await intent_agent.execute(intent_context)

        assert intent_output.success is True

        # 2. 规划
        plan_agent = MockPlanAgent()
        plan_context = AgentContext(
            task_id="integration-test",
            state=State.PLANNING,
            metadata={"intent": intent_output.result}
        )
        plan_output = await plan_agent.execute(plan_context)

        assert plan_output.success is True

        # 3. 执行
        exec_agent = MockExecAgent()
        exec_context = AgentContext(
            task_id="integration-test",
            state=State.EXECUTING,
            metadata={"plan": plan_output.result}
        )
        exec_output = await exec_agent.execute(exec_context)

        assert exec_output.success is True

        # 4. 验证
        verify_agent = MockVerifyAgent()
        verify_context = AgentContext(
            task_id="integration-test",
            state=State.VERIFYING,
            metadata={"execution_results": exec_output.result["execution_results"]}
        )
        verify_output = await verify_agent.execute(verify_context)

        assert verify_output.success is True
        assert verify_output.next_state == State.SUCCESS

