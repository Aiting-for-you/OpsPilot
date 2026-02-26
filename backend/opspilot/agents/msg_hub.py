"""
消息中心 - Message Hub

实现消息驱动的多智能体通信，兼容AgentScope和独立运行模式。

核心功能：
1. 消息定义与路由
2. 发布/订阅机制
3. 消息历史记录
4. 广播与单播
"""

from __future__ import annotations

import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union


class MessageType(Enum):
    """消息类型"""
    # 任务相关
    TASK_REQUEST = "task_request"          # 任务请求
    TASK_RESULT = "task_result"            # 任务结果
    
    # Agent通信
    AGENT_MESSAGE = "agent_message"        # Agent间消息
    AGENT_BROADCAST = "agent_broadcast"    # Agent广播
    
    # 工具相关
    TOOL_CALL = "tool_call"                # 工具调用请求
    TOOL_RESULT = "tool_result"            # 工具调用结果
    
    # 状态相关
    STATE_CHANGE = "state_change"          # 状态变化
    PROGRESS_UPDATE = "progress_update"    # 进度更新
    
    # 控制相关
    CONTROL = "control"                    # 控制消息
    ERROR = "error"                        # 错误消息


@dataclass
class AgentMessage:
    """
    Agent消息
    
    兼容AgentScope的Msg格式，同时支持独立运行。
    """
    name: str                               # 发送者名称
    content: Any                            # 消息内容
    msg_type: MessageType = MessageType.AGENT_MESSAGE
    timestamp: float = field(default_factory=time.time)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # 路由信息
    sender: Optional[str] = None            # 发送者ID
    receiver: Optional[str] = None          # 接收者ID（None表示广播）
    reply_to: Optional[str] = None          # 回复的消息ID
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    
    # 追踪信息
    trace_id: Optional[str] = None          # 追踪ID
    parent_id: Optional[str] = None         # 父消息ID
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "name": self.name,
            "content": self.content,
            "msg_type": self.msg_type.value,
            "timestamp": self.timestamp,
            "message_id": self.message_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "reply_to": self.reply_to,
            "metadata": self.metadata,
            "tags": list(self.tags),
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AgentMessage:
        """从字典反序列化"""
        return cls(
            name=data["name"],
            content=data["content"],
            msg_type=MessageType(data.get("msg_type", "agent_message")),
            timestamp=data.get("timestamp", time.time()),
            message_id=data.get("message_id", str(uuid.uuid4())[:8]),
            sender=data.get("sender"),
            receiver=data.get("receiver"),
            reply_to=data.get("reply_to"),
            metadata=data.get("metadata", {}),
            tags=set(data.get("tags", [])),
            trace_id=data.get("trace_id"),
            parent_id=data.get("parent_id"),
        )
    
    def reply(self, content: Any, sender: str) -> AgentMessage:
        """创建回复消息"""
        return AgentMessage(
            name=sender,
            content=content,
            msg_type=self.msg_type,
            sender=sender,
            receiver=self.sender,
            reply_to=self.message_id,
            trace_id=self.trace_id,
            parent_id=self.message_id,
        )


class MessageSubscriber:
    """消息订阅者"""
    
    def __init__(
        self,
        name: str,
        handler: Optional[Callable[[AgentMessage], None]] = None,
        subscribed_types: Optional[Set[MessageType]] = None,
    ):
        self.name = name
        self.handler = handler
        self.subscribed_types = subscribed_types or set()
        self.message_queue: List[AgentMessage] = []
        self.max_queue_size = 100
    
    def can_handle(self, msg: AgentMessage) -> bool:
        """检查是否能处理该消息"""
        if not self.subscribed_types:
            return True
        return msg.msg_type in self.subscribed_types
    
    def receive(self, msg: AgentMessage) -> None:
        """接收消息"""
        if len(self.message_queue) >= self.max_queue_size:
            self.message_queue.pop(0)
        self.message_queue.append(msg)
        
        if self.handler:
            self.handler(msg)
    
    def get_messages(self, clear: bool = True) -> List[AgentMessage]:
        """获取消息"""
        messages = self.message_queue.copy()
        if clear:
            self.message_queue.clear()
        return messages


