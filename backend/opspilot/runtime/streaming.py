"""
SSE 流式输出模块

基于 AgentScope Runtime 的 AaaS (Agent-as-a-Service) 能力。
提供实时流式输出，支持前端实时展示 Agent 执行进度。

特性：
- Server-Sent Events (SSE) 流式输出
- OpenAI SDK 兼容格式
- 任务进度实时推送
- 支持中断与恢复
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Union


class StreamEventType(Enum):
    """流式事件类型"""
    # 任务事件
    TASK_START = "task_start"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETE = "task_complete"
    TASK_ERROR = "task_error"
    
    # Agent 事件
    AGENT_START = "agent_start"
    AGENT_MESSAGE = "agent_message"
    AGENT_TOOL_CALL = "agent_tool_call"
    AGENT_TOOL_RESULT = "agent_tool_result"
    AGENT_COMPLETE = "agent_complete"
    
    # LLM 事件
    LLM_TOKEN = "llm_token"
    LLM_COMPLETE = "llm_complete"
    
    # 系统事件
    HEARTBEAT = "heartbeat"
    INTERRUPT = "interrupt"
    RESUME = "resume"


@dataclass
class StreamEvent:
    """流式事件"""
    event_type: StreamEventType
    data: Dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    
    def to_sse(self) -> str:
        """转换为 SSE 格式"""
        return (
            f"event: {self.event_type.value}\n"
            f"id: {self.event_id}\n"
            f"data: {json.dumps(self.data, ensure_ascii=False)}\n\n"
        )
    
    def to_openai_format(self) -> Dict[str, Any]:
        """转换为 OpenAI 格式"""
        return {
            "id": self.event_id,
            "object": "chat.completion.chunk",
            "created": int(self.timestamp),
            "choices": [{
                "index": 0,
                "delta": self.data,
                "finish_reason": None,
            }],
        }


class StreamWriter:
    """
    流式写入器
    
    管理流式事件的写入和发送。
    """
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self._queue: asyncio.Queue[Optional[StreamEvent]] = asyncio.Queue()
        self._closed = False
        self._buffer: List[StreamEvent] = []
    
    async def write(self, event: StreamEvent) -> None:
        """
        写入事件
        
        Args:
            event: 流式事件
        """
        if self._closed:
            return
        self._buffer.append(event)
        await self._queue.put(event)
    
    async def write_event(
        self,
        event_type: StreamEventType,
        data: Dict[str, Any],
    ) -> None:
        """
        写入事件（便捷方法）
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        event = StreamEvent(
            event_type=event_type,
            data={"task_id": self.task_id, **data},
        )
        await self.write(event)
    
    def close(self) -> None:
        """关闭流"""
        self._closed = True
        self._queue.put_nowait(None)
    
    async def __aiter__(self) -> AsyncGenerator[StreamEvent, None]:
        """异步迭代器"""
        while True:
            event = await self._queue.get()
            if event is None:
                break
            yield event
    
    async def to_sse_stream(self) -> AsyncGenerator[str, None]:
        """转换为 SSE 流"""
        async for event in self:
            yield event.to_sse()
    
    async def to_openai_stream(self) -> AsyncGenerator[str, None]:
        """转换为 OpenAI 格式流"""
        async for event in self:
            yield f"data: {json.dumps(event.to_openai_format())}\n\n"
        yield "data: [DONE]\n\n"


