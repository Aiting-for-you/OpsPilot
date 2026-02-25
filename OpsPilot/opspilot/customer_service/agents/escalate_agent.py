"""
工单升级Agent

职责：当问题无法解决时升级到专家或上级部门
"""
from typing import Optional, Dict, Any, List
from enum import Enum

from opspilot.agents.base import (
    BaseAgent,
    AgentConfig,
    AgentRole,
    AgentContext,
    AgentOutput,
    BaseLLMClient,
)


class EscalationLevel(str, Enum):
    """升级级别"""
    LEVEL_1 = "level_1"     # 升级到组长
    LEVEL_2 = "level_2"     # 升级到主管
    LEVEL_3 = "level_3"     # 升级到经理
    ESCALATE_EXTERNAL = "external"  # 转接外部


class EscalationReason(str, Enum):
    """升级原因"""
    TECHNICAL_ISSUE = "technical_issue"       # 技术问题无法解决
    CUSTOMER_REQUEST = "customer_request"     # 客户要求升级
    NO_SOLUTION = "no_solution"               # 未找到解决方案
    POLICY_VIOLATION = "policy_violation"     # 涉及政策违规
    REFUND_EXCEED_LIMIT = "refund_exceed_limit"  # 退款超权限
    COMPLAINT = "complaint"                  # 投诉工单
    TIMEOUT = "timeout"                       # 处理超时


class EscalateAgent(BaseAgent):
    """
    工单升级Agent
    
    职责：当问题无法解决时，评估是否需要升级并执行升级操作
    """

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        config = AgentConfig(
            name="EscalateAgent",
            role=AgentRole.VERIFICATION,
            description="工单升级Agent，评估并执行工单升级",
            temperature=0.3,
        )
        super().__init__(config, llm_client)
        
        # 升级规则配置
        self.escalation_rules = {
            "refund_request": {"threshold": 5000, "level": EscalationLevel.LEVEL_2},
            "complaint": {"threshold": 0, "level": EscalationLevel.LEVEL_2},
            "technical_issue": {"threshold": 0, "level": EscalationLevel.LEVEL_3},
            "policy_violation": {"threshold": 0, "level": EscalationLevel.LEVEL_3},
        }

    async def _execute(self, context: AgentContext) -> AgentOutput:
        """执行工单升级评估"""
        # 从context中获取工单信息
        ticket_data = context.metadata.get("ticket_data", {})
        classification = context.metadata.get("classification", {})
        solution = context.metadata.get("solution", {})
        retry_count = context.metadata.get("retry_count", 0)
        
        if not ticket_data:
            return AgentOutput(
                success=False,
                error="缺少工单数据"
            )
        
        # 评估是否需要升级
        escalation = self._evaluate_escalation(
            ticket_data=ticket_data,
            classification=classification,
            solution=solution,
            retry_count=retry_count,
        )
        
        if escalation.get("should_escalate"):
            # 执行升级
            escalation_result = self._perform_escalation(escalation)
            return AgentOutput(
                success=True,
                result=escalation_result,
                reasoning=escalation.get("reason", "")
            )
        
        return AgentOutput(
            success=True,
            result={"should_escalate": False, "message": "工单不需要升级"},
            reasoning="工单可在当前级别解决"
        )

    def _evaluate_escalation(
        self,
        ticket_data: Dict[str, Any],
        classification: Dict[str, Any],
        solution: Dict[str, Any],
        retry_count: int,
    ) -> Dict[str, Any]:
        """评估是否需要升级"""
        ticket_type = classification.get("ticket_type", "other")
        priority = classification.get("priority", "normal")
        
        # 检查是否有解决方案
        has_solution = solution.get("resolution", "") if solution else ""
        
        # 检查重试次数
        if retry_count >= 3:
            return {
                "should_escalate": True,
                "reason": "处理重试次数超过3次，需要升级",
                "escalation_level": EscalationLevel.LEVEL_1,
                "escalation_reason": EscalationReason.TIMEOUT,
            }
        
        # 检查是否找到解决方案
        if not has_solution or has_solution == "无法解决":
            # 检查是否有升级规则
            rule = self.escalation_rules.get(ticket_type)
            if rule:
                return {
                    "should_escalate": True,
                    "reason": f"工单类型 {ticket_type} 触发升级规则",
                    "escalation_level": rule["level"],
                    "escalation_reason": EscalationReason.NO_SOLUTION,
                }
        
        # 检查退款金额
        if ticket_type == "refund_request":
            refund_amount = ticket_data.get("refund_amount", 0)
            rule = self.escalation_rules.get("refund_request", {})
            if refund_amount > rule.get("threshold", 0):
                return {
                    "should_escalate": True,
                    "reason": f"退款金额 {refund_amount} 超过阈值",
                    "escalation_level": rule["level"],
                    "escalation_reason": EscalationReason.REFUND_EXCEED_LIMIT,
                }
        
        # 检查投诉工单
        if ticket_type == "complaint":
            rule = self.escalation_rules.get("complaint", {})
            return {
                "should_escalate": True,
                "reason": "投诉工单需要升级处理",
                "escalation_level": rule.get("level", EscalationLevel.LEVEL_2),
                "escalation_reason": EscalationReason.COMPLAINT,
            }
        
        return {"should_escalate": False}

    def _perform_escalation(self, escalation: Dict[str, Any]) -> Dict[str, Any]:
        """执行升级操作"""
        level = escalation.get("escalation_level", EscalationLevel.LEVEL_1)
        reason = escalation.get("escalation_reason", EscalationReason.NO_SOLUTION)
        
        # 确定升级目标
        escalation_targets = {
            EscalationLevel.LEVEL_1: {
                "target": "组长",
                "department": "客服组-组长",
                "contact": "supervisor@company.com",
            },
            EscalationLevel.LEVEL_2: {
                "target": "主管",
                "department": "客服部-主管",
                "contact": "manager@company.com",
            },
            EscalationLevel.LEVEL_3: {
                "target": "经理",
                "department": "客服部-经理",
                "contact": "senior.manager@company.com",
            },
            EscalationLevel.ESCALATE_EXTERNAL: {
                "target": "外部专家",
                "department": "专家团队",
                "contact": "expert@company.com",
            },
        }
        
        target = escalation_targets.get(level, escalation_targets[EscalationLevel.LEVEL_1])
        
        return {
            "escalated": True,
            "escalation_level": level.value,
            "escalation_reason": reason.value,
            "target_department": target["department"],
            "target_contact": target["contact"],
            "estimated_response_time": self._get_sla_time(level),
            "actions": [
                f"创建升级工单",
                f"通知{target['target']}",
                f"转移工单到{target['department']}",
            ],
        }

    def _get_sla_time(self, level: EscalationLevel) -> str:
        """获取升级响应时间"""
        sla_times = {
            EscalationLevel.LEVEL_1: "30分钟",
            EscalationLevel.LEVEL_2: "1小时",
            EscalationLevel.LEVEL_3: "2小时",
            EscalationLevel.ESCALATE_EXTERNAL: "4小时",
        }
        return sla_times.get(level, "1小时")

    def get_system_prompt(self, context: AgentContext) -> str:
        """获取系统提示"""
        return """你是一个专业的工单升级助手。
你的任务是评估工单是否需要升级，并执行升级操作。

升级条件：
1. 处理重试超过3次仍无法解决
2. 涉及技术难题
3. 退款金额超过5000元
4. 客户投诉工单
5. 涉及政策违规

请根据工单信息做出准确的升级决策。"""


