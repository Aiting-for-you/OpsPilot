"""
角色权限控制（RBAC）模块

实现基于角色的访问控制，支持：
- 角色权限矩阵
- 金额上限校验
- 敏感操作二次确认
- 数据访问范围控制
"""

from enum import Enum
from typing import Optional, List, Dict, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
import functools
import asyncio

from opspilot.utils.exceptions import opspilotError


class Permission(str, Enum):
    """权限类型"""
    # 订单权限
    ORDER_CREATE = "order:create"
    ORDER_VIEW = "order:view"
    ORDER_APPROVE = "order:approve"
    ORDER_CANCEL = "order:cancel"
    
    # 供应商权限
    SUPPLIER_VIEW = "supplier:view"
    SUPPLIER_EDIT = "supplier:edit"
    
    # 库存权限
    INVENTORY_VIEW = "inventory:view"
    INVENTORY_EDIT = "inventory:edit"
    
    # 财务权限
    FINANCE_VIEW = "finance:view"
    FINANCE_APPROVE = "finance:approve"
    BUDGET_QUERY = "budget:query"
    
    # 合同权限
    CONTRACT_VIEW = "contract:view"
    CONTRACT_SIGN = "contract:sign"
    CONTRACT_AUDIT = "contract:audit"
    
    # 支付权限
    PAYMENT_CREATE = "payment:create"
    PAYMENT_APPROVE = "payment:approve"
    
    # 系统权限
    SYSTEM_ADMIN = "system:admin"
    USER_MANAGE = "user:manage"
    ALL_DATA_ACCESS = "data:all"


class Role(str, Enum):
    """角色类型"""
    JUNIOR_BUYER = "junior_buyer"      # 初级采购员
    SENIOR_BUYER = "senior_buyer"      # 高级采购员
    FINANCE_AUDITOR = "finance_auditor" # 财务审核员
    SYSTEM_ADMIN = "system_admin"       # 系统管理员


@dataclass
class RolePermission:
    """角色权限配置"""
    role: Role
    name: str
    description: str
    
    # 金额上限（元）
    amount_limit: float = 0.0  # 0表示无限制
    
    # 权限列表
    permissions: Set[Permission] = field(default_factory=set)
    
    # 敏感操作列表（需要二次确认）
    sensitive_actions: Set[str] = field(default_factory=set)
    
    # 审批权限
    can_approve_amount: float = 0.0  # 可审批的金额上限
    
    # 数据访问范围
    data_scope: str = "self"  # self / department / all
    
    @classmethod
    def get_default_permissions(cls) -> Dict[Role, 'RolePermission']:
        """获取默认角色权限配置"""
        return {
            Role.JUNIOR_BUYER: cls(
                role=Role.JUNIOR_BUYER,
                name="初级采购员",
                description="基础采购权限，金额受限",
                amount_limit=100_000,  # 10万元
                permissions={
                    Permission.ORDER_CREATE,
                    Permission.ORDER_VIEW,
                    Permission.SUPPLIER_VIEW,
                    Permission.INVENTORY_VIEW,
                },
                sensitive_actions=set(),
                can_approve_amount=0,
                data_scope="self",
            ),
            
            Role.SENIOR_BUYER: cls(
                role=Role.SENIOR_BUYER,
                name="高级采购员",
                description="高级采购权限，可查看供应商信息",
                amount_limit=500_000,  # 50万元
                permissions={
                    Permission.ORDER_CREATE,
                    Permission.ORDER_VIEW,
                    Permission.SUPPLIER_VIEW,
                    Permission.SUPPLIER_EDIT,
                    Permission.INVENTORY_VIEW,
                    Permission.INVENTORY_EDIT,
                },
                sensitive_actions={"supplier_edit"},
                can_approve_amount=0,
                data_scope="department",
            ),
            
            Role.FINANCE_AUDITOR: cls(
                role=Role.FINANCE_AUDITOR,
                name="财务审核员",
                description="财务审核权限，可审批订单",
                amount_limit=0,  # 无限制
                permissions={
                    Permission.ORDER_VIEW,
                    Permission.FINANCE_VIEW,
                    Permission.FINANCE_APPROVE,
                    Permission.BUDGET_QUERY,
                    Permission.CONTRACT_VIEW,
                    Permission.CONTRACT_AUDIT,
                    Permission.PAYMENT_APPROVE,
                },
                sensitive_actions={"payment_approve", "contract_audit"},
                can_approve_amount=1_000_000,  # 100万元
                data_scope="department",
            ),
            
            Role.SYSTEM_ADMIN: cls(
                role=Role.SYSTEM_ADMIN,
                name="系统管理员",
                description="系统最高权限",
                amount_limit=0,  # 无限制
                permissions=set(Permission),  # 所有权限
                sensitive_actions={"system_admin", "user_manage"},
                can_approve_amount=0,  # 无限制
                data_scope="all",
            ),
        }


