"""
认证授权模块

职责：
- 用户认证（JWT）
- 角色权限控制（RBAC）
- 敏感操作管理
- 审批流程管理
"""

from opspilot.auth.rbac import (
    Role,
    Permission,
    UserRole,
    RolePermission,
    RBACManager,
    require_permission,
    require_role,
    get_rbac_manager,
)

__all__ = [
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "RBACManager",
    "require_permission",
    "require_role",
    "get_rbac_manager",
]
