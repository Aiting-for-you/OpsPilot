"""
审批工作流测试

测试审批流程功能：
- 审批请求创建
- 审批通过/拒绝
- 审批过期
- 待审批列表查询
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from opspilot.auth.approval import (
    ApprovalStatus,
    ApprovalType,
    ApprovalRequest,
    ApprovalRule,
    ApprovalWorkflow,
    get_approval_workflow,
)


class TestApprovalStatus:
    """审批状态测试"""
    
    def test_status_values(self):
        """测试状态值"""
        assert ApprovalStatus.PENDING.value == "pending"
        assert ApprovalStatus.APPROVED.value == "approved"
        assert ApprovalStatus.REJECTED.value == "rejected"
        assert ApprovalStatus.EXPIRED.value == "expired"
        assert ApprovalStatus.CANCELLED.value == "cancelled"


class TestApprovalType:
    """审批类型测试"""
    
    def test_type_values(self):
        """测试类型值"""
        assert ApprovalType.AMOUNT_EXCEEDED.value == "amount_exceeded"
        assert ApprovalType.SENSITIVE_ACTION.value == "sensitive_action"
        assert ApprovalType.PAYMENT.value == "payment"
        assert ApprovalType.CONTRACT.value == "contract"
        assert ApprovalType.ORDER_CANCEL.value == "order_cancel"


class TestApprovalRequest:
    """审批请求测试"""
    
    def test_request_creation(self):
        """测试创建审批请求"""
        request = ApprovalRequest(
            request_id="approval-001",
            approval_type=ApprovalType.AMOUNT_EXCEEDED,
            user_id="user-001",
            user_role="senior_buyer",
            title="超额采购订单审批",
            description="采购金额150,000元，超过限额100,000元",
            data={"order_id": "order-123", "amount": 150000},
        )
        
        assert request.request_id == "approval-001"
        assert request.approval_type == ApprovalType.AMOUNT_EXCEEDED
        assert request.status == ApprovalStatus.PENDING
        assert request.user_id == "user-001"
    
    def test_request_to_dict(self):
        """测试审批请求转换为字典"""
        request = ApprovalRequest(
            request_id="approval-001",
            approval_type=ApprovalType.PAYMENT,
            user_id="user-001",
            user_role="senior_buyer",
            title="付款审批",
            description="供应商付款审批",
            data={"payment_id": "pay-123"},
        )
        
        data = request.to_dict()
        
        assert data["request_id"] == "approval-001"
        assert data["approval_type"] == "payment"
        assert data["status"] == "pending"
        assert data["user_id"] == "user-001"


class TestApprovalRule:
    """审批规则测试"""
    
    def test_rule_creation(self):
        """测试创建审批规则"""
        rule = ApprovalRule(
            approval_type=ApprovalType.AMOUNT_EXCEEDED,
            name="超额订单审批",
            description="金额超过角色限额需要审批",
            min_amount=100_000,
            required_roles=["finance_auditor", "system_admin"],
        )
        
        assert rule.approval_type == ApprovalType.AMOUNT_EXCEEDED
        assert rule.min_amount == 100_000
        assert "finance_auditor" in rule.required_roles


class TestApprovalWorkflow:
    """审批工作流测试"""
    
    @pytest.fixture
    def workflow(self):
        """创建审批工作流实例"""
        return ApprovalWorkflow()
    
    def test_workflow_creation(self, workflow):
        """测试工作流创建"""
        assert workflow is not None
        assert len(workflow._requests) == 0
    
    def test_create_approval_request(self, workflow):
        """测试创建审批请求"""
        request_id = workflow.create_approval_request(
            user_id="user-001",
            user_role="senior_buyer",
            approval_type=ApprovalType.AMOUNT_EXCEEDED,
            title="超额订单审批",
            description="采购金额150,000元",
            data={"order_id": "order-123", "amount": 150000},
        )
        
        assert request_id is not None
        assert request_id.startswith("approval-")
        
        request = workflow.get_request(request_id)
        assert request is not None
        assert request.status == ApprovalStatus.PENDING
    
    def test_approve_request(self, workflow):
        """测试审批通过"""
        request_id = workflow.create_approval_request(
            user_id="user-001",
            user_role="senior_buyer",
            approval_type=ApprovalType.AMOUNT_EXCEEDED,
            title="超额订单审批",
            description="采购金额150,000元",
            data={"amount": 150000},
        )
        
        result = workflow.approve(
            request_id=request_id,
            approver_id="finance-001",
            comment="同意采购，价格合理",
        )
        
        assert result is True
        
        request = workflow.get_request(request_id)
        assert request.status == ApprovalStatus.APPROVED
        assert request.approved_by == "finance-001"
        assert "同意采购" in request.approval_comment
    
    def test_reject_request(self, workflow):
        """测试审批拒绝"""
        request_id = workflow.create_approval_request(
            user_id="user-001",
            user_role="senior_buyer",
            approval_type=ApprovalType.AMOUNT_EXCEEDED,
            title="超额订单审批",
            description="采购金额150,000元",
            data={"amount": 150000},
        )
        
        result = workflow.reject(
            request_id=request_id,
            approver_id="finance-001",
            comment="价格过高，需重新议价",
        )
        
        assert result is True
        
        request = workflow.get_request(request_id)
        assert request.status == ApprovalStatus.REJECTED
        assert request.approved_by == "finance-001"
    
    def test_approve_nonexistent_request(self, workflow):
        """测试审批不存在的请求"""
        result = workflow.approve(
            request_id="nonexistent",
            approver_id="finance-001",
            comment="comment",
        )
        
        assert result is False
    
    def test_approve_already_processed(self, workflow):
        """测试重复审批"""
        request_id = workflow.create_approval_request(
            user_id="user-001",
            user_role="senior_buyer",
            approval_type=ApprovalType.AMOUNT_EXCEEDED,
            title="超额订单审批",
            description="description",
            data={},
        )
        
        # 第一次审批
        workflow.approve(request_id, "finance-001", "同意")
        
        # 第二次审批应该失败
        result = workflow.approve(request_id, "finance-002", "同意")
        assert result is False
    
    def test_get_pending_requests(self, workflow):
        """测试获取待审批列表"""
        # 创建多个审批请求
        workflow.create_approval_request(
            user_id="user-001",
            user_role="senior_buyer",
            approval_type=ApprovalType.AMOUNT_EXCEEDED,
            title="审批1",
            description="desc1",
            data={},
        )
        
        request_id2 = workflow.create_approval_request(
            user_id="user-002",
            user_role="junior_buyer",
            approval_type=ApprovalType.SENSITIVE_ACTION,
            title="审批2",
            description="desc2",
            data={},
        )
        
        # 审批其中一个
        workflow.approve(request_id2, "finance-001", "同意")
        
        # 获取待审批列表
        pending = workflow.get_pending_requests()
        
        assert len(pending) == 1
        assert pending[0].title == "审批1"
    
    def test_get_user_requests(self, workflow):
        """测试获取用户发起的审批"""
        workflow.create_approval_request(
            user_id="user-001",
            user_role="senior_buyer",
            approval_type=ApprovalType.AMOUNT_EXCEEDED,
            title="审批1",
            description="desc1",
            data={},
        )
        
        workflow.create_approval_request(
            user_id="user-001",
            user_role="senior_buyer",
            approval_type=ApprovalType.PAYMENT,
            title="审批2",
            description="desc2",
            data={},
        )
        
        workflow.create_approval_request(
            user_id="user-002",
            user_role="junior_buyer",
            approval_type=ApprovalType.AMOUNT_EXCEEDED,
            title="审批3",
            description="desc3",
            data={},
        )
        
        user_requests = workflow.get_user_requests("user-001")
        
        assert len(user_requests) == 2
    
    def test_get_request(self, workflow):
        """测试获取审批详情"""
        request_id = workflow.create_approval_request(
            user_id="user-001",
            user_role="senior_buyer",
            approval_type=ApprovalType.CONTRACT,
            title="合同审批",
            description="供应商合同签署",
            data={"contract_id": "contract-001"},
        )
        
        request = workflow.get_request(request_id)
        
        assert request is not None
        assert request.title == "合同审批"
        assert request.data["contract_id"] == "contract-001"
    
    def test_get_nonexistent_request(self, workflow):
        """测试获取不存在的审批"""
        request = workflow.get_request("nonexistent")
        assert request is None
    
    def test_cancel_request(self, workflow):
        """测试取消审批请求"""
        request_id = workflow.create_approval_request(
            user_id="user-001",
            user_role="senior_buyer",
            approval_type=ApprovalType.AMOUNT_EXCEEDED,
            title="审批",
            description="desc",
            data={},
        )
        
        result = workflow.cancel(request_id, "user-001")
        
        assert result is True
        
        request = workflow.get_request(request_id)
        assert request.status == ApprovalStatus.CANCELLED
    
    def test_cancel_already_processed(self, workflow):
        """测试取消已处理的审批"""
        request_id = workflow.create_approval_request(
            user_id="user-001",
            user_role="senior_buyer",
            approval_type=ApprovalType.AMOUNT_EXCEEDED,
            title="审批",
            description="desc",
            data={},
        )
        
        workflow.approve(request_id, "finance-001", "同意")
        
        result = workflow.cancel(request_id, "user-001")
        assert result is False


class TestGetApprovalWorkflow:
    """全局工作流测试"""
    
    def test_get_workflow_singleton(self):
        """测试获取全局工作流（单例）"""
        workflow1 = get_approval_workflow()
        workflow2 = get_approval_workflow()
        
        assert workflow1 is workflow2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
