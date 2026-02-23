"""
工单工作队列

职责：管理工单队列、优先级调度、SLA监控
"""
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime, timedelta
import heapq
import uuid


class QueueType(str, Enum):
    """队列类型"""
    URGENT = "urgent"     # 紧急队列
    NORMAL = "normal"    # 普通队列
    LOW = "low"          # 低优先级队列
    ESCALATED = "escalated"  # 升级队列


class TicketQueue:
    """
    工单队列管理
    
    支持优先级队列、多队列管理、自动调度
    """
    
    def __init__(self):
        # 队列存储
        self.queues: Dict[QueueType, List[Dict[str, Any]]] = {
            QueueType.URGENT: [],
            QueueType.NORMAL: [],
            QueueType.LOW: [],
            QueueType.ESCALATED: [],
        }
        
        # 队列配置
        self.queue_config = {
            QueueType.URGENT: {
                "max_size": 100,
                "timeout_minutes": 30,
                "auto_escalate": True,
            },
            QueueType.NORMAL: {
                "max_size": 500,
                "timeout_minutes": 120,
                "auto_escalate": True,
            },
            QueueType.LOW: {
                "max_size": 1000,
                "timeout_minutes": 480,
                "auto_escalate": False,
            },
            QueueType.ESCALATED: {
                "max_size": 200,
                "timeout_minutes": 60,
                "auto_escalate": True,
            },
        }
        
        # 已入队工单跟踪
        self.enqueued_tickets: Dict[str, Dict[str, Any]] = {}
    
    def enqueue(
        self,
        ticket_data: Dict[str, Any],
        priority: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        入队
        
        Args:
            ticket_data: 工单数据
            priority: 优先级 (high/normal/low)
        """
        ticket_id = ticket_data.get("ticket_id", str(uuid.uuid4()))
        
        # 确定队列类型
        queue_type = self._get_queue_type(priority, ticket_data)
        
        # 检查队列容量
        if len(self.queues[queue_type]) >= self.queue_config[queue_type]["max_size"]:
            return {
                "success": False,
                "error": f"队列 {queue_type.value} 已满",
            }
        
        # 创建队列项
        queue_item = {
            "ticket_id": ticket_id,
            "ticket_data": ticket_data,
            "queue_type": queue_type.value,
            "enqueue_time": datetime.now().isoformat(),
            "priority_score": self._calculate_priority_score(priority, ticket_data),
            "sla_deadline": self._calculate_sla_deadline(queue_type),
        }
        
        # 加入队列（使用堆保持优先级顺序）
        heapq.heappush(self.queues[queue_type], queue_item)
        
        # 跟踪已入队工单
        self.enqueued_tickets[ticket_id] = {
            **queue_item,
            "status": "queued",
        }
        
        return {
            "success": True,
            "ticket_id": ticket_id,
            "queue_type": queue_type.value,
            "position": len(self.queues[queue_type]),
            "sla_deadline": queue_item["sla_deadline"],
        }
    
    def dequeue(self, queue_type: Optional[QueueType] = None) -> Optional[Dict[str, Any]]:
        """
        出队
        
        Args:
            queue_type: 指定队列类型，None表示从最高优先级队列取
        """
        if queue_type:
            if not self.queues[queue_type]:
                return None
            
            item = heapq.heappop(self.queues[queue_type])
            self._update_ticket_status(item["ticket_id"], "dequeued")
            return item
        
        # 从高优先级队列开始检查
        for qt in [QueueType.ESCALATED, QueueType.URGENT, QueueType.NORMAL, QueueType.LOW]:
            if self.queues[qt]:
                item = heapq.heappop(self.queues[qt])
                self._update_ticket_status(item["ticket_id"], "dequeued")
                return item
        
        return None
    
    def get_queue_status(self, queue_type: Optional[QueueType] = None) -> Dict[str, Any]:
        """获取队列状态"""
        if queue_type:
            return {
                "queue_type": queue_type.value,
                "size": len(self.queues[queue_type]),
                "config": self.queue_config[queue_type],
            }
        
        # 返回所有队列状态
        return {
            "queues": {
                qt.value: {
                    "size": len(self.queues[qt]),
                    "max_size": self.queue_config[qt]["max_size"],
                }
                for qt in QueueType
            },
            "total_enqueued": len(self.enqueued_tickets),
        }
    
    def get_ticket_position(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """获取工单在队列中的位置"""
        if ticket_id not in self.enqueued_tickets:
            return None
        
        queue_type = QueueType(self.enqueued_tickets[ticket_id]["queue_type"])
        
        # 查找位置
        position = 0
        for i, item in enumerate(self.queues[queue_type]):
            if item["ticket_id"] == ticket_id:
                position = i + 1
                break
        
        return {
            "ticket_id": ticket_id,
            "queue_type": queue_type.value,
            "position": position,
            "total_in_queue": len(self.queues[queue_type]),
            "enqueue_time": self.enqueued_tickets[ticket_id]["enqueue_time"],
        }
    
    def remove_ticket(self, ticket_id: str) -> bool:
        """从队列中移除工单"""
        if ticket_id not in self.enqueued_tickets:
            return False
        
        queue_type = QueueType(self.enqueued_tickets[ticket_id]["queue_type"])
        
        # 重建队列（移除指定工单）
        new_queue = [item for item in self.queues[queue_type] if item["ticket_id"] != ticket_id]
        self.queues[queue_type] = new_queue
        heapq.heapify(self.queues[queue_type])
        
        del self.enqueued_tickets[ticket_id]
        
        return True
    
    def get_pending_tickets(
        self,
        queue_type: Optional[QueueType] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """获取待处理工单列表"""
        results = []
        
        if queue_type:
            queues_to_check = [queue_type]
        else:
            queues_to_check = list(QueueType)
        
        for qt in queues_to_check:
            for item in self.queues[qt][:limit]:
                results.append({
                    "ticket_id": item["ticket_id"],
                    "queue_type": item["queue_type"],
                    "enqueue_time": item["enqueue_time"],
                    "priority_score": item["priority_score"],
                    "sla_deadline": item["sla_deadline"],
                })
        
        return results
    
    def check_sla_violations(self) -> List[Dict[str, Any]]:
        """检查SLA违规"""
        violations = []
        now = datetime.now()
        
        for ticket_id, ticket_info in self.enqueued_tickets.items():
            if ticket_info.get("status") != "queued":
                continue
            
            sla_deadline = datetime.fromisoformat(ticket_info["sla_deadline"])
            
            if now > sla_deadline:
                violations.append({
                    "ticket_id": ticket_id,
                    "queue_type": ticket_info["queue_type"],
                    "enqueue_time": ticket_info["enqueue_time"],
                    "sla_deadline": ticket_info["sla_deadline"],
                    "violation_minutes": int((now - sla_deadline).total_seconds() / 60),
                })
        
        return violations
    
    def _get_queue_type(
        self,
        priority: Optional[str],
        ticket_data: Dict[str, Any],
    ) -> QueueType:
        """确定队列类型"""
        # 检查是否升级
        if ticket_data.get("escalated"):
            return QueueType.ESCALATED
        
        # 根据优先级
        if priority == "high":
            return QueueType.URGENT
        elif priority == "low":
            return QueueType.LOW
        
        return QueueType.NORMAL
    
    def _calculate_priority_score(self, priority: Optional[str], ticket_data: Dict[str, Any]) -> float:
        """计算优先级分数"""
        base_score = 0.0
        
        if priority == "high":
            base_score = 100.0
        elif priority == "normal":
            base_score = 50.0
        elif priority == "low":
            base_score = 10.0
        
        # VIP客户加分
        if ticket_data.get("customer_tier") == "vip":
            base_score += 50.0
        
        # SLA紧急程度
        if ticket_data.get("sla_breach_minutes", 0) < 30:
            base_score += 30.0
        
        return base_score
    
    def _calculate_sla_deadline(self, queue_type: QueueType) -> str:
        """计算SLA截止时间"""
        timeout_minutes = self.queue_config[queue_type]["timeout_minutes"]
        deadline = datetime.now() + timedelta(minutes=timeout_minutes)
        return deadline.isoformat()
    
    def _update_ticket_status(self, ticket_id: str, status: str):
        """更新工单状态"""
        if ticket_id in self.enqueued_tickets:
            self.enqueued_tickets[ticket_id]["status"] = status


# 全局队列实例
_ticket_queue: Optional[TicketQueue] = None


def get_ticket_queue() -> TicketQueue:
    """获取工单队列实例"""
    global _ticket_queue
    if _ticket_queue is None:
        _ticket_queue = TicketQueue()
    return _ticket_queue
