"""
OpsPilot自研审批处理器

实现OpsPilot自己的审批逻辑
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import logging

from opspilot.approval.config import ApprovalConfig, ApprovalRule, ApprovalLevel
from opspilot.notification import (
    NotificationMessage,
    NotificationType,
    get_notification_service,
    send_approval_notification,
)

logger = logging.getLogger(__name__)


class ApprovalStatus(str, Enum):
    """审批状态"""
    PENDING = "pending"       # 待审批
    APPROVED = "approved"     # 已批准
    REJECTED = "rejected"     # 已拒绝
    TIMEOUT = "timeout"       # 超时
    CANCELLED = "cancelled"   # 已取消


@dataclass
class ApprovalRequest:
    """审批请求"""
    request_id: str
    tool_name: str
    params: Dict[str, Any]
    level: ApprovalLevel
    reason: str
    requester: str
    created_at: datetime = field(default_factory=datetime.now)
    status: ApprovalStatus = ApprovalStatus.PENDING
    approver: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class OpsPilotApprovalHandler:
    """
    OpsPilot审批处理器
    
    功能：
    - 创建审批请求
    - 查询审批状态
    - 批准/拒绝审批
    - 超时处理
    """
    
    def __init__(self, config: Optional[ApprovalConfig] = None):
        self.config = config or ApprovalConfig()
        self._pending_requests: Dict[str, ApprovalRequest] = {}
        self._request_history: List[ApprovalRequest] = []
    
    async def request_approval(
        self,
        tool_name: str,
        params: Dict[str, Any],
        requester: str,
        reason: str = "",
    ) -> ApprovalRequest:
        """
        请求审批
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            requester: 请求者
            reason: 请求原因
            
        Returns:
            审批请求对象
        """
        # 检查是否需要审批
        rule = self.config.get_rule_for_tool(tool_name)
        if not rule or not rule.require_approval:
            # 不需要审批，自动批准
            request = ApprovalRequest(
                request_id=f"auto-{datetime.now().timestamp()}",
                tool_name=tool_name,
                params=params,
                level=ApprovalLevel.LOW,
                reason=reason,
                requester=requester,
                status=ApprovalStatus.APPROVED,
                approver="system",
                approved_at=datetime.now(),
                approval_reason="自动批准（无需审批）",
            )
            logger.info(f"自动批准工具调用: {tool_name}")
            return request
        
        # 创建审批请求
        request_id = f"approval-{datetime.now().timestamp()}"
        request = ApprovalRequest(
            request_id=request_id,
            tool_name=tool_name,
            params=params,
            level=rule.level,
            reason=reason,
            requester=requester,
        )
        
        self._pending_requests[request_id] = request
        logger.info(f"创建审批请求: {request_id}, 工具: {tool_name}, 级别: {rule.level}")
        
        # 发送通知（可以集成通知系统）
        await self._send_notification(request, rule)
        
        # 检查超时自动批准
        if rule.auto_approve_after:
            asyncio.create_task(
                self._auto_approve_after_timeout(request_id, rule.auto_approve_after)
            )
        
        return request
    
    async def approve(
        self,
        request_id: str,
        approver: str,
        reason: str = "",
    ) -> bool:
        """批准审批"""
        request = self._pending_requests.get(request_id)
        if not request:
            logger.warning(f"审批请求不存在: {request_id}")
            return False
        
        if request.status != ApprovalStatus.PENDING:
            logger.warning(f"审批请求已处理: {request_id}, 状态: {request.status}")
            return False
        
        request.status = ApprovalStatus.APPROVED
        request.approver = approver
        request.approved_at = datetime.now()
        request.approval_reason = reason
        
        self._request_history.append(request)
        del self._pending_requests[request_id]
        
        logger.info(f"审批已批准: {request_id}, 审批人: {approver}")
        
        # 发送审批通过通知
        notification_service = get_notification_service()
        if notification_service and notification_service.is_configured():
            await send_approval_notification(
                notification_type=NotificationType.APPROVAL_APPROVED,
                request_id=request.request_id,
                tool_name=request.tool_name,
                requester=request.requester,
                approver=approver,
                level=request.level.value,
                reason=reason,
            )
        
        return True
    
    async def reject(
        self,
        request_id: str,
        approver: str,
        reason: str,
    ) -> bool:
        """拒绝审批"""
        request = self._pending_requests.get(request_id)
        if not request:
            logger.warning(f"审批请求不存在: {request_id}")
            return False
        
        if request.status != ApprovalStatus.PENDING:
            logger.warning(f"审批请求已处理: {request_id}, 状态: {request.status}")
            return False
        
        request.status = ApprovalStatus.REJECTED
        request.approver = approver
        request.approved_at = datetime.now()
        request.approval_reason = reason
        
        self._request_history.append(request)
        del self._pending_requests[request_id]
        
        logger.info(f"审批已拒绝: {request_id}, 审批人: {approver}, 原因: {reason}")
        
        # 发送审批拒绝通知
        notification_service = get_notification_service()
        if notification_service and notification_service.is_configured():
            await send_approval_notification(
                notification_type=NotificationType.APPROVAL_REJECTED,
                request_id=request.request_id,
                tool_name=request.tool_name,
                requester=request.requester,
                approver=approver,
                level=request.level.value,
                reason=reason,
            )
        
        return True
    
    def get_status(self, request_id: str) -> Optional[ApprovalRequest]:
        """获取审批状态"""
        # 先查待处理队列
        if request_id in self._pending_requests:
            return self._pending_requests[request_id]
        
        # 再查历史记录
        for request in self._request_history:
            if request.request_id == request_id:
                return request
        
        return None
    
    def get_pending_requests(self) -> List[ApprovalRequest]:
        """获取所有待审批请求"""
        return list(self._pending_requests.values())
    
    async def _send_notification(self, request: ApprovalRequest, rule: ApprovalRule):
        """发送审批通知"""
        opspilot_config = self.config.opspilot_config
        
        message = f"""审批请求
工具: {request.tool_name}
级别: {request.level.value}
请求人: {request.requester}
原因: {request.reason}
参数: {request.params}"""
        
        logger.info(f"审批通知:\n{message}")
        
        # 使用通知服务发送通知
        notification_service = get_notification_service()
        if notification_service and notification_service.is_configured():
            await send_approval_notification(
                notification_type=NotificationType.APPROVAL_REQUEST,
                request_id=request.request_id,
                tool_name=request.tool_name,
                requester=request.requester,
                level=request.level.value,
                reason=request.reason,
            )
    
    async def _auto_approve_after_timeout(self, request_id: str, timeout: int):
        """超时后自动批准"""
        await asyncio.sleep(timeout)
        
        request = self._pending_requests.get(request_id)
        if request and request.status == ApprovalStatus.PENDING:
            await self.approve(
                request_id,
                "system",
                f"超时自动批准（{timeout}秒）",
            )
