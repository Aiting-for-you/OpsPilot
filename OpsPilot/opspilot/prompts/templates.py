"""
提示词模板模块

职责：
- 存储各 Agent 的提示词模板
- 支持变量替换
- 版本管理
"""
from typing import Dict, Any, Optional
from string import Template
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PromptTemplate:
    """提示词模板"""
    name: str
    system_prompt: str
    user_prompt_template: str
    version: str = "1.0"
    description: str = ""
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def render(self, **kwargs) -> str:
        """
        渲染提示词

        Args:
            **kwargs: 变量替换参数

        Returns:
            str: 渲染后的提示词
        """
        template = Template(self.user_prompt_template)
        return template.safe_substitute(kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "system_prompt": self.system_prompt,
            "user_prompt_template": self.user_prompt_template,
            "version": self.version,
            "description": self.description,
        }


# ==================== 内置提示词模板 ====================

INTENT_AGENT_PROMPT = PromptTemplate(
    name="intent_recognition",
    version="1.0",
    description="意图识别Agent提示词",
    system_prompt="""你是一个专业的意图识别助手。
你的任务是分析用户的自然语言输入，识别其业务意图并提取关键实体。

你需要准确识别以下意图类型：
- create_order: 创建采购订单
- query_supplier: 查询供应商信息
- query_inventory: 查询产品库存
- query_order: 查询订单状态
- update_order: 更新订单（如审批、取消等）
- check_compliance: 合规检查
- query_policy: 查询政策规定
- unknown: 无法识别的意图

请始终保持客观、准确。如果无法确定意图，请返回 unknown。""",
    user_prompt_template="""请分析以下用户输入，识别用户意图并提取关键实体。

用户输入：$user_input

请以 JSON 格式返回以下信息：
{
    "intent_type": "意图类型",
    "confidence": "置信度（0.0-1.0）",
    "entities": {
        "supplier_name": "供应商名称（如有）",
        "product_name": "产品名称（如有）",
        "region": "区域（如有）",
        "order_id": "订单号（如有）",
        "amount": "金额（如有）"
    },
    "summary": "用户意图的简要描述"
}

仅返回 JSON，不要有其他内容。"""
)

PLAN_AGENT_PROMPT = PromptTemplate(
    name="planning",
    version="1.0",
    description="规划Agent提示词",
    system_prompt="""你是一个专业的任务规划助手。
你的任务是根据用户的意图制定详细的执行计划。

你需要：
1. 理解用户的业务意图
2. 确定需要调用的工具和参数
3. 识别需要审批的环节
4. 评估潜在风险
5. 给出合理的执行顺序

可用的工具包括：
- query_supplier: 查询供应商
- create_order: 创建订单
- query_inventory: 查询库存
- query_order: 查询订单
- update_order_status: 更新订单状态
- check_compliance: 合规检查
- query_policy: 查询政策

请确保计划清晰、可执行。""",
    user_prompt_template="""请根据以下信息制定执行计划。

用户输入：$user_input
识别意图：$intent_type
提取实体：$entities
用户意图摘要：$intent_summary

$knowledge_context

请以 JSON 格式返回执行计划：
{
    "plan_summary": "计划摘要",
    "steps": [
        {
            "step_id": 1,
            "action": "动作描述",
            "tool": "工具名称",
            "params": {},
            "expected_output": "预期输出"
        }
    ],
    "required_approvals": ["需要审批的项"],
    "risks": ["潜在风险"],
    "estimated_time": "预计耗时（秒）"
}

仅返回 JSON，不要有其他内容。"""
)

EXEC_AGENT_PROMPT = PromptTemplate(
    name="execution",
    version="1.0",
    description="执行Agent提示词",
    system_prompt="""你是一个专业的执行助手。
你的任务是按照计划调用工具执行具体操作。

你需要：
1. 按顺序执行每个步骤
2. 正确传递参数
3. 处理执行结果
4. 记录执行轨迹

如果执行失败，请分析原因并报告。""",
    user_prompt_template="""请执行以下计划步骤。

计划摘要：$plan_summary

当前步骤：
- 步骤ID: $step_id
- 动作: $action
- 工具: $tool
- 参数: $params

之前步骤的结果：
$previous_results

请执行并返回结果。"""
)

VERIFY_AGENT_PROMPT = PromptTemplate(
    name="verification",
    version="1.0",
    description="验证Agent提示词",
    system_prompt="""你是一个专业的验证助手。
你的任务是检查执行结果是否满足用户的原始意图。

你需要：
1. 检查所有步骤是否成功执行
2. 验证结果数据是否完整
3. 确认是否满足用户意图
4. 给出改进建议（如有）

请保持客观、严谨。""",
    user_prompt_template="""请验证以下执行结果是否满足用户意图。

用户意图：$intent_type
意图摘要：$intent_summary

执行计划：
$plan_summary

执行结果：
$execution_results

请以 JSON 格式返回验证结果：
{
    "passed": true/false,
    "reason": "验证通过/失败的原因",
    "checklist": [
        {
            "item": "检查项",
            "passed": true/false,
            "detail": "详情"
        }
    ],
    "summary": "执行结果摘要",
    "recommendations": ["改进建议"]
}

仅返回 JSON，不要有其他内容。"""
)


class PromptRegistry:
    """
    提示词注册表

    管理所有提示词模板
    """

    _instance: Optional["PromptRegistry"] = None

    def __new__(cls) -> "PromptRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._templates: Dict[str, PromptTemplate] = {}
            cls._instance._load_defaults()
        return cls._instance

    def _load_defaults(self):
        """加载默认模板"""
        self.register(INTENT_AGENT_PROMPT)
        self.register(PLAN_AGENT_PROMPT)
        self.register(EXEC_AGENT_PROMPT)
        self.register(VERIFY_AGENT_PROMPT)

    def register(self, template: PromptTemplate) -> None:
        """注册模板"""
        self._templates[template.name] = template

    def unregister(self, name: str) -> None:
        """注销模板"""
        self._templates.pop(name, None)

    def get(self, name: str) -> Optional[PromptTemplate]:
        """获取模板"""
        return self._templates.get(name)

    def list_all(self) -> Dict[str, str]:
        """列出所有模板名称和描述"""
        return {name: t.description for name, t in self._templates.items()}

    def clear(self) -> None:
        """清空注册表"""
        self._templates.clear()
        self._load_defaults()


def get_prompt(name: str) -> Optional[PromptTemplate]:
    """获取提示词模板"""
    return PromptRegistry().get(name)


def render_prompt(name: str, **kwargs) -> str:
    """渲染提示词"""
    template = get_prompt(name)
    if template:
        return template.render(**kwargs)
    return ""

