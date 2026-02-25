"""
状态机模块单元测试
"""
import pytest
from datetime import datetime

from opspilot.core.state_machine import (
    State,
    StateConfig,
    StateTransition,
    StateMachine,
    STATE_CONFIGS,
    ALLOWED_TRANSITIONS,
)
from opspilot.core.context import StateMachineContext
from opspilot.utils.exceptions import InvalidTransitionError, MaxRetryExceededError


class TestStateEnum:
    """状态枚举测试"""

    def test_all_states_defined(self):
        """测试所有状态都已定义"""
        expected_states = [
            "INIT", "PLANNING", "AUDITING", "EXECUTING",
            "VERIFYING", "SUCCESS", "RETRY", "REJECTED"
        ]
        for state_name in expected_states:
            assert hasattr(State, state_name)

    def test_state_is_string_enum(self):
        """测试状态是字符串枚举"""
        assert State.INIT.value == "INIT"
        assert isinstance(State.INIT.value, str)


class TestStateTransition:
    """状态转换记录测试"""

    def test_create_transition(self):
        """测试创建转换记录"""
        transition = StateTransition(
            from_state=State.INIT,
            to_state=State.PLANNING,
            event="user_input"
        )
        assert transition.from_state == State.INIT
        assert transition.to_state == State.PLANNING
        assert transition.event == "user_input"
        assert isinstance(transition.timestamp, datetime)

    def test_transition_to_dict(self):
        """测试转换记录序列化"""
        transition = StateTransition(
            from_state=State.INIT,
            to_state=State.PLANNING,
            event="user_input",
            metadata={"key": "value"}
        )
        data = transition.to_dict()

        assert data["from_state"] == "INIT"
        assert data["to_state"] == "PLANNING"
        assert data["event"] == "user_input"
        assert data["metadata"] == {"key": "value"}
        assert "timestamp" in data

    def test_transition_from_dict(self):
        """测试从字典创建转换记录"""
        data = {
            "from_state": "INIT",
            "to_state": "PLANNING",
            "event": "user_input",
            "timestamp": "2024-01-01T12:00:00",
            "metadata": {"key": "value"}
        }
        transition = StateTransition.from_dict(data)

        assert transition.from_state == State.INIT
        assert transition.to_state == State.PLANNING
        assert transition.event == "user_input"
        assert transition.metadata == {"key": "value"}


class TestStateConfig:
    """状态配置测试"""

    def test_state_config_exists(self):
        """测试所有状态都有配置"""
        for state in State:
            assert state in STATE_CONFIGS

    def test_init_state_config(self):
        """测试 INIT 状态配置"""
        config = STATE_CONFIGS[State.INIT]
        assert "intent_recognition" in config.allowed_actions
        assert "call_tool" in config.forbidden_actions
        assert config.prompt_constraint != ""

    def test_is_action_allowed(self):
        """测试动作允许检查"""
        config = StateConfig(
            name=State.INIT,
            allowed_actions=["action1", "action2"],
            forbidden_actions=["action3"]
        )

        assert config.is_action_allowed("action1") is True
        assert config.is_action_allowed("action3") is False


class TestAllowedTransitions:
    """状态转换规则测试"""

    def test_init_transitions(self):
        """测试 INIT 状态的转换"""
        assert State.PLANNING in ALLOWED_TRANSITIONS[State.INIT]
        assert len(ALLOWED_TRANSITIONS[State.INIT]) == 1

    def test_auditing_transitions(self):
        """测试 AUDITING 状态的转换"""
        transitions = ALLOWED_TRANSITIONS[State.AUDITING]
        assert State.EXECUTING in transitions
        assert State.REJECTED in transitions

    def test_all_states_have_transitions(self):
        """测试所有状态都有转换规则"""
        for state in State:
            assert state in ALLOWED_TRANSITIONS


