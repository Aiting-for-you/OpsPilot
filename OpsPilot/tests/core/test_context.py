"""
上下文管理模块单元测试
"""
import pytest
from datetime import datetime

from opspilot.core.context import (
    StateMachineContext,
    TaskContext,
    ContextManager,
)
from opspilot.core.state_machine import State


class TestStateMachineContext:
    """状态机上下文测试"""

    def test_create_context(self):
        """测试创建上下文"""
        context = StateMachineContext.create()
        assert context.task_id is not None
        assert context.current_state == State.INIT
        assert context.retry_count == 0
        assert context.max_retries == 3

    def test_create_context_with_task_id(self):
        """测试带任务ID创建上下文"""
        context = StateMachineContext.create(task_id="test-123")
        assert context.task_id == "test-123"

    def test_create_context_with_max_retries(self):
        """测试自定义最大重试次数"""
        context = StateMachineContext.create(max_retries=5)
        assert context.max_retries == 5

    def test_context_to_dict(self):
        """测试上下文序列化"""
        context = StateMachineContext.create(task_id="test-123")
        context.current_state = State.PLANNING
        context.retry_count = 1

        data = context.to_dict()

        assert data["task_id"] == "test-123"
        assert data["current_state"] == "PLANNING"
        assert data["retry_count"] == 1
        assert "created_at" in data
        assert "updated_at" in data

    def test_context_from_dict(self):
        """测试从字典创建上下文"""
        data = {
            "task_id": "test-123",
            "current_state": "EXECUTING",
            "history": [],
            "retry_count": 2,
            "max_retries": 5,
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:30:00",
            "metadata": {"key": "value"}
        }

        context = StateMachineContext.from_dict(data)

        assert context.task_id == "test-123"
        assert context.current_state == State.EXECUTING
        assert context.retry_count == 2
        assert context.max_retries == 5
        assert context.metadata == {"key": "value"}

    def test_get_last_transition(self):
        """测试获取最后转换"""
        context = StateMachineContext.create()
        assert context.get_last_transition() is None

        # 添加转换记录
        from opspilot.core.state_machine import StateTransition
        transition = StateTransition(
            from_state=State.INIT,
            to_state=State.PLANNING,
            event="test"
        )
        context.history.append(transition)

        last = context.get_last_transition()
        assert last == transition

    def test_get_transition_count(self):
        """测试获取转换次数"""
        context = StateMachineContext.create()
        assert context.get_transition_count() == 0

        from opspilot.core.state_machine import StateTransition
        context.history.append(StateTransition(
            from_state=State.INIT,
            to_state=State.PLANNING,
            event="test"
        ))

        assert context.get_transition_count() == 1


class TestTaskContext:
    """任务上下文测试"""

    def test_create_task_context(self):
        """测试创建任务上下文"""
        context = TaskContext.create(user_input="帮我创建一个订单")

        assert context.task_id is not None
        assert context.user_input == "帮我创建一个订单"
        assert context.state_context is not None
        assert context.state_context.task_id == context.task_id

    def test_task_context_to_dict(self):
        """测试任务上下文序列化"""
        context = TaskContext.create(
            user_input="测试输入",
            task_id="task-123"
        )
        context.intent = "create_order"
        context.plan = {"steps": ["step1", "step2"]}

        data = context.to_dict()

        assert data["task_id"] == "task-123"
        assert data["user_input"] == "测试输入"
        assert data["intent"] == "create_order"
        assert data["plan"] == {"steps": ["step1", "step2"]}
        assert data["state_context"] is not None

    def test_task_context_from_dict(self):
        """测试从字典创建任务上下文"""
        data = {
            "task_id": "task-123",
            "user_input": "测试输入",
            "intent": "query_inventory",
            "plan": {"steps": ["step1"]},
            "execution_results": [{"result": "ok"}],
            "final_result": {"status": "success"},
            "state_context": {
                "task_id": "task-123",
                "current_state": "SUCCESS",
                "history": [],
                "retry_count": 0,
                "max_retries": 3,
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:30:00",
                "metadata": {}
            },
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:30:00",
            "metadata": {}
        }

        context = TaskContext.from_dict(data)

        assert context.task_id == "task-123"
        assert context.intent == "query_inventory"
        assert context.final_result == {"status": "success"}
        assert context.state_context.current_state == State.SUCCESS

    def test_add_execution_result(self):
        """测试添加执行结果"""
        context = TaskContext.create(user_input="test")

        context.add_execution_result({"step": 1, "result": "ok"})
        context.add_execution_result({"step": 2, "result": "done"})

        assert len(context.execution_results) == 2
        assert context.execution_results[0]["step"] == 1

    def test_set_final_result(self):
        """测试设置最终结果"""
        context = TaskContext.create(user_input="test")

        context.set_final_result({"status": "success", "data": {}})

        assert context.final_result["status"] == "success"


class TestContextManager:
    """上下文管理器测试"""

    @pytest.fixture
    def manager(self):
        """创建上下文管理器"""
        return ContextManager()

    def test_create_context(self, manager):
        """测试创建上下文"""
        context = manager.create_context(user_input="测试输入")

        assert context.task_id in manager.list_contexts()
        assert len(manager.list_contexts()) == 1

    def test_get_context(self, manager):
        """测试获取上下文"""
        created = manager.create_context(user_input="测试")
        retrieved = manager.get_context(created.task_id)

        assert retrieved is created

    def test_get_nonexistent_context(self, manager):
        """测试获取不存在的上下文"""
        result = manager.get_context("nonexistent")
        assert result is None

    def test_update_context(self, manager):
        """测试更新上下文"""
        context = manager.create_context(user_input="测试")
        context.intent = "new_intent"

        manager.update_context(context)

        retrieved = manager.get_context(context.task_id)
        assert retrieved.intent == "new_intent"

    def test_delete_context(self, manager):
        """测试删除上下文"""
        context = manager.create_context(user_input="测试")

        result = manager.delete_context(context.task_id)

        assert result is True
        assert context.task_id not in manager.list_contexts()

    def test_delete_nonexistent_context(self, manager):
        """测试删除不存在的上下文"""
        result = manager.delete_context("nonexistent")
        assert result is False

    def test_list_contexts(self, manager):
        """测试列出所有上下文"""
        c1 = manager.create_context(user_input="test1")
        c2 = manager.create_context(user_input="test2")
        c3 = manager.create_context(user_input="test3")

        task_ids = manager.list_contexts()

        assert len(task_ids) == 3
        assert c1.task_id in task_ids
        assert c2.task_id in task_ids
        assert c3.task_id in task_ids

    def test_clear_all(self, manager):
        """测试清空所有上下文"""
        manager.create_context(user_input="test1")
        manager.create_context(user_input="test2")

        manager.clear_all()

        assert len(manager.list_contexts()) == 0