class StreamManager:
    """
    流式管理器
    
    管理多个任务的流式输出。
    """
    
    def __init__(self):
        self._writers: Dict[str, StreamWriter] = {}
        self._lock = asyncio.Lock()
    
    async def create_writer(self, task_id: str) -> StreamWriter:
        """
        创建流式写入器
        
        Args:
            task_id: 任务 ID
        
        Returns:
            StreamWriter: 流式写入器
        """
        async with self._lock:
            if task_id in self._writers:
                return self._writers[task_id]
            
            writer = StreamWriter(task_id)
            self._writers[task_id] = writer
            return writer
    
    async def get_writer(self, task_id: str) -> Optional[StreamWriter]:
        """
        获取流式写入器
        
        Args:
            task_id: 任务 ID
        
        Returns:
            StreamWriter: 流式写入器
        """
        return self._writers.get(task_id)
    
    async def close_writer(self, task_id: str) -> None:
        """
        关闭流式写入器
        
        Args:
            task_id: 任务 ID
        """
        async with self._lock:
            writer = self._writers.pop(task_id, None)
            if writer:
                writer.close()
    
    async def broadcast(
        self,
        event_type: StreamEventType,
        data: Dict[str, Any],
    ) -> None:
        """
        广播事件到所有写入器
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        for writer in self._writers.values():
            await writer.write_event(event_type, data)


# 全局流式管理器
_stream_manager: Optional[StreamManager] = None


def get_stream_manager() -> StreamManager:
    """获取全局流式管理器"""
    global _stream_manager
    if _stream_manager is None:
        _stream_manager = StreamManager()
    return _stream_manager


async def create_task_stream(
    task_id: str,
    process_fn: Callable[[StreamWriter], Any],
) -> AsyncGenerator[str, None]:
    """
    创建任务流
    
    Args:
        task_id: 任务 ID
        process_fn: 处理函数
    
    Yields:
        str: SSE 格式的事件
    """
    manager = get_stream_manager()
    writer = await manager.create_writer(task_id)
    
    async def run_process():
        try:
            await process_fn(writer)
        finally:
            writer.close()
            await manager.close_writer(task_id)
    
    # 启动处理任务
    process_task = asyncio.create_task(run_process())
    
    # 流式返回事件
    async for sse in writer.to_sse_stream():
        yield sse
    
    # 等待处理完成
    await process_task


class StreamingTaskExecutor:
    """
    流式任务执行器
    
    支持任务执行过程中的实时流式输出。
    """
    
    def __init__(self):
        self.manager = get_stream_manager()
    
    async def execute_with_stream(
        self,
        task_id: str,
        execute_fn: Callable[..., Any],
        *args,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """
        执行任务并流式输出
        
        Args:
            task_id: 任务 ID
            execute_fn: 执行函数
            *args: 位置参数
            **kwargs: 关键字参数
        
        Yields:
            str: SSE 格式的事件
        """
        writer = await self.manager.create_writer(task_id)
        
        async def run():
            try:
                # 发送任务开始事件
                await writer.write_event(
                    StreamEventType.TASK_START,
                    {"message": "任务开始执行"},
                )
                
                # 执行任务
                result = await execute_fn(*args, **kwargs)
                
                # 发送任务完成事件
                await writer.write_event(
                    StreamEventType.TASK_COMPLETE,
                    {"result": result, "message": "任务执行完成"},
                )
            
            except Exception as e:
                # 发送错误事件
                await writer.write_event(
                    StreamEventType.TASK_ERROR,
                    {"error": str(e), "message": "任务执行失败"},
                )
            
            finally:
                writer.close()
                await self.manager.close_writer(task_id)
        
        # 启动执行任务
        execute_task = asyncio.create_task(run())
        
        # 流式返回事件
        async for sse in writer.to_sse_stream():
            yield sse
        
        # 等待执行完成
        await execute_task
    
    async def execute_agent_with_stream(
        self,
        task_id: str,
        agent_name: str,
        agent_fn: Callable[..., Any],
        *args,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """
        执行 Agent 并流式输出
        
        Args:
            task_id: 任务 ID
            agent_name: Agent 名称
            agent_fn: Agent 执行函数
            *args: 位置参数
            **kwargs: 关键字参数
        
        Yields:
            str: SSE 格式的事件
        """
        writer = await self.manager.create_writer(task_id)
        
        async def run():
            try:
                # 发送 Agent 开始事件
                await writer.write_event(
                    StreamEventType.AGENT_START,
                    {"agent_name": agent_name, "message": f"{agent_name} 开始执行"},
                )
                
                # 执行 Agent
                result = await agent_fn(*args, **kwargs)
                
                # 发送 Agent 消息事件
                await writer.write_event(
                    StreamEventType.AGENT_MESSAGE,
                    {
                        "agent_name": agent_name,
                        "content": result,
                        "message": f"{agent_name} 执行完成",
                    },
                )
                
                # 发送 Agent 完成事件
                await writer.write_event(
                    StreamEventType.AGENT_COMPLETE,
                    {"agent_name": agent_name, "result": result},
                )
            
            except Exception as e:
                await writer.write_event(
                    StreamEventType.TASK_ERROR,
                    {"agent_name": agent_name, "error": str(e)},
                )
            
            finally:
                writer.close()
                await self.manager.close_writer(task_id)
        
        execute_task = asyncio.create_task(run())
        
        async for sse in writer.to_sse_stream():
            yield sse
        
        await execute_task
