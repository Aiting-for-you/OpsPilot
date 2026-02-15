"""
AgentScope 适配器模块

将 opspilot Agent 与 AgentScope 框架集成。

文档原文：
- "AgentScope 负责：MsgHub 消息中心、FSM 状态机、Agent 编排、博弈协调"
- "MsgHub 消息中心：多对多通信，而非点对点"
- "AgentScope 原生 MCP 支持"
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Type
from dataclasses import dataclass
import asyncio


# AgentScope imports
try:
    from agentscope.agents import AgentBase as ASAgentBase
    from agentscope.message import Msg
    from agentscope.utils import init_logger
    AGENTSCOPE_AVAILABLE = True
except ImportError:
    AGENTSCOPE_AVAILABLE = False
    ASAgentBase = object
    Msg = None


@dataclass
class AgentScopeConfig:
    """AgentScope 配置"""
    name: str
    model_config_name: str = "default"
    use_dist: bool = False  # 是否启用分布式
    max_retries: int = 3
    timeout: int = 60


class AgentScopeAdapter:
    """
    AgentScope 适配器
    
    提供与 AgentScope 框架的集成能力。
    
    示例:
        >>> adapter = AgentScopeAdapter()
        >>> if adapter.available:
        ...     agent = adapter.create_agent(config)
    """
    
    def __init__(self):
        """初始化适配器"""
        self._available = AGENTSCOPE_AVAILABLE
    
    @property
    def available(self) -> bool:
        """AgentScope 是否可用"""
        return self._available
    
    def create_agent_class(
        self,
        name: str,
        role: str,
        execute_fn: Callable,
    ) -> Type:
        """
        创建 AgentScope Agent 类
        
        Args:
            name: Agent 名称
            role: Agent 角色
            execute_fn: 执行函数
        
        Returns:
            Type: Agent 类
        """
        if not self._available:
            raise ImportError("AgentScope 未安装")
        
        class OpsAgent(ASAgentBase):
            """opspilot Agent - 继承 AgentScope AgentBase"""
            
            def __init__(self, name: str, model_config_name: str = "default", **kwargs):
                super().__init__(name=name, model_config_name=model_config_name, **kwargs)
                self._role = role
                self._execute_fn = execute_fn
            
            def reply(self, x: Msg = None) -> Msg:
                """
                AgentScope Agent 的回复方法
                
                Args:
                    x: 输入消息
                
                Returns:
                    Msg: 输出消息
                """
                # 异步调用包装
                if asyncio.iscoroutinefunction(self._execute_fn):
                    result = asyncio.run(self._execute_fn(x))
                else:
                    result = self._execute_fn(x)
                
                # 返回 AgentScope 消息
                return Msg(
                    name=self.name,
                    content=result,
                    role="assistant",
                )
        
        OpsAgent.__name__ = name
        return OpsAgent
    
    def create_message(
        self,
        name: str,
        content: Any,
        role: str = "user",
        **kwargs,
    ) -> Optional["Msg"]:
        """
        创建 AgentScope 消息
        
        Args:
            name: 发送者名称
            content: 消息内容
            role: 角色
        
        Returns:
            Msg: AgentScope 消息
        """
        if not self._available:
            return None
        
        return Msg(
            name=name,
            content=content,
            role=role,
            **kwargs,
        )
    
    def to_dist(self, agent) -> Any:
        """
        将 Agent 转换为分布式模式
        
        AgentScope 的 RpcAgent 能力
        
        Args:
            agent: Agent 实例
        
        Returns:
            分布式 Agent
        """
        if not self._available:
            raise ImportError("AgentScope 未安装")
        
        if hasattr(agent, 'to_dist'):
            return agent.to_dist()
        
        return agent


class OpsAgentBase:
    """
    opspilot Agent 基类
    
    自动适配 AgentScope 或使用独立实现。
    当 AgentScope 可用时，继承 AgentScope AgentBase；
    否则使用独立实现。
    """
    
    def __init__(
        self,
        name: str,
        role: str = "assistant",
        description: str = "",
        model_config: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化 Agent
        
        Args:
            name: Agent 名称
            role: Agent 角色
            description: Agent 描述
            model_config: 模型配置
        """
        self.name = name
        self.role = role
        self.description = description
        self.model_config = model_config or {}
        
        # AgentScope 适配
        self._adapter = AgentScopeAdapter()
        self._as_agent = None
        
        if self._adapter.available:
            self._init_agentscope_agent()
    
    def _init_agentscope_agent(self):
        """初始化 AgentScope Agent"""
        # 创建动态 Agent 类
        agent_class = self._adapter.create_agent_class(
            name=self.name,
            role=self.role,
            execute_fn=self._execute,
        )
        
        # 实例化
        self._as_agent = agent_class(
            name=self.name,
            model_config_name=self.model_config.get("model_name", "default"),
        )
    
    async def _execute(self, message: Any) -> Any:
        """
        Agent 执行逻辑（子类实现）
        
        Args:
            message: 输入消息
        
        Returns:
            执行结果
        """
        raise NotImplementedError("子类需实现 _execute 方法")
    
    async def run(self, input: Any) -> Any:
        """
        运行 Agent
        
        Args:
            input: 输入
        
        Returns:
            输出
        """
        if self._as_agent is not None:
            # 使用 AgentScope 执行
            msg = self._adapter.create_message(
                name="user",
                content=input,
            )
            result = self._as_agent.reply(msg)
            return result.content
        else:
            # 独立执行
            return await self._execute(input)
    
    def to_dist(self) -> Any:
        """
        转换为分布式 Agent
        
        使用 AgentScope 的 RpcAgent 能力
        """
        if self._as_agent is not None:
            return self._adapter.to_dist(self._as_agent)
        raise NotImplementedError("分布式模式需要 AgentScope")


class IntentAgent(OpsAgentBase):
    """意图识别 Agent"""
    
    def __init__(self, **kwargs):
        super().__init__(role="intent", description="识别用户意图", **kwargs)
    
    async def _execute(self, message: Any) -> Dict[str, Any]:
        """识别意图"""
        # 子类实现具体逻辑
        return {"intent": "unknown", "confidence": 0.0}


class PlanAgent(OpsAgentBase):
    """规划 Agent"""
    
    def __init__(self, **kwargs):
        super().__init__(role="planning", description="制定执行计划", **kwargs)
    
    async def _execute(self, message: Any) -> Dict[str, Any]:
        """制定计划"""
        # 子类实现具体逻辑
        return {"plan": [], "steps": []}


class ExecAgent(OpsAgentBase):
    """执行 Agent"""
    
    def __init__(self, **kwargs):
        super().__init__(role="execution", description="执行任务", **kwargs)
    
    async def _execute(self, message: Any) -> Dict[str, Any]:
        """执行任务"""
        # 子类实现具体逻辑
        return {"result": None, "status": "pending"}


class VerifyAgent(OpsAgentBase):
    """验证 Agent"""
    
    def __init__(self, **kwargs):
        super().__init__(role="verification", description="验证执行结果", **kwargs)
    
    async def _execute(self, message: Any) -> Dict[str, Any]:
        """验证结果"""
        # 子类实现具体逻辑
        return {"valid": False, "issues": []}


# 全局适配器实例
_adapter = AgentScopeAdapter()


def is_agentscope_available() -> bool:
    """检查 AgentScope 是否可用"""
    return _adapter.available


def create_agentscope_message(
    name: str,
    content: Any,
    role: str = "user",
) -> Optional["Msg"]:
    """创建 AgentScope 消息的便捷函数"""
    return _adapter.create_message(name, content, role)