class TestStateMachine:
    """状态机测试"""

    @pytest.fixture
    def state_machine(self):
        """创建状态机实例"""
        context = StateMachineContext.create(task_id="test-task")
        return StateMachine(context=context)

    def test_create_state_machine(self, state_machine):
        """测试创建状态机"""
        assert state_machine.context is not None
        assert state_machine.get_current_state() == State.INIT

    def test_can_transition_valid(self, state_machine):
        """测试合法转换检查"""
        assert state_machine.can_transition(State.PLANNING) is True

    def test_can_transition_invalid(self, state_machine):
        """测试非法转换检查"""
        # INIT 不能直接跳到 EXECUTING
        assert state_machine.can_transition(State.EXECUTING) is False

    def test_transition_success(self, state_machine):
        """测试成功转换"""
        transition = state_machine.transition(
            target_state=State.PLANNING,
            event="user_input"
        )

        assert transition.from_state == State.INIT
        assert transition.to_state == State.PLANNING
        assert state_machine.get_current_state() == State.PLANNING
        assert len(state_machine.context.history) == 1

    def test_transition_invalid_raises_error(self, state_machine):
        """测试非法转换抛出异常"""
        with pytest.raises(InvalidTransitionError) as exc_info:
            state_machine.transition(
                target_state=State.EXECUTING,
                event="invalid_jump"
            )

        assert "INIT" in str(exc_info.value)
        assert "EXECUTING" in str(exc_info.value)

    def test_transition_without_context_raises_error(self):
        """测试无上下文转换抛出异常"""
        sm = StateMachine(context=None)
        with pytest.raises(InvalidTransitionError):
            sm.transition(State.PLANNING, event="test")

    def test_get_allowed_actions(self, state_machine):
        """测试获取允许的动作"""
        actions = state_machine.get_allowed_actions()
        assert "intent_recognition" in actions
        assert "task_decomposition" in actions

    def test_get_forbidden_actions(self, state_machine):
        """测试获取禁止的动作"""
        actions = state_machine.get_forbidden_actions()
        assert "call_tool" in actions
        assert "execute_operation" in actions

    def test_get_prompt_constraint(self, state_machine):
        """测试获取提示词约束"""
        constraint = state_machine.get_prompt_constraint()
        assert "意图" in constraint

    def test_is_action_allowed(self, state_machine):
        """测试动作允许检查"""
        assert state_machine.is_action_allowed("intent_recognition") is True
        assert state_machine.is_action_allowed("call_tool") is False

    def test_retry_count_increment(self, state_machine):
        """测试重试计数增加"""
        # 先转换到可以进入 RETRY 的状态
        state_machine.transition(State.PLANNING, event="plan")
        state_machine.transition(State.AUDITING, event="audit")
        state_machine.transition(State.EXECUTING, event="execute")
        state_machine.transition(State.VERIFYING, event="verify")

        # 进入 RETRY
        state_machine.transition(State.RETRY, event="retry")
        assert state_machine.context.retry_count == 1

    def test_max_retry_exceeded(self, state_machine):
        """测试超过最大重试次数"""
        # 设置最大重试次数为 1
        state_machine.context.max_retries = 1

        # 转换到 RETRY 状态
        state_machine.transition(State.PLANNING, event="plan")
        state_machine.transition(State.AUDITING, event="audit")
        state_machine.transition(State.EXECUTING, event="execute")
        state_machine.transition(State.VERIFYING, event="verify")
        state_machine.transition(State.RETRY, event="retry")

        # 再次尝试进入 RETRY 应该失败
        state_machine.transition(State.EXECUTING, event="retry_exec")
        state_machine.transition(State.VERIFYING, event="verify")

        with pytest.raises(MaxRetryExceededError):
            state_machine.transition(State.RETRY, event="retry_again")

    def test_listener_notification(self, state_machine):
        """测试监听器通知"""
        events = []

        def listener(transition):
            events.append(transition)

        state_machine.add_listener(listener)
        state_machine.transition(State.PLANNING, event="test")

        assert len(events) == 1
        assert events[0].to_state == State.PLANNING

    def test_full_workflow(self, state_machine):
        """测试完整工作流"""
        # INIT -> PLANNING
        state_machine.transition(State.PLANNING, event="user_input")
        assert state_machine.get_current_state() == State.PLANNING

        # PLANNING -> AUDITING
        state_machine.transition(State.AUDITING, event="plan_done")
        assert state_machine.get_current_state() == State.AUDITING

        # AUDITING -> EXECUTING
        state_machine.transition(State.EXECUTING, event="audit_passed")
        assert state_machine.get_current_state() == State.EXECUTING

        # EXECUTING -> VERIFYING
        state_machine.transition(State.VERIFYING, event="exec_done")
        assert state_machine.get_current_state() == State.VERIFYING

        # VERIFYING -> SUCCESS
        state_machine.transition(State.SUCCESS, event="verified")
        assert state_machine.get_current_state() == State.SUCCESS

        # 检查历史记录
        assert len(state_machine.context.history) == 5

