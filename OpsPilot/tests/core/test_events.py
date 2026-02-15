"""
事件系统模块单元测试
"""
import pytest
from datetime import datetime

from opspilot.core.events import (
    EventType,
    BaseEvent,
    StateChangedEvent,
    TaskCreatedEvent,
    TaskCompletedEvent,
    TaskFailedEvent,
    AgentStartedEvent,
    AgentCompletedEvent,
    ToolCalledEvent,
    ToolResultEvent,
    ErrorEvent,
    EventBus,
    get_event_bus,
    subscribe,
    publish,
)


class TestEventType:
    """事件类型枚举测试"""

    def test_all_event_types_defined(self):
        """测试所有事件类型都已定义"""
        expected_types = [
            "STATE_CHANGED",
            "STATE_MACHINE_CREATED",
            "STATE_MACHINE_RESTORED",
            "TASK_CREATED",
            "TASK_COMPLETED",
            "TASK_FAILED",
            "AGENT_STARTED",
            "AGENT_COMPLETED",
            "AGENT_FAILED",
            "TOOL_CALLED",
            "TOOL_SUCCESS",
            "TOOL_FAILED",
            "ERROR_OCCURRED",
            "LOG_RECORD",
        ]
        for type_name in expected_types:
            assert hasattr(EventType, type_name)


class TestBaseEvent:
    """基础事件测试"""

    def test_create_base_event(self):
        """测试创建基础事件"""
        event = BaseEvent(event_type=EventType.STATE_CHANGED)
        assert event.event_type == EventType.STATE_CHANGED
        assert isinstance(event.timestamp, datetime)

    def test_base_event_to_dict(self):
        """测试基础事件序列化"""
        event = BaseEvent(
            event_type=EventType.STATE_CHANGED,
            metadata={"key": "value"}
        )
        data = event.to_dict()

        assert data["event_type"] == "state_changed"
        assert data["metadata"] == {"key": "value"}
        assert "timestamp" in data


class TestStateChangedEvent:
    """状态变化事件测试"""

    def test_create_state_changed_event(self):
        """测试创建状态变化事件"""
        event = StateChangedEvent(
            task_id="task-123",
            from_state="INIT",
            to_state="PLANNING",
            event="user_input"
        )

        assert event.task_id == "task-123"
        assert event.from_state == "INIT"
        assert event.to_state == "PLANNING"
        assert event.event_type == EventType.STATE_CHANGED

    def test_state_changed_event_to_dict(self):
        """测试状态变化事件序列化"""
        event = StateChangedEvent(
            task_id="task-123",
            from_state="INIT",
            to_state="PLANNING",
            event="user_input"
        )
        data = event.to_dict()

        assert data["task_id"] == "task-123"
        assert data["from_state"] == "INIT"
        assert data["to_state"] == "PLANNING"
        assert data["event"] == "user_input"


class TestTaskEvents:
    """任务事件测试"""

    def test_task_created_event(self):
        """测试任务创建事件"""
        event = TaskCreatedEvent(
            task_id="task-123",
            user_input="帮我创建订单"
        )

        assert event.task_id == "task-123"
        assert event.user_input == "帮我创建订单"
        assert event.event_type == EventType.TASK_CREATED

    def test_task_completed_event(self):
        """测试任务完成事件"""
        event = TaskCompletedEvent(
            task_id="task-123",
            result={"status": "success"}
        )

        assert event.result == {"status": "success"}
        assert event.event_type == EventType.TASK_COMPLETED

    def test_task_failed_event(self):
        """测试任务失败事件"""
        event = TaskFailedEvent(
            task_id="task-123",
            error="工具调用失败",
            error_code="TOOL_ERROR"
        )

        assert event.error == "工具调用失败"
        assert event.error_code == "TOOL_ERROR"


class TestAgentEvents:
    """Agent 事件测试"""

    def test_agent_started_event(self):
        """测试 Agent 启动事件"""
        event = AgentStartedEvent(
            task_id="task-123",
            agent_name="ExecAgent",
            state="EXECUTING"
        )

        assert event.agent_name == "ExecAgent"
        assert event.state == "EXECUTING"

    def test_agent_completed_event(self):
        """测试 Agent 完成事件"""
        event = AgentCompletedEvent(
            task_id="task-123",
            agent_name="PlanAgent",
            result={"plan": "step1, step2"}
        )

        assert event.agent_name == "PlanAgent"
        assert event.result is not None


