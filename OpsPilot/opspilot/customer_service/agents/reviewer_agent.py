"""
工单审核Agent - 复用VerifyAgent

职责：审核解决方案质量
"""
from typing import Optional, Dict, Any, List
from datetime import datetime

from opspilot.agents.base import (
    BaseAgent,
    AgentConfig,
    AgentRole,
    AgentContext,
    AgentOutput,
    BaseLLMClient,
)


class TicketReviewerAgent(BaseAgent):
    """
    工单审核Agent
    
    复用验证逻辑，审核解决方案质量
    """

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        config = AgentConfig(
            name="TicketReviewerAgent",
            role=AgentRole.VERIFICATION,
            description="工单审核Agent，验证解决方案质量",
            temperature=0.2,
        )
        super().__init__(config, llm_client)

    async def _execute(self, context: AgentContext) -> AgentOutput:
        """执行工单审核"""
        # 获取上下文信息
        classification = context.metadata.get("classification", {})
        routing = context.metadata.get("routing", {})
        solution = context.metadata.get("solution", {})
        
        if not solution:
            return AgentOutput(
                success=False,
                error="缺少解决方案"
            )
        
        # 构建审核提示
        prompt = self._build_review_prompt(
            classification=classification,
            routing=routing,
            solution=solution,
        )
        
        # 调用LLM
        response = await self.llm.generate_json(prompt)
        
        # 解析响应
        review = self._parse_response(response)
        
        return AgentOutput(
            success=review.get("passed", False),
            result=review,
            reasoning=review.get("reason", "")
        )

    def _build_review_prompt(
        self,
        classification: Dict[str, Any],
        routing: Dict[str, Any],
        solution: Dict[str, Any],
    ) -> str:
        """构建审核提示"""
        return f"""请审核以下工单解决方案。

工单分类：{classification.get('ticket_type', 'unknown')}
优先级：{classification.get('priority', 'normal')}
分配部门：{routing.get('assigned_department', 'unknown')}

解决方案：
- 操作：{solution.get('action_taken', '')}
- 描述：{solution.get('resolution', '')}
- 预计完成：{solution.get('estimated_completion', '')}
- 需要跟进：{solution.get('requires_followup', False)}
- 客户通知：{solution.get('customer_notification', '')}

请以JSON格式返回审核结果：
{{
    "passed": true/false,
    "quality_score": 0-100分,
    "reason": "审核通过/失败原因",
    "checklist": [
        {{
            "item": "检查项",
            "passed": true/false,
            "detail": "详情"
        }}
    ],
    "improvement_suggestions": ["改进建议"]
}}

仅返回JSON，不要有其他内容。"""

    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析响应"""
        return {
            "passed": response.get("passed", False),
            "quality_score": response.get("quality_score", 0),
            "reason": response.get("reason", ""),
            "checklist": response.get("checklist", []),
            "improvement_suggestions": response.get("improvement_suggestions", []),
            "reviewed_at": datetime.now().isoformat(),
        }

    def get_system_prompt(self, context: AgentContext) -> str:
        """获取系统提示"""
        return """你是一个专业的工单审核助手。
你的任务是审核工单解决方案的质量。
你需要检查：
1. 解决方案是否完整
2. 是否解决了客户问题
3. 客户通知是否清晰友好
4. 后续跟进是否合理

确保解决方案符合服务质量标准。"""


class MockTicketReviewerAgent(TicketReviewerAgent):
    """
    Mock工单审核Agent - 简单规则审核
    """

    async def _execute(self, context: AgentContext) -> AgentOutput:
        """执行工单审核（简单规则）"""
        solution = context.metadata.get("solution", {})
        classification = context.metadata.get("classification", {})
        
        # 简单质量检查
        checklist = [
            {
                "item": "解决方案不为空",
                "passed": bool(solution.get("resolution")),
                "detail": "检查解决方案是否为空"
            },
            {
                "item": "有客户通知",
                "passed": bool(solution.get("customer_notification")),
                "detail": "检查是否有客户通知"
            },
            {
                "item": "操作记录完整",
                "passed": bool(solution.get("action_taken")),
                "detail": "检查操作记录"
            },
        ]
        
        # 计算通过项
        passed_items = sum(1 for item in checklist if item["passed"])
        quality_score = int(passed_items / len(checklist) * 100)
        
        # 判断是否通过
        passed = passed_items >= 2  # 至少2项通过
        
        result = {
            "passed": passed,
            "quality_score": quality_score,
            "reason": "审核通过" if passed else "审核不通过，请改进解决方案",
            "checklist": checklist,
            "improvement_suggestions": [] if passed else ["请完善解决方案内容"],
            "reviewed_at": datetime.now().isoformat(),
        }
        
        return AgentOutput(
            success=passed,
            result=result,
            reasoning=result["reason"]
        )
