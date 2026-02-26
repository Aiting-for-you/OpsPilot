"""
LLM Mock 类

模拟 LLM 客户端用于测试
"""
from typing import Dict, Any, List, Optional, AsyncIterator, Callable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import json
import random


@dataclass
class MockResponse:
    """模拟 LLM 响应"""
    content: str
    role: str = "assistant"
    model: str = "mock-model"
    usage: Dict[str, int] = field(default_factory=lambda: {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150})
    finish_reason: str = "stop"
    latency_ms: int = 100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "role": self.role,
            "model": self.model,
            "usage": self.usage,
            "finish_reason": self.finish_reason,
            "latency_ms": self.latency_ms,
        }


def create_mock_response(
    content: str,
    latency_ms: int = 100,
    **kwargs
) -> MockResponse:
    """
    创建模拟响应

    Args:
        content: 响应内容
        latency_ms: 模拟延迟（毫秒）
        **kwargs: 其他参数

    Returns:
        MockResponse 对象
    """
    return MockResponse(
        content=content,
        latency_ms=latency_ms,
        **kwargs
    )


class MockLLMClient:
    """
    Mock LLM 客户端

    用于测试场景，可配置预定义响应
    """

    def __init__(
        self,
        default_response: str = "这是一个模拟响应。",
        responses: Optional[Dict[str, str]] = None,
        latency_ms: int = 100,
        error_rate: float = 0.0,
    ):
        """
        初始化 Mock 客户端

        Args:
            default_response: 默认响应文本
            responses: 关键词到响应的映射 {"关键词": "响应"}
            latency_ms: 模拟延迟
            error_rate: 错误率 (0.0 - 1.0)
        """
        self.default_response = default_response
        self.responses = responses or {}
        self.latency_ms = latency_ms
        self.error_rate = error_rate
        self.call_count = 0
        self.call_history: List[Dict[str, Any]] = []

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """
        生成响应

        Args:
            prompt: 用户输入
            system_prompt: 系统提示
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            响应文本
        """
        self.call_count += 1
        self.call_history.append({
            "prompt": prompt[:200],  # 只保留前200字符
            "system_prompt": system_prompt[:100] if system_prompt else None,
            "timestamp": datetime.now().isoformat(),
        })

        # 模拟延迟
        await asyncio.sleep(self.latency_ms / 1000)

        # 模拟错误
        if self.error_rate > 0 and random.random() < self.error_rate:
            raise RuntimeError("模拟 LLM 调用错误")

        # 查找匹配的响应
        for keyword, response in self.responses.items():
            if keyword in prompt:
                return response

        return self.default_response

    async def generate_with_usage(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> MockResponse:
        """
        生成响应（包含使用量信息）

        Args:
            prompt: 用户输入
            system_prompt: 系统提示
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            MockResponse 对象
        """
        content = await self.generate(prompt, system_prompt, temperature, max_tokens)
        return MockResponse(
            content=content,
            usage={
                "prompt_tokens": len(prompt) // 4,  # 粗略估算
                "completion_tokens": len(content) // 4,
                "total_tokens": (len(prompt) + len(content)) // 4,
            },
            latency_ms=self.latency_ms,
        )

    def reset(self):
        """重置状态"""
        self.call_count = 0
        self.call_history = []


class MockStreamingLLMClient:
    """
    Mock 流式 LLM 客户端

    模拟流式响应
    """

    def __init__(
        self,
        default_response: str = "这是一个流式模拟响应。",
        chunk_size: int = 5,
        latency_ms_per_chunk: int = 50,
    ):
        """
        初始化流式 Mock 客户端

        Args:
            default_response: 默认响应文本
            chunk_size: 每块字符数
            latency_ms_per_chunk: 每块延迟
        """
        self.default_response = default_response
        self.chunk_size = chunk_size
        self.latency_ms_per_chunk = latency_ms_per_chunk

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """
        流式生成响应

        Args:
            prompt: 用户输入
            system_prompt: 系统提示
            temperature: 温度参数
            max_tokens: 最大 token 数

        Yields:
            响应文本片段
        """
        response = self.default_response
        for i in range(0, len(response), self.chunk_size):
            chunk = response[i:i + self.chunk_size]
            await asyncio.sleep(self.latency_ms_per_chunk / 1000)
            yield chunk


class IntentMockLLMClient(MockLLMClient):
    """
    意图识别 Mock 客户端

    预配置意图识别场景的响应
    """

    def __init__(self, **kwargs):
        responses = {
            "供应商": "INTENT: query_supplier",
            "查询供应商": "INTENT: query_supplier",
            "库存": "INTENT: query_inventory",
            "查询库存": "INTENT: query_inventory",
            "创建订单": "INTENT: create_order",
            "下单": "INTENT: create_order",
            "订单状态": "INTENT: query_order",
            "查询订单": "INTENT: query_order",
            "合规": "INTENT: check_compliance",
            "政策": "INTENT: query_policy",
        }
        super().__init__(
            default_response="INTENT: unknown",
            responses=responses,
            **kwargs
        )


class PlanningMockLLMClient(MockLLMClient):
    """
    规划 Mock 客户端

    预配置规划场景的响应
    """

    def __init__(self, **kwargs):
        responses = {
            "供应商": '''```json
{
    "steps": [
        {"tool": "query_supplier", "params": {"supplier_name": "华南"}},
        {"tool": "query_inventory", "params": {"sku": "SKU001"}}
    ]
}
```''',
            "订单": '''```json
{
    "steps": [
        {"tool": "query_supplier", "params": {"region": "华南"}},
        {"tool": "create_order", "params": {"supplier_id": "SUP001", "products": [{"sku": "SKU001", "quantity": 100}]}}
    ]
}
```''',
        }
        super().__init__(
            default_response='''```json
{
    "steps": [
        {"tool": "unknown", "params": {}}
    ]
}
```''',
            responses=responses,
            **kwargs
        )


class AgentMockLLMClient:
    """
    Agent 专用 Mock 客户端

    支持多轮对话和上下文
    """

    def __init__(self, agent_type: str = "generic"):
        """
        初始化

        Args:
            agent_type: Agent 类型 (intent/planning/execution/verification)
        """
        self.agent_type = agent_type
        self.conversation_history: List[Dict[str, str]] = []

    async def chat(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        多轮对话

        Args:
            message: 用户消息
            context: 上下文信息

        Returns:
            响应字典
        """
        self.conversation_history.append({"role": "user", "content": message})

        # 根据类型生成响应
        if self.agent_type == "intent":
            response = self._generate_intent_response(message)
        elif self.agent_type == "planning":
            response = self._generate_planning_response(message)
        elif self.agent_type == "execution":
            response = self._generate_execution_response(message)
        else:
            response = {"content": "Mock response", "confidence": 0.9}

        self.conversation_history.append({"role": "assistant", "content": response.get("content", "")})
        return response

    def _generate_intent_response(self, message: str) -> Dict[str, Any]:
        """生成意图识别响应"""
        intents = {
            "供应商": {"intent": "query_supplier", "confidence": 0.95},
            "库存": {"intent": "query_inventory", "confidence": 0.92},
            "订单": {"intent": "create_order", "confidence": 0.88},
            "合规": {"intent": "check_compliance", "confidence": 0.90},
        }
        for keyword, data in intents.items():
            if keyword in message:
                return {"content": json.dumps(data), **data}
        return {"content": '{"intent": "unknown", "confidence": 0.5}', "intent": "unknown", "confidence": 0.5}

    def _generate_planning_response(self, message: str) -> Dict[str, Any]:
        """生成规划响应"""
        plan = {
            "steps": [
                {"step": 1, "action": "analyze", "description": "分析用户需求"},
                {"step": 2, "action": "plan", "description": "制定执行计划"},
                {"step": 3, "action": "execute", "description": "执行计划"},
            ]
        }
        return {"content": json.dumps(plan, ensure_ascii=False), "plan": plan}

    def _generate_execution_response(self, message: str) -> Dict[str, Any]:
        """生成执行响应"""
        result = {
            "status": "success",
            "message": "执行完成",
            "data": {"processed": True},
        }
        return {"content": json.dumps(result, ensure_ascii=False), "result": result}
