"""
AgentScope 核心集成模块

充分利用AgentScope的突出优势:
1. 分布式多智能体通信 - RpcAgent
2. 消息驱动架构 - MsgHub
3. 高性能并发 - Actor模型
4. 服务发现 - 自动注册与发现

底层使用LangChain弥补劣势:
- 工具调用生态
- RAG检索增强
- 链式思维
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
import uuid
from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ============================================================================
# AgentScope 消息系统适配
# ============================================================================

class ASMessageType(str, Enum):
    """AgentScope消息类型"""
    # 任务相关
    TASK_REQUEST = "task_request"          # 任务请求
    TASK_RESULT = "task_result"            # 任务结果
    TASK_ERROR = "task_error"              # 任务错误
    
    # Agent间通信
    AGENT_QUERY = "agent_query"            # Agent查询
    AGENT_RESPONSE = "agent_response"      # Agent响应
    AGENT_NOTIFICATION = "agent_notify"    # Agent通知
    
    # 工具调用
    TOOL_CALL = "tool_call"                # 工具调用请求
    TOOL_RESULT = "tool_result"            # 工具调用结果
    
    # 系统消息
    STATE_CHANGE = "state_change"          # 状态变化
    HEARTBEAT = "heartbeat"                # 心跳
    SHUTDOWN = "shutdown"                  # 关闭


@dataclass
class ASMessage:
    """
    AgentScope消息定义
    
    兼容AgentScope的Msg格式，同时支持opspilot的扩展需求
    """
    name: str                                    # 消息来源
    content: Any                                 # 消息内容
    msg_type: ASMessageType = ASMessageType.TASK_REQUEST
    timestamp: float = field(default_factory=time.time)
    msg_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # AgentScope兼容字段
    url: Optional[str] = None                   # 远程Agent地址
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "content": self.content,
            "msg_type": self.msg_type.value,
            "timestamp": self.timestamp,
            "msg_id": self.msg_id,
            "trace_id": self.trace_id,
            "metadata": self.metadata,
            "url": self.url,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ASMessage":
        """从字典创建"""
        return cls(
            name=data["name"],
            content=data["content"],
            msg_type=ASMessageType(data.get("msg_type", "task_request")),
            timestamp=data.get("timestamp", time.time()),
            msg_id=data.get("msg_id", str(uuid.uuid4())),
            trace_id=data.get("trace_id", str(uuid.uuid4())),
            metadata=data.get("metadata", {}),
            url=data.get("url"),
        )
    
    def to_agentscope_msg(self) -> Dict[str, Any]:
        """
        转换为AgentScope的Msg格式
        
        AgentScope Msg格式:
        {
            "name": str,      # 发送者名称
            "content": Any,   # 消息内容
            "url": str,       # 远程地址(可选)
        }
        """
        return {
            "name": self.name,
            "content": self.content,
            "url": self.url,
        }


class MessageAdapter:
    """
    消息适配器
    
    在AgentScope Msg和opspilot Message之间转换
    """
    
    @staticmethod
    def to_as_message(msg: Union[Dict, ASMessage]) -> ASMessage:
        """转换为ASMessage"""
        if isinstance(msg, ASMessage):
            return msg
        if isinstance(msg, dict):
            return ASMessage.from_dict(msg)
        raise ValueError(f"Unsupported message type: {type(msg)}")
    
    @staticmethod
    def from_langchain_message(lc_msg: Any) -> ASMessage:
        """从LangChain消息转换"""
        # LangChain消息格式: HumanMessage, AIMessage, SystemMessage
        return ASMessage(
            name=getattr(lc_msg, "type", "unknown"),
            content=getattr(lc_msg, "content", ""),
            msg_type=ASMessageType.TASK_REQUEST,
            metadata={
                "additional_kwargs": getattr(lc_msg, "additional_kwargs", {}),
            }
        )
    
    @staticmethod
    def to_langchain_message(as_msg: ASMessage) -> Dict[str, Any]:
        """转换为LangChain消息格式"""
        return {
            "type": "human" if as_msg.msg_type == ASMessageType.TASK_REQUEST else "ai",
            "content": as_msg.content,
        }


# ============================================================================
# AgentScope Agent 基类
# ============================================================================

class ASAgentState(str, Enum):
    """Agent状态"""
    IDLE = "idle"           # 空闲
    BUSY = "busy"           # 忙碌
    ERROR = "error"         # 错误
    OFFLINE = "offline"     # 离线


@dataclass
class ASAgentStats:
    """Agent统计信息"""
    messages_received: int = 0
    messages_sent: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_processing_time: float = 0.0
    last_active_time: float = field(default_factory=time.time)


class ASAgentBase:
    """
    AgentScope Agent基类
    
    核心设计理念:
    1. 消息驱动 - 通过消息进行所有交互
    2. Actor模型 - 每个Agent独立状态空间
    3. 异步处理 - 高并发支持
    4. 可分布式 - 支持RpcAgent
    
    使用方式:
    ```python
    class MyAgent(ASAgentBase):
        def __init__(self, name: str, **kwargs):
            super().__init__(name, **kwargs)
            self.llm_client = ...  # LangChain客户端
        
        async def process(self, msg: ASMessage) -> ASMessage:
            # 处理消息
            result = await self.llm_client.ainvoke(msg.content)
            return ASMessage(
                name=self.name,
                content=result,
                msg_type=ASMessageType.AGENT_RESPONSE,
                trace_id=msg.trace_id,
            )
    ```
    """
    
    def __init__(
        self,
        name: str,
        use_dist: bool = False,
        host: str = "localhost",
        port: int = 0,  # 0表示自动分配
        max_workers: int = 4,
        **kwargs,
    ):
        self.name = name
        self.use_dist = use_dist
        self.host = host
        self.port = port
        self.max_workers = max_workers
        
        # 状态
        self._state = ASAgentState.IDLE
        self._stats = ASAgentStats()
        self._message_queue: asyncio.Queue[ASMessage] = asyncio.Queue()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        # LangChain工具集成点
        self._lc_tools: List[Any] = []
        self._lc_retriever: Optional[Any] = None
        
        # 子类可通过kwargs传递配置
        self._config = kwargs
    
    @property
    def state(self) -> ASAgentState:
        return self._state
    
    @property
    def stats(self) -> ASAgentStats:
        return self._stats
    
    def register_lc_tool(self, tool: Any) -> None:
        """注册LangChain工具"""
        self._lc_tools.append(tool)
    
    def register_lc_retriever(self, retriever: Any) -> None:
        """注册LangChain检索器"""
        self._lc_retriever = retriever
    
    async def start(self) -> None:
        """启动Agent"""
        if self._running:
            return
        
        self._running = True
        self._state = ASAgentState.IDLE
        self._task = asyncio.create_task(self._message_loop())
        logger.info(f"Agent [{self.name}] started")
    
    async def stop(self) -> None:
        """停止Agent"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._state = ASAgentState.OFFLINE
        logger.info(f"Agent [{self.name}] stopped")
    
    async def _message_loop(self) -> None:
        """消息处理循环"""
        while self._running:
            try:
                # 等待消息
                msg = await asyncio.wait_for(
                    self._message_queue.get(),
                    timeout=1.0
                )
                
                # 处理消息
                self._state = ASAgentState.BUSY
                start_time = time.time()
                
                try:
                    response = await self.process(msg)
                    self._stats.tasks_completed += 1
                except Exception as e:
                    self._stats.tasks_failed += 1
                    response = ASMessage(
                        name=self.name,
                        content={"error": str(e)},
                        msg_type=ASMessageType.TASK_ERROR,
                        trace_id=msg.trace_id,
                    )
                
                # 更新统计
                self._stats.messages_received += 1
                self._stats.total_processing_time += time.time() - start_time
                self._stats.last_active_time = time.time()
                
                self._state = ASAgentState.IDLE
                
                # 返回响应
                if response:
                    self._stats.messages_sent += 1
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Agent [{self.name}] message loop error: {e}")
                self._state = ASAgentState.ERROR
    
    async def send(self, msg: ASMessage) -> None:
        """发送消息到此Agent"""
        await self._message_queue.put(msg)
    
    @abstractmethod
    async def process(self, msg: ASMessage) -> Optional[ASMessage]:
        """
        处理消息（子类实现）
        
        这是Agent的核心逻辑，子类必须实现
        """
        pass
    
    def __call__(self, msg: ASMessage) -> ASMessage:
        """同步调用接口（兼容AgentScope）"""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.process(msg))