class MessageHub:
    """
    消息中心
    
    实现消息的发布、订阅、路由和存储。
    支持单播、广播和组播。
    
    示例:
        >>> hub = MessageHub()
        >>> hub.subscribe("agent1", handler, {MessageType.TASK_REQUEST})
        >>> hub.publish(message)
    """
    
    _instance: Optional[MessageHub] = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        max_history: int = 1000,
        enable_history: bool = True,
    ):
        """
        初始化消息中心
        
        Args:
            max_history: 最大历史记录数
            enable_history: 是否启用历史记录
        """
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self.max_history = max_history
        self.enable_history = enable_history
        
        # 订阅者注册表
        self._subscribers: Dict[str, MessageSubscriber] = {}
        
        # 类型订阅映射
        self._type_subscribers: Dict[MessageType, Set[str]] = defaultdict(set)
        
        # 消息历史
        self._history: List[AgentMessage] = []
        
        # 追踪映射
        self._trace_messages: Dict[str, List[str]] = defaultdict(list)
        
        self._initialized = True
    
    @classmethod
    def get_instance(cls) -> MessageHub:
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def subscribe(
        self,
        subscriber_name: str,
        handler: Optional[Callable[[AgentMessage], None]] = None,
        message_types: Optional[Set[MessageType]] = None,
    ) -> None:
        """
        订阅消息
        
        Args:
            subscriber_name: 订阅者名称
            handler: 消息处理函数
            message_types: 订阅的消息类型
        """
        subscriber = MessageSubscriber(
            name=subscriber_name,
            handler=handler,
            subscribed_types=message_types or set(),
        )
        self._subscribers[subscriber_name] = subscriber
        
        # 更新类型映射
        if message_types:
            for msg_type in message_types:
                self._type_subscribers[msg_type].add(subscriber_name)
    
    def unsubscribe(self, subscriber_name: str) -> None:
        """取消订阅"""
        if subscriber_name in self._subscribers:
            subscriber = self._subscribers[subscriber_name]
            
            # 清理类型映射
            for msg_type in subscriber.subscribed_types:
                self._type_subscribers[msg_type].discard(subscriber_name)
            
            del self._subscribers[subscriber_name]
    
    def publish(
        self,
        msg: AgentMessage,
        exclude: Optional[Set[str]] = None,
    ) -> int:
        """
        发布消息
        
        Args:
            msg: 消息对象
            exclude: 排除的订阅者
        
        Returns:
            接收消息的订阅者数量
        """
        exclude = exclude or set()
        
        # 记录历史
        if self.enable_history:
            self._add_history(msg)
        
        # 确定接收者
        if msg.receiver:
            # 单播
            receivers = {msg.receiver}
        elif msg.msg_type in self._type_subscribers:
            # 类型订阅
            receivers = self._type_subscribers[msg.msg_type].copy()
        else:
            # 广播
            receivers = set(self._subscribers.keys())
        
        # 排除发送者
        if msg.sender:
            receivers.discard(msg.sender)
        
        # 排除指定订阅者
        receivers -= exclude
        
        # 发送消息
        sent_count = 0
        for name in receivers:
            if name in self._subscribers:
                subscriber = self._subscribers[name]
                if subscriber.can_handle(msg):
                    subscriber.receive(msg)
                    sent_count += 1
        
        return sent_count
    
    def send_to(
        self,
        msg: AgentMessage,
        receiver: str,
    ) -> bool:
        """
        发送消息给指定接收者
        
        Args:
            msg: 消息对象
            receiver: 接收者名称
        
        Returns:
            是否发送成功
        """
        msg.receiver = receiver
        
        if self.enable_history:
            self._add_history(msg)
        
        if receiver in self._subscribers:
            self._subscribers[receiver].receive(msg)
            return True
        
        return False
    
    def broadcast(
        self,
        msg: AgentMessage,
        exclude: Optional[Set[str]] = None,
    ) -> int:
        """
        广播消息
        
        Args:
            msg: 消息对象
            exclude: 排除的订阅者
        
        Returns:
            接收消息的订阅者数量
        """
        msg.receiver = None  # 清除接收者，表示广播
        return self.publish(msg, exclude)
    
    def get_messages(
        self,
        subscriber_name: str,
        clear: bool = True,
    ) -> List[AgentMessage]:
        """
        获取订阅者的消息
        
        Args:
            subscriber_name: 订阅者名称
            clear: 是否清空队列
        
        Returns:
            消息列表
        """
        if subscriber_name in self._subscribers:
            return self._subscribers[subscriber_name].get_messages(clear)
        return []
    
    def _add_history(self, msg: AgentMessage) -> None:
        """添加到历史记录"""
        if len(self._history) >= self.max_history:
            self._history.pop(0)
        
        self._history.append(msg)
        
        # 更新追踪映射
        if msg.trace_id:
            self._trace_messages[msg.trace_id].append(msg.message_id)
    
    def get_history(
        self,
        limit: int = 100,
        msg_type: Optional[MessageType] = None,
        sender: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> List[AgentMessage]:
        """
        获取历史消息
        
        Args:
            limit: 最大数量
            msg_type: 消息类型过滤
            sender: 发送者过滤
            trace_id: 追踪ID过滤
        
        Returns:
            消息列表
        """
        messages = self._history
        
        if msg_type:
            messages = [m for m in messages if m.msg_type == msg_type]
        
        if sender:
            messages = [m for m in messages if m.sender == sender]
        
        if trace_id:
            messages = [m for m in messages if m.trace_id == trace_id]
        
        return messages[-limit:]
    
    def get_trace(self, trace_id: str) -> List[AgentMessage]:
        """获取追踪链"""
        message_ids = self._trace_messages.get(trace_id, [])
        id_to_msg = {m.message_id: m for m in self._history}
        return [id_to_msg[mid] for mid in message_ids if mid in id_to_msg]
    
    def clear_history(self) -> None:
        """清空历史"""
        self._history.clear()
        self._trace_messages.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "subscriber_count": len(self._subscribers),
            "history_count": len(self._history),
            "trace_count": len(self._trace_messages),
            "subscribers": list(self._subscribers.keys()),
        }


