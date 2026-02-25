"""
上下文管理模块

职责：
- 状态机上下文管理
- 任务执行上下文
- 状态持久化支持
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import uuid

from opspilot.core.state_machine import State, StateTransition


@dataclass
class StateMachineContext:
    """
    状态机上下文

    保存状态机运行时的所有状态信息，支持序列化和持久化
    """
    task_id: str
    current_state: State = State.INIT
    history: List[StateTransition] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, task_id: Optional[str] = None, max_retries: int = 3) -> "StateMachineContext":
        """
        创建新的状态机上下文

        Args:
            task_id: 任务ID，为 None 时自动生成
            max_retries: 最大重试次数

        Returns:
            StateMachineContext: 新创建的上下文
        """
        return cls(
            task_id=task_id or str(uuid.uuid4()),
            current_state=State.INIT,
            max_retries=max_retries,
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于序列化"""
        return {
            "task_id": self.task_id,
            "current_state": self.current_state.value,
            "history": [t.to_dict() for t in self.history],
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateMachineContext":
        """从字典创建，用于反序列化"""
        return cls(
            task_id=data["task_id"],
            current_state=State(data["current_state"]),
            history=[StateTransition.from_dict(t) for t in data.get("history", [])],
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {}),
        )

    def get_last_transition(self) -> Optional[StateTransition]:
        """获取最后一次状态转换"""
        return self.history[-1] if self.history else None

    def get_transition_count(self) -> int:
        """获取状态转换次数"""
        return len(self.history)


@dataclass
class TaskContext:
    """
    任务执行上下文

    保存任务执行的完整信息，包括：
    - 用户输入
    - 执行计划
    - 中间结果
    - 最终结果
    """
    task_id: str
    user_input: str = ""
    intent: Optional[str] = None
    plan: Optional[Dict[str, Any]] = None
    execution_results: List[Dict[str, Any]] = field(default_factory=list)
    final_result: Optional[Dict[str, Any]] = None
    state_context: Optional[StateMachineContext] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        user_input: str,
        task_id: Optional[str] = None,
        max_retries: int = 3
    ) -> "TaskContext":
        """
        创建新的任务上下文

        Args:
            user_input: 用户输入
            task_id: 任务ID
            max_retries: 最大重试次数

        Returns:
            TaskContext: 新创建的任务上下文
        """
        task_id = task_id or str(uuid.uuid4())
        state_context = StateMachineContext.create(task_id=task_id, max_retries=max_retries)

        return cls(
            task_id=task_id,
            user_input=user_input,
            state_context=state_context,
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "user_input": self.user_input,
            "intent": self.intent,
            "plan": self.plan,
            "execution_results": self.execution_results,
            "final_result": self.final_result,
            "state_context": self.state_context.to_dict() if self.state_context else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskContext":
        """从字典创建"""
        state_context_data = data.get("state_context")
        state_context = (
            StateMachineContext.from_dict(state_context_data)
            if state_context_data else None
        )

        return cls(
            task_id=data["task_id"],
            user_input=data.get("user_input", ""),
            intent=data.get("intent"),
            plan=data.get("plan"),
            execution_results=data.get("execution_results", []),
            final_result=data.get("final_result"),
            state_context=state_context,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {}),
        )

    def add_execution_result(self, result: Dict[str, Any]) -> None:
        """添加执行结果"""
        self.execution_results.append(result)
        self.updated_at = datetime.now()

    def set_final_result(self, result: Dict[str, Any]) -> None:
        """设置最终结果"""
        self.final_result = result
        self.updated_at = datetime.now()


class ContextManager:
    """
    上下文管理器

    职责：
    - 管理多个任务的上下文
    - 提供上下文的创建、获取、删除
    - 与持久化层交互（后续实现）
    """

    def __init__(self):
        self._contexts: Dict[str, TaskContext] = {}

    def create_context(
        self,
        user_input: str,
        task_id: Optional[str] = None,
        max_retries: int = 3
    ) -> TaskContext:
        """
        创建新的任务上下文

        Args:
            user_input: 用户输入
            task_id: 任务ID
            max_retries: 最大重试次数

        Returns:
            TaskContext: 新创建的上下文
        """
        context = TaskContext.create(
            user_input=user_input,
            task_id=task_id,
            max_retries=max_retries
        )
        self._contexts[context.task_id] = context
        return context

    def get_context(self, task_id: str) -> Optional[TaskContext]:
        """获取任务上下文"""
        return self._contexts.get(task_id)

    def update_context(self, context: TaskContext) -> None:
        """更新任务上下文"""
        context.updated_at = datetime.now()
        self._contexts[context.task_id] = context

    def delete_context(self, task_id: str) -> bool:
        """删除任务上下文"""
        if task_id in self._contexts:
            del self._contexts[task_id]
            return True
        return False

    def list_contexts(self) -> List[str]:
        """列出所有任务ID"""
        return list(self._contexts.keys())

    def clear_all(self) -> None:
        """清空所有上下文"""
        self._contexts.clear()

