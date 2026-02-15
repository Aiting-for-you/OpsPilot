"""
A2A (Agent-to-Agent) 协议模块

基于 AgentScope Runtime 的 A2A 通信能力。
实现智能体间的标准化通信协议。

特性：
- Agent 发现与注册
- 标准化消息格式
- 技能发布与发现
- 多协议支持（HTTP/gRPC）
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union


class AgentStatus(Enum):
    """Agent 状态"""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"


class MessageType(Enum):
    """消息类型"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    HEARTBEAT = "heartbeat"


@dataclass
class AgentSkill:
    """Agent 技能"""
    id: str
    name: str
    description: str
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "tags": self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentSkill":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            input_schema=data.get("input_schema"),
            output_schema=data.get("output_schema"),
            tags=data.get("tags", []),
        )


@dataclass
class AgentCard:
    """
    Agent 名片
    
    描述 Agent 的身份和能力。
    """
    agent_id: str
    name: str
    description: str
    version: str = "1.0.0"
    skills: List[AgentSkill] = field(default_factory=list)
    endpoints: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: AgentStatus = AgentStatus.ONLINE
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "skills": [s.to_dict() for s in self.skills],
            "endpoints": self.endpoints,
            "metadata": self.metadata,
            "status": self.status.value,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentCard":
        return cls(
            agent_id=data["agent_id"],
            name=data["name"],
            description=data["description"],
            version=data.get("version", "1.0.0"),
            skills=[AgentSkill.from_dict(s) for s in data.get("skills", [])],
            endpoints=data.get("endpoints", {}),
            metadata=data.get("metadata", {}),
            status=AgentStatus(data.get("status", "online")),
        )


@dataclass
class A2AMessage:
    """
    A2A 消息
    
    Agent 间通信的标准消息格式。
    """
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: Optional[str] = None
    sender_id: str = ""
    receiver_id: Optional[str] = None  # None 表示广播
    message_type: MessageType = MessageType.REQUEST
    skill_id: Optional[str] = None
    content: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    ttl: int = 3600  # 消息存活时间（秒）
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "message_type": self.message_type.value,
            "skill_id": self.skill_id,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "A2AMessage":
        return cls(
            message_id=data["message_id"],
            conversation_id=data.get("conversation_id"),
            sender_id=data["sender_id"],
            receiver_id=data.get("receiver_id"),
            message_type=MessageType(data["message_type"]),
            skill_id=data.get("skill_id"),
            content=data.get("content"),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", time.time()),
            ttl=data.get("ttl", 3600),
        )
    
    def create_response(
        self,
        content: Any,
        sender_id: str,
    ) -> "A2AMessage":
        """创建响应消息"""
        return A2AMessage(
            conversation_id=self.conversation_id or self.message_id,
            sender_id=sender_id,
            receiver_id=self.sender_id,
            message_type=MessageType.RESPONSE,
            skill_id=self.skill_id,
            content=content,
        )


