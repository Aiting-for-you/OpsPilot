"""
工单跟进Agent

职责：跟踪工单状态、收集客户满意度、处理关闭和重新打开
"""
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime, timedelta

from opspilot.agents.base import (
    BaseAgent,
    AgentConfig,
    AgentRole,
    AgentContext,
    AgentOutput,
    BaseLLMClient,
)


class FollowUpStatus(str, Enum):
    """跟进状态"""
    PENDING = "pending"           # 待跟进
    IN_PROGRESS = "in_progress"  # 跟进中
    COMPLETED = "completed"      # 跟进完成
    CUSTOMER_UNSATISFIED = "customer_unsatisfied"  # 客户不满意
    REOPENED = "reopened"        # 已重新打开


class SatisfactionLevel(str, Enum):
    """满意度级别"""
    VERY_SATISFIED = "very_satisfied"   # 非常满意
    SATISFIED = "satisfied"             # 满意
    NEUTRAL = "neutral"                 # 一般
    DISSATISFIED = "dissatisfied"       # 不满意
    VERY_DISSATISFIED = "very_dissatisfied"  # 非常不满意


class FollowUpAgent(BaseAgent):
    """
    工单跟进Agent
    
    职责：跟踪工单状态、收集客户满意度、发送跟进通知
    """

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        config = AgentConfig(
            name="FollowUpAgent",
            role=AgentRole.VERIFICATION,
            description="工单跟进Agent，跟踪工单状态和客户满意度",
            temperature=0.3,
        )
        super().__init__(config, llm_client)
        
        # 跟进配置
        self.follow_up_config = {
            "auto_follow_up_after_hours": 24,  # 工单解决后24小时自动跟进
            "reopen_within_hours": 72,         # 72小时内可重新打开
            "satisfaction_survey_required": True,  # 需要满意度调查
        }

    async def _execute(self, context: AgentContext) -> AgentOutput:
        """执行工单跟进"""
        action = context.metadata.get("action", "check_status")
        
        if action == "check_status":
            return await self._check_follow_up_status(context)
        elif action == "collect_satisfaction":
            return await self._collect_satisfaction(context)
        elif action == "send_notification":
            return await self._send_follow_up_notification(context)
        elif action == "reopen":
            return await self._reopen_ticket(context)
        elif action == "close":
            return await self._close_ticket(context)
        else:
            return AgentOutput(
                success=False,
                error=f"未知操作: {action}"
            )

    async def _check_follow_up_status(self, context: AgentContext) -> AgentOutput:
        """检查跟进状态"""
        ticket_data = context.metadata.get("ticket_data", {})
        ticket_id = ticket_data.get("ticket_id", "")
        
        # Mock状态数据
        status_data = {
            "ticket_id": ticket_id,
            "follow_up_status": FollowUpStatus.PENDING.value,
            "last_follow_up_time": None,
            "next_follow_up_time": self._calculate_next_follow_up(datetime.now()),
            "satisfaction_score": None,
            "resolution_time_hours": ticket_data.get("resolution_time_hours", 0),
            "customer_response_required": True,
        }
        
        return AgentOutput(
            success=True,
            result=status_data,
            reasoning=f"工单 {ticket_id} 跟进状态已更新"
        )

    async def _collect_satisfaction(self, context: AgentContext) -> AgentOutput:
        """收集客户满意度"""
        ticket_data = context.metadata.get("ticket_data", {})
        customer_feedback = context.metadata.get("customer_feedback", "")
        
        # 如果没有客户反馈，使用LLM分析
        if not customer_feedback:
            satisfaction = await self._analyze_satisfaction(ticket_data)
        else:
            satisfaction = self._parse_feedback(customer_feedback)
        
        # 生成满意度调查结果
        survey_result = {
            "satisfaction_level": satisfaction.get("level", SatisfactionLevel.NEUTRAL.value),
            "score": satisfaction.get("score", 3),
            "feedback": customer_feedback,
            "would_recommend": satisfaction.get("would_recommend", None),
            "follow_up_required": satisfaction.get("level") in [
                SatisfactionLevel.DISSATISFIED.value,
                SatisfactionLevel.VERY_DISSATISFIED.value,
            ],
            "survey_time": datetime.now().isoformat(),
        }
        
        return AgentOutput(
            success=True,
            result=survey_result,
            reasoning=f"满意度: {satisfaction.get('level')}, 评分: {satisfaction.get('score')}/5"
        )

    async def _send_follow_up_notification(self, context: AgentContext) -> AgentOutput:
        """发送跟进通知"""
        ticket_data = context.metadata.get("ticket_data", {})
        customer_info = context.metadata.get("customer_info", {})
        
        notification = {
            "ticket_id": ticket_data.get("ticket_id"),
            "customer_email": customer_info.get("email", ""),
            "customer_phone": customer_info.get("phone", ""),
            "subject": "工单处理结果跟进",
            "content": self._generate_follow_up_message(ticket_data),
            "send_time": datetime.now().isoformat(),
            "channels": ["email", "sms"] if customer_info.get("phone") else ["email"],
        }
        
        return AgentOutput(
            success=True,
            result=notification,
            reasoning="跟进通知已发送"
        )

    async def _reopen_ticket(self, context: AgentContext) -> AgentOutput:
        """重新打开工单"""
        ticket_data = context.metadata.get("ticket_data", {})
        reason = context.metadata.get("reopen_reason", "")
        
        # 检查是否在可重新打开时间范围内
        resolved_time = ticket_data.get("resolved_time")
        if resolved_time:
            resolved_dt = datetime.fromisoformat(resolved_time)
            hours_since_resolved = (datetime.now() - resolved_dt).total_seconds() / 3600
            
            if hours_since_resolved > self.follow_up_config["reopen_within_hours"]:
                return AgentOutput(
                    success=False,
                    error=f"工单已超过{self.follow_up_config['reopen_within_hours']}小时可重新打开时限"
                )
        
        reopen_result = {
            "ticket_id": ticket_data.get("ticket_id"),
            "reopened": True,
            "reopen_reason": reason,
            "reopen_time": datetime.now().isoformat(),
            "previous_status": ticket_data.get("status", "resolved"),
            "new_status": "reopened",
            "assignee": ticket_data.get("original_assignee"),
        }
        
        return AgentOutput(
            success=True,
            result=reopen_result,
            reasoning=f"工单已重新打开，原因: {reason}"
        )

    async def _close_ticket(self, context: AgentContext) -> AgentOutput:
        """关闭工单"""
        ticket_data = context.metadata.get("ticket_data", {})
        
        close_result = {
            "ticket_id": ticket_data.get("ticket_id"),
            "closed": True,
            "close_time": datetime.now().isoformat(),
            "final_status": "closed",
            "archive_required": True,
        }
        
        return AgentOutput(
            success=True,
            result=close_result,
            reasoning="工单已关闭"
        )

    async def _analyze_satisfaction(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析满意度（LLM）"""
        # Mock分析结果
        resolution = ticket_data.get("resolution", "")
        
        if "无法解决" in resolution:
            return {
                "level": SatisfactionLevel.DISSATISFIED.value,
                "score": 2,
                "would_recommend": False,
            }
        
        return {
            "level": SatisfactionLevel.SATISFIED.value,
            "score": 4,
            "would_recommend": True,
        }

    def _parse_feedback(self, feedback: str) -> Dict[str, Any]:
        """解析客户反馈"""
        feedback_lower = feedback.lower()
        
        if any(word in feedback_lower for word in ["非常满意", "非常好", "谢谢", "感谢"]):
            return {
                "level": SatisfactionLevel.VERY_SATISFIED.value,
                "score": 5,
                "would_recommend": True,
            }
        elif any(word in feedback_lower for word in ["满意", "不错", "可以"]):
            return {
                "level": SatisfactionLevel.SATISFIED.value,
                "score": 4,
                "would_recommend": True,
            }
        elif any(word in feedback_lower for word in ["不满意", "太差", "失望"]):
            return {
                "level": SatisfactionLevel.DISSATISFIED.value,
                "score": 2,
                "would_recommend": False,
            }
        
        return {
            "level": SatisfactionLevel.NEUTRAL.value,
            "score": 3,
            "would_recommend": None,
        }

    def _calculate_next_follow_up(self, from_time: datetime) -> str:
        """计算下次跟进时间"""
        next_follow_up = from_time + timedelta(
            hours=self.follow_up_config["auto_follow_up_after_hours"]
        )
        return next_follow_up.isoformat()

    def _generate_follow_up_message(self, ticket_data: Dict[str, Any]) -> str:
        """生成跟进消息"""
        ticket_id = ticket_data.get("ticket_id", "")
        resolution = ticket_data.get("resolution", "")
        
        return f"""尊敬的客户，

感谢您对我们的支持！您的工单 (ID: {ticket_id}) 已处理完成。

处理结果：{resolution}

请您对本次服务进行评价，您的反馈对我们非常重要。

如有任何问题，请随时联系我们。

祝好！
客服团队
"""

    def get_system_prompt(self, context: AgentContext) -> str:
        """获取系统提示"""
        return """你是一个专业的工单跟进助手。
你的任务是：
1. 跟踪工单状态
2. 收集客户满意度
3. 发送跟进通知
4. 处理工单重新打开
5. 处理工单关闭

请根据工单信息执行相应的跟进操作。"""


class MockFollowUpAgent(FollowUpAgent):
    """
    Mock工单跟进Agent - 使用规则模拟
    """

    async def _execute(self, context: AgentContext) -> AgentOutput:
        """执行工单跟进（Mock）"""
        action = context.metadata.get("action", "check_status")
        ticket_data = context.metadata.get("ticket_data", {})
        
        if action == "check_status":
            return AgentOutput(
                success=True,
                result={
                    "ticket_id": ticket_data.get("ticket_id"),
                    "follow_up_status": FollowUpStatus.COMPLETED.value,
                    "satisfaction_score": 4,
                },
                reasoning="工单跟进完成"
            )
        
        return await super()._execute(context)
