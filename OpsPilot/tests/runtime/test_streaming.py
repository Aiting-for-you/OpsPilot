"""
流式输出模块单元测试
"""
import pytest
import asyncio
import json

from opspilot.runtime.streaming import (
    StreamEventType,
    StreamEvent,
    StreamWriter,
    StreamManager,
    StreamingTaskExecutor,
    get_stream_manager,
    create_task_stream,
)


class TestStreamEventType:
    """流式事件类型测试"""

    def test_event_types(self):
        """测试事件类型枚举"""
        assert StreamEventType.TASK_START.value == "task_start"
        assert StreamEventType.TASK_PROGRESS.value == "task_progress"
        assert StreamEventType.TASK_COMPLETE.value == "task_complete"
        assert StreamEventType.AGENT_START.value == "agent_start"
        assert StreamEventType.LLM_TOKEN.value == "llm_token"
        assert StreamEventType.HEARTBEAT.value == "heartbeat"


class TestStreamEvent:
    """流式事件测试"""

    def test_create_event(self):
        """测试创建事件"""
        event = StreamEvent(
            event_type=StreamEventType.TASK_START,
            data={"task_id": "test-123", "message": "开始"},
        )
        
        assert event.event_type == StreamEventType.TASK_START
        assert event.data["task_id"] == "test-123"
        assert event.event_id is not None
        assert event.timestamp > 0

    def test_to_sse(self):
        """测试转换为 SSE 格式"""
        event = StreamEvent(
            event_type=StreamEventType.TASK_START,
            data={"message": "开始"},
        )
        
        sse = event.to_sse()
        
        assert "event: task_start" in sse
        assert "id:" in sse
        assert "data:" in sse
        assert "开始" in sse

    def test_to_openai_format(self):
        """测试转换为 OpenAI 格式"""
        event = StreamEvent(
            event_type=StreamEventType.LLM_TOKEN,
            data={"content": "Hello"},
        )
        
        openai_format = event.to_openai_format()
        
        assert openai_format["object"] == "chat.completion.chunk"
        assert "choices" in openai_format
        assert openai_format["choices"][0]["delta"]["content"] == "Hello"


class TestStreamWriter:
    """流式写入器测试"""

    @pytest.fixture
    def writer(self):
        return StreamWriter(task_id="test-task-123")

    def test_initial_state(self, writer):
        """测试初始状态"""
        assert writer.task_id == "test-task-123"
        assert writer._closed is False
        assert len(writer._buffer) == 0

    @pytest.mark.asyncio
    async def test_write_event(self, writer):
        """测试写入事件"""
        await writer.write_event(
            StreamEventType.TASK_START,
            {"message": "任务开始"},
        )
        
        assert len(writer._buffer) == 1
        event = writer._buffer[0]
        assert event.event_type == StreamEventType.TASK_START
        assert event.data["task_id"] == "test-task-123"

    @pytest.mark.asyncio
    async def test_write_multiple_events(self, writer):
        """测试写入多个事件"""
        await writer.write_event(StreamEventType.TASK_START, {"step": 1})
        await writer.write_event(StreamEventType.TASK_PROGRESS, {"step": 2})
        await writer.write_event(StreamEventType.TASK_COMPLETE, {"step": 3})
        
        assert len(writer._buffer) == 3

    @pytest.mark.asyncio
    async def test_close_writer(self, writer):
        """测试关闭写入器"""
        await writer.write_event(StreamEventType.TASK_START, {})
        writer.close()
        
        assert writer._closed is True

    @pytest.mark.asyncio
    async def test_write_after_close(self, writer):
        """测试关闭后写入"""
        writer.close()
        await writer.write_event(StreamEventType.TASK_START, {})
        
        assert len(writer._buffer) == 0

    @pytest.mark.asyncio
    async def test_to_sse_stream(self, writer):
        """测试转换为 SSE 流"""
        await writer.write_event(StreamEventType.TASK_START, {"message": "开始"})
        await writer.write_event(StreamEventType.TASK_COMPLETE, {"message": "完成"})
        writer.close()
        
        sse_events = []
        async for sse in writer.to_sse_stream():
            sse_events.append(sse)
        
        assert len(sse_events) == 2

    @pytest.mark.asyncio
    async def test_to_openai_stream(self, writer):
        """测试转换为 OpenAI 流"""
        await writer.write_event(StreamEventType.LLM_TOKEN, {"content": "Hello"})
        writer.close()
        
        openai_events = []
        async for event in writer.to_openai_stream():
            openai_events.append(event)
        
        assert len(openai_events) == 2  # 事件 + [DONE]
        assert "[DONE]" in openai_events[-1]