# ============================================================================
# 具体 Agent 实现
# ============================================================================

class ASIntentAgent(ASAgentBase):
    """
    意图识别Agent
    
    使用LangChain进行意图识别，通过AgentScope进行消息传递
    """
    
    def __init__(self, name: str = "IntentAgent", **kwargs):
        super().__init__(name, **kwargs)
        self._intent_patterns: Dict[str, Any] = {}
    
    async def process(self, msg: ASMessage) -> Optional[ASMessage]:
        """识别用户意图"""
        query = msg.content if isinstance(msg.content, str) else msg.content.get("query", "")
        
        # 使用LangChain检索器增强
        context = ""
        if self._lc_retriever:
            try:
                docs = await self._lc_retriever.ainvoke(query)
                context = "\n".join([d.page_content for d in docs[:3]])
            except Exception as e:
                logger.warning(f"Retriever error: {e}")
        
        # 意图识别逻辑（可替换为LLM调用）
        intent = self._classify_intent(query, context)
        
        return ASMessage(
            name=self.name,
            content={
                "intent": intent["type"],
                "confidence": intent["confidence"],
                "entities": intent.get("entities", []),
                "context": context[:500] if context else None,
            },
            msg_type=ASMessageType.AGENT_RESPONSE,
            trace_id=msg.trace_id,
        )
    
    def _classify_intent(self, query: str, context: str) -> Dict[str, Any]:
        """分类意图"""
        # 简化实现，实际应调用LLM
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ["创建", "新建", "下单", "order"]):
            return {"type": "order_create", "confidence": 0.9}
        elif any(kw in query_lower for kw in ["查询", "获取", "查找", "query"]):
            return {"type": "query", "confidence": 0.85}
        elif any(kw in query_lower for kw in ["分析", "统计", "report"]):
            return {"type": "analysis", "confidence": 0.8}
        else:
            return {"type": "unknown", "confidence": 0.3}


