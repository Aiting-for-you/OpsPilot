"""
状态机模块

职责：
- 状态定义与枚举
- 状态转换控制
- 转换合法性验证
- 行为约束查询

与 PRD 状态定义保持一致
"""
from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field

from opspilot.utils.exceptions import (
    InvalidTransitionError,
    MaxRetryExceededError,
)


class State(str, Enum):
    """
    业务状态枚举

    与 PRD 定义一致：
    INIT -> PLANNING -> AUDITING -> EXECUTING -> VERIFYING -> SUCCESS
                                                     |
                                                     v
                                                   RETRY -> EXECUTING
    """
    INIT = "INIT"
    PLANNING = "PLANNING"
    AUDITING = "AUDITING"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    SUCCESS = "SUCCESS"
    RETRY = "RETRY"
    REJECTED = "REJECTED"


@dataclass
class StateTransition:
    """状态转换记录"""
    from_state: State
    to_state: State
    event: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "event": self.event,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateTransition":
        """从字典创建"""
        return cls(
            from_state=State(data["from_state"]),
            to_state=State(data["to_state"]),
            event=data["event"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class StateConfig:
    """状态配置"""
    name: State
    allowed_actions: List[str] = field(default_factory=list)
    forbidden_actions: List[str] = field(default_factory=list)
    prompt_constraint: str = ""

    def is_action_allowed(self, action: str) -> bool:
        """检查动作是否允许"""
        if action in self.forbidden_actions:
            return False
        if not self.allowed_actions:
            return True  # 未定义允许列表则全部允许
        return action in self.allowed_actions


# ==================== 状态配置表 ====================

STATE_CONFIGS: Dict[State, StateConfig] = {
    State.INIT: StateConfig(
        name=State.INIT,
        allowed_actions=["intent_recognition", "task_decomposition"],
        forbidden_actions=["call_tool", "execute_operation"],
        prompt_constraint="仅解析用户意图，不做业务决策",
    ),
    State.PLANNING: StateConfig(
        name=State.PLANNING,
        allowed_actions=["rag_search", "create_plan"],
        forbidden_actions=["create_order", "payment"],
        prompt_constraint="制定方案，禁止直接执行",
    ),
    State.AUDITING: StateConfig(
        name=State.AUDITING,
        allowed_actions=["compliance_check", "budget_review"],
        forbidden_actions=["modify_plan"],
        prompt_constraint="仅审核，不修改原方案",
    ),
    State.EXECUTING: StateConfig(
        name=State.EXECUTING,
        allowed_actions=["call_mcp_tool", "gui_action"],
        forbidden_actions=["skip_verification"],
        prompt_constraint="执行并记录轨迹，等待验证",
    ),
    State.VERIFYING: StateConfig(
        name=State.VERIFYING,
        allowed_actions=["check_result", "log_record"],
        forbidden_actions=["re_execute"],
        prompt_constraint="验证结果，记录偏差",
    ),
    State.RETRY: StateConfig(
        name=State.RETRY,
        allowed_actions=["retry_execution"],
        forbidden_actions=["skip_audit"],
        prompt_constraint="重试次数 +1，超过 3 次人工介入",
    ),
    State.REJECTED: StateConfig(
        name=State.REJECTED,
        allowed_actions=["return_reason", "suggest_modification"],
        forbidden_actions=["force_execute"],
        prompt_constraint="说明驳回原因，建议修改方案",
    ),
    State.SUCCESS: StateConfig(
        name=State.SUCCESS,
        allowed_actions=["archive_log", "notify_user"],
        forbidden_actions=["modify_result"],
        prompt_constraint="任务完成，输出最终结果",
    ),
}


# ==================== 状态转换规则 ====================

ALLOWED_TRANSITIONS: Dict[State, List[State]] = {
    State.INIT: [State.PLANNING],
    State.PLANNING: [State.AUDITING],
    State.AUDITING: [State.EXECUTING, State.REJECTED],
    State.EXECUTING: [State.VERIFYING, State.RETRY],
    State.VERIFYING: [State.SUCCESS, State.RETRY],
    State.RETRY: [State.EXECUTING],
    State.REJECTED: [State.INIT],
    State.SUCCESS: [State.INIT],  # 任务完成，等待新任务
}


class StateMachine:
    """
    状态机核心控制器

    职责：
    - 管理状态转换
    - 验证转换合法性
    - 提供行为约束查询

    注意：
    - 状态转换必须通过 transition() 方法
    - 不能直接修改 context.current_state
    """

    def __init__(self, context: Optional["StateMachineContext"] = None):
        """
        初始化状态机

        Args:
            context: 状态机上下文，为 None 时需要后续设置
        """
        self._context = context
        self._listeners: List[Callable[[StateTransition], None]] = []

    @property
    def context(self) -> Optional["StateMachineContext"]:
        """获取当前上下文"""
        return self._context

    @context.setter
    def context(self, value: "StateMachineContext") -> None:
        """设置上下文"""
        self._context = value

    def add_listener(self, listener: Callable[[StateTransition], None]) -> None:
        """
        添加状态转换监听器

        Args:
            listener: 监听函数，接收 StateTransition 参数
        """
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[StateTransition], None]) -> None:
        """移除监听器"""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def get_current_state(self) -> Optional[State]:
        """获取当前状态"""
        return self._context.current_state if self._context else None

    def can_transition(self, target_state: State) -> bool:
        """
        检查是否可以转换到目标状态

        Args:
            target_state: 目标状态

        Returns:
            bool: 是否可以转换
        """
        if not self._context:
            return False

        current = self._context.current_state
        allowed = ALLOWED_TRANSITIONS.get(current, [])

        # 检查重试次数
        if target_state == State.RETRY:
            if self._context.retry_count >= self._context.max_retries:
                return False

        return target_state in allowed

    def transition(
        self,
        target_state: State,
        event: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StateTransition:
        """
        执行状态转换

        Args:
            target_state: 目标状态
            event: 触发事件
            metadata: 附加信息

        Returns:
            StateTransition: 转换记录

        Raises:
            InvalidTransitionError: 非法状态转换
            MaxRetryExceededError: 超过最大重试次数
        """
        if not self._context:
            raise InvalidTransitionError(
                from_state="None",
                to_state=target_state.value,
                allowed_transitions=[]
            )

        current = self._context.current_state
        allowed = ALLOWED_TRANSITIONS.get(current, [])

        # 验证转换合法性
        if target_state not in allowed:
            raise InvalidTransitionError(
                from_state=current.value,
                to_state=target_state.value,
                allowed_transitions=[s.value for s in allowed]
            )

        # 检查重试次数
        if target_state == State.RETRY:
            if self._context.retry_count >= self._context.max_retries:
                raise MaxRetryExceededError(
                    max_retry=self._context.max_retries,
                    current_retry=self._context.retry_count
                )
            self._context.retry_count += 1

        # 创建转换记录
        transition = StateTransition(
            from_state=current,
            to_state=target_state,
            event=event,
            metadata=metadata or {}
        )

        # 更新状态
        self._context.current_state = target_state
        self._context.history.append(transition)
        self._context.updated_at = datetime.now()

        # 通知监听器
        for listener in self._listeners:
            listener(transition)

        return transition

    def get_allowed_actions(self) -> List[str]:
        """
        获取当前状态允许的动作

        Returns:
            List[str]: 允许的动作列表
        """
        if not self._context:
            return []

        config = STATE_CONFIGS.get(self._context.current_state)
        return config.allowed_actions if config else []

    def get_forbidden_actions(self) -> List[str]:
        """
        获取当前状态禁止的动作

        Returns:
            List[str]: 禁止的动作列表
        """
        if not self._context:
            return []

        config = STATE_CONFIGS.get(self._context.current_state)
        return config.forbidden_actions if config else []

    def get_prompt_constraint(self) -> str:
        """
        获取当前状态的提示词约束

        Returns:
            str: 提示词约束文本
        """
        if not self._context:
            return ""

        config = STATE_CONFIGS.get(self._context.current_state)
        return config.prompt_constraint if config else ""

    def is_action_allowed(self, action: str) -> bool:
        """
        检查动作是否允许

        Args:
            action: 动作名称

        Returns:
            bool: 是否允许
        """
        if not self._context:
            return False

        config = STATE_CONFIGS.get(self._context.current_state)
        return config.is_action_allowed(action) if config else False

    def get_state_config(self, state: Optional[State] = None) -> Optional[StateConfig]:
        """
        获取状态配置

        Args:
            state: 状态，为 None 时使用当前状态

        Returns:
            StateConfig: 状态配置
        """
        target = state or (self._context.current_state if self._context else None)
        return STATE_CONFIGS.get(target) if target else None


# 避免循环导入，在此导入 Context
from opspilot.core.context import StateMachineContext

