"""
Agent Actor模式 - Agent Actor Pattern

实现Actor模型的Agent，支持独立运行和分布式扩展。

核心功能：
1. Actor生命周期管理
2. 消息处理循环
3. 状态隔离
4. 分布式支持
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

from opspilot.agents.msg_hub import (
    AgentMessage,
    MessageType,
    MessageHub,
    get_message_hub,
)
from opspilot.agents.base import AgentRole, AgentConfig, AgentContext, AgentOutput
from opspilot.utils.exceptions import AgentError


class ActorState(Enum):
    """Actor状态"""
    IDLE = "idle"            # 空闲
    RUNNING = "running"      # 运行中
    WAITING = "waiting"      # 等待消息
    STOPPED = "stopped"      # 已停止
    ERROR = "error"          # 错误


@dataclass
class ActorStats:
    """Actor统计信息"""
    messages_received: int = 0
    messages_sent: int = 0
    tasks_completed: int = 0
    errors: int = 0
    total_processing_time: float = 0.0
    last_active_time: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "messages_received": self.messages_received,
            "messages_sent": self.messages_sent,
            "tasks_completed": self.tasks_completed,
            "errors": self.errors,
            "total_processing_time": self.total_processing_time,
            "last_active_time": self.last_active_time,
        }


class BaseActor(ABC):
    """
    Actor基类
    
    实现Actor模型的核心特性：
    - 独立的状态空间
    - 消息驱动的行为
    - 异步消息处理
    - 状态隔离
    
    示例:
        >>> class MyActor(BaseActor):
        ...     async def handle_message(self, msg: AgentMessage) -> Optional[AgentMessage]:
        ...         # 处理消息
        ...         return reply
    """
    
    def __init__(
        self,
        name: str,
        role: AgentRole,
        config: Optional[AgentConfig] = None,
        subscribed_types: Optional[Set[MessageType]] = None,
    ):
        """
        初始化Actor
        
        Args:
            name: Actor名称
            role: Agent角色
            config: 配置
            subscribed_types: 订阅的消息类型
        """
        self.name = name
        self.role = role
        self.config = config or AgentConfig()
        self.subscribed_types = subscribed_types or {
            MessageType.TASK_REQUEST,
            MessageType.AGENT_MESSAGE,
        }
        
        # 状态
        self._state = ActorState.IDLE
        self._context: Dict[str, Any] = {}
        self._stats = ActorStats()
        
        # 消息队列
        self._message_queue: asyncio.Queue = asyncio.Queue()
        
        # 消息中心
        self._hub = get_message_hub()
        
        # 注册到消息中心
        self._hub.subscribe(
            self.name,
            handler=self._on_message_received,
            message_types=self.subscribed_types,
        )
        
        # 运行任务
        self._run_task: Optional[asyncio.Task] = None
    
    @property
    def state(self) -> ActorState:
        """获取当前状态"""
        return self._state
    
    @property
    def stats(self) -> ActorStats:
        """获取统计信息"""
        return self._stats
    
    def _on_message_received(self, msg: AgentMessage) -> None:
        """消息接收回调"""
        self._message_queue.put_nowait(msg)
        self._stats.messages_received += 1
        self._stats.last_active_time = time.time()
    
    async def start(self) -> None:
        """启动Actor"""
        if self._state == ActorState.RUNNING:
            return
        
        self._state = ActorState.RUNNING
        self._run_task = asyncio.create_task(self._run_loop())
    
    async def stop(self) -> None:
        """停止Actor"""
        self._state = ActorState.STOPPED
        
        if self._run_task:
            self._run_task.cancel()
            try:
                await self._run_task
            except asyncio.CancelledError:
                pass
        
        # 取消订阅
        self._hub.unsubscribe(self.name)
    
    async def _run_loop(self) -> None:
        """主循环"""
        while self._state == ActorState.RUNNING:
            try:
                # 等待消息
                self._state = ActorState.WAITING
                
                try:
                    msg = await asyncio.wait_for(
                        self._message_queue.get(),
                        timeout=1.0,
                    )
                except asyncio.TimeoutError:
                    continue
                
                # 处理消息
                self._state = ActorState.RUNNING
                start_time = time.time()
                
                try:
                    response = await self.handle_message(msg)
                    
                    # 发送响应
                    if response:
                        await self.send(response)
                    
                    self._stats.tasks_completed += 1
                
                except Exception as e:
                    self._stats.errors += 1
                    await self._handle_error(e, msg)
                
                finally:
                    elapsed = time.time() - start_time
                    self._stats.total_processing_time += elapsed
            
            except asyncio.CancelledError:
                break
            
            except Exception as e:
                self._stats.errors += 1
                self._state = ActorState.ERROR
        
        self._state = ActorState.STOPPED
    
    @abstractmethod
    async def handle_message(self, msg: AgentMessage) -> Optional[AgentMessage]:
        """
        处理消息（子类实现）
        
        Args:
            msg: 接收的消息
        
        Returns:
            响应消息（可选）
        """
        pass
    
    async def _handle_error(self, error: Exception, msg: AgentMessage) -> None:
        """处理错误"""
        error_msg = AgentMessage(
            name=self.name,
            content={"error": str(error), "original_msg": msg.message_id},
            msg_type=MessageType.ERROR,
            sender=self.name,
            trace_id=msg.trace_id,
        )
        await self.send(error_msg)
    
    async def send(
        self,
        msg: AgentMessage,
        receiver: Optional[str] = None,
    ) -> bool:
        """
        发送消息
        
        Args:
            msg: 消息对象
            receiver: 接收者（可选）
        
        Returns:
            是否发送成功
        """
        msg.sender = self.name
        if receiver:
            msg.receiver = receiver
        
        self._stats.messages_sent += 1
        
        if receiver:
            return self._hub.send_to(msg, receiver)
        else:
            self._hub.publish(msg)
            return True
    
    async def broadcast(
        self,
        content: Any,
        exclude: Optional[Set[str]] = None,
    ) -> int:
        """
        广播消息
        
        Args:
            content: 消息内容
            exclude: 排除的接收者
        
        Returns:
            接收者数量
        """
        msg = AgentMessage(
            name=self.name,
            content=content,
            msg_type=MessageType.AGENT_BROADCAST,
            sender=self.name,
        )
        return self._hub.broadcast(msg, exclude)
    
    def set_context(self, key: str, value: Any) -> None:
        """设置上下文"""
        self._context[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文"""
        return self._context.get(key, default)
    
    def clear_context(self) -> None:
        """清空上下文"""
        self._context.clear()