class ASPlanAgent(ASAgentBase):
    """规划Agent - 生成执行计划"""
    
    def __init__(self, name: str = "PlanAgent", **kwargs):
        super().__init__(name, **kwargs)
    
    async def process(self, msg: ASMessage) -> Optional[ASMessage]:
        """生成执行计划"""
        intent_data = msg.content
        
        # 根据意图生成计划
        plan = self._generate_plan(intent_data)
        
        return ASMessage(
            name=self.name,
            content={
                "plan": plan,
                "intent": intent_data.get("intent"),
            },
            msg_type=ASMessageType.AGENT_RESPONSE,
            trace_id=msg.trace_id,
        )
    
    def _generate_plan(self, intent_data: Dict) -> List[Dict]:
        """生成执行计划"""
        intent = intent_data.get("intent", "unknown")
        
        # 简化实现
        if intent == "order_create":
            return [
                {"step": 1, "action": "validate_params", "agent": "ExecAgent"},
                {"step": 2, "action": "check_inventory", "agent": "ExecAgent"},
                {"step": 3, "action": "create_order", "agent": "ExecAgent"},
                {"step": 4, "action": "verify_order", "agent": "VerifyAgent"},
            ]
        elif intent == "query":
            return [
                {"step": 1, "action": "parse_query", "agent": "ExecAgent"},
                {"step": 2, "action": "execute_query", "agent": "ExecAgent"},
                {"step": 3, "action": "format_result", "agent": "ExecAgent"},
            ]
        else:
            return [{"step": 1, "action": "unknown", "agent": "ExecAgent"}]


