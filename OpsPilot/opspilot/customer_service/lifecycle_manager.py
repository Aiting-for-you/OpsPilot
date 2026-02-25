"""
工单生命周期管理

职责：管理工单状态流转、SLA监控、时效追踪
"""
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
from datetime import datetime, timedelta
import uuid


class TicketStatus(str, Enum):
    """工单状态"""
    CREATED = "created"              # 新建待处理
    CLASSIFIED = "classified"         # 已分类
    ROUTED = "routed"                # 已路由
    ASSIGNED = "assigned"            # 已分配
    PROCESSING = "processing"         # 处理中
    PENDING_REVIEW = "pending_review" # 待审核
    RESOLVED = "resolved"            # 已解决
    CLOSED = "closed"                # 已关闭
    ESCALATED = "escalated"          # 已升级
    REOPENED = "reopened"            # 已重新打开
    PENDING = "pending"              # 等待中（客户回复）


class LifecycleEvent(str, Enum):
    """生命周期事件"""
    CREATED = "created"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"
    ESCALATED = "escalated"
    SLA_WARNING = "sla_warning"
    SLA_BREACHED = "sla_breached"


class LifecycleManager:
    """
    工单生命周期管理器
    
    管理工单状态流转、时效追踪、SLA监控、事件记录
    """
    
    def __init__(self):
        # 工单生命周期数据
        self.ticket_lifecycles: Dict[str, Dict[str, Any]] = {}
        
        # 状态转换配置
        self.transitions = {
            TicketStatus.OPEN: [TicketStatus.IN_PROGRESS, TicketStatus.ESCALATED],
            TicketStatus.IN_PROGRESS: [TicketStatus.PENDING, TicketStatus.RESOLVED, TicketStatus.ESCALATED],
            TicketStatus.PENDING: [TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED, TicketStatus.ESCALATED],
            TicketStatus.RESOLVED: [TicketStatus.CLOSED, TicketStatus.REOPENED],
            TicketStatus.CLOSED: [TicketStatus.REOPENED],
            TicketStatus.REOPENED: [TicketStatus.IN_PROGRESS, TicketStatus.ESCALATED],
            TicketStatus.ESCALATED: [TicketStatus.IN_PROGRESS],
        }
        
        # SLA配置
        self.sla_config = {
            "response": {
                TicketPriority.HIGH: 15,    # 分钟
                "high": 15,
                TicketPriority.NORMAL: 60,
                "normal": 60,
                TicketPriority.LOW: 240,
                "low": 240,
            },
            "resolution": {
                TicketPriority.HIGH: 240,    # 分钟
                "high": 240,
                TicketPriority.NORMAL: 1440,  # 分钟 = 24小时
                "normal": 1440,
                TicketPriority.LOW: 4320,    # 分钟 = 72小时
                "low": 4320,
            },
        }
        
        # 事件回调
        self.event_listeners: Dict[LifecycleEvent, List[Callable]] = {}
        
        # SLA监控检查间隔（分钟）
        self.sla_check_interval = 5
    
    async def create_ticket(
        self,
        ticket_id: str,
        ticket_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """创建工单生命周期"""
        priority = ticket_data.get("priority", "normal")
        
        # 创建生命周期记录
        lifecycle = {
            "ticket_id": ticket_id,
            "current_status": TicketStatus.OPEN.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status_history": [
                {
                    "status": TicketStatus.OPEN.value,
                    "timestamp": datetime.now().isoformat(),
                    "reason": "工单创建",
                }
            ],
            "sla": {
                "response_deadline": self._calculate_sla_deadline(priority, "response"),
                "resolution_deadline": self._calculate_sla_deadline(priority, "resolution"),
                "response_met": None,
                "resolution_met": None,
            },
            "metrics": {
                "first_response_time": None,
                "resolution_time_minutes": None,
                "pending_time_minutes": 0,
            },
            "escalation_count": 0,
            "reopen_count": 0,
        }
        
        self.ticket_lifecycles[ticket_id] = lifecycle
        
        # 触发事件
        await self._trigger_event(LifecycleEvent.CREATED, ticket_id, ticket_data)
        
        return lifecycle
    
    async def transition_status(
        self,
        ticket_id: str,
        new_status: TicketStatus,
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """状态转换"""
        if ticket_id not in self.ticket_lifecycles:
            return {"success": False, "error": "工单不存在"}
        
        lifecycle = self.ticket_lifecycles[ticket_id]
        current_status = TicketStatus(lifecycle["current_status"])
        
        # 验证转换合法性
        if new_status not in self.transitions.get(current_status, []):
            return {
                "success": False,
                "error": f"不允许从 {current_status.value} 转换到 {new_status.value}",
            }
        
        # 记录转换
        old_status = current_status.value
        lifecycle["current_status"] = new_status.value
        lifecycle["updated_at"] = datetime.now().isoformat()
        
        # 记录历史
        lifecycle["status_history"].append({
            "status": new_status.value,
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "metadata": metadata or {},
        })
        
        # 处理特定状态的逻辑
        if new_status == TicketStatus.IN_PROGRESS:
            # 记录首次响应时间
            if not lifecycle["metrics"]["first_response_time"]:
                lifecycle["metrics"]["first_response_time"] = datetime.now().isoformat()
        
        elif new_status == TicketStatus.RESOLVED:
            # 计算解决时间
            created = datetime.fromisoformat(lifecycle["created_at"])
            resolved = datetime.now()
            lifecycle["metrics"]["resolution_time_minutes"] = int(
                (resolved - created).total_seconds() / 60
            )
            
            # 检查SLA
            lifecycle["sla"]["resolution_met"] = resolved <= datetime.fromisoformat(
                lifecycle["sla"]["resolution_deadline"]
            )
            
            if lifecycle["metrics"]["first_response_time"]:
                first_response = datetime.fromisoformat(lifecycle["metrics"]["first_response_time"])
                lifecycle["metrics"]["first_response_time"] = first_response.isoformat()
        
        elif new_status == TicketStatus.ESCALATED:
            lifecycle["escalation_count"] += 1
        
        elif new_status == TicketStatus.REOPENED:
            lifecycle["reopen_count"] += 1
        
        # 触发事件
        await self._trigger_event(
            LifecycleEvent(new_status.value),
            ticket_id,
            {"old_status": old_status, "new_status": new_status.value, "reason": reason}
        )
        
        return {
            "success": True,
            "old_status": old_status,
            "new_status": new_status.value,
        }
    
    def get_lifecycle(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """获取生命周期"""
        return self.ticket_lifecycles.get(ticket_id)
    
    def get_sla_status(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """获取SLA状态"""
        if ticket_id not in self.ticket_lifecycles:
            return None
        
        lifecycle = self.ticket_lifecycles[ticket_id]
        now = datetime.now()
        
        response_deadline = datetime.fromisoformat(lifecycle["sla"]["response_deadline"])
        resolution_deadline = datetime.fromisoformat(lifecycle["sla"]["resolution_deadline"])
        
        # 计算剩余时间
        response_remaining = (response_deadline - now).total_seconds() / 60
        resolution_remaining = (resolution_deadline - now).total_seconds() / 60
        
        return {
            "ticket_id": ticket_id,
            "status": lifecycle["current_status"],
            "response_deadline": lifecycle["sla"]["response_deadline"],
            "resolution_deadline": lifecycle["sla"]["resolution_deadline"],
            "response_remaining_minutes": max(0, int(response_remaining)),
            "resolution_remaining_minutes": max(0, int(resolution_remaining)),
            "response_warning": response_remaining <= 30 and response_remaining > 0,
            "resolution_warning": resolution_remaining <= 60 and resolution_remaining > 0,
            "response_breached": response_remaining < 0,
            "resolution_breached": resolution_remaining < 0,
            "response_met": lifecycle["sla"]["response_met"],
            "resolution_met": lifecycle["sla"]["resolution_met"],
        }
    
    def check_sla_warnings(self) -> List[Dict[str, Any]]:
        """检查SLA警告"""
        warnings = []
        now = datetime.now()
        
        for ticket_id, lifecycle in self.ticket_lifecycles.items():
            if lifecycle["current_status"] in ["resolved", "closed"]:
                continue
            
            response_deadline = datetime.fromisoformat(lifecycle["sla"]["response_deadline"])
            resolution_deadline = datetime.fromisoformat(lifecycle["sla"]["resolution_deadline"])
            
            response_remaining = (response_deadline - now).total_seconds() / 60
            resolution_remaining = (resolution_deadline - now).total_seconds() / 60
            
            # 响应时间警告
            if 0 < response_remaining <= 30:
                warnings.append({
                    "ticket_id": ticket_id,
                    "type": "response_warning",
                    "remaining_minutes": int(response_remaining),
                    "deadline": lifecycle["sla"]["response_deadline"],
                })
            
            # 解决时间警告
            if 0 < resolution_remaining <= 60:
                warnings.append({
                    "ticket_id": ticket_id,
                    "type": "resolution_warning",
                    "remaining_minutes": int(resolution_remaining),
                    "deadline": lifecycle["sla"]["resolution_deadline"],
                })
            
            # SLA违规
            if response_remaining < 0 and lifecycle["sla"]["response_met"] is None:
                warnings.append({
                    "ticket_id": ticket_id,
                    "type": "response_breached",
                    "breach_minutes": int(-response_remaining),
                    "deadline": lifecycle["sla"]["response_deadline"],
                })
                lifecycle["sla"]["response_met"] = False
            
            if resolution_remaining < 0 and lifecycle["sla"]["resolution_met"] is None:
                warnings.append({
                    "ticket_id": ticket_id,
                    "type": "resolution_breached",
                    "breach_minutes": int(-resolution_remaining),
                    "deadline": lifecycle["sla"]["resolution_deadline"],
                })
                lifecycle["sla"]["resolution_met"] = False
        
        return warnings
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计数据"""
        total = len(self.ticket_lifecycles)
        
        status_counts = {}
        sla_breaches = {"response": 0, "resolution": 0}
        total_response_time = 0
        total_resolution_time = 0
        resolved_count = 0
        
        for lifecycle in self.ticket_lifecycles.values():
            status = lifecycle["current_status"]
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if lifecycle["sla"]["response_met"] is False:
                sla_breaches["response"] += 1
            
            if lifecycle["sla"]["resolution_met"] is False:
                sla_breaches["resolution"] += 1
            
            if lifecycle["metrics"]["first_response_time"]:
                resolved_count += 1
            
            if lifecycle["metrics"]["resolution_time_minutes"]:
                total_resolution_time += lifecycle["metrics"]["resolution_time_minutes"]
        
        avg_resolution_time = (
            total_resolution_time / resolved_count if resolved_count > 0 else 0
        )
        
        return {
            "total_tickets": total,
            "by_status": status_counts,
            "sla_breaches": sla_breaches,
            "avg_resolution_time_minutes": int(avg_resolution_time),
            "resolution_rate": status_counts.get("resolved", 0) / total if total > 0 else 0,
        }
    
    def register_listener(self, event: LifecycleEvent, callback: Callable):
        """注册事件监听器"""
        if event not in self.event_listeners:
            self.event_listeners[event] = []
        self.event_listeners[event].append(callback)
    
    async def _trigger_event(self, event: LifecycleEvent, ticket_id: str, data: Dict[str, Any]):
        """触发事件"""
        if event in self.event_listeners:
            for callback in self.event_listeners[event]:
                try:
                    await callback(ticket_id, data)
                except Exception as e:
                    print(f"事件回调错误: {e}")
    
    def _calculate_sla_deadline(self, priority: str, sla_type: str) -> str:
        """计算SLA截止时间"""
        minutes = self.sla_config[sla_type].get(priority, 60)
        deadline = datetime.now() + timedelta(minutes=minutes)
        return deadline.isoformat()


# 为了避免循环导入，在这里定义
class TicketPriority(str, Enum):
    """工单优先级"""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


# 全局生命周期管理器
_lifecycle_manager: Optional[LifecycleManager] = None


def get_lifecycle_manager() -> LifecycleManager:
    """获取生命周期管理器实例"""
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = LifecycleManager()
    return _lifecycle_manager
