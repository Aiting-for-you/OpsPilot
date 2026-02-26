"""
事件系统模块

职责：
- 定义事件类型
- 事件发布/订阅机制
- 状态变化通知

使用方式：
    from opspilot.core.events import EventBus, StateChangedEvent

    # 订阅事件
    def on_state_changed(event):
        print(f"状态变化: {event.from_state} -> {event.to_state}")

    EventBus.subscribe(StateChangedEvent, on_state_changed)

    # 发布事件
    EventBus.publish(StateChangedEvent(
        task_id="xxx",
        from_state="INIT",
        to_state="PLANNING"
    ))
"""
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, Callable, List, Type
from dataclasses import dataclass, field


class EventType(str, Enum):
    """事件类型枚举"""
    # 状态相关
    STATE_CHANGED = "state_changed"
    STATE_MACHINE_CREATED = "state_machine_created"
    STATE_MACHINE_RESTORED = "state_machine_restored"

    # 任务相关
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"

    # Agent 相关
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"

    # 工具相关
    TOOL_CALLED = "tool_called"
    TOOL_SUCCESS = "tool_success"
    TOOL_FAILED = "tool_failed"

    # 系统相关
    ERROR_OCCURRED = "error_occurred"
    LOG_RECORD = "log_record"


@dataclass
class BaseEvent:
    """事件基类"""
    event_type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class StateChangedEvent(BaseEvent):
    """状态变化事件"""
    event_type: EventType = EventType.STATE_CHANGED
    task_id: str = ""
    from_state: str = ""
    to_state: str = ""
    event: str = ""  # 触发事件名称

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "task_id": self.task_id,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "event": self.event,
        })
        return data


@dataclass
class TaskCreatedEvent(BaseEvent):
    """任务创建事件"""
    event_type: EventType = EventType.TASK_CREATED
    task_id: str = ""
    user_input: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "task_id": self.task_id,
            "user_input": self.user_input,
        })
        return data


@dataclass
class TaskCompletedEvent(BaseEvent):
    """任务完成事件"""
    event_type: EventType = EventType.TASK_COMPLETED
    task_id: str = ""
    result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "task_id": self.task_id,
            "result": self.result,
        })
        return data


@dataclass
class TaskFailedEvent(BaseEvent):
    """任务失败事件"""
    event_type: EventType = EventType.TASK_FAILED
    task_id: str = ""
    error: str = ""
    error_code: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "task_id": self.task_id,
            "error": self.error,
            "error_code": self.error_code,
        })
        return data


@dataclass
class AgentStartedEvent(BaseEvent):
    """Agent 启动事件"""
    event_type: EventType = EventType.AGENT_STARTED
    task_id: str = ""
    agent_name: str = ""
    state: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "state": self.state,
        })
        return data


@dataclass
class AgentCompletedEvent(BaseEvent):
    """Agent 完成事件"""
    event_type: EventType = EventType.AGENT_COMPLETED
    task_id: str = ""
    agent_name: str = ""
    result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "result": self.result,
        })
        return data


@dataclass
class AgentFailedEvent(BaseEvent):
    """Agent 失败事件"""
    event_type: EventType = EventType.AGENT_FAILED
    task_id: str = ""
    agent_name: str = ""
    error: str = ""
    error_code: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "error": self.error,
            "error_code": self.error_code,
        })
        return data


@dataclass
class ToolCalledEvent(BaseEvent):
    """工具调用事件"""
    event_type: EventType = EventType.TOOL_CALLED
    task_id: str = ""
    tool_name: str = ""
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "task_id": self.task_id,
            "tool_name": self.tool_name,
            "params": self.params,
        })
        return data


@dataclass
class ToolResultEvent(BaseEvent):
    """工具结果事件"""
    event_type: EventType = EventType.TOOL_SUCCESS
    task_id: str = ""
    tool_name: str = ""
    success: bool = True
    result: Optional[Any] = None
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "task_id": self.task_id,
            "tool_name": self.tool_name,
            "success": self.success,
            "result": self.result,
            "error": self.error,
        })
        return data


@dataclass
class ErrorEvent(BaseEvent):
    """错误事件"""
    event_type: EventType = EventType.ERROR_OCCURRED
    error_code: str = ""
    error_message: str = ""
    task_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "error_code": self.error_code,
            "error_message": self.error_message,
            "task_id": self.task_id,
        })
        return data


# ==================== 事件总线 ====================

class EventBus:
    """
    事件总线

    职责：
    - 管理事件订阅
    - 发布事件
    - 同步/异步事件处理

    使用单例模式，全局共享一个事件总线
    """

    _instance: Optional["EventBus"] = None

    def __new__(cls) -> "EventBus":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._global_subscribers: List[Callable] = []
        self._initialized = True

    @classmethod
    def get_instance(cls) -> "EventBus":
        """获取单例实例"""
        return cls()

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[BaseEvent], None]
    ) -> None:
        """
        订阅特定类型的事件

        Args:
            event_type: 事件类型
            handler: 事件处理函数
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def subscribe_all(self, handler: Callable[[BaseEvent], None]) -> None:
        """
        订阅所有事件

        Args:
            handler: 事件处理函数
        """
        self._global_subscribers.append(handler)

    def unsubscribe(
        self,
        event_type: EventType,
        handler: Callable[[BaseEvent], None]
    ) -> None:
        """
        取消订阅

        Args:
            event_type: 事件类型
            handler: 事件处理函数
        """
        if event_type in self._subscribers:
            if handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)

    def publish(self, event: BaseEvent) -> None:
        """
        发布事件

        事件会同步传递给所有订阅者

        Args:
            event: 事件对象
        """
        # 通知特定类型的订阅者
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                # 避免一个处理器失败影响其他处理器
                print(f"Event handler error: {e}")

        # 通知全局订阅者
        for handler in self._global_subscribers:
            try:
                handler(event)
            except Exception as e:
                print(f"Global event handler error: {e}")

    def clear(self) -> None:
        """清空所有订阅"""
        self._subscribers.clear()
        self._global_subscribers.clear()


# ==================== 便捷函数 ====================

def get_event_bus() -> EventBus:
    """获取事件总线实例"""
    return EventBus.get_instance()


def subscribe(event_type: EventType, handler: Callable[[BaseEvent], None]) -> None:
    """订阅事件"""
    get_event_bus().subscribe(event_type, handler)


def publish(event: BaseEvent) -> None:
    """发布事件"""
    get_event_bus().publish(event)