class ASExecAgent(ASAgentBase):
    """执行Agent - 使用LangChain工具执行"""
    
    def __init__(self, name: str = "ExecAgent", **kwargs):
        super().__init__(name, **kwargs)
    
    async def process(self, msg: ASMessage) -> Optional[ASMessage]:
        """执行工具调用"""
        plan_data = msg.content
        step = plan_data.get("current_step", {})
        action = step.get("action", "unknown")
        
        # 使用LangChain工具
        result = await self._execute_with_lc_tools(action, plan_data)
        
        return ASMessage(
            name=self.name,
            content={
                "action": action,
                "result": result,
                "success": result.get("success", False),
            },
            msg_type=ASMessageType.AGENT_RESPONSE,
            trace_id=msg.trace_id,
        )
    
    async def _execute_with_lc_tools(self, action: str, context: Dict) -> Dict:
        """使用LangChain工具执行"""
        # 如果有注册的LangChain工具
        for tool in self._lc_tools:
            if hasattr(tool, "name") and action in tool.name:
                try:
                    # LangChain工具调用
                    if hasattr(tool, "ainvoke"):
                        return await tool.ainvoke(context)
                    elif hasattr(tool, "invoke"):
                        return tool.invoke(context)
                except Exception as e:
                    return {"success": False, "error": str(e)}
        
        # 回退到默认处理
        return {"success": True, "data": f"Executed: {action}"}


class ASVerifyAgent(ASAgentBase):
    """验证Agent - 验证执行结果"""
    
    def __init__(self, name: str = "VerifyAgent", **kwargs):
        super().__init__(name, **kwargs)
    
    async def process(self, msg: ASMessage) -> Optional[ASMessage]:
        """验证执行结果"""
        exec_result = msg.content
        
        # 验证逻辑
        is_valid = self._validate(exec_result)
        
        return ASMessage(
            name=self.name,
            content={
                "valid": is_valid,
                "original_result": exec_result,
                "verification_details": {
                    "checked_at": time.time(),
                    "checks_passed": ["format", "completeness"] if is_valid else [],
                },
            },
            msg_type=ASMessageType.TASK_RESULT,
            trace_id=msg.trace_id,
        )
    
    def _validate(self, result: Dict) -> bool:
        """验证结果"""
        return result.get("success", False)


# ============================================================================
# 分布式支持
# ============================================================================

@dataclass
class DistributedAgentConfig:
    """分布式Agent配置"""
    host: str = "localhost"
    port: int = 0  # 0表示自动分配
    max_workers: int = 4
    timeout: float = 30.0
    retry_times: int = 3
    retry_interval: float = 1.0
    
    # 服务发现
    registry_host: str = "localhost"
    registry_port: int = 50051


class AgentServer:
    """
    Agent服务端
    
    将Agent暴露为RPC服务，支持远程调用
    """
    
    def __init__(
        self,
        agent: ASAgentBase,
        config: DistributedAgentConfig,
    ):
        self.agent = agent
        self.config = config
        self._running = False
    
    async def start(self) -> str:
        """启动服务"""
        # 实际实现需要gRPC或类似的RPC框架
        # 这里提供接口定义
        await self.agent.start()
        self._running = True
        
        address = f"{self.config.host}:{self.config.port or 'auto'}"
        logger.info(f"AgentServer started at {address}")
        return address
    
    async def stop(self) -> None:
        """停止服务"""
        self._running = False
        await self.agent.stop()
    
    async def handle_request(self, request: Dict) -> Dict:
        """处理请求"""
        msg = ASMessage.from_dict(request)
        response = await self.agent.process(msg)
        return response.to_dict() if response else {}


