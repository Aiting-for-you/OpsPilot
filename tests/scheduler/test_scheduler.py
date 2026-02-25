"""
任务调度器测试

测试任务调度系统的核心功能：
- 任务添加、取消、查询
- 优先级队列
- 定时任务
- 周期性任务
- 重试机制
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from opspilot.scheduler.task_scheduler import (
    TaskScheduler,
    ScheduledTask,
    TaskPriority,
    TaskStatus,
    TaskType,
    get_scheduler,
)


class TestTaskPriority:
    """任务优先级测试"""
    
    def test_priority_values(self):
        """测试优先级值"""
        assert TaskPriority.LOW.value == 1
        assert TaskPriority.NORMAL.value == 5
        assert TaskPriority.HIGH.value == 10
        assert TaskPriority.URGENT.value == 20
    
    def test_priority_comparison(self):
        """测试优先级比较"""
        assert TaskPriority.URGENT.value > TaskPriority.HIGH.value
        assert TaskPriority.HIGH.value > TaskPriority.NORMAL.value
        assert TaskPriority.NORMAL.value > TaskPriority.LOW.value


class TestTaskStatus:
    """任务状态测试"""
    
    def test_status_values(self):
        """测试状态值"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.QUEUED.value == "queued"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"
        assert TaskStatus.RETRYING.value == "retrying"


class TestTaskType:
    """任务类型测试"""
    
    def test_type_values(self):
        """测试类型值"""
        assert TaskType.ONE_TIME.value == "one_time"
        assert TaskType.SCHEDULED.value == "scheduled"
        assert TaskType.RECURRING.value == "recurring"


class TestScheduledTask:
    """调度任务测试"""
    
    def test_task_creation(self):
        """测试任务创建"""
        task = ScheduledTask(
            task_id="test-001",
            name="测试任务",
            task_type=TaskType.ONE_TIME,
            target=lambda: "result",
        )
        
        assert task.task_id == "test-001"
        assert task.name == "测试任务"
        assert task.task_type == TaskType.ONE_TIME
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.NORMAL
        assert task.max_retries == 3
        assert task.retry_count == 0
    
    def test_task_comparison(self):
        """测试任务比较（优先级队列）"""
        task1 = ScheduledTask(
            task_id="task-1",
            name="低优先级",
            task_type=TaskType.ONE_TIME,
            target=lambda: None,
            priority=TaskPriority.LOW,
        )
        
        task2 = ScheduledTask(
            task_id="task-2",
            name="高优先级",
            task_type=TaskType.ONE_TIME,
            target=lambda: None,
            priority=TaskPriority.HIGH,
        )
        
        # 高优先级应该"小于"低优先级（堆顶元素）
        assert task2 < task1


