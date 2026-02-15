"""
多智能体协作模式 - Multi-Agent Collaboration

实现多种协作模式，支持顺序、并行、条件分支执行。

核心功能：
1. 顺序协作
2. 并行协作
3. 条件分支
4. 混合模式
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from opspilot.agents.msg_hub import (
    AgentMessage,
    MessageType,
    MessageHub,
    get_message_hub,
    create_message,
)
from opspilot.agents.actor import (
    BaseActor,
    ActorState,
    ActorRegistry,
    create_actor,
)
from opspilot.agents.base import AgentRole, AgentOutput
from opspilot.core.state_machine import State
from opspilot.utils.exceptions import AgentError


class CollaborationMode(Enum):
    """协作模式"""
    SEQUENTIAL = "sequential"      # 顺序执行
    PARALLEL = "parallel"          # 并行执行
    CONDITIONAL = "conditional"    # 条件分支
    ITERATIVE = "iterative"        # 迭代执行
    PIPELINE = "pipeline"          # 流水线
    HIERARCHICAL = "hierarchical"  # 层级协作


@dataclass
class CollaborationContext:
    """协作上下文"""
    task_id: str
    query: str
    mode: CollaborationMode
    
    # 输入输出
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    
    # 执行状态
    current_step: int = 0
    total_steps: int = 0
    started_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    
    # 消息追踪
    trace_id: str = field(default_factory=lambda: str(int(time.time() * 1000))[-8:])
    
    # 中间结果
    intermediate_results: Dict[str, Any] = field(default_factory=dict)
    
    # 错误信息
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "query": self.query,
            "mode": self.mode.value,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "trace_id": self.trace_id,
            "errors": self.errors,
        }


@dataclass
class CollaborationResult:
    """协作结果"""
    success: bool
    context: CollaborationContext
    final_output: Any
    agent_outputs: Dict[str, AgentOutput] = field(default_factory=dict)
    elapsed_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "final_output": self.final_output,
            "elapsed_time": self.elapsed_time,
            "context": self.context.to_dict(),
        }


class BaseCollaboration:
    """
    协作模式基类
    
    定义协作的基本流程和接口。
    """
    
    def __init__(
        self,
        actors: Optional[Dict[str, BaseActor]] = None,
        timeout: float = 300.0,
    ):
        """
        初始化协作模式
        
        Args:
            actors: Actor字典
            timeout: 超时时间（秒）
        """
        self.actors = actors or {}
        self.timeout = timeout
        self.hub = get_message_hub()
    
    async def execute(
        self,
        context: CollaborationContext,
    ) -> CollaborationResult:
        """
        执行协作
        
        Args:
            context: 协作上下文
        
        Returns:
            协作结果
        """
        raise NotImplementedError
    
    def _create_message(
        self,
        content: Any,
        msg_type: MessageType = MessageType.TASK_REQUEST,
        receiver: Optional[str] = None,
        context: Optional[CollaborationContext] = None,
    ) -> AgentMessage:
        """创建消息"""
        return AgentMessage(
            name="orchestrator",
            content=content,
            msg_type=msg_type,
            receiver=receiver,
            trace_id=context.trace_id if context else None,
        )


class SequentialCollaboration(BaseCollaboration):
    """
    顺序协作模式
    
    Agent按顺序依次执行：
    Intent → Planning → Execution → Verification
    """
    
    # 默认执行顺序
    DEFAULT_SEQUENCE = [
        AgentRole.INTENT,
        AgentRole.PLANNING,
        AgentRole.EXECUTION,
        AgentRole.VERIFICATION,
    ]
    
    def __init__(
        self,
        actors: Optional[Dict[str, BaseActor]] = None,
        sequence: Optional[List[AgentRole]] = None,
        timeout: float = 300.0,
    ):
        super().__init__(actors, timeout)
        self.sequence = sequence or self.DEFAULT_SEQUENCE
    
    async def execute(
        self,
        context: CollaborationContext,
    ) -> CollaborationResult:
        """执行顺序协作"""
        start_time = time.time()
        context.total_steps = len(self.sequence)
        
        current_data = context.input_data.copy()
        current_data["query"] = context.query
        
        agent_outputs = {}
        
        try:
            for step_idx, role in enumerate(self.sequence):
                context.current_step = step_idx + 1
                
                # 获取对应角色的Actor
                actor = self._get_actor_by_role(role)
                if not actor:
                    continue
                
                # 创建消息
                msg = self._create_message(
                    content=current_data,
                    msg_type=MessageType.TASK_REQUEST,
                    receiver=actor.name,
                    context=context,
                )
                
                # 发送并等待响应
                response = await self._send_and_wait(
                    actor, msg, context
                )
                
                if response:
                    current_data = response.content if isinstance(response.content, dict) else {"result": response.content}
                    context.intermediate_results[actor.name] = current_data
                    
                    # 记录输出
                    agent_outputs[actor.name] = AgentOutput(
                        agent_name=actor.name,
                        status="success",
                        result=current_data,
                    )
            
            context.completed_at = time.time()
            
            return CollaborationResult(
                success=True,
                context=context,
                final_output=current_data,
                agent_outputs=agent_outputs,
                elapsed_time=time.time() - start_time,
            )
        
        except Exception as e:
            context.errors.append({
                "step": context.current_step,
                "error": str(e),
                "timestamp": time.time(),
            })
            
            return CollaborationResult(
                success=False,
                context=context,
                final_output=None,
                agent_outputs=agent_outputs,
                elapsed_time=time.time() - start_time,
            )
    
    def _get_actor_by_role(self, role: AgentRole) -> Optional[BaseActor]:
        """根据角色获取Actor"""
        for actor in self.actors.values():
            if actor.role == role:
                return actor
        return None
    
    async def _send_and_wait(
        self,
        actor: BaseActor,
        msg: AgentMessage,
        context: CollaborationContext,
        timeout: float = 60.0,
    ) -> Optional[AgentMessage]:
        """发送消息并等待响应"""
        # 直接调用处理方法
        try:
            response = await asyncio.wait_for(
                actor.handle_message(msg),
                timeout=timeout,
            )
            return response
        except asyncio.TimeoutError:
            context.errors.append({
                "actor": actor.name,
                "error": "timeout",
            })
            return None


class ParallelCollaboration(BaseCollaboration):
    """
    并行协作模式
    
    多个Agent同时执行，结果合并。
    """
    
    def __init__(
        self,
        actors: Optional[Dict[str, BaseActor]] = None,
        max_concurrent: int = 5,
        timeout: float = 300.0,
    ):
        super().__init__(actors, timeout)
        self.max_concurrent = max_concurrent
    
    async def execute(
        self,
        context: CollaborationContext,
    ) -> CollaborationResult:
        """执行并行协作"""
        start_time = time.time()
        
        # 获取要执行的Actor
        actors_to_run = list(self.actors.values())
        context.total_steps = len(actors_to_run)
        
        # 创建并发任务
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def run_with_semaphore(actor: BaseActor):
            async with semaphore:
                msg = self._create_message(
                    content=context.input_data,
                    receiver=actor.name,
                    context=context,
                )
                return actor.name, await actor.handle_message(msg)
        
        # 并行执行
        tasks = [run_with_semaphore(actor) for actor in actors_to_run]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 收集结果
        agent_outputs = {}
        final_results = {}
        
        for result in results:
            if isinstance(result, Exception):
                context.errors.append({
                    "error": str(result),
                })
            else:
                actor_name, response = result
                if response:
                    agent_outputs[actor_name] = AgentOutput(
                        agent_name=actor_name,
                        status="success",
                        result=response.content,
                    )
                    final_results[actor_name] = response.content
        
        context.completed_at = time.time()
        
        return CollaborationResult(
            success=len(context.errors) == 0,
            context=context,
            final_output=final_results,
            agent_outputs=agent_outputs,
            elapsed_time=time.time() - start_time,
        )


class ConditionalCollaboration(BaseCollaboration):
    """
    条件分支协作模式
    
    根据条件选择不同的执行路径。
    """
    
    def __init__(
        self,
        actors: Optional[Dict[str, BaseActor]] = None,
        conditions: Optional[Dict[str, List[AgentRole]]] = None,
        default_path: Optional[List[AgentRole]] = None,
        timeout: float = 300.0,
    ):
        super().__init__(actors, timeout)
        self.conditions = conditions or {}
        self.default_path = default_path or []
    
    async def execute(
        self,
        context: CollaborationContext,
    ) -> CollaborationResult:
        """执行条件分支协作"""
        start_time = time.time()
        
        # 首先执行意图识别
        intent_actor = self._get_actor_by_role(AgentRole.INTENT)
        
        if intent_actor:
            msg = self._create_message(
                content={"query": context.query},
                receiver=intent_actor.name,
                context=context,
            )
            
            response = await intent_actor.handle_message(msg)
            
            if response:
                intent = response.content.get("intent", "unknown") if isinstance(response.content, dict) else "unknown"
            else:
                intent = "unknown"
        else:
            intent = self._classify_intent(context.query)
        
        # 选择执行路径
        path = self._select_path(intent)
        context.total_steps = len(path)
        
        # 按路径执行
        current_data = {"query": context.query, "intent": intent}
        agent_outputs = {}
        
        for step_idx, role in enumerate(path):
            context.current_step = step_idx + 1
            
            actor = self._get_actor_by_role(role)
            if not actor:
                continue
            
            msg = self._create_message(
                content=current_data,
                receiver=actor.name,
                context=context,
            )
            
            response = await actor.handle_message(msg)
            
            if response:
                current_data = response.content if isinstance(response.content, dict) else {"result": response.content}
                agent_outputs[actor.name] = AgentOutput(
                    agent_name=actor.name,
                    status="success",
                    result=current_data,
                )
        
        context.completed_at = time.time()
        
        return CollaborationResult(
            success=True,
            context=context,
            final_output=current_data,
            agent_outputs=agent_outputs,
            elapsed_time=time.time() - start_time,
        )
    
    def _get_actor_by_role(self, role: AgentRole) -> Optional[BaseActor]:
        """根据角色获取Actor"""
        for actor in self.actors.values():
            if actor.role == role:
                return actor
        return None
    
    def _select_path(self, intent: str) -> List[AgentRole]:
        """选择执行路径"""
        # 意图到路径的映射
        intent_paths = {
            "order_create": [
                AgentRole.PLANNING,
                AgentRole.EXECUTION,
                AgentRole.VERIFICATION,
            ],
            "query": [
                AgentRole.EXECUTION,
            ],
            "update": [
                AgentRole.PLANNING,
                AgentRole.EXECUTION,
                AgentRole.VERIFICATION,
            ],
        }
        
        return intent_paths.get(intent, self.default_path)
    
    def _classify_intent(self, query: str) -> str:
        """简单意图分类"""
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ["创建", "下单", "采购"]):
            return "order_create"
        elif any(kw in query_lower for kw in ["查询", "搜索", "查找"]):
            return "query"
        elif any(kw in query_lower for kw in ["修改", "更新", "变更"]):
            return "update"
        else:
            return "unknown"


class PipelineCollaboration(BaseCollaboration):
    """
    流水线协作模式
    
    数据流过多个处理阶段。
    """
    
    def __init__(
        self,
        actors: Optional[Dict[str, BaseActor]] = None,
        stages: Optional[List[str]] = None,
        timeout: float = 300.0,
    ):
        super().__init__(actors, timeout)
        self.stages = stages or []
    
    async def execute(
        self,
        context: CollaborationContext,
    ) -> CollaborationResult:
        """执行流水线协作"""
        start_time = time.time()
        
        # 数据流
        data_stream = [context.input_data]
        
        agent_outputs = {}
        context.total_steps = len(self.stages)
        
        for stage_idx, stage in enumerate(self.stages):
            context.current_step = stage_idx + 1
            
            actor = self.actors.get(stage)
            if not actor:
                continue
            
            # 处理当前阶段的所有数据
            stage_outputs = []
            
            for data in data_stream:
                msg = self._create_message(
                    content=data,
                    receiver=actor.name,
                    context=context,
                )
                
                response = await actor.handle_message(msg)
                
                if response:
                    stage_outputs.append(response.content)
            
            # 更新数据流
            data_stream = stage_outputs
            
            agent_outputs[stage] = AgentOutput(
                agent_name=stage,
                status="success",
                result=stage_outputs,
            )
        
        context.completed_at = time.time()
        
        # 最终结果是数据流的最后一个元素
        final_output = data_stream[-1] if data_stream else None
        
        return CollaborationResult(
            success=True,
            context=context,
            final_output=final_output,
            agent_outputs=agent_outputs,
            elapsed_time=time.time() - start_time,
        )


class CollaborationOrchestrator:
    """
    协作编排器
    
    管理多种协作模式，选择最佳模式执行任务。
    """
    
    def __init__(
        self,
        actors: Optional[Dict[str, BaseActor]] = None,
        default_mode: CollaborationMode = CollaborationMode.SEQUENTIAL,
    ):
        """
        初始化编排器
        
        Args:
            actors: Actor字典
            default_mode: 默认协作模式
        """
        self.actors = actors or {}
        self.default_mode = default_mode
        
        # 注册协作模式
        self._mode_handlers: Dict[CollaborationMode, BaseCollaboration] = {
            CollaborationMode.SEQUENTIAL: SequentialCollaboration(self.actors),
            CollaborationMode.PARALLEL: ParallelCollaboration(self.actors),
            CollaborationMode.CONDITIONAL: ConditionalCollaboration(self.actors),
            CollaborationMode.PIPELINE: PipelineCollaboration(self.actors),
        }
    
    def register_actor(self, actor: BaseActor) -> None:
        """注册Actor"""
        self.actors[actor.name] = actor
        ActorRegistry.register(actor)
    
    def unregister_actor(self, name: str) -> None:
        """注销Actor"""
        if name in self.actors:
            del self.actors[name]
            ActorRegistry.unregister(name)
    
    async def execute(
        self,
        query: str,
        mode: Optional[CollaborationMode] = None,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> CollaborationResult:
        """
        执行协作
        
        Args:
            query: 用户查询
            mode: 协作模式
            input_data: 输入数据
        
        Returns:
            协作结果
        """
        mode = mode or self.default_mode
        
        # 创建上下文
        context = CollaborationContext(
            task_id=str(int(time.time() * 1000))[-8:],
            query=query,
            mode=mode,
            input_data=input_data or {},
        )
        
        # 获取协作处理器
        handler = self._mode_handlers.get(mode)
        if not handler:
            handler = self._mode_handlers[CollaborationMode.SEQUENTIAL]
        
        # 执行
        return await handler.execute(context)
    
    def select_mode(self, query: str) -> CollaborationMode:
        """
        根据查询选择最佳协作模式
        
        Args:
            query: 用户查询
        
        Returns:
            推荐的协作模式
        """
        query_lower = query.lower()
        
        # 简单的模式选择逻辑
        if any(kw in query_lower for kw in ["同时", "并行", "一起"]):
            return CollaborationMode.PARALLEL
        
        if any(kw in query_lower for kw in ["如果", "条件", "根据"]):
            return CollaborationMode.CONDITIONAL
        
        # 默认顺序执行
        return CollaborationMode.SEQUENTIAL


# 便捷函数
def create_orchestrator(
    actor_configs: Optional[List[Dict[str, Any]]] = None,
    default_mode: CollaborationMode = CollaborationMode.SEQUENTIAL,
) -> CollaborationOrchestrator:
    """
    创建编排器的便捷函数
    
    Args:
        actor_configs: Actor配置列表
        default_mode: 默认协作模式
    
    Returns:
        编排器实例
    """
    orchestrator = CollaborationOrchestrator(default_mode=default_mode)
    
    if actor_configs:
        for config in actor_configs:
            role = config.get("role")
            name = config.get("name")
            actor = create_actor(role, name)
            orchestrator.register_actor(actor)
    
    return orchestrator


async def run_collaboration(
    query: str,
    mode: CollaborationMode = CollaborationMode.SEQUENTIAL,
    actors: Optional[Dict[str, BaseActor]] = None,
) -> CollaborationResult:
    """
    运行协作的便捷函数
    
    Args:
        query: 用户查询
        mode: 协作模式
        actors: Actor字典
    
    Returns:
        协作结果
    """
    orchestrator = CollaborationOrchestrator(actors=actors, default_mode=mode)
    return await orchestrator.execute(query, mode)

