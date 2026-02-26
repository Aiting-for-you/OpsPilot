"""
审批工作流模块

实现敏感操作的人工审批流程：
- 自动冻结敏感操作
- 审批请求创建与管理
- 多渠道通知
- 审批结果处理
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from opspilot.auth.rbac import (
    RBACManager,
    get_rbac_manager,
    PermissionDeniedError,
    AmountLimitExceededError,
)


class ApprovalStatus(str, Enum):
    """审批状态"""
    PENDING = "pending"          # 待审批
    APPROVED = "approved"        # 已通过
    REJECTED = "rejected"        # 已拒绝
    EXPIRED = "expired"          # 已过期
    CANCELLED = "cancelled"      # 已取消


class ApprovalType(str, Enum):
    """审批类型"""
    AMOUNT_EXCEEDED = "amount_exceeded"    # 金额超限
    SENSITIVE_ACTION = "sensitive_action"  # 敏感操作
    PAYMENT = "payment"                    # 支付审批
    CONTRACT = "contract"                  # 合同签署
    ORDER_CANCEL = "order_cancel"          # 订单取消


@dataclass
class ApprovalRequest:
    """审批请求"""
    request_id: str
    approval_type: ApprovalType
    user_id: str
    user_role: str
    
    # 审批内容
    title: str
    description: str
    data: Dict[str, Any]  # 审批相关数据
    
    # 审批状态
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    # 审批结果
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_comment: Optional[str] = None
    
    # 通知信息
    notified_users: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "approval_type": self.approval_type.value,
            "user_id": self.user_id,
            "user_role": self.user_role,
            "title": self.title,
            "description": self.description,
            "data": self.data,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approval_comment": self.approval_comment,
            "notified_users": self.notified_users,
        }


@dataclass
class ApprovalRule:
    """审批规则"""
    approval_type: ApprovalType
    name: str
    description: str
    
    # 触发条件
    min_amount: float = 0.0  # 最小金额触发
    max_amount: float = float('inf')  # 最大金额
    
    # 审批人
    required_roles: List[str] = field(default_factory=list)  # 需要的角色
    required_permissions: List[str] = field(default_factory=list)  # 需要的权限
    
    # 超时设置
    timeout_hours: int = 24  # 审批超时时间（小时）
    
    # 自动处理
    auto_approve: bool = False  # 是否自动审批
    auto_reject: bool = False   # 是否自动拒绝


class ApprovalWorkflowError(Exception):
    """审批工作流错误"""
    pass


class ApprovalWorkflow:
    """
    审批工作流管理器
    
    职责：
    - 创建审批请求
    - 管理审批流程
    - 处理审批结果
    - 发送通知
    """
    
    def __init__(self, rbac_manager: Optional[RBACManager] = None):
        """
        初始化审批工作流
        
        Args:
            rbac_manager: RBAC 管理器
        """
        self._rbac = rbac_manager or get_rbac_manager()
        self._requests: Dict[str, ApprovalRequest] = {}
        self._rules = self._init_default_rules()
        self._notifier = None  # 将在后续集成通知系统
    
    def _init_default_rules(self) -> Dict[ApprovalType, ApprovalRule]:
        """初始化默认审批规则"""
        return {
            ApprovalType.AMOUNT_EXCEEDED: ApprovalRule(
                approval_type=ApprovalType.AMOUNT_EXCEEDED,
                name="超额订单审批",
                description="采购金额超过角色上限的订单",
                min_amount=100_000,
                required_roles=["finance_auditor", "system_admin"],
                required_permissions=["finance:approve"],
                timeout_hours=24,
            ),
            
            ApprovalType.PAYMENT: ApprovalRule(
                approval_type=ApprovalType.PAYMENT,
                name="支付审批",
                description="支付操作审批",
                required_roles=["finance_auditor", "system_admin"],
                required_permissions=["payment:approve"],
                timeout_hours=12,
            ),
            
            ApprovalType.CONTRACT: ApprovalRule(
                approval_type=ApprovalType.CONTRACT,
                name="合同审批",
                description="合同签署审批",
                required_roles=["finance_auditor", "system_admin"],
                required_permissions=["contract:audit"],
                timeout_hours=48,
            ),
            
            ApprovalType.SENSITIVE_ACTION: ApprovalRule(
                approval_type=ApprovalType.SENSITIVE_ACTION,
                name="敏感操作审批",
                description="敏感操作审批",
                required_roles=["senior_buyer", "finance_auditor", "system_admin"],
                timeout_hours=6,
            ),
        }
    
    def set_notifier(self, notifier: Any):
        """设置通知器"""
        self._notifier = notifier
    
    def create_approval_request(
        self,
        user_id: str,
        approval_type: ApprovalType,
        title: str,
        description: str,
        data: Dict[str, Any],
        expires_in_hours: Optional[int] = None,
    ) -> ApprovalRequest:
        """
        创建审批请求
        
        Args:
            user_id: 用户ID
            approval_type: 审批类型
            title: 标题
            description: 描述
            data: 审批数据
            expires_in_hours: 过期时间（小时）
            
        Returns:
            ApprovalRequest: 审批请求
        """
        # 获取用户角色
        user_role = self._rbac.get_user_role(user_id)
        if not user_role:
            raise ApprovalWorkflowError(f"用户 {user_id} 无角色")
        
        # 获取审批规则
        rule = self._rules.get(approval_type)
        if not rule:
            raise ApprovalWorkflowError(f"未找到审批类型 {approval_type.value} 的规则")
        
        # 检查自动处理
        if rule.auto_approve:
            request = ApprovalRequest(
                request_id=str(uuid.uuid4()),
                approval_type=approval_type,
                user_id=user_id,
                user_role=user_role.role.value,
                title=title,
                description=description,
                data=data,
                status=ApprovalStatus.APPROVED,
                approved_by="auto",
                approved_at=datetime.now(),
                approval_comment="自动审批通过",
            )
            self._requests[request.request_id] = request
            return request
        
        if rule.auto_reject:
            request = ApprovalRequest(
                request_id=str(uuid.uuid4()),
                approval_type=approval_type,
                user_id=user_id,
                user_role=user_role.role.value,
                title=title,
                description=description,
                data=data,
                status=ApprovalStatus.REJECTED,
                approved_by="auto",
                approved_at=datetime.now(),
                approval_comment="自动拒绝",
            )
            self._requests[request.request_id] = request
            return request
        
        # 计算过期时间
        expires_at = None
        timeout = expires_in_hours or rule.timeout_hours
        if timeout > 0:
            from datetime import timedelta
            expires_at = datetime.now() + timedelta(hours=timeout)
        
        # 创建审批请求
        request = ApprovalRequest(
            request_id=str(uuid.uuid4()),
            approval_type=approval_type,
            user_id=user_id,
            user_role=user_role.role.value,
            title=title,
            description=description,
            data=data,
            expires_at=expires_at,
        )
        
        self._requests[request.request_id] = request
        
        # 查找审批人
        approvers = self._find_approvers(rule)
        request.notified_users = approvers
        
        # 发送通知
        if self._notifier and approvers:
            self._send_notification(request, approvers)
        
        return request
    
    def _find_approvers(self, rule: ApprovalRule) -> List[str]:
        """
        查找符合条件的审批人
        
        Args:
            rule: 审批规则
            
        Returns:
            List[str]: 审批人ID列表
        """
        approvers = []
        
        # 遍历所有用户，查找符合条件者
        # 实际实现中应该从数据库查询
        # 这里简化为从已注册用户中查找
        for user_id, user_role in self._rbac._user_roles.items():
            # 检查角色
            if user_role.role.value in rule.required_roles:
                approvers.append(user_id)
                continue
            
            # 检查权限
            role_perm = self._rbac.get_role_permission(user_role.role)
            for perm in role_perm.permissions:
                if perm.value in rule.required_permissions:
                    approvers.append(user_id)
                    break
        
        return approvers
    
    def _send_notification(
        self,
        request: ApprovalRequest,
        approvers: List[str],
    ):
        """
        发送审批通知
        
        Args:
            request: 审批请求
            approvers: 审批人列表
        """
        if not self._notifier:
            return
        
        # 构造通知内容
        notification_data = {
            "type": "approval_request",
            "request_id": request.request_id,
            "title": request.title,
            "description": request.description,
            "user_id": request.user_id,
            "created_at": request.created_at.isoformat(),
        }
        
        # 发送通知（具体实现依赖通知系统）
        # self._notifier.send(...)
    
    def get_approval_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """获取审批请求"""
        return self._requests.get(request_id)
    
    def approve(
        self,
        request_id: str,
        approver_id: str,
        comment: Optional[str] = None,
    ) -> ApprovalRequest:
        """
        审批通过
        
        Args:
            request_id: 审批请求ID
            approver_id: 审批人ID
            comment: 审批意见
            
        Returns:
            ApprovalRequest: 审批请求
        """
        request = self.get_approval_request(request_id)
        if not request:
            raise ApprovalWorkflowError(f"审批请求 {request_id} 不存在")
        
        if request.status != ApprovalStatus.PENDING:
            raise ApprovalWorkflowError(
                f"审批请求状态为 {request.status.value}，无法审批"
            )
        
        # 检查是否过期
        if request.expires_at and datetime.now() > request.expires_at:
            request.status = ApprovalStatus.EXPIRED
            raise ApprovalWorkflowError(f"审批请求已过期")
        
        # 更新审批状态
        request.status = ApprovalStatus.APPROVED
        request.approved_by = approver_id
        request.approved_at = datetime.now()
        request.approval_comment = comment
        
        return request
    
    def reject(
        self,
        request_id: str,
        approver_id: str,
        comment: Optional[str] = None,
    ) -> ApprovalRequest:
        """
        审批拒绝
        
        Args:
            request_id: 审批请求ID
            approver_id: 审批人ID
            comment: 拒绝原因
            
        Returns:
            ApprovalRequest: 审批请求
        """
        request = self.get_approval_request(request_id)
        if not request:
            raise ApprovalWorkflowError(f"审批请求 {request_id} 不存在")
        
        if request.status != ApprovalStatus.PENDING:
            raise ApprovalWorkflowError(
                f"审批请求状态为 {request.status.value}，无法审批"
            )
        
        # 检查是否过期
        if request.expires_at and datetime.now() > request.expires_at:
            request.status = ApprovalStatus.EXPIRED
            raise ApprovalWorkflowError(f"审批请求已过期")
        
        # 更新审批状态
        request.status = ApprovalStatus.REJECTED
        request.approved_by = approver_id
        request.approved_at = datetime.now()
        request.approval_comment = comment
        
        return request
    
    def cancel(self, request_id: str) -> ApprovalRequest:
        """
        取消审批请求
        
        Args:
            request_id: 审批请求ID
            
        Returns:
            ApprovalRequest: 审批请求
        """
        request = self.get_approval_request(request_id)
        if not request:
            raise ApprovalWorkflowError(f"审批请求 {request_id} 不存在")
        
        request.status = ApprovalStatus.CANCELLED
        return request
    
    def check_expired(self) -> List[ApprovalRequest]:
        """
        检查过期的审批请求
        
        Returns:
            List[ApprovalRequest]: 过期的审批请求列表
        """
        expired = []
        now = datetime.now()
        
        for request in self._requests.values():
            if (
                request.status == ApprovalStatus.PENDING
                and request.expires_at
                and now > request.expires_at
            ):
                request.status = ApprovalStatus.EXPIRED
                expired.append(request)
        
        return expired
    
    def get_pending_requests(self, user_id: str) -> List[ApprovalRequest]:
        """
        获取用户待审批的请求
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[ApprovalRequest]: 待审批请求列表
        """
        return [
            req for req in self._requests.values()
            if req.status == ApprovalStatus.PENDING and user_id in req.notified_users
        ]
    
    def get_user_requests(self, user_id: str) -> List[ApprovalRequest]:
        """
        获取用户发起的审批请求
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[ApprovalRequest]: 审批请求列表
        """
        return [
            req for req in self._requests.values()
            if req.user_id == user_id
        ]


# 全局审批工作流实例
_approval_workflow: Optional[ApprovalWorkflow] = None


def get_approval_workflow() -> ApprovalWorkflow:
    """获取全局审批工作流实例"""
    global _approval_workflow
    if _approval_workflow is None:
        _approval_workflow = ApprovalWorkflow()
    return _approval_workflow