class IntentActor(BaseActor):
    """
    意图识别Actor
    
    处理用户查询，识别意图。
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(
            name="intent_agent",
            role=AgentRole.INTENT,
            config=config,
            subscribed_types={MessageType.TASK_REQUEST},
        )
    
    async def handle_message(self, msg: AgentMessage) -> Optional[AgentMessage]:
        """处理消息"""
        # 支持多种消息类型
        if msg.msg_type not in (MessageType.TASK_REQUEST, MessageType.AGENT_MESSAGE):
            return None
        
        # 提取用户查询
        query = msg.content.get("query") if isinstance(msg.content, dict) else msg.content
        
        # 意图识别（简化版，实际使用LLM）
        intent = self._classify_intent(query)
        
        # 返回结果
        return msg.reply(
            content={
                "intent": intent,
                "query": query,
                "confidence": 0.85,
            },
            sender=self.name,
        )
    
    def _classify_intent(self, query: str) -> str:
        """分类意图"""
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ["创建", "下单", "采购"]):
            return "order_create"
        elif any(kw in query_lower for kw in ["查询", "搜索", "查找"]):
            return "query"
        elif any(kw in query_lower for kw in ["修改", "更新", "变更"]):
            return "update"
        elif any(kw in query_lower for kw in ["取消", "删除", "作废"]):
            return "cancel"
        else:
            return "unknown"


class PlanActor(BaseActor):
    """
    规划Actor
    
    根据意图生成执行计划。
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(
            name="plan_agent",
            role=AgentRole.PLANNING,
            config=config,
            subscribed_types={MessageType.AGENT_MESSAGE},
        )
        
        # 监听意图识别结果
        self._hub.subscribe(
            self.name,
            message_types={MessageType.AGENT_MESSAGE},
        )
    
    async def handle_message(self, msg: AgentMessage) -> Optional[AgentMessage]:
        """处理消息"""
        content = msg.content
        
        if not isinstance(content, dict):
            return None
        
        intent = content.get("intent")
        if not intent:
            return None
        
        # 生成计划
        plan = self._generate_plan(intent)
        
        return msg.reply(
            content={
                "plan": plan,
                "intent": intent,
            },
            sender=self.name,
        )
    
    def _generate_plan(self, intent: str) -> List[Dict[str, Any]]:
        """生成执行计划"""
        # 简化的计划生成
        plan_templates = {
            "order_create": [
                {"step": 1, "action": "query_supplier", "description": "查询供应商"},
                {"step": 2, "action": "check_inventory", "description": "检查库存"},
                {"step": 3, "action": "create_order", "description": "创建订单"},
                {"step": 4, "action": "verify_order", "description": "验证订单"},
            ],
            "query": [
                {"step": 1, "action": "search", "description": "搜索信息"},
                {"step": 2, "action": "format_result", "description": "格式化结果"},
            ],
            "update": [
                {"step": 1, "action": "query_target", "description": "查询目标"},
                {"step": 2, "action": "validate_change", "description": "验证变更"},
                {"step": 3, "action": "apply_change", "description": "应用变更"},
            ],
        }
        
        return plan_templates.get(intent, [])