class AgentRegistry(ABC):
    """
    Agent 注册中心抽象
    
    定义 Agent 发现与注册的标准接口。
    """
    
    @abstractmethod
    async def register(self, agent_card: AgentCard) -> bool:
        """注册 Agent"""
        pass
    
    @abstractmethod
    async def unregister(self, agent_id: str) -> bool:
        """注销 Agent"""
        pass
    
    @abstractmethod
    async def discover(
        self,
        skill_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[AgentCard]:
        """发现 Agent"""
        pass
    
    @abstractmethod
    async def get_agent(self, agent_id: str) -> Optional[AgentCard]:
        """获取 Agent 信息"""
        pass
    
    @abstractmethod
    async def heartbeat(self, agent_id: str) -> bool:
        """心跳"""
        pass


class LocalAgentRegistry(AgentRegistry):
    """
    本地 Agent 注册中心
    
    适用于单机开发和测试。
    """
    
    def __init__(self):
        self._agents: Dict[str, AgentCard] = {}
        self._heartbeats: Dict[str, float] = {}
        self._lock = asyncio.Lock()
    
    async def register(self, agent_card: AgentCard) -> bool:
        """注册 Agent"""
        async with self._lock:
            self._agents[agent_card.agent_id] = agent_card
            self._heartbeats[agent_card.agent_id] = time.time()
        return True
    
    async def unregister(self, agent_id: str) -> bool:
        """注销 Agent"""
        async with self._lock:
            self._agents.pop(agent_id, None)
            self._heartbeats.pop(agent_id, None)
        return True
    
    async def discover(
        self,
        skill_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[AgentCard]:
        """发现 Agent"""
        results = []
        
        for agent in self._agents.values():
            # 检查技能
            if skill_id:
                if not any(s.id == skill_id for s in agent.skills):
                    continue
            
            # 检查标签
            if tags:
                agent_tags = set()
                for skill in agent.skills:
                    agent_tags.update(skill.tags)
                if not any(t in agent_tags for t in tags):
                    continue
            
            results.append(agent)
        
        return results
    
    async def get_agent(self, agent_id: str) -> Optional[AgentCard]:
        """获取 Agent 信息"""
        return self._agents.get(agent_id)
    
    async def heartbeat(self, agent_id: str) -> bool:
        """心跳"""
        if agent_id in self._agents:
            self._heartbeats[agent_id] = time.time()
            return True
        return False
    
    async def cleanup_stale(self, timeout: int = 300) -> int:
        """
        清理过期 Agent
        
        Args:
            timeout: 超时时间（秒）
        
        Returns:
            int: 清理的 Agent 数量
        """
        now = time.time()
        stale_agents = []
        
        async with self._lock:
            for agent_id, last_heartbeat in self._heartbeats.items():
                if now - last_heartbeat > timeout:
                    stale_agents.append(agent_id)
            
            for agent_id in stale_agents:
                self._agents.pop(agent_id, None)
                self._heartbeats.pop(agent_id, None)
        
        return len(stale_agents)


class A2AClient:
    """
    A2A 客户端
    
    用于发送 A2A 消息和调用远程 Agent。
    """
    
    def __init__(
        self,
        agent_id: str,
        registry: AgentRegistry,
    ):
        self.agent_id = agent_id
        self.registry = registry
    
    async def discover_agents(
        self,
        skill_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[AgentCard]:
        """发现 Agent"""
        return await self.registry.discover(skill_id, tags)
    
    async def send_message(
        self,
        message: A2AMessage,
        endpoint: Optional[str] = None,
    ) -> Optional[A2AMessage]:
        """
        发送消息
        
        Args:
            message: 消息
            endpoint: 端点（可选）
        
        Returns:
            A2AMessage: 响应消息
        """
        # 获取目标 Agent
        if message.receiver_id:
            target_agent = await self.registry.get_agent(message.receiver_id)
            if not target_agent:
                return None
            
            # 使用 HTTP 发送
            if endpoint or target_agent.endpoints.get("http"):
                return await self._send_http(
                    message,
                    endpoint or target_agent.endpoints["http"],
                )
        
        return None
    
    async def _send_http(
        self,
        message: A2AMessage,
        endpoint: str,
    ) -> Optional[A2AMessage]:
        """通过 HTTP 发送消息"""
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{endpoint}/a2a/message",
                    json=message.to_dict(),
                    timeout=60.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return A2AMessage.from_dict(data)
        
        except Exception as e:
            # 降级处理
            pass
        
        return None
    
    async def invoke_skill(
        self,
        agent_id: str,
        skill_id: str,
        input_data: Any,
        timeout: float = 60.0,
    ) -> Any:
        """
        调用远程技能
        
        Args:
            agent_id: 目标 Agent ID
            skill_id: 技能 ID
            input_data: 输入数据
            timeout: 超时时间
        
        Returns:
            Any: 执行结果
        """
        # 创建请求消息
        message = A2AMessage(
            sender_id=self.agent_id,
            receiver_id=agent_id,
            message_type=MessageType.REQUEST,
            skill_id=skill_id,
            content=input_data,
        )
        
        # 发送并等待响应
        response = await self.send_message(message)
        
        if response and response.message_type == MessageType.RESPONSE:
            return response.content
        
        return None


class A2AServer:
    """
    A2A 服务端
    
    提供 Agent 的 A2A 服务能力。
    """
    
    def __init__(
        self,
        agent_card: AgentCard,
        registry: AgentRegistry,
    ):
        self.agent_card = agent_card
        self.registry = registry
        self._skill_handlers: Dict[str, Callable] = {}
    
    def register_skill_handler(
        self,
        skill_id: str,
        handler: Callable,
    ) -> None:
        """
        注册技能处理器
        
        Args:
            skill_id: 技能 ID
            handler: 处理函数
        """
        self._skill_handlers[skill_id] = handler
    
    async def start(self) -> None:
        """启动服务"""
        await self.registry.register(self.agent_card)
    
    async def stop(self) -> None:
        """停止服务"""
        await self.registry.unregister(self.agent_card.agent_id)
    
    async def handle_message(
        self,
        message: A2AMessage,
    ) -> Optional[A2AMessage]:
        """
        处理消息
        
        Args:
            message: 消息
        
        Returns:
            A2AMessage: 响应消息
        """
        # 处理心跳
        if message.message_type == MessageType.HEARTBEAT:
            await self.registry.heartbeat(self.agent_card.agent_id)
            return message.create_response(
                content={"status": "ok"},
                sender_id=self.agent_card.agent_id,
            )
        
        # 处理技能调用
        if message.message_type == MessageType.REQUEST and message.skill_id:
            handler = self._skill_handlers.get(message.skill_id)
            
            if handler:
                try:
                    import asyncio
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(message.content)
                    else:
                        result = handler(message.content)
                    
                    return message.create_response(
                        content=result,
                        sender_id=self.agent_card.agent_id,
                    )
                
                except Exception as e:
                    return message.create_response(
                        content={"error": str(e)},
                        sender_id=self.agent_card.agent_id,
                    )
        
        return None


def create_agent_card(
    agent_id: str,
    name: str,
    description: str,
    skills: Optional[List[Dict[str, Any]]] = None,
    endpoints: Optional[Dict[str, str]] = None,
) -> AgentCard:
    """
    创建 Agent 名片
    
    Args:
        agent_id: Agent ID
        name: 名称
        description: 描述
        skills: 技能列表
        endpoints: 端点
    
    Returns:
        AgentCard: Agent 名片
    """
    skill_objects = []
    if skills:
        for s in skills:
            skill_objects.append(AgentSkill(
                id=s["id"],
                name=s["name"],
                description=s.get("description", ""),
                input_schema=s.get("input_schema"),
                output_schema=s.get("output_schema"),
                tags=s.get("tags", []),
            ))
    
    return AgentCard(
        agent_id=agent_id,
        name=name,
        description=description,
        skills=skill_objects,
        endpoints=endpoints or {},
    )


# 全局注册中心
_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """获取全局注册中心"""
    global _registry
    if _registry is None:
        _registry = LocalAgentRegistry()
    return _registry
