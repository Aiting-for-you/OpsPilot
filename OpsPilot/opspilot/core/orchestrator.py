"""
编排器模块

职责：
- 协调多个 Agent 协作
- 管理任务执行流程
- 集成状态机、记忆、工具
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio

from opspilot.core.state_machine import StateMachine, State
from opspilot.core.context import TaskContext, ContextManager
from opspilot.core.events import EventBus, StateChangedEvent, TaskCreatedEvent, TaskCompletedEvent
from opspilot.agents.base import BaseAgent, AgentContext
from opspilot.agents.intent_agent import IntentType
from opspilot.memory.base import MemoryManager
from opspilot.memory.short_term import ShortTermMemory
from opspilot.memory.knowledge import KnowledgeBase
from opspilot.tools.base import ToolRouter


class Orchestrator:
    """
    编排器

    协调所有组件完成用户任务
    """

    def __init__(
        self,
        agent_registry: Optional["AgentRegistry"] = None,
        context_manager: Optional[ContextManager] = None,
        memory_manager: Optional[MemoryManager] = None,
        tool_router: Optional[ToolRouter] = None
    ):
        """
        初始化编排器

        Args:
            agent_registry: Agent 注册表
            context_manager: 上下文管理器
            memory_manager: 记忆管理器
            tool_router: 工具路由器
        """
        from opspilot.agents.base import AgentRegistry
        self._agent_registry = agent_registry or AgentRegistry()
        self._context_manager = context_manager or ContextManager()
        self._memory_manager = memory_manager or MemoryManager()
        self._tool_router = tool_router
        self._event_bus = EventBus.get_instance()

    def set_tool_router(self, router: ToolRouter) -> None:
        """设置工具路由器"""
        self._tool_router = router

    async def process(self, user_input: str) -> Dict[str, Any]:
        """
        处理用户输入

        这是编排器的主入口方法

        Args:
            user_input: 用户输入

        Returns:
            Dict[str, Any]: 处理结果
        """
        # 创建任务上下文
        task_context = self._context_manager.create_context(user_input)

        # 发布任务创建事件
        self._event_bus.publish(TaskCreatedEvent(
            task_id=task_context.task_id,
            user_input=user_input
        ))

        try:
            # 执行任务流程
            result = await self._execute_task(task_context)

            # 发布任务完成事件
            self._event_bus.publish(TaskCompletedEvent(
                task_id=task_context.task_id,
                result=result
            ))

            return {
                "task_id": task_context.task_id,
                "success": True,
                "result": result,
                "state": task_context.state_context.current_state.value
            }

        except Exception as e:
            return {
                "task_id": task_context.task_id,
                "success": False,
                "error": str(e),
                "state": task_context.state_context.current_state.value
            }

    async def _execute_task(self, task_context: TaskContext) -> Dict[str, Any]:
        """
        执行任务

        按照 INIT -> PLANNING -> AUDITING -> EXECUTING -> VERIFYING -> SUCCESS 流程执行

        Args:
            task_context: 任务上下文

        Returns:
            Dict[str, Any]: 执行结果
        """
        # 获取状态机
        state_machine = StateMachine(context=task_context.state_context)

        # 添加状态变化监听器
        def on_state_change(transition):
            self._event_bus.publish(StateChangedEvent(
                task_id=task_context.task_id,
                from_state=transition.from_state.value,
                to_state=transition.to_state.value,
                event=transition.event
            ))
            # 记录到短期记忆
            asyncio.create_task(self._record_state_change(task_context.task_id, transition))

        state_machine.add_listener(on_state_change)

        # 阶段 1: 意图识别 (INIT -> PLANNING)
        intent_result = await self._run_intent_agent(task_context)
        task_context.intent = intent_result.get("intent_type")
        task_context.metadata["intent"] = intent_result

        # 转换状态
        state_machine.transition(State.PLANNING, event="intent_recognized")

        # 阶段 2: 规划 (PLANNING -> AUDITING)
        plan_result = await self._run_plan_agent(task_context)
        task_context.plan = plan_result
        task_context.metadata["plan"] = plan_result

        # 转换状态
        state_machine.transition(State.AUDITING, event="plan_created")

        # 阶段 3: 审核 (AUDITING -> EXECUTING)
        audit_result = await self._run_audit(task_context, plan_result)
        task_context.metadata["audit"] = audit_result

        if not audit_result.get("approved", True):
            # 审核不通过
            state_machine.transition(State.REJECTED, event="audit_rejected")
            return {
                "status": "rejected",
                "reason": audit_result.get("reason", "审核未通过"),
                "plan": plan_result
            }

        # 转换状态
        state_machine.transition(State.EXECUTING, event="audit_passed")

        # 阶段 4: 执行 (EXECUTING -> VERIFYING)
        execution_result = await self._run_exec_agent(task_context)
        task_context.metadata["execution_results"] = execution_result.get("execution_results", [])

        # 转换状态
        state_machine.transition(State.VERIFYING, event="execution_completed")

        # 阶段 5: 验证 (VERIFYING -> SUCCESS)
        verification_result = await self._run_verify_agent(task_context)
        task_context.metadata["verification"] = verification_result

        if verification_result.get("passed", False):
            state_machine.transition(State.SUCCESS, event="verification_passed")
            task_context.set_final_result({
                "status": "success",
                "intent": intent_result,
                "plan": plan_result,
                "execution": execution_result,
                "verification": verification_result
            })
        else:
            state_machine.transition(State.RETRY, event="verification_failed")
            task_context.set_final_result({
                "status": "retry_needed",
                "reason": verification_result.get("reason"),
                "verification": verification_result
            })

        # 更新上下文
        self._context_manager.update_context(task_context)

        return task_context.final_result or {"status": "completed"}

    async def _run_intent_agent(self, task_context: TaskContext) -> Dict[str, Any]:
        """运行意图识别 Agent"""
        from opspilot.agents.intent_agent import MockIntentAgent

        agent = self._agent_registry.get("IntentAgent") or MockIntentAgent()

        context = AgentContext(
            task_id=task_context.task_id,
            state=State.INIT,
            user_input=task_context.user_input
        )

        output = await agent.execute(context)
        return output.result or {}

    async def _run_plan_agent(self, task_context: TaskContext) -> Dict[str, Any]:
        """运行规划 Agent"""
        from opspilot.agents.plan_agent import MockPlanAgent

        agent = self._agent_registry.get("PlanAgent") or MockPlanAgent()

        # 获取知识上下文
        knowledge_context = ""
        if self._memory_manager._knowledge:
            knowledge_context = await self._memory_manager.knowledge.get_context_for_task(
                task_context.user_input
            )

        context = AgentContext(
            task_id=task_context.task_id,
            state=State.PLANNING,
            user_input=task_context.user_input,
            knowledge_context=knowledge_context,
            metadata=task_context.metadata
        )

        output = await agent.execute(context)
        return output.result or {}

    async def _run_audit(self, task_context: TaskContext, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行审核

        检查计划是否需要审批，以及是否满足审批条件
        """
        # 简单实现：检查计划中的 required_approvals
        required_approvals = plan.get("required_approvals", [])

        # Mock 审核：如果需要审批，默认通过
        # 实际实现中应该调用审核服务或人工审核
        return {
            "approved": True,
            "required_approvals": required_approvals,
            "auditor": "system",
            "audited_at": datetime.now().isoformat()
        }

    async def _run_exec_agent(self, task_context: TaskContext) -> Dict[str, Any]:
        """运行执行 Agent"""
        from opspilot.agents.exec_agent import MockExecAgent

        agent = self._agent_registry.get("ExecAgent") or MockExecAgent()

        # 设置工具路由器
        if self._tool_router and hasattr(agent, 'set_tool_router'):
            agent.set_tool_router(self._tool_router)

        context = AgentContext(
            task_id=task_context.task_id,
            state=State.EXECUTING,
            metadata=task_context.metadata
        )

        output = await agent.execute(context)
        return output.result or {}

    async def _run_verify_agent(self, task_context: TaskContext) -> Dict[str, Any]:
        """运行验证 Agent"""
        from opspilot.agents.verify_agent import MockVerifyAgent

        agent = self._agent_registry.get("VerifyAgent") or MockVerifyAgent()

        context = AgentContext(
            task_id=task_context.task_id,
            state=State.VERIFYING,
            metadata=task_context.metadata
        )

        output = await agent.execute(context)
        return output.result or {}

    async def _record_state_change(self, task_id: str, transition) -> None:
        """记录状态变化到短期记忆"""
        if self._memory_manager._short_term:
            await self._memory_manager.short_term.remember(
                content=f"状态从 {transition.from_state.value} 变为 {transition.to_state.value}，事件: {transition.event}",
                task_id=task_id,
                agent_name="Orchestrator"
            )

    def get_task_context(self, task_id: str) -> Optional[TaskContext]:
        """获取任务上下文"""
        return self._context_manager.get_context(task_id)

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        context = self.get_task_context(task_id)
        if not context:
            return None

        return {
            "task_id": task_id,
            "state": context.state_context.current_state.value,
            "intent": context.intent,
            "created_at": context.created_at.isoformat(),
            "updated_at": context.updated_at.isoformat()
        }

