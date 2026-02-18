"""任务调度系统 - 定时任务、优先级队列、重试机制"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from uuid import uuid4
import heapq

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 5
    HIGH = 10
    URGENT = 20


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskType(Enum):
    """任务类型"""
    ONE_TIME = "one_time"  # 一次性任务
    SCHEDULED = "scheduled"  # 定时任务
    RECURRING = "recurring"  # 周期性任务


@dataclass
class ScheduledTask:
    """调度任务"""
    task_id: str
    name: str
    task_type: TaskType
    target: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    
    # 调度配置
    scheduled_time: Optional[datetime] = None  # 定时执行时间
    interval: Optional[int] = None  # 周期性任务间隔（秒）
    cron_expression: Optional[str] = None  # cron 表达式
    
    # 重试配置
    max_retries: int = 3
    retry_count: int = 0
    retry_interval: int = 60  # 重试间隔（秒）
    
    # 执行信息
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Any = None
    
    # 元数据
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other: "ScheduledTask") -> bool:
        """用于优先级队列比较"""
        # 先按优先级降序，再按创建时间升序
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value
        return self.created_at < other.created_at


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, max_concurrent_tasks: int = 10):
        self.max_concurrent_tasks = max_concurrent_tasks
        
        # 任务存储
        self.tasks: Dict[str, ScheduledTask] = {}
        self.task_queue: List[ScheduledTask] = []  # 优先级队列
        
        # 运行状态
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.is_running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        
        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "cancelled_tasks": 0,
        }
    
    async def start(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("调度器已在运行")
            return
        
        self.is_running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("任务调度器已启动")
    
    async def stop(self):
        """停止调度器"""
        self.is_running = False
        
        # 取消所有运行中的任务
        for task_id, task in self.running_tasks.items():
            task.cancel()
            logger.info(f"已取消任务: {task_id}")
        
        # 等待调度任务完成
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("任务调度器已停止")
    
    def add_task(
        self,
        name: str,
        target: Callable,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        task_type: TaskType = TaskType.ONE_TIME,
        scheduled_time: Optional[datetime] = None,
        interval: Optional[int] = None,
        max_retries: int = 3,
        retry_interval: int = 60,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """添加任务"""
        task_id = f"task-{uuid4().hex[:8]}"
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            task_type=task_type,
            target=target,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            scheduled_time=scheduled_time,
            interval=interval,
            max_retries=max_retries,
            retry_interval=retry_interval,
            tags=tags or [],
            metadata=metadata or {},
        )
        
        self.tasks[task_id] = task
        self.stats["total_tasks"] += 1
        
        # 加入队列
        heapq.heappush(self.task_queue, task)
        logger.info(f"任务已添加: {name} (ID: {task_id}, 优先级: {priority.name})")
        
        return task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        # 如果任务正在运行，取消它
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            task.status = TaskStatus.CANCELLED
            self.stats["cancelled_tasks"] += 1
            logger.info(f"任务已取消: {task_id}")
            return True
        
        # 如果任务在队列中，标记为取消
        if task.status in [TaskStatus.PENDING, TaskStatus.QUEUED]:
            task.status = TaskStatus.CANCELLED
            self.stats["cancelled_tasks"] += 1
            logger.info(f"任务已取消: {task_id}")
            return True
        
        return False
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """获取任务详情"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(
        self,
        status: Optional[TaskStatus] = None,
        tag: Optional[str] = None,
        limit: int = 100,
    ) -> List[ScheduledTask]:
        """获取任务列表"""
        tasks = list(self.tasks.values())
        
        # 过滤
        if status:
            tasks = [t for t in tasks if t.status == status]
        if tag:
            tasks = [t for t in tasks if tag in t.tags]
        
        # 排序（按创建时间降序）
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return tasks[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "running_tasks": len(self.running_tasks),
            "queued_tasks": len(self.task_queue),
            "total_tasks_stored": len(self.tasks),
        }
    
    async def _scheduler_loop(self):
        """调度器主循环"""
        while self.is_running:
            try:
                # 1. 检查定时任务
                await self._check_scheduled_tasks()
                
                # 2. 执行队列中的任务
                await self._process_queue()
                
                # 3. 检查周期性任务
                await self._check_recurring_tasks()
                
                # 短暂休眠
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"调度器循环异常: {e}", exc_info=True)
                await asyncio.sleep(5)
    
    async def _check_scheduled_tasks(self):
        """检查定时任务"""
        now = datetime.now()
        
        for task in list(self.tasks.values()):
            if (
                task.task_type == TaskType.SCHEDULED
                and task.status == TaskStatus.PENDING
                and task.scheduled_time
                and task.scheduled_time <= now
            ):
                # 到达执行时间，加入队列
                task.status = TaskStatus.QUEUED
                heapq.heappush(self.task_queue, task)
                logger.info(f"定时任务已入队: {task.name}")
    
    async def _process_queue(self):
        """处理任务队列"""
        while (
            self.task_queue
            and len(self.running_tasks) < self.max_concurrent_tasks
        ):
            # 弹出最高优先级任务
            task = heapq.heappop(self.task_queue)
            
            # 跳过已取消的任务
            if task.status == TaskStatus.CANCELLED:
                continue
            
            # 跳过已完成的任务
            if task.status == TaskStatus.COMPLETED:
                continue
            
            # 启动任务
            asyncio.create_task(self._execute_task(task))
    
    async def _execute_task(self, task: ScheduledTask):
        """执行任务"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        logger.info(f"开始执行任务: {task.name}")
        
        try:
            # 执行目标函数
            if asyncio.iscoroutinefunction(task.target):
                result = await task.target(*task.args, **task.kwargs)
            else:
                result = await asyncio.to_thread(
                    task.target, *task.args, **task.kwargs
                )
            
            # 标记完成
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now()
            self.stats["completed_tasks"] += 1
            
            logger.info(f"任务完成: {task.name}")
            
        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            self.stats["cancelled_tasks"] += 1
            logger.info(f"任务已取消: {task.name}")
            
        except Exception as e:
            logger.error(f"任务执行失败: {task.name} - {e}", exc_info=True)
            
            # 检查是否需要重试
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.RETRYING
                task.error_message = str(e)
                
                # 延迟重试
                await asyncio.sleep(task.retry_interval)
                
                # 重新加入队列
                heapq.heappush(self.task_queue, task)
                logger.info(f"任务重试 ({task.retry_count}/{task.max_retries}): {task.name}")
            else:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                task.completed_at = datetime.now()
                self.stats["failed_tasks"] += 1
                
        finally:
            # 从运行列表移除
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]
    
    async def _check_recurring_tasks(self):
        """检查周期性任务"""
        now = datetime.now()
        
        for task in list(self.tasks.values()):
            if (
                task.task_type == TaskType.RECURRING
                and task.status == TaskStatus.COMPLETED
                and task.interval
            ):
                # 检查是否到达下一次执行时间
                next_run = task.completed_at + timedelta(seconds=task.interval)
                
                if now >= next_run:
                    # 创建新的任务实例
                    new_task_id = self.add_task(
                        name=f"{task.name} (周期)",
                        target=task.target,
                        args=task.args,
                        kwargs=task.kwargs,
                        priority=task.priority,
                        task_type=TaskType.RECURRING,
                        interval=task.interval,
                        max_retries=task.max_retries,
                        tags=task.tags,
                    )
                    logger.info(f"周期任务已重新调度: {task.name} -> {new_task_id}")


# 全局调度器实例
_scheduler: Optional[TaskScheduler] = None


def get_scheduler() -> TaskScheduler:
    """获取全局调度器实例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler()
    return _scheduler
