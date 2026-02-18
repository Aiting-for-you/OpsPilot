"""
审批配置模块

定义审批规则和配置
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Pattern
import re


class ApprovalLevel(str, Enum):
    """审批级别"""
    LOW = "low"           # 低风险，无需审批
    MEDIUM = "medium"     # 中风险，需要确认
    HIGH = "high"         # 高风险，需要审批
    CRITICAL = "critical" # 关键操作，需要多级审批


@dataclass
class ApprovalRule:
    """审批规则"""
    name: str
    pattern: str                    # 工具名称匹配模式（支持通配符）
    level: ApprovalLevel
    require_approval: bool = True
    auto_approve_after: Optional[int] = None  # 超时自动批准（秒）
    approvers: List[str] = field(default_factory=list)  # 审批人列表
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def matches(self, tool_name: str) -> bool:
        """检查工具名称是否匹配规则"""
        # 将通配符模式转换为正则表达式
        regex_pattern = self.pattern.replace("*", ".*")
        return bool(re.match(regex_pattern, tool_name, re.IGNORECASE))


@dataclass
class ApprovalConfig:
    """审批配置"""
    default_provider: str = "langchain"  # opspilot | langchain
    
    # 默认审批规则
    rules: List[ApprovalRule] = field(default_factory=lambda: [
        ApprovalRule(
            name="删除操作",
            pattern="delete_*",
            level=ApprovalLevel.HIGH,
            require_approval=True,
        ),
        ApprovalRule(
            name="更新操作",
            pattern="update_*",
            level=ApprovalLevel.MEDIUM,
            require_approval=True,
        ),
        ApprovalRule(
            name="创建操作",
            pattern="create_*",
            level=ApprovalLevel.MEDIUM,
            require_approval=True,
        ),
        ApprovalRule(
            name="查询操作",
            pattern="query_*",
            level=ApprovalLevel.LOW,
            require_approval=False,
        ),
    ])
    
    # LangChain特定配置
    langchain_config: Dict[str, Any] = field(default_factory=lambda: {
        "timeout_seconds": 300,  # 5分钟超时
        "require_reason": True,  # 需要填写原因
    })
    
    # OpsPilot特定配置
    opspilot_config: Dict[str, Any] = field(default_factory=lambda: {
        "webhook_url": None,  # 审批通知webhook
        "slack_channel": None,  # Slack通知频道
    })
    
    def get_rule_for_tool(self, tool_name: str) -> Optional[ApprovalRule]:
        """获取适用于工具的审批规则"""
        for rule in self.rules:
            if rule.matches(tool_name):
                return rule
        return None
    
    def requires_approval(self, tool_name: str) -> bool:
        """检查工具是否需要审批"""
        rule = self.get_rule_for_tool(tool_name)
        return rule.require_approval if rule else False