@dataclass
class UserRole:
    """用户角色关联"""
    user_id: str
    role: Role
    department: Optional[str] = None
    assigned_at: datetime = field(default_factory=datetime.now)
    assigned_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "role": self.role.value,
            "department": self.department,
            "assigned_at": self.assigned_at.isoformat(),
            "assigned_by": self.assigned_by,
        }


class PermissionDeniedError(opspilotError):
    """权限拒绝错误"""
    pass


class AmountLimitExceededError(opspilotError):
    """金额超限错误"""
    pass


class SensitiveActionError(opspilotError):
    """敏感操作错误"""
    pass


class RBACManager:
    """
    RBAC 管理器
    
    职责：
    - 管理用户角色
    - 校验权限
    - 校验金额上限
    - 管理敏感操作
    """
    
    def __init__(self):
        """初始化 RBAC 管理器"""
        self._user_roles: Dict[str, UserRole] = {}
        self._role_permissions = RolePermission.get_default_permissions()
    
    def assign_role(
        self,
        user_id: str,
        role: Role,
        department: Optional[str] = None,
        assigned_by: Optional[str] = None,
    ) -> UserRole:
        """
        为用户分配角色
        
        Args:
            user_id: 用户ID
            role: 角色类型
            department: 部门
            assigned_by: 分配者ID
            
        Returns:
            UserRole: 用户角色关联
        """
        user_role = UserRole(
            user_id=user_id,
            role=role,
            department=department,
            assigned_by=assigned_by,
        )
        self._user_roles[user_id] = user_role
        return user_role
    
    def get_user_role(self, user_id: str) -> Optional[UserRole]:
        """获取用户角色"""
        return self._user_roles.get(user_id)
    
    def get_role_permission(self, role: Role) -> RolePermission:
        """获取角色权限配置"""
        return self._role_permissions[role]
    
    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """
        检查用户是否有指定权限
        
        Args:
            user_id: 用户ID
            permission: 权限类型
            
        Returns:
            bool: 是否有权限
        """
        user_role = self.get_user_role(user_id)
        if not user_role:
            return False
        
        role_perm = self.get_role_permission(user_role.role)
        return permission in role_perm.permissions
    
    def check_permission(self, user_id: str, permission: Permission) -> None:
        """
        校验权限，无权限抛出异常
        
        Args:
            user_id: 用户ID
            permission: 权限类型
            
        Raises:
            PermissionDeniedError: 权限不足
        """
        if not self.has_permission(user_id, permission):
            user_role = self.get_user_role(user_id)
            role_name = user_role.role.value if user_role else "无角色"
            raise PermissionDeniedError(
                f"用户 {user_id}（角色：{role_name}）无权限执行 {permission.value}"
            )
    
    def check_amount_limit(self, user_id: str, amount: float) -> None:
        """
        校验金额上限
        
        Args:
            user_id: 用户ID
            amount: 金额
            
        Raises:
            AmountLimitExceededError: 金额超限
        """
        user_role = self.get_user_role(user_id)
        if not user_role:
            raise PermissionDeniedError(f"用户 {user_id} 无角色")
        
        role_perm = self.get_role_permission(user_role.role)
        
        # 0 表示无限制
        if role_perm.amount_limit > 0 and amount > role_perm.amount_limit:
            raise AmountLimitExceededError(
                f"订单金额 {amount} 超过角色 {user_role.role.value} 上限 {role_perm.amount_limit}"
            )
    
    def is_sensitive_action(self, user_id: str, action: str) -> bool:
        """
        检查是否为敏感操作
        
        Args:
            user_id: 用户ID
            action: 操作名称
            
        Returns:
            bool: 是否为敏感操作
        """
        user_role = self.get_user_role(user_id)
        if not user_role:
            return False
        
        role_perm = self.get_role_permission(user_role.role)
        return action in role_perm.sensitive_actions
    
    def can_approve_amount(self, user_id: str, amount: float) -> bool:
        """
        检查是否可审批指定金额
        
        Args:
            user_id: 用户ID
            amount: 金额
            
        Returns:
            bool: 是否可审批
        """
        user_role = self.get_user_role(user_id)
        if not user_role:
            return False
        
        role_perm = self.get_role_permission(user_role.role)
        
        # 0 表示无限制
        if role_perm.can_approve_amount == 0:
            return True
        
        return amount <= role_perm.can_approve_amount
    
    def get_data_scope(self, user_id: str) -> str:
        """
        获取数据访问范围
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: 数据范围（self/department/all）
        """
        user_role = self.get_user_role(user_id)
        if not user_role:
            return "self"
        
        role_perm = self.get_role_permission(user_role.role)
        return role_perm.data_scope
    
    def validate_data_access(
        self,
        user_id: str,
        target_user_id: str,
        target_department: Optional[str] = None,
    ) -> bool:
        """
        校验数据访问权限
        
        Args:
            user_id: 当前用户ID
            target_user_id: 目标数据用户ID
            target_department: 目标数据部门
            
        Returns:
            bool: 是否有权限访问
        """
        user_role = self.get_user_role(user_id)
        if not user_role:
            return False
        
        role_perm = self.get_role_permission(user_role.role)
        
        # 全部数据权限
        if role_perm.data_scope == "all":
            return True
        
        # 部门数据权限
        if role_perm.data_scope == "department":
            return user_role.department == target_department
        
        # 仅自己数据
        return user_id == target_user_id


