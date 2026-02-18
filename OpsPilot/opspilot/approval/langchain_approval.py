"""
LangChain人工审批回调集成

集成LangChain的HumanApprovalCallback功能
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
import logging

logger = logging.getLogger(__name__)

# 尝试导入LangChain
try:
    from langchain.callbacks.base import BaseCallbackHandler
    from langchain.schema import AgentAction
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseCallbackHandler = object
    AgentAction = None
    logger.warning("LangChain未安装，HumanApprovalCallback不可用")

from opspilot.approval.config import ApprovalConfig, ApprovalLevel
from opspilot.approval.opspilot_approval import (
    ApprovalRequest,
    ApprovalStatus,
)


@dataclass
class ApprovalCallback:
    """审批回调信息"""
    tool_name: str
    tool_input: Dict[str, Any]
    request_id: str
    requires_approval: bool
    approved: Optional[bool] = None
    reason: Optional[str] = None


class LangChainApprovalHandler(BaseCallbackHandler if LANGCHAIN_AVAILABLE else object):
    """
    LangChain人工审批处理器
    
    集成LangChain的回调机制，在工具调用前请求人工审批
    """
    
    def __init__(
        self,
        config: Optional[ApprovalConfig] = None,
        approval_callback: Optional[Callable[[ApprovalCallback], bool]] = None,
    ):
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain未安装，无法使用LangChainApprovalHandler")
        
        super().__init__()
        self.config = config or ApprovalConfig()
        self.approval_callback = approval_callback
        self._pending_approvals: Dict[str, ApprovalCallback] = {}
        self._approval_results: Dict[str, bool] = {}
        
        # LangChain配置
        self.timeout_seconds = self.config.langchain_config.get("timeout_seconds", 300)
        self.require_reason = self.config.langchain_config.get("require_reason", True)
    
    def on_agent_action(
        self,
        action: AgentAction,
        *,
        run_id: str,
        parent_run_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Agent动作回调
        
        在Agent执行工具前触发，用于请求审批
        """
        tool_name = action.tool
        tool_input = action.tool_input
        
        # 检查是否需要审批
        if not self.config.requires_approval(tool_name):
            logger.debug(f"工具 {tool_name} 无需审批")
            return
        
        # 创建审批回调
        callback = ApprovalCallback(
            tool_name=tool_name,
            tool_input=tool_input if isinstance(tool_input, dict) else {"input": tool_input},
            request_id=f"lc-{run_id}-{datetime.now().timestamp()}",
            requires_approval=True,
        )
        
        self._pending_approvals[callback.request_id] = callback
        
        logger.info(f"LangChain审批请求: {callback.request_id}, 工具: {tool_name}")
        
        # 调用审批回调（同步阻塞）
        if self.approval_callback:
            try:
                approved = self.approval_callback(callback)
                self._approval_results[callback.request_id] = approved
                
                if not approved:
                    # 审批被拒绝，抛出异常阻止工具执行
                    raise ValueError(f"工具调用 {tool_name} 被拒绝审批")
            except Exception as e:
                logger.error(f"审批回调执行失败: {e}")
                raise
        else:
            # 没有设置回调，使用默认行为（等待人工确认）
            logger.warning(f"未设置审批回调，工具 {tool_name} 将等待人工确认")
    
    async def request_approval(
        self,
        tool_name: str,
        params: Dict[str, Any],
        requester: str,
        reason: str = "",
    ) -> ApprovalRequest:
        """
        异步审批请求接口
        
        与OpsPilot接口保持一致
        """
        # 检查是否需要审批
        if not self.config.requires_approval(tool_name):
            # 自动批准
            return ApprovalRequest(
                request_id=f"lc-auto-{datetime.now().timestamp()}",
                tool_name=tool_name,
                params=params,
                level=ApprovalLevel.LOW,
                reason=reason,
                requester=requester,
                status=ApprovalStatus.APPROVED,
                approver="system",
                approved_at=datetime.now(),
                approval_reason="自动批准",
            )
        
        # 创建审批请求
        request_id = f"lc-approval-{datetime.now().timestamp()}"
        request = ApprovalRequest(
            request_id=request_id,
            tool_name=tool_name,
            params=params,
            level=self.config.get_rule_for_tool(tool_name).level,
            reason=reason,
            requester=requester,
        )
        
        logger.info(f"创建LangChain审批请求: {request_id}")
        
        # 模拟等待审批（实际应用中应该等待外部输入）
        await asyncio.sleep(0.1)  # 短暂延迟
        
        return request
    
    def get_pending_approvals(self) -> List[ApprovalCallback]:
        """获取所有待审批请求"""
        return [
            cb for cb in self._pending_approvals.values()
            if cb.approved is None
        ]
    
    def approve(self, request_id: str, reason: str = "") -> bool:
        """批准审批"""
        callback = self._pending_approvals.get(request_id)
        if not callback:
            logger.warning(f"审批请求不存在: {request_id}")
            return False
        
        callback.approved = True
        callback.reason = reason
        self._approval_results[request_id] = True
        
        logger.info(f"LangChain审批已批准: {request_id}")
        return True
    
    def reject(self, request_id: str, reason: str) -> bool:
        """拒绝审批"""
        callback = self._pending_approvals.get(request_id)
        if not callback:
            logger.warning(f"审批请求不存在: {request_id}")
            return False
        
        callback.approved = False
        callback.reason = reason
        self._approval_results[request_id] = False
        
        logger.info(f"LangChain审批已拒绝: {request_id}, 原因: {reason}")
        return True
    
    def get_result(self, request_id: str) -> Optional[bool]:
        """获取审批结果"""
        return self._approval_results.get(request_id)
    
    @staticmethod
    def is_available() -> bool:
        """检查LangChain是否可用"""
        return LANGCHAIN_AVAILABLE