class TestStreamManager:
    """流式管理器测试"""

    @pytest.fixture
    def manager(self):
        return StreamManager()

    @pytest.mark.asyncio
    async def test_create_writer(self, manager):
        """测试创建写入器"""
        writer = await manager.create_writer("task-1")
        
        assert writer.task_id == "task-1"
        assert "task-1" in manager._writers

    @pytest.mark.asyncio
    async def test_get_writer(self, manager):
        """测试获取写入器"""
        await manager.create_writer("task-1")
        
        writer = await manager.get_writer("task-1")
        assert writer is not None
        assert writer.task_id == "task-1"
        
        # 不存在的写入器
        writer = await manager.get_writer("nonexistent")
        assert writer is None

    @pytest.mark.asyncio
    async def test_close_writer(self, manager):
        """测试关闭写入器"""
        await manager.create_writer("task-1")
        await manager.close_writer("task-1")
        
        assert "task-1" not in manager._writers

    @pytest.mark.asyncio
    async def test_broadcast(self, manager):
        """测试广播事件"""
        writer1 = await manager.create_writer("task-1")
        writer2 = await manager.create_writer("task-2")
        
        await manager.broadcast(
            StreamEventType.HEARTBEAT,
            {"message": "心跳"},
        )
        
        assert len(writer1._buffer) == 1
        assert len(writer2._buffer) == 1


class TestStreamingTaskExecutor:
    """流式任务执行器测试"""

    @pytest.fixture
    def executor(self):
        return StreamingTaskExecutor()

    @pytest.mark.asyncio
    async def test_execute_with_stream_success(self, executor):
        """测试执行任务并流式输出（成功）"""
        async def execute_fn():
            await asyncio.sleep(0.1)
            return {"status": "success"}
        
        events = []
        async for sse in executor.execute_with_stream("task-1", execute_fn):
            events.append(sse)
        
        assert len(events) >= 2  # TASK_START + TASK_COMPLETE
        assert "task_start" in events[0]
        assert "task_complete" in events[-1]

    @pytest.mark.asyncio
    async def test_execute_with_stream_error(self, executor):
        """测试执行任务并流式输出（错误）"""
        async def execute_fn():
            raise ValueError("测试错误")
        
        events = []
        async for sse in executor.execute_with_stream("task-1", execute_fn):
            events.append(sse)
        
        assert len(events) >= 1
        assert "task_error" in events[-1]

    @pytest.mark.asyncio
    async def test_execute_agent_with_stream(self, executor):
        """测试执行 Agent 并流式输出"""
        async def agent_fn():
            return "Agent 执行结果"
        
        events = []
        async for sse in executor.execute_agent_with_stream(
            "task-1",
            "TestAgent",
            agent_fn,
        ):
            events.append(sse)
        
        assert len(events) >= 2  # AGENT_START + AGENT_COMPLETE
        assert "agent_start" in events[0]


class TestGetStreamManager:
    """获取流式管理器测试"""

    def test_get_stream_manager(self):
        """测试获取全局流式管理器"""
        manager1 = get_stream_manager()
        manager2 = get_stream_manager()
        
        assert manager1 is manager2


class TestCreateTaskStream:
    """创建任务流测试"""

    @pytest.mark.asyncio
    async def test_create_task_stream(self):
        """测试创建任务流"""
        async def process_fn(writer):
            await writer.write_event(
                StreamEventType.TASK_START,
                {"message": "开始"},
            )
            await asyncio.sleep(0.1)
            await writer.write_event(
                StreamEventType.TASK_COMPLETE,
                {"message": "完成"},
            )
        
        events = []
        async for sse in create_task_stream("task-1", process_fn):
            events.append(sse)
        
        assert len(events) == 2