class ExecActor(BaseActor):
    """
    执行Actor
    
    执行计划中的步骤。
    """
    
    def __init__(
        self,
        name: str = "exec_agent",
        tool_registry: Optional[Dict[str, Any]] = None,
        config: Optional[AgentConfig] = None,
    ):
        super().__init__(
            name=name,
            role=AgentRole.EXECUTION,
            config=config,
            subscribed_types={MessageType.AGENT_MESSAGE, MessageType.TOOL_CALL},
        )
        self.tool_registry = tool_registry or {}
    
    async def handle_message(self, msg: AgentMessage) -> Optional[AgentMessage]:
        """处理消息"""
        if msg.msg_type == MessageType.TOOL_CALL:
            return await self._handle_tool_call(msg)
        else:
            return await self._handle_plan(msg)
    
    async def _handle_plan(self, msg: AgentMessage) -> Optional[AgentMessage]:
        """处理计划"""
        content = msg.content
        
        if not isinstance(content, dict):
            return None
        
        plan = content.get("plan", [])
        results = []
        
        for step in plan:
            action = step.get("action")
            result = await self._execute_step(action)
            results.append(result)
        
        return msg.reply(
            content={
                "results": results,
                "plan": plan,
            },
            sender=self.name,
        )
    
    async def _handle_tool_call(self, msg: AgentMessage) -> Optional[AgentMessage]:
        """处理工具调用"""
        content = msg.content
        
        tool_name = content.get("tool")
        params = content.get("params", {})
        
        # 执行工具
        result = await self._execute_tool(tool_name, params)
        
        return msg.reply(
            content={
                "tool": tool_name,
                "result": result,
            },
            msg_type=MessageType.TOOL_RESULT,
            sender=self.name,
        )
    
    async def _execute_step(self, action: str) -> Dict[str, Any]:
        """执行步骤"""
        # 简化的执行逻辑
        return {
            "action": action,
            "status": "completed",
            "output": f"执行 {action} 完成",
        }
    
    async def _execute_tool(self, tool_name: str, params: Dict) -> Any:
        """执行工具"""
        if tool_name in self.tool_registry:
            tool = self.tool_registry[tool_name]
            if callable(tool):
                return await tool(params) if asyncio.iscoroutinefunction(tool) else tool(params)
        
        return {"error": f"工具 {tool_name} 不存在"}


class VerifyActor(BaseActor):
    """
    验证Actor
    
    验证执行结果。
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(
            name="verify_agent",
            role=AgentRole.VERIFICATION,
            config=config,
        )
    
    async def handle_message(self, msg: AgentMessage) -> Optional[AgentMessage]:
        """处理消息"""
        content = msg.content
        
        if not isinstance(content, dict):
            return None
        
        results = content.get("results", [])
        
        # 验证结果
        verification = self._verify_results(results)
        
        return msg.reply(
            content={
                "verification": verification,
                "success": verification.get("passed", False),
            },
            sender=self.name,
        )
    
    def _verify_results(self, results: List[Dict]) -> Dict[str, Any]:
        """验证结果"""
        if not results:
            return {"passed": False, "reason": "无执行结果"}
        
        # 检查所有步骤是否成功
        all_success = all(
            r.get("status") == "completed"
            for r in results
        )
        
        return {
            "passed": all_success,
            "steps_verified": len(results),
            "details": results,
        }


# Actor注册表
class ActorRegistry:
    """Actor注册表"""
    
    _actors: Dict[str, BaseActor] = {}
    
    @classmethod
    def register(cls, actor: BaseActor) -> None:
        """注册Actor"""
        cls._actors[actor.name] = actor
    
    @classmethod
    def unregister(cls, name: str) -> None:
        """注销Actor"""
        if name in cls._actors:
            del cls._actors[name]
    
    @classmethod
    def get(cls, name: str) -> Optional[BaseActor]:
        """获取Actor"""
        return cls._actors.get(name)
    
    @classmethod
    def get_all(cls) -> Dict[str, BaseActor]:
        """获取所有Actor"""
        return cls._actors.copy()
    
    @classmethod
    async def start_all(cls) -> None:
        """启动所有Actor"""
        for actor in cls._actors.values():
            await actor.start()
    
    @classmethod
    async def stop_all(cls) -> None:
        """停止所有Actor"""
        for actor in cls._actors.values():
            await actor.stop()
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """获取所有Actor统计"""
        return {
            name: actor.stats.to_dict()
            for name, actor in cls._actors.items()
        }


# 便捷函数
def create_actor(
    role: AgentRole,
    name: Optional[str] = None,
    config: Optional[AgentConfig] = None,
    **kwargs,
) -> BaseActor:
    """
    创建Actor的便捷函数
    
    Args:
        role: Agent角色
        name: 名称
        config: 配置
    
    Returns:
        Actor实例
    """
    actor_classes = {
        AgentRole.INTENT: IntentActor,
        AgentRole.PLANNING: PlanActor,
        AgentRole.EXECUTION: ExecActor,
        AgentRole.VERIFICATION: VerifyActor,
    }
    
    actor_class = actor_classes.get(role, ExecActor)
    
    if role == AgentRole.EXECUTION:
        return actor_class(name=name or "exec_agent", config=config, **kwargs)
    
    return actor_class(config=config)

