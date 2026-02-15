"""
混合编排器

融合AgentScope和LangChain的优势:
┌─────────────────────────────────────────────────────────────────┐
│                    Hybrid Orchestration                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   AgentScope Layer (调度层)                                     │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  MsgHub ──► IntentAgent ──► PlanAgent ──► Coordination   │  │
│   │                    │              │                       │  │
│   │                    └──────────────┴──► 分发任务           │  │
│   └─────────────────────────────────────────────────────────┘  │
│                           │                                     │
│                           ▼                                     │
│   LangChain Layer (执行层)                                      │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  Tool Router ──► MCP Tools ──► RAG ──► Chain Executor   │  │
│   │       │              │           │          │            │  │
│   │       └──────────────┴───────────┴──────────┘            │  │
│   │                       结果聚合                            │  │
│   └─────────────────────────────────────────────────────────┘  │
│                           │                                     │
│                           ▼                                     │
│   Verification Layer (验证层)                                   │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  VerifyAgent ──► 结果校验 ──► 输出格式化                  │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

核心设计原则:
1. AgentScope负责: 多智能体调度、消息路由、分布式通信
2. LangChain负责: 工具调用、RAG检索、链式执行
3. 解耦设计: 调度层不关心执行细节，执行层不关心调度逻辑
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from opspilot.integration.agentscope_integration import (
    ASAgentBase,
    ASExecAgent,
    ASIntentAgent,
    ASMessage,
    ASMessageType,
    ASPlanAgent,
    ASVerifyAgent,
    ServiceRegistry,
    create_agent,
)
from opspilot.integration.langchain_integration import (
    LCChainExecutor,
    LCRetrieverAdapter,
    LCToolAdapter,
    LCToolRegistry,
    MCPToolWrapper,
)

logger = logging.getLogger(__name__)


# ============================================================================
# 混合编排配置
# ============================================================================

class OrchestrationMode(str, Enum):
    """编排模式"""
    SEQUENTIAL = "sequential"       # 顺序执行
    PARALLEL = "parallel"           # 并行执行
    CONDITIONAL = "conditional"     # 条件分支
    PIPELINE = "pipeline"           # 流水线
    HYBRID = "hybrid"               # 混合模式


@dataclass
class HybridOrchestratorConfig:
    """混合编排器配置"""
    # AgentScope配置
    use_distributed: bool = False
    max_workers: int = 4
    
    # LangChain配置
    enable_rag: bool = True
    enable_memory: bool = True
    
    # 执行配置
    mode: OrchestrationMode = OrchestrationMode.SEQUENTIAL
    timeout: float = 60.0
    max_retries: int = 3
    
    # 幂等性配置
    enable_idempotency: bool = True
    idempotency_ttl: float = 3600.0  # 1小时
    
    # 缓存配置
    enable_cache: bool = True
    cache_ttl: float = 300.0  # 5分钟


# ============================================================================
# 工作流定义
# ============================================================================

@dataclass
class WorkflowStep:
    """工作流步骤"""
    name: str
    agent_type: str  # intent, plan, exec, verify
    action: str
    dependencies: List[str] = field(default_factory=list)
    condition: Optional[Callable[[Dict], bool]] = None
    retry_on_failure: bool = True
    timeout: Optional[float] = None


@dataclass
class WorkflowContext:
    """工作流上下文"""
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    current_step: int = 0
    status: str = "pending"
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    
    # 数据存储
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    step_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    # 幂等性
    idempotency_key: Optional[str] = None
    cached_result: Optional[Dict] = None


class BaseWorkflow:
    """工作流基类"""
    
    def __init__(self, steps: List[WorkflowStep] = None):
        self.steps = steps or []
    
    def add_step(self, step: WorkflowStep) -> None:
        """添加步骤"""
        self.steps.append(step)
    
    def get_dependencies(self, step_name: str) -> List[str]:
        """获取步骤依赖"""
        for step in self.steps:
            if step.name == step_name:
                return step.dependencies
        return []
    
    def validate(self) -> bool:
        """验证工作流"""
        step_names = {s.name for s in self.steps}
        for step in self.steps:
            for dep in step.dependencies:
                if dep not in step_names:
                    logger.error(f"Step {step.name} has invalid dependency: {dep}")
                    return False
        return True


class SequentialWorkflow(BaseWorkflow):
    """顺序工作流"""
    
    @classmethod
    def create_default(cls) -> "SequentialWorkflow":
        """创建默认工作流"""
        return cls(steps=[
            WorkflowStep(
                name="intent_recognition",
                agent_type="intent",
                action="recognize",
            ),
            WorkflowStep(
                name="planning",
                agent_type="plan",
                action="plan",
                dependencies=["intent_recognition"],
            ),
            WorkflowStep(
                name="execution",
                agent_type="exec",
                action="execute",
                dependencies=["planning"],
            ),
            WorkflowStep(
                name="verification",
                agent_type="verify",
                action="verify",
                dependencies=["execution"],
            ),
        ])


class ParallelWorkflow(BaseWorkflow):
    """并行工作流"""
    
    @classmethod
    def create_for_query(cls) -> "ParallelWorkflow":
        """创建查询并行工作流"""
        return cls(steps=[
            WorkflowStep(
                name="intent_recognition",
                agent_type="intent",
                action="recognize",
            ),
            # 并行执行多个查询
            WorkflowStep(
                name="query_supplier",
                agent_type="exec",
                action="query_supplier",
                dependencies=["intent_recognition"],
            ),
            WorkflowStep(
                name="query_inventory",
                agent_type="exec",
                action="query_inventory",
                dependencies=["intent_recognition"],
            ),
            WorkflowStep(
                name="query_order",
                agent_type="exec",
                action="query_order",
                dependencies=["intent_recognition"],
            ),
            # 汇总结果
            WorkflowStep(
                name="aggregate_results",
                agent_type="exec",
                action="aggregate",
                dependencies=["query_supplier", "query_inventory", "query_order"],
            ),
            WorkflowStep(
                name="verification",
                agent_type="verify",
                action="verify",
                dependencies=["aggregate_results"],
            ),
        ])


class ConditionalWorkflow(BaseWorkflow):
    """条件分支工作流"""
    
    @classmethod
    def create_with_branches(cls) -> "ConditionalWorkflow":
        """创建带分支的工作流"""
        def is_order_intent(context: Dict) -> bool:
            return context.get("intent", {}).get("type") == "order_create"
        
        def is_query_intent(context: Dict) -> bool:
            return context.get("intent", {}).get("type") == "query"
        
        return cls(steps=[
            WorkflowStep(
                name="intent_recognition",
                agent_type="intent",
                action="recognize",
            ),
            # 订单创建分支
            WorkflowStep(
                name="order_create_flow",
                agent_type="exec",
                action="create_order",
                dependencies=["intent_recognition"],
                condition=is_order_intent,
            ),
            # 查询分支
            WorkflowStep(
                name="query_flow",
                agent_type="exec",
                action="execute_query",
                dependencies=["intent_recognition"],
                condition=is_query_intent,
            ),
            # 验证
            WorkflowStep(
                name="verification",
                agent_type="verify",
                action="verify",
                dependencies=["order_create_flow", "query_flow"],
            ),
        ])


# ============================================================================
# 幂等性管理
# ============================================================================

class IdempotencyManager:
    """
    幂等性管理器
    
    确保相同请求不会被重复执行
    """
    
    def __init__(self, ttl: float = 3600.0):
        self.ttl = ttl
        self._results: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, float] = {}
    
    def generate_key(self, input_data: Dict) -> str:
        """生成幂等性Key"""
        import hashlib
        import json
        
        # 使用输入数据的哈希作为Key
        content = json.dumps(input_data, sort_keys=True, default=str)
        return hashlib.md5(content.encode()).hexdigest()
    
    def check(self, key: str) -> Optional[Dict]:
        """
        检查是否有缓存结果
        
        Returns:
            如果存在有效缓存则返回结果，否则返回None
        """
        if key in self._results:
            timestamp = self._timestamps.get(key, 0)
            if time.time() - timestamp < self.ttl:
                logger.info(f"Idempotency hit: {key}")
                return self._results[key]
            else:
                # 过期，清除
                self.clear(key)
        return None
    
    def store(self, key: str, result: Dict) -> None:
        """存储结果"""
        self._results[key] = result
        self._timestamps[key] = time.time()
    
    def clear(self, key: str) -> None:
        """清除缓存"""
        self._results.pop(key, None)
        self._timestamps.pop(key, None)


# ============================================================================
# 结果缓存
# ============================================================================

class ResultCache:
    """结果缓存"""
    
    def __init__(self, ttl: float = 300.0):
        self.ttl = ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, float] = {}
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Dict]:
        """获取缓存"""
        if key in self._cache:
            timestamp = self._timestamps.get(key, 0)
            if time.time() - timestamp < self.ttl:
                self._hits += 1
                return self._cache[key]
        self._misses += 1
        return None
    
    def set(self, key: str, value: Dict) -> None:
        """设置缓存"""
        self._cache[key] = value
        self._timestamps[key] = time.time()
    
    def stats(self) -> Dict[str, Any]:
        """获取统计"""
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total > 0 else 0,
        }


# ============================================================================
# 混合编排器
# ============================================================================

class HybridOrchestrator:
    """
    混合编排器
    
    核心职责:
    1. AgentScope调度 - 管理Agent生命周期、消息路由
    2. LangChain执行 - 工具调用、RAG检索、链式执行
    3. 工作流管理 - 顺序/并行/条件分支
    4. 容错机制 - 重试、降级、超时处理
    5. 幂等性保证 - 请求去重、结果缓存
    
    使用示例:
    ```python
    config = HybridOrchestratorConfig(
        mode=OrchestrationMode.SEQUENTIAL,
        enable_rag=True,
    )
    
    orchestrator = HybridOrchestrator(config)
    
    # 注册MCP工具
    orchestrator.register_mcp_tools(erp_server)
    
    # 注册LangChain工具
    orchestrator.register_lc_tools([tool1, tool2])
    
    # 执行工作流
    result = await orchestrator.execute({
        "query": "查询供应商信息",
    })
    ```
    """
    
    def __init__(self, config: HybridOrchestratorConfig = None):
        self.config = config or HybridOrchestratorConfig()
        
        # AgentScope组件
        self._agents: Dict[str, ASAgentBase] = {}
        self._service_registry = ServiceRegistry()
        
        # LangChain组件
        self._lc_tool_registry = LCToolRegistry()
        self._lc_chain_executor = LCChainExecutor()
        self._lc_retriever: Optional[LCRetrieverAdapter] = None
        
        # 工作流
        self._workflows: Dict[str, BaseWorkflow] = {}
        
        # 幂等性和缓存
        self._idempotency_manager = IdempotencyManager(
            ttl=self.config.idempotency_ttl
        ) if self.config.enable_idempotency else None
        
        self._result_cache = ResultCache(
            ttl=self.config.cache_ttl
        ) if self.config.enable_cache else None
        
        # 初始化
        self._initialize()
    
    def _initialize(self) -> None:
        """初始化编排器"""
        # 创建默认Agent
        self._create_default_agents()
        
        # 注册默认工作流
        self._register_default_workflows()
        
        logger.info("HybridOrchestrator initialized")
    
    def _create_default_agents(self) -> None:
        """创建默认Agent"""
        agent_configs = [
            ("intent_agent", ASIntentAgent),
            ("plan_agent", ASPlanAgent),
            ("exec_agent", ASExecAgent),
            ("verify_agent", ASVerifyAgent),
        ]
        
        for name, agent_class in agent_configs:
            agent = agent_class(name=name)
            self._agents[name] = agent
            self._service_registry.register(
                name=name,
                address=f"local://{name}",
                metadata={"type": agent_class.__name__},
            )
    
    def _register_default_workflows(self) -> None:
        """注册默认工作流"""
        self._workflows["sequential"] = SequentialWorkflow.create_default()
        self._workflows["parallel"] = ParallelWorkflow.create_for_query()
        self._workflows["conditional"] = ConditionalWorkflow.create_with_branches()
    
    # -------------------------------------------------------------------------
    # 工具注册
    # -------------------------------------------------------------------------
    
    def register_mcp_tools(self, mcp_server: Any) -> None:
        """
        注册MCP工具
        
        自动将MCP Server的工具转换为LangChain工具
        """
        wrapper = MCPToolWrapper(mcp_server)
        lc_tools = wrapper.get_langchain_tools()
        
        for tool in lc_tools:
            self._lc_tool_registry.register(tool)
        
        # 注册到ExecAgent
        exec_agent = self._agents.get("exec_agent")
        if exec_agent:
            for tool in lc_tools:
                exec_agent.register_lc_tool(tool)
        
        logger.info(f"Registered {len(lc_tools)} MCP tools")
    
    def register_lc_tools(self, tools: List[Any]) -> None:
        """
        注册LangChain工具
        
        Args:
            tools: LangChain工具列表或LCToolAdapter列表
        """
        for tool in tools:
            self._lc_tool_registry.register(tool)
        
        # 注册到ExecAgent
        exec_agent = self._agents.get("exec_agent")
        if exec_agent:
            for tool in tools:
                exec_agent.register_lc_tool(tool)
    
    def register_retriever(self, retriever: LCRetrieverAdapter) -> None:
        """注册LangChain检索器"""
        self._lc_retriever = retriever
        self._lc_chain_executor.register_retriever(retriever)
        
        # 注册到所有Agent
        for agent in self._agents.values():
            agent.register_lc_retriever(retriever)
    
    # -------------------------------------------------------------------------
    # 执行入口
    # -------------------------------------------------------------------------
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        workflow_name: str = None,
        idempotency_key: str = None,
    ) -> Dict[str, Any]:
        """
        执行工作流
        
        Args:
            input_data: 输入数据
            workflow_name: 工作流名称
            idempotency_key: 幂等性Key（可选）
        
        Returns:
            执行结果
        """
        # 创建上下文
        context = WorkflowContext(
            input_data=input_data,
            idempotency_key=idempotency_key,
        )
        
        # 幂等性检查
        if self._idempotency_manager:
            key = idempotency_key or self._idempotency_manager.generate_key(input_data)
            cached = self._idempotency_manager.check(key)
            if cached:
                context.cached_result = cached
                context.status = "cached"
                return cached
        
        # 选择工作流
        workflow = self._select_workflow(workflow_name, input_data)
        
        # 执行工作流
        try:
            result = await self._execute_workflow(workflow, context)
            context.status = "completed"
            context.end_time = time.time()
            
            # 存储结果
            if self._idempotency_manager:
                self._idempotency_manager.store(key, result)
            
            return result
            
        except Exception as e:
            context.status = "failed"
            context.errors.append({
                "error": str(e),
                "time": time.time(),
            })
            raise
    
    def _select_workflow(
        self,
        workflow_name: str,
        input_data: Dict,
    ) -> BaseWorkflow:
        """选择工作流"""
        if workflow_name and workflow_name in self._workflows:
            return self._workflows[workflow_name]
        
        # 根据模式选择
        mode = self.config.mode
        workflow_map = {
            OrchestrationMode.SEQUENTIAL: "sequential",
            OrchestrationMode.PARALLEL: "parallel",
            OrchestrationMode.CONDITIONAL: "conditional",
        }
        
        return self._workflows.get(
            workflow_map.get(mode, "sequential"),
            self._workflows["sequential"],
        )
    
    async def _execute_workflow(
        self,
        workflow: BaseWorkflow,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """执行工作流"""
        # 验证工作流
        if not workflow.validate():
            raise ValueError("Invalid workflow")
        
        # 根据执行模式分发
        if self.config.mode == OrchestrationMode.PARALLEL:
            return await self._execute_parallel(workflow, context)
        elif self.config.mode == OrchestrationMode.CONDITIONAL:
            return await self._execute_conditional(workflow, context)
        else:
            return await self._execute_sequential(workflow, context)
    
    async def _execute_sequential(
        self,
        workflow: BaseWorkflow,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """顺序执行"""
        for step in workflow.steps:
            # 检查依赖
            for dep in step.dependencies:
                if dep not in context.step_results:
                    raise ValueError(f"Dependency not satisfied: {dep}")
            
            # 检查条件
            if step.condition and not step.condition(context.step_results):
                continue
            
            # 执行步骤
            result = await self._execute_step(step, context)
            context.step_results[step.name] = result
            context.current_step += 1
        
        return {
            "success": True,
            "results": context.step_results,
            "workflow_id": context.workflow_id,
        }
    
    async def _execute_parallel(
        self,
        workflow: BaseWorkflow,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """并行执行"""
        # 构建依赖图
        completed = set()
        pending = list(workflow.steps)
        
        while pending:
            # 找出可以并行执行的步骤
            ready = []
            not_ready = []
            
            for step in pending:
                if all(dep in completed for dep in step.dependencies):
                    ready.append(step)
                else:
                    not_ready.append(step)
            
            if not ready:
                raise ValueError("Circular dependency detected")
            
            # 并行执行
            tasks = [self._execute_step(step, context) for step in ready]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for step, result in zip(ready, results):
                if isinstance(result, Exception):
                    raise result
                context.step_results[step.name] = result
                completed.add(step.name)
            
            pending = not_ready
        
        return {
            "success": True,
            "results": context.step_results,
            "workflow_id": context.workflow_id,
        }
    
    async def _execute_conditional(
        self,
        workflow: BaseWorkflow,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """条件分支执行"""
        for step in workflow.steps:
            # 检查依赖
            for dep in step.dependencies:
                if dep not in context.step_results:
                    # 依赖可能因条件不满足而跳过
                    continue
            
            # 检查条件
            if step.condition and not step.condition(context.step_results):
                continue
            
            # 执行步骤
            result = await self._execute_step(step, context)
            context.step_results[step.name] = result
        
        return {
            "success": True,
            "results": context.step_results,
            "workflow_id": context.workflow_id,
        }
    
    async def _execute_step(
        self,
        step: WorkflowStep,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """执行单个步骤"""
        # 获取Agent
        agent = self._agents.get(f"{step.agent_type}_agent")
        if not agent:
            raise ValueError(f"Agent not found: {step.agent_type}")
        
        # 构建消息
        msg = ASMessage(
            name="orchestrator",
            content={
                "action": step.action,
                "input": context.input_data,
                "step_results": context.step_results,
            },
            msg_type=ASMessageType.TASK_REQUEST,
            trace_id=context.trace_id,
        )
        
        # 执行（带重试）
        for attempt in range(self.config.max_retries):
            try:
                result = await agent.process(msg)
                
                if result:
                    return result.content
                return {}
                
            except Exception as e:
                if not step.retry_on_failure or attempt == self.config.max_retries - 1:
                    raise
                
                await asyncio.sleep(2 ** attempt)  # 指数退避
        
        return {}
    
    # -------------------------------------------------------------------------
    # Agent管理
    # -------------------------------------------------------------------------
    
    def register_agent(self, name: str, agent: ASAgentBase) -> None:
        """注册Agent"""
        self._agents[name] = agent
        self._service_registry.register(
            name=name,
            address=f"local://{name}",
            metadata={"type": agent.__class__.__name__},
        )
    
    def get_agent(self, name: str) -> Optional[ASAgentBase]:
        """获取Agent"""
        return self._agents.get(name)
    
    async def start_all_agents(self) -> None:
        """启动所有Agent"""
        for agent in self._agents.values():
            await agent.start()
    
    async def stop_all_agents(self) -> None:
        """停止所有Agent"""
        for agent in self._agents.values():
            await agent.stop()
    
    # -------------------------------------------------------------------------
    # 统计与监控
    # -------------------------------------------------------------------------
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        agent_stats = {}
        for name, agent in self._agents.items():
            agent_stats[name] = {
                "state": agent.state.value,
                "messages_received": agent.stats.messages_received,
                "tasks_completed": agent.stats.tasks_completed,
                "tasks_failed": agent.stats.tasks_failed,
            }
        
        return {
            "agents": agent_stats,
            "tools": {
                "count": len(self._lc_tool_registry.list_tools()),
                "categories": self._lc_tool_registry.list_categories(),
            },
            "cache": self._result_cache.stats() if self._result_cache else None,
            "workflows": list(self._workflows.keys()),
        }


# ============================================================================
# 工厂函数
# ============================================================================

def create_hybrid_orchestrator(
    mode: OrchestrationMode = OrchestrationMode.SEQUENTIAL,
    enable_rag: bool = True,
    enable_cache: bool = True,
    enable_idempotency: bool = True,
    **kwargs,
) -> HybridOrchestrator:
    """
    创建混合编排器
    
    Args:
        mode: 编排模式
        enable_rag: 启用RAG
        enable_cache: 启用缓存
        enable_idempotency: 启用幂等性
        **kwargs: 其他配置
    
    Returns:
        HybridOrchestrator实例
    """
    config = HybridOrchestratorConfig(
        mode=mode,
        enable_rag=enable_rag,
        enable_cache=enable_cache,
        enable_idempotency=enable_idempotency,
        **kwargs,
    )
    return HybridOrchestrator(config)

