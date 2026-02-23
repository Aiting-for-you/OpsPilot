"""
Agent 基础模块

职责：
- Agent 抽象基类
- Agent 生命周期管理
- LLM 调用接口（Mock）
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import uuid
import asyncio

from opspilot.core.state_machine import State
from opspilot.core.events import EventBus, AgentStartedEvent, AgentCompletedEvent, AgentFailedEvent
from opspilot.utils.exceptions import (
    AgentTimeoutError,
    AgentExecutionError,
    PromptLoadError,
)


class AgentRole(str, Enum):
    """Agent 角色类型"""
    INTENT = "intent"       # 意图识别
    PLANNING = "planning"   # 规划
    EXECUTION = "execution" # 执行
    VERIFICATION = "verification"  # 验证


@dataclass
class AgentConfig:
    """Agent 配置"""
    name: str
    role: AgentRole
    description: str = ""
    model: str = "default"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 60


@dataclass
class AgentContext:
    """Agent 执行上下文"""
    task_id: str
    state: State
    user_input: str = ""
    history: List[Dict[str, Any]] = field(default_factory=list)
    memory_context: str = ""
    knowledge_context: str = ""
    tool_results: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentOutput:
    """Agent 输出"""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    next_state: Optional[State] = None
    tools_to_call: List[Dict[str, Any]] = field(default_factory=list)
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    agent_name: str = ""  # 执行此输出的Agent名称

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "next_state": self.next_state.value if self.next_state else None,
            "tools_to_call": self.tools_to_call,
            "reasoning": self.reasoning,
            "metadata": self.metadata,
            "agent_name": self.agent_name,
        }


class BaseLLMClient(ABC):
    """
    LLM 客户端抽象基类

    定义 LLM 调用接口，支持 Mock 实现
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """
        生成文本

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            str: 生成的文本
        """
        pass

    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成 JSON 格式输出

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            schema: JSON Schema

        Returns:
            Dict[str, Any]: JSON 输出
        """
        pass


class MockLLMClient(BaseLLMClient):
    """
    Mock LLM 客户端

    用于开发和测试，返回预设的响应
    """

    def __init__(self):
        self._responses: Dict[str, str] = {}
        self._json_responses: Dict[str, Dict[str, Any]] = {}

    def set_response(self, prompt_pattern: str, response: str) -> None:
        """设置预设响应"""
        self._responses[prompt_pattern] = response

    def set_json_response(self, prompt_pattern: str, response: Dict[str, Any]) -> None:
        """设置预设 JSON 响应"""
        self._json_responses[prompt_pattern] = response

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """生成文本（Mock）"""
        # 查找匹配的预设响应
        for pattern, response in self._responses.items():
            if pattern in prompt:
                return response

        # 默认响应
        return "这是一个 Mock 响应。请配置具体的预设响应。"

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """生成 JSON（Mock）"""
        # 查找匹配的预设响应
        for pattern, response in self._json_responses.items():
            if pattern in prompt:
                return response

        # 默认响应
        return {"status": "mock", "message": "请配置具体的预设响应"}


class BaseAgent(ABC):
    """
    Agent 抽象基类

    定义 Agent 的基本行为和生命周期
    """

    def __init__(
        self,
        config: AgentConfig,
        llm_client: Optional[BaseLLMClient] = None
    ):
        """
        初始化 Agent

        Args:
            config: Agent 配置
            llm_client: LLM 客户端
        """
        self.config = config
        self._llm = llm_client or MockLLMClient()
        self._event_bus = EventBus.get_instance()

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def role(self) -> AgentRole:
        return self.config.role

    @property
    def llm(self) -> BaseLLMClient:
        return self._llm

    def set_llm_client(self, client: BaseLLMClient) -> None:
        """设置 LLM 客户端"""
        self._llm = client

    async def execute(
        self,
        context: AgentContext,
        raise_on_error: bool = False
    ) -> AgentOutput:
        """
        执行 Agent

        Args:
            context: 执行上下文
            raise_on_error: 是否在错误时抛出异常（默认返回 AgentOutput.error）

        Returns:
            AgentOutput: 执行结果

        Raises:
            AgentTimeoutError: Agent 执行超时
            AgentExecutionError: Agent 执行失败
        """
        start_time = datetime.now()

        # 发布开始事件
        self._event_bus.publish(AgentStartedEvent(
            task_id=context.task_id,
            agent_name=self.name,
            state=context.state.value
        ))

        try:
            # 执行具体逻辑（带超时控制）
            output = await asyncio.wait_for(
                self._execute(context),
                timeout=self.config.timeout
            )

            # 发布完成事件
            self._event_bus.publish(AgentCompletedEvent(
                task_id=context.task_id,
                agent_name=self.name,
                result=output.to_dict()
            ))

            return output

        except asyncio.TimeoutError:
            # 发布失败事件
            self._event_bus.publish(AgentFailedEvent(
                task_id=context.task_id,
                agent_name=self.name,
                error=f"Agent 执行超时: {self.config.timeout}s"
            ))

            if raise_on_error:
                raise AgentTimeoutError(self.name, self.config.timeout)

            return AgentOutput(
                success=False,
                error=f"Agent 执行超时: {self.config.timeout}s"
            )

        except Exception as e:
            # 发布失败事件
            self._event_bus.publish(AgentFailedEvent(
                task_id=context.task_id,
                agent_name=self.name,
                error=str(e)
            ))

            if raise_on_error:
                raise AgentExecutionError(self.name, str(e))

            return AgentOutput(
                success=False,
                error=str(e)
            )

    @abstractmethod
    async def _execute(self, context: AgentContext) -> AgentOutput:
        """
        具体执行逻辑（子类实现）

        Args:
            context: 执行上下文

        Returns:
            AgentOutput: 执行结果
        """
        pass

    def get_system_prompt(self, context: AgentContext) -> str:
        """
        获取系统提示

        子类可重写以提供特定的系统提示

        Args:
            context: 执行上下文

        Returns:
            str: 系统提示
        """
        return f"你是{self.config.name}，职责是{self.config.description}。"

    def build_prompt(self, context: AgentContext) -> str:
        """
        构建提示

        子类可重写以提供特定的提示构建逻辑

        Args:
            context: 执行上下文

        Returns:
            str: 提示
        """
        parts = []

        # 用户输入
        if context.user_input:
            parts.append(f"用户输入：{context.user_input}")

        # 记忆上下文
        if context.memory_context:
            parts.append(f"历史记忆：\n{context.memory_context}")

        # 知识上下文
        if context.knowledge_context:
            parts.append(context.knowledge_context)

        # 工具结果
        if context.tool_results:
            parts.append("工具执行结果：")
            for result in context.tool_results:
                parts.append(f"- {result}")

        return "\n\n".join(parts)


class AgentRegistry:
    """
    Agent 注册表

    管理所有 Agent 实例
    """

    _instance: Optional["AgentRegistry"] = None

    def __new__(cls) -> "AgentRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._agents: Dict[str, BaseAgent] = {}
        return cls._instance

    def register(self, agent: BaseAgent) -> None:
        """注册 Agent"""
        self._agents[agent.name] = agent

    def unregister(self, name: str) -> None:
        """注销 Agent"""
        self._agents.pop(name, None)

    def get(self, name: str) -> Optional[BaseAgent]:
        """获取 Agent"""
        return self._agents.get(name)

    def get_by_role(self, role: AgentRole) -> List[BaseAgent]:
        """按角色获取 Agent"""
        return [a for a in self._agents.values() if a.role == role]

    def list_all(self) -> List[str]:
        """列出所有 Agent 名称"""
        return list(self._agents.keys())

    def clear(self) -> None:
        """清空注册表"""
        self._agents.clear()