# 便捷函数
def create_message(
    name: str,
    content: Any,
    msg_type: MessageType = MessageType.AGENT_MESSAGE,
    sender: Optional[str] = None,
    receiver: Optional[str] = None,
    **kwargs,
) -> AgentMessage:
    """创建消息的便捷函数"""
    return AgentMessage(
        name=name,
        content=content,
        msg_type=msg_type,
        sender=sender,
        receiver=receiver,
        **kwargs,
    )


def get_message_hub() -> MessageHub:
    """获取消息中心单例"""
    return MessageHub.get_instance()


def subscribe(
    name: str,
    handler: Optional[Callable] = None,
    message_types: Optional[Set[MessageType]] = None,
) -> None:
    """订阅消息的便捷函数"""
    hub = get_message_hub()
    hub.subscribe(name, handler, message_types)


def publish(msg: AgentMessage) -> int:
    """发布消息的便捷函数"""
    hub = get_message_hub()
    return hub.publish(msg)


def broadcast(
    name: str,
    content: Any,
    sender: Optional[str] = None,
    exclude: Optional[Set[str]] = None,
) -> int:
    """广播消息的便捷函数"""
    msg = create_message(
        name=name,
        content=content,
        msg_type=MessageType.AGENT_BROADCAST,
        sender=sender,
    )
    hub = get_message_hub()
    return hub.broadcast(msg, exclude)

