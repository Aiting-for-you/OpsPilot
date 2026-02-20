"""
RBAC 权限控制测试

测试基于角色的访问控制功能：
- 角色权限配置
- 权限校验
- 金额上限校验
- 敏感操作检查
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from opspilot.auth.rbac import (
    Permission,
    Role,
    RolePermission,
    RBACManager,
    PermissionDeniedError,
    AmountLimitExceededError,
    require_permission,
    require_role,
    get_rbac_manager,
)


class TestPermission:
    """权限枚举测试"""
    
    def test_order_permissions(self):
        """测试订单权限"""
        assert Permission.ORDER_CREATE.value == "order:create"
        assert Permission.ORDER_VIEW.value == "order:view"
        assert Permission.ORDER_APPROVE.value == "order:approve"
        assert Permission.ORDER_CANCEL.value == "order:cancel"
    
    def test_supplier_permissions(self):
        """测试供应商权限"""
        assert Permission.SUPPLIER_VIEW.value == "supplier:view"
        assert Permission.SUPPLIER_EDIT.value == "supplier:edit"
    
    def test_inventory_permissions(self):
        """测试库存权限"""
        assert Permission.INVENTORY_VIEW.value == "inventory:view"
        assert Permission.INVENTORY_EDIT.value == "inventory:edit"
    
    def test_finance_permissions(self):
        """测试财务权限"""
        assert Permission.FINANCE_VIEW.value == "finance:view"
        assert Permission.FINANCE_APPROVE.value == "finance:approve"
        assert Permission.BUDGET_QUERY.value == "budget:query"
    
    def test_system_permissions(self):
        """测试系统权限"""
        assert Permission.SYSTEM_ADMIN.value == "system:admin"
        assert Permission.USER_MANAGE.value == "user:manage"
        assert Permission.ALL_DATA_ACCESS.value == "data:all"


class TestRole:
    """角色枚举测试"""
    
    def test_role_values(self):
        """测试角色值"""
        assert Role.JUNIOR_BUYER.value == "junior_buyer"
        assert Role.SENIOR_BUYER.value == "senior_buyer"
        assert Role.FINANCE_AUDITOR.value == "finance_auditor"
        assert Role.SYSTEM_ADMIN.value == "system_admin"


class TestRolePermission:
    """角色权限配置测试"""
    
    def test_default_permissions_junior_buyer(self):
        """测试初级采购员默认权限"""
        permissions = RolePermission.get_default_permissions()
        junior = permissions[Role.JUNIOR_BUYER]
        
        assert junior.role == Role.JUNIOR_BUYER
        assert junior.name == "初级采购员"
        assert junior.amount_limit == 100_000  # 10万
        assert Permission.ORDER_CREATE in junior.permissions
        assert Permission.ORDER_VIEW in junior.permissions
        assert Permission.ORDER_APPROVE not in junior.permissions
        assert junior.data_scope == "self"
    
    def test_default_permissions_senior_buyer(self):
        """测试高级采购员默认权限"""
        permissions = RolePermission.get_default_permissions()
        senior = permissions[Role.SENIOR_BUYER]
        
        assert senior.role == Role.SENIOR_BUYER
        assert senior.amount_limit == 500_000  # 50万
        assert Permission.SUPPLIER_EDIT in senior.sensitive_actions
        assert senior.data_scope == "department"
    
    def test_default_permissions_finance_auditor(self):
        """测试财务审核员默认权限"""
        permissions = RolePermission.get_default_permissions()
        finance = permissions[Role.FINANCE_AUDITOR]
        
        assert finance.role == Role.FINANCE_AUDITOR
        assert Permission.FINANCE_APPROVE in finance.permissions
        assert Permission.ORDER_APPROVE in finance.permissions
        assert finance.can_approve_amount == 1_000_000  # 100万
    
    def test_default_permissions_system_admin(self):
        """测试系统管理员默认权限"""
        permissions = RolePermission.get_default_permissions()
        admin = permissions[Role.SYSTEM_ADMIN]
        
        assert admin.role == Role.SYSTEM_ADMIN
        assert Permission.SYSTEM_ADMIN in admin.permissions
        assert Permission.USER_MANAGE in admin.permissions
        assert Permission.ALL_DATA_ACCESS in admin.permissions
        assert admin.amount_limit == 0  # 无限制
        assert admin.data_scope == "all"


class TestRBACManager:
    """RBAC 管理器测试"""
    
    @pytest.fixture
    def manager(self):
        """创建 RBAC 管理器实例"""
        return RBACManager()
    
    def test_manager_creation(self, manager):
        """测试管理器创建"""
        assert manager is not None
        assert len(manager._user_roles) == 0
    
    def test_assign_role(self, manager):
        """测试分配角色"""
        manager.assign_role("user-001", Role.SENIOR_BUYER, "采购部")
        
        assert "user-001" in manager._user_roles
        assert manager._user_roles["user-001"]["role"] == Role.SENIOR_BUYER
        assert manager._user_roles["user-001"]["department"] == "采购部"
    
    def test_get_user_role(self, manager):
        """测试获取用户角色"""
        manager.assign_role("user-001", Role.JUNIOR_BUYER)
        
        role = manager.get_user_role("user-001")
        assert role == Role.JUNIOR_BUYER
        
        # 不存在的用户
        role = manager.get_user_role("nonexistent")
        assert role is None
    
    def test_has_permission(self, manager):
        """测试权限校验"""
        manager.assign_role("user-001", Role.SENIOR_BUYER)
        
        # 高级采购员有创建订单权限
        assert manager.has_permission("user-001", Permission.ORDER_CREATE) is True
        
        # 高级采购员没有系统管理权限
        assert manager.has_permission("user-001", Permission.SYSTEM_ADMIN) is False
    
    def test_has_permission_nonexistent_user(self, manager):
        """测试不存在用户的权限校验"""
        assert manager.has_permission("nonexistent", Permission.ORDER_VIEW) is False
    
    def test_check_permission_success(self, manager):
        """测试权限检查（有权限）"""
        manager.assign_role("user-001", Role.SENIOR_BUYER)
        
        # 不应抛出异常
        manager.check_permission("user-001", Permission.ORDER_CREATE)
    
    def test_check_permission_denied(self, manager):
        """测试权限检查（无权限）"""
        manager.assign_role("user-001", Role.JUNIOR_BUYER)
        
        with pytest.raises(PermissionDeniedError):
            manager.check_permission("user-001", Permission.SYSTEM_ADMIN)
    
    def test_check_amount_limit_within_limit(self, manager):
        """测试金额校验（在限额内）"""
        manager.assign_role("user-001", Role.JUNIOR_BUYER)
        
        # 初级采购员限额10万，下单5万应该允许
        result = manager.check_amount_limit("user-001", 50_000)
        assert result is True
    
    def test_check_amount_limit_exceeded(self, manager):
        """测试金额校验（超出限额）"""
        manager.assign_role("user-001", Role.JUNIOR_BUYER)
        
        # 初级采购员限额10万，下单15万应该不允许
        with pytest.raises(AmountLimitExceededError):
            manager.check_amount_limit("user-001", 150_000)
    
    def test_check_amount_limit_unlimited(self, manager):
        """测试金额校验（无限制）"""
        manager.assign_role("user-001", Role.SYSTEM_ADMIN)
        
        # 系统管理员无金额限制
        result = manager.check_amount_limit("user-001", 10_000_000)
        assert result is True
    
    def test_is_sensitive_action(self, manager):
        """测试敏感操作检查"""
        manager.assign_role("user-001", Role.SENIOR_BUYER)
        
        # 高级采购员编辑供应商是敏感操作
        assert manager.is_sensitive_action("user-001", "supplier_edit") is True
        
        # 普通操作不是敏感操作
        assert manager.is_sensitive_action("user-001", "order_create") is False
    
    def test_can_approve_amount(self, manager):
        """测试审批权限检查"""
        manager.assign_role("user-001", Role.FINANCE_AUDITOR)
        
        # 财务审核员可审批100万以内
        assert manager.can_approve_amount("user-001", 500_000) is True
        assert manager.can_approve_amount("user-001", 1_500_000) is False
    
    def test_validate_data_access_self(self, manager):
        """测试数据访问范围校验（仅本人）"""
        manager.assign_role("user-001", Role.JUNIOR_BUYER)
        
        # 可以访问自己的数据
        assert manager.validate_data_access("user-001", "user-001") is True
        
        # 不能访问他人的数据
        assert manager.validate_data_access("user-001", "user-002") is False
    
    def test_validate_data_access_department(self, manager):
        """测试数据访问范围校验（部门）"""
        manager.assign_role("user-001", Role.SENIOR_BUYER, "采购部")
        
        # 可以访问部门数据（这里简化测试）
        assert manager.validate_data_access("user-001", "user-002", "采购部") is True
    
    def test_validate_data_access_all(self, manager):
        """测试数据访问范围校验（全部）"""
        manager.assign_role("user-001", Role.SYSTEM_ADMIN)
        
        # 系统管理员可以访问所有数据
        assert manager.validate_data_access("user-001", "any-user") is True


class TestRequirePermissionDecorator:
    """权限装饰器测试"""
    
    @pytest.fixture
    def manager(self):
        """获取 RBAC 管理器"""
        return get_rbac_manager()
    
    @pytest.mark.asyncio
    async def test_require_permission_success(self, manager):
        """测试权限装饰器（有权限）"""
        manager.assign_role("user-001", Role.SENIOR_BUYER)
        
        @require_permission(Permission.ORDER_CREATE)
        async def create_order(user_id: str):
            return "order_created"
        
        result = await create_order("user-001")
        assert result == "order_created"
    
    @pytest.mark.asyncio
    async def test_require_permission_denied(self, manager):
        """测试权限装饰器（无权限）"""
        manager.assign_role("user-002", Role.JUNIOR_BUYER)
        
        @require_permission(Permission.SYSTEM_ADMIN)
        async def admin_action(user_id: str):
            return "admin_action"
        
        with pytest.raises(PermissionDeniedError):
            await admin_action("user-002")


class TestRequireRoleDecorator:
    """角色装饰器测试"""
    
    @pytest.fixture
    def manager(self):
        """获取 RBAC 管理器"""
        return get_rbac_manager()
    
    @pytest.mark.asyncio
    async def test_require_role_success(self, manager):
        """测试角色装饰器（有角色）"""
        manager.assign_role("admin-001", Role.SYSTEM_ADMIN)
        
        @require_role(Role.SYSTEM_ADMIN)
        async def admin_only(user_id: str):
            return "admin_action"
        
        result = await admin_only("admin-001")
        assert result == "admin_action"
    
    @pytest.mark.asyncio
    async def test_require_role_denied(self, manager):
        """测试角色装饰器（无角色）"""
        manager.assign_role("user-001", Role.JUNIOR_BUYER)
        
        @require_role(Role.SYSTEM_ADMIN)
        async def admin_only(user_id: str):
            return "admin_action"
        
        with pytest.raises(PermissionDeniedError):
            await admin_only("user-001")


class TestExceptions:
    """异常测试"""
    
    def test_permission_denied_error(self):
        """测试权限拒绝异常"""
        error = PermissionDeniedError(
            user_id="user-001",
            permission=Permission.SYSTEM_ADMIN,
        )
        
        assert "user-001" in str(error)
        assert "system:admin" in str(error)
    
    def test_amount_limit_exceeded_error(self):
        """测试金额超限异常"""
        error = AmountLimitExceededError(
            user_id="user-001",
            amount=150_000,
            limit=100_000,
        )
        
        assert "user-001" in str(error)
        assert "150000" in str(error)
        assert "100000" in str(error)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