# 全局 RBAC 管理器实例
_rbac_manager: Optional[RBACManager] = None


def get_rbac_manager() -> RBACManager:
    """获取全局 RBAC 管理器实例"""
    global _rbac_manager
    if _rbac_manager is None:
        _rbac_manager = RBACManager()
    return _rbac_manager


def require_permission(permission: Permission):
    """
    权限装饰器
    
    使用示例：
        @require_permission(Permission.ORDER_CREATE)
        async def create_order(user_id: str, ...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 从参数中获取 user_id
            user_id = kwargs.get("user_id") or (args[0] if args else None)
            if not user_id:
                raise ValueError("缺少 user_id 参数")
            
            # 校验权限
            rbac = get_rbac_manager()
            rbac.check_permission(user_id, permission)
            
            # 执行原函数
            return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 从参数中获取 user_id
            user_id = kwargs.get("user_id") or (args[0] if args else None)
            if not user_id:
                raise ValueError("缺少 user_id 参数")
            
            # 校验权限
            rbac = get_rbac_manager()
            rbac.check_permission(user_id, permission)
            
            # 执行原函数
            return func(*args, **kwargs)
        
        # 根据函数类型返回不同的 wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def require_role(role: Role):
    """
    角色装饰器
    
    使用示例：
        @require_role(Role.SYSTEM_ADMIN)
        async def system_config(user_id: str, ...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 从参数中获取 user_id
            user_id = kwargs.get("user_id") or (args[0] if args else None)
            if not user_id:
                raise ValueError("缺少 user_id 参数")
            
            # 校验角色
            rbac = get_rbac_manager()
            user_role = rbac.get_user_role(user_id)
            
            if not user_role or user_role.role != role:
                raise PermissionDeniedError(
                    f"用户 {user_id} 需要角色 {role.value}"
                )
            
            # 执行原函数
            return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 从参数中获取 user_id
            user_id = kwargs.get("user_id") or (args[0] if args else None)
            if not user_id:
                raise ValueError("缺少 user_id 参数")
            
            # 校验角色
            rbac = get_rbac_manager()
            user_role = rbac.get_user_role(user_id)
            
            if not user_role or user_role.role != role:
                raise PermissionDeniedError(
                    f"用户 {user_id} 需要角色 {role.value}"
                )
            
            # 执行原函数
            return func(*args, **kwargs)
        
        # 根据函数类型返回不同的 wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
