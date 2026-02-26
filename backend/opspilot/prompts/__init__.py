"""
提示词模块

包含:
- templates: 提示词模板定义
- loader: 提示词加载器
"""

from opspilot.prompts.templates import (
    PromptTemplate,
    PromptRegistry,
    INTENT_AGENT_PROMPT,
    PLAN_AGENT_PROMPT,
    EXEC_AGENT_PROMPT,
    VERIFY_AGENT_PROMPT,
    get_prompt,
    render_prompt,
)

from opspilot.prompts.loader import PromptLoader

__all__ = [
    "PromptTemplate",
    "PromptRegistry",
    "INTENT_AGENT_PROMPT",
    "PLAN_AGENT_PROMPT",
    "EXEC_AGENT_PROMPT",
    "VERIFY_AGENT_PROMPT",
    "get_prompt",
    "render_prompt",
    "PromptLoader",
]