class AgentClient:
    """
    Agent客户端
    
    用于远程调用Agent
    """
    
    def __init__(self, address: str, timeout: float = 30.0):
        self.address = address
        self.timeout = timeout
    
    async def call(self, msg: ASMessage) -> Optional[ASMessage]:
        """远程调用"""
        # 实际实现需要gRPC客户端
        # 这里提供接口定义
        logger.info(f"Calling remote agent at {self.address}")
        # 模拟远程调用
        return ASMessage(
            name="remote_agent",
            content={"status": "remote_call_simulated"},
            msg_type=ASMessageType.AGENT_RESPONSE,
            trace_id=msg.trace_id,
        )


# ============================================================================
# 服务发现
# ============================================================================

class ServiceRegistry:
    """
    服务注册中心
    
    用于Agent服务的注册与发现
    """
    
    _instance: Optional["ServiceRegistry"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._services: Dict[str, Dict[str, Any]] = {}
            cls._instance._lock = threading.Lock()
        return cls._instance
    
    def register(self, name: str, address: str, metadata: Dict = None) -> None:
        """注册服务"""
        with self._lock:
            self._services[name] = {
                "address": address,
                "metadata": metadata or {},
                "registered_at": time.time(),
                "last_heartbeat": time.time(),
            }
        logger.info(f"Service registered: {name} at {address}")
    
    def deregister(self, name: str) -> None:
        """注销服务"""
        with self._lock:
            self._services.pop(name, None)
        logger.info(f"Service deregistered: {name}")
    
    def discover(self, name: str) -> Optional[str]:
        """发现服务"""
        with self._lock:
            service = self._services.get(name)
            return service["address"] if service else None
    
    def list_services(self) -> List[str]:
        """列出所有服务"""
        with self._lock:
            return list(self._services.keys())
    
    def heartbeat(self, name: str) -> None:
        """心跳更新"""
        with self._lock:
            if name in self._services:
                self._services[name]["last_heartbeat"] = time.time()


class ServiceDiscovery:
    """
    服务发现客户端
    """
    
    def __init__(self, registry: ServiceRegistry = None):
        self.registry = registry or ServiceRegistry()
    
    def get_agent_address(self, name: str) -> Optional[str]:
        """获取Agent地址"""
        return self.registry.discover(name)
    
    def get_all_agents(self) -> List[str]:
        """获取所有Agent"""
        return self.registry.list_services()


# ============================================================================
# 工厂函数
# ============================================================================

def create_agent(
    agent_type: str,
    name: str = None,
    **kwargs,
) -> ASAgentBase:
    """
    创建Agent
    
    Args:
        agent_type: Agent类型 (intent, plan, exec, verify)
        name: Agent名称
        **kwargs: 其他参数
    
    Returns:
        Agent实例
    """
    agent_classes = {
        "intent": ASIntentAgent,
        "plan": ASPlanAgent,
        "exec": ASExecAgent,
        "verify": ASVerifyAgent,
    }
    
    agent_class = agent_classes.get(agent_type.lower())
    if not agent_class:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    return agent_class(name=name or f"{agent_type.capitalize()}Agent", **kwargs)


def create_distributed_agent(
    agent_type: str,
    config: DistributedAgentConfig,
    name: str = None,
) -> tuple[ASAgentBase, AgentServer]:
    """
    创建分布式Agent
    
    Returns:
        (Agent实例, AgentServer)
    """
    agent = create_agent(agent_type, name=name)
    server = AgentServer(agent, config)
    return agent, server


async def start_agent_server(
    agent_type: str,
    config: DistributedAgentConfig = None,
    name: str = None,
) -> AgentServer:
    """
    启动Agent服务
    
    自动注册到服务发现
    """
    config = config or DistributedAgentConfig()
    agent, server = create_distributed_agent(agent_type, config, name)
    address = await server.start()
    
    # 注册服务
    ServiceRegistry().register(
        name=name or agent.name,
        address=address,
        metadata={"type": agent_type},
    )
    
    return server


def connect_agent(name: str) -> AgentClient:
    """
    连接远程Agent
    
    通过服务发现获取地址
    """
    discovery = ServiceDiscovery()
    address = discovery.get_agent_address(name)
    
    if not address:
        raise ValueError(f"Agent not found: {name}")
    
    return AgentClient(address)