class MockEscalateAgent(EscalateAgent):
    """
    Mock工单升级Agent - 使用规则判断
    """

    async def _execute(self, context: AgentContext) -> AgentOutput:
        """执行工单升级评估（Mock）"""
        ticket_data = context.metadata.get("ticket_data", {})
        classification = context.metadata.get("classification", {})
        retry_count = context.metadata.get("retry_count", 0)
        
        ticket_type = classification.get("ticket_type", "other")
        
        # Mock判断逻辑
        should_escalate = False
        escalation_level = EscalationLevel.LEVEL_1
        escalation_reason = EscalationReason.NO_SOLUTION
        
        if retry_count >= 3:
            should_escalate = True
            escalation_reason = EscalationReason.TIMEOUT
        elif ticket_type == "complaint":
            should_escalate = True
            escalation_reason = EscalationReason.COMPLAINT
            escalation_level = EscalationLevel.LEVEL_2
        elif ticket_type == "refund_request":
            refund_amount = ticket_data.get("refund_amount", 0)
            if refund_amount > 5000:
                should_escalate = True
                escalation_reason = EscalationReason.REFUND_EXCEED_LIMIT
                escalation_level = EscalationLevel.LEVEL_2
        
        if should_escalate:
            result = self._perform_escalation({
                "should_escalate": True,
                "escalation_level": escalation_level,
                "escalation_reason": escalation_reason,
            })
            return AgentOutput(
                success=True,
                result=result,
                reasoning=f"工单已升级到{result['target_department']}",
            )
        
        return AgentOutput(
            success=True,
            result={"should_escalate": False, "message": "工单不需要升级"},
            reasoning="工单可在当前级别解决"
        )