class TestTaskScheduler:
    """任务调度器测试"""
    
    @pytest.fixture
    def scheduler(self):
        """创建调度器实例"""
        return TaskScheduler(max_concurrent_tasks=5)
    
    def test_scheduler_creation(self, scheduler):
        """测试调度器创建"""
        assert scheduler.max_concurrent_tasks == 5
        assert scheduler.is_running is False
        assert len(scheduler.tasks) == 0
        assert len(scheduler.task_queue) == 0
        assert scheduler.stats["total_tasks"] == 0
    
    def test_add_task(self, scheduler):
        """测试添加任务"""
        task_id = scheduler.add_task(
            name="测试任务",
            target=lambda: "result",
            priority=TaskPriority.HIGH,
        )
        
        assert task_id.startswith("task-")
        assert task_id in scheduler.tasks
        assert scheduler.stats["total_tasks"] == 1
        
        task = scheduler.get_task(task_id)
        assert task.name == "测试任务"
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING
    
    def test_add_task_with_args(self, scheduler):
        """测试带参数的任务"""
        def target_func(a, b, c=10):
            return a + b + c
        
        task_id = scheduler.add_task(
            name="带参数任务",
            target=target_func,
            args=(1, 2),
            kwargs={"c": 3},
        )
        
        task = scheduler.get_task(task_id)
        assert task.args == (1, 2)
        assert task.kwargs == {"c": 3}
    
    def test_add_scheduled_task(self, scheduler):
        """测试定时任务"""
        scheduled_time = datetime.now() + timedelta(hours=1)
        
        task_id = scheduler.add_task(
            name="定时任务",
            target=lambda: "result",
            task_type=TaskType.SCHEDULED,
            scheduled_time=scheduled_time,
        )
        
        task = scheduler.get_task(task_id)
        assert task.task_type == TaskType.SCHEDULED
        assert task.scheduled_time == scheduled_time
    
    def test_add_recurring_task(self, scheduler):
        """测试周期性任务"""
        task_id = scheduler.add_task(
            name="周期任务",
            target=lambda: "result",
            task_type=TaskType.RECURRING,
            interval=3600,  # 1小时
        )
        
        task = scheduler.get_task(task_id)
        assert task.task_type == TaskType.RECURRING
        assert task.interval == 3600
    
    def test_cancel_task(self, scheduler):
        """测试取消任务"""
        task_id = scheduler.add_task(
            name="待取消任务",
            target=lambda: "result",
        )
        
        # 取消任务
        result = scheduler.cancel_task(task_id)
        assert result is True
        
        task = scheduler.get_task(task_id)
        assert task.status == TaskStatus.CANCELLED
        assert scheduler.stats["cancelled_tasks"] == 1
    
    def test_cancel_nonexistent_task(self, scheduler):
        """测试取消不存在的任务"""
        result = scheduler.cancel_task("nonexistent-task")
        assert result is False
    
    def test_get_all_tasks(self, scheduler):
        """测试获取所有任务"""
        scheduler.add_task(name="任务1", target=lambda: None)
        scheduler.add_task(name="任务2", target=lambda: None)
        scheduler.add_task(name="任务3", target=lambda: None)
        
        tasks = scheduler.get_all_tasks()
        assert len(tasks) == 3
    
    def test_get_tasks_by_status(self, scheduler):
        """测试按状态获取任务"""
        id1 = scheduler.add_task(name="任务1", target=lambda: None)
        id2 = scheduler.add_task(name="任务2", target=lambda: None)
        
        scheduler.cancel_task(id1)
        
        pending_tasks = scheduler.get_all_tasks(status=TaskStatus.PENDING)
        cancelled_tasks = scheduler.get_all_tasks(status=TaskStatus.CANCELLED)
        
        assert len(pending_tasks) == 1
        assert len(cancelled_tasks) == 1
    
    def test_get_stats(self, scheduler):
        """测试获取统计信息"""
        scheduler.add_task(name="任务1", target=lambda: None)
        scheduler.add_task(name="任务2", target=lambda: None)
        
        stats = scheduler.get_stats()
        
        assert stats["total_tasks"] == 2
        assert stats["total_tasks_stored"] == 2
        assert stats["queued_tasks"] == 2
        assert stats["running_tasks"] == 0
    
    @pytest.mark.asyncio
    async def test_scheduler_start_stop(self, scheduler):
        """测试调度器启动和停止"""
        await scheduler.start()
        assert scheduler.is_running is True
        
        await scheduler.stop()
        assert scheduler.is_running is False
    
    @pytest.mark.asyncio
    async def test_execute_task(self, scheduler):
        """测试执行任务"""
        call_count = 0
        
        def target_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        task_id = scheduler.add_task(
            name="执行任务",
            target=target_func,
        )
        
        await scheduler.start()
        
        # 等待任务执行
        await asyncio.sleep(2)
        
        task = scheduler.get_task(task_id)
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "success"
        assert call_count == 1
        
        await scheduler.stop()
    
    @pytest.mark.asyncio
    async def test_execute_async_task(self, scheduler):
        """测试执行异步任务"""
        async def async_target():
            await asyncio.sleep(0.1)
            return "async_result"
        
        task_id = scheduler.add_task(
            name="异步任务",
            target=async_target,
        )
        
        await scheduler.start()
        await asyncio.sleep(2)
        
        task = scheduler.get_task(task_id)
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "async_result"
        
        await scheduler.stop()
    
    @pytest.mark.asyncio
    async def test_task_retry(self, scheduler):
        """测试任务重试"""
        call_count = 0
        
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("模拟失败")
            return "success"
        
        task_id = scheduler.add_task(
            name="重试任务",
            target=failing_func,
            max_retries=3,
            retry_interval=1,
        )
        
        await scheduler.start()
        await asyncio.sleep(5)
        
        task = scheduler.get_task(task_id)
        # 应该在第3次成功
        assert task.status == TaskStatus.COMPLETED
        assert task.retry_count == 2
        
        await scheduler.stop()
    
    @pytest.mark.asyncio
    async def test_task_max_retries_exceeded(self, scheduler):
        """测试超过最大重试次数"""
        def always_fail():
            raise ValueError("总是失败")
        
        task_id = scheduler.add_task(
            name="失败任务",
            target=always_fail,
            max_retries=2,
            retry_interval=1,
        )
        
        await scheduler.start()
        await asyncio.sleep(5)
        
        task = scheduler.get_task(task_id)
        assert task.status == TaskStatus.FAILED
        assert task.retry_count == 2
        assert "总是失败" in task.error_message
        
        await scheduler.stop()


class TestGetScheduler:
    """全局调度器测试"""
    
    def test_get_scheduler_singleton(self):
        """测试获取全局调度器（单例）"""
        scheduler1 = get_scheduler()
        scheduler2 = get_scheduler()
        
        assert scheduler1 is scheduler2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