class TestToolEvents:
    """工具事件测试"""

    def test_tool_called_event(self):
        """测试工具调用事件"""
        event = ToolCalledEvent(
            task_id="task-123",
            tool_name="create_order",
            params={"sku": "123", "qty": 1}
        )

        assert event.tool_name == "create_order"
        assert event.params == {"sku": "123", "qty": 1}
        assert event.event_type == EventType.TOOL_CALLED

    def test_tool_result_event_success(self):
        """测试工具结果事件（成功）"""
        event = ToolResultEvent(
            task_id="task-123",
            tool_name="create_order",
            success=True,
            result={"order_id": "ORD-001"}
        )

        assert event.success is True
        assert event.result == {"order_id": "ORD-001"}

    def test_tool_result_event_failure(self):
        """测试工具结果事件（失败）"""
        event = ToolResultEvent(
            task_id="task-123",
            tool_name="create_order",
            success=False,
            error="库存不足"
        )

        assert event.success is False
        assert event.error == "库存不足"


class TestErrorEvent:
    """错误事件测试"""

    def test_error_event(self):
        """测试错误事件"""
        event = ErrorEvent(
            error_code="CONFIG_ERROR",
            error_message="配置文件不存在",
            task_id="task-123"
        )

        assert event.error_code == "CONFIG_ERROR"
        assert event.error_message == "配置文件不存在"
        assert event.task_id == "task-123"


class TestEventBus:
    """事件总线测试"""

    @pytest.fixture
    def event_bus(self):
        """创建事件总线实例（清空之前的状态）"""
        bus = get_event_bus()
        bus.clear()
        return bus

    def test_subscribe_and_publish(self, event_bus):
        """测试订阅和发布事件"""
        received = []

        def handler(event):
            received.append(event)

        event_bus.subscribe(EventType.STATE_CHANGED, handler)

        event = StateChangedEvent(
            task_id="task-123",
            from_state="INIT",
            to_state="PLANNING",
            event="test"
        )
        event_bus.publish(event)

        assert len(received) == 1
        assert received[0].task_id == "task-123"

    def test_multiple_subscribers(self, event_bus):
        """测试多个订阅者"""
        received1 = []
        received2 = []

        def handler1(event):
            received1.append(event)

        def handler2(event):
            received2.append(event)

        event_bus.subscribe(EventType.STATE_CHANGED, handler1)
        event_bus.subscribe(EventType.STATE_CHANGED, handler2)

        event = StateChangedEvent(task_id="task-123")
        event_bus.publish(event)

        assert len(received1) == 1
        assert len(received2) == 1

    def test_subscribe_all(self, event_bus):
        """测试订阅所有事件"""
        received = []

        def handler(event):
            received.append(event)

        event_bus.subscribe_all(handler)

        event_bus.publish(StateChangedEvent(task_id="task-1"))
        event_bus.publish(TaskCreatedEvent(task_id="task-2"))

        assert len(received) == 2

    def test_unsubscribe(self, event_bus):
        """测试取消订阅"""
        received = []

        def handler(event):
            received.append(event)

        event_bus.subscribe(EventType.STATE_CHANGED, handler)
        event_bus.unsubscribe(EventType.STATE_CHANGED, handler)

        event = StateChangedEvent(task_id="task-123")
        event_bus.publish(event)

        assert len(received) == 0

    def test_handler_exception_isolated(self, event_bus):
        """测试处理器异常隔离"""
        received = []

        def bad_handler(event):
            raise Exception("Handler error")

        def good_handler(event):
            received.append(event)

        event_bus.subscribe(EventType.STATE_CHANGED, bad_handler)
        event_bus.subscribe(EventType.STATE_CHANGED, good_handler)

        event = StateChangedEvent(task_id="task-123")
        event_bus.publish(event)

        # 即使 bad_handler 抛出异常，good_handler 也应该被调用
        assert len(received) == 1

    def test_singleton(self):
        """测试单例模式"""
        bus1 = EventBus()
        bus2 = EventBus()

        assert bus1 is bus2

    def test_clear(self, event_bus):
        """测试清空订阅"""
        received = []

        def handler(event):
            received.append(event)

        event_bus.subscribe(EventType.STATE_CHANGED, handler)
        event_bus.clear()

        event = StateChangedEvent(task_id="task-123")
        event_bus.publish(event)

        assert len(received) == 0


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_subscribe_function(self):
        """测试 subscribe 便捷函数"""
        bus = get_event_bus()
        bus.clear()

        received = []

        def handler(event):
            received.append(event)

        subscribe(EventType.STATE_CHANGED, handler)

        event = StateChangedEvent(task_id="task-123")
        publish(event)

        assert len(received) == 1

