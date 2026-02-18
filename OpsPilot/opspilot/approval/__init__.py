"""
人工审批模块

集成多种审批实现：
- OpsPilotApprovalHandler: OpsPilot自研审批处理
- LangChainApprovalHandler: LangChain人工审批回调
- ApprovalFactory: 审批工厂，根据配置选择实现

职责：
- 敏感操作审批
- 高风险任务确认
- 大额操作审核
"""

from opspilot.approval.opspilot_approval import (
    OpsPilotApprovalHandler,
    ApprovalRequest,
    ApprovalStatus,
)

from opspilot.approval.langchain_approval import (
    LangChainApprovalHandler,
    ApprovalCallback,
)

from opspilot.approval.factory import (
    ApprovalFactory,
    ApprovalProvider,
    get_approval_handler,
    create_approval_handler,
)

from opspilot.approval.config import (
    ApprovalConfig,
    ApprovalRule,
)

__all__ = [
    # OpsPilot审批
    "OpsPilotApprovalHandler",
    "ApprovalRequest",
    "ApprovalStatus",
    # LangChain审批
    "LangChainApprovalHandler",
    "ApprovalCallback",
    # 工厂类
    "ApprovalFactory",
    "ApprovalProvider",
    "get_approval_handler",
    "create_approval_handler",
    # 配置
    "ApprovalConfig",
    "ApprovalRule",
]
