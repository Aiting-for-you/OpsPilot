"""
提示词模板模块单元测试
"""
import pytest

from opspilot.prompts.templates import (
    PromptTemplate,
    PromptRegistry,
    INTENT_AGENT_PROMPT,
    PLAN_AGENT_PROMPT,
    get_prompt,
    render_prompt,
)


class TestPromptTemplate:
    """提示词模板测试"""

    def test_create_template(self):
        """测试创建模板"""
        template = PromptTemplate(
            name="test",
            system_prompt="系统提示",
            user_prompt_template="用户提示: $input"
        )

        assert template.name == "test"
        assert template.version == "1.0"

    def test_render(self):
        """测试渲染"""
        template = PromptTemplate(
            name="test",
            system_prompt="系统提示",
            user_prompt_template="输入: $input, 类型: $type"
        )

        result = template.render(input="测试", type="示例")

        assert "测试" in result
        assert "示例" in result

    def test_render_missing_var(self):
        """测试缺少变量时安全处理"""
        template = PromptTemplate(
            name="test",
            system_prompt="",
            user_prompt_template="输入: $input, 类型: $type"
        )

        result = template.render(input="测试")

        assert "测试" in result
        assert "$type" in result  # 未替换

    def test_to_dict(self):
        """测试转换为字典"""
        template = PromptTemplate(
            name="test",
            system_prompt="系统提示",
            user_prompt_template="用户提示",
            description="测试模板"
        )

        data = template.to_dict()

        assert data["name"] == "test"
        assert data["description"] == "测试模板"


class TestPromptRegistry:
    """提示词注册表测试"""

    @pytest.fixture
    def registry(self):
        reg = PromptRegistry()
        reg.clear()
        return reg

    def test_singleton(self):
        """测试单例模式"""
        reg1 = PromptRegistry()
        reg2 = PromptRegistry()

        assert reg1 is reg2

    def test_register(self, registry):
        """测试注册"""
        template = PromptTemplate(
            name="custom",
            system_prompt="",
            user_prompt_template=""
        )
        registry.register(template)

        assert registry.get("custom") is template

    def test_unregister(self, registry):
        """测试注销"""
        template = PromptTemplate(
            name="to_remove",
            system_prompt="",
            user_prompt_template=""
        )
        registry.register(template)
        registry.unregister("to_remove")

        assert registry.get("to_remove") is None

    def test_list_all(self, registry):
        """测试列出所有"""
        names = registry.list_all()

        assert "intent_recognition" in names

    def test_default_templates_loaded(self, registry):
        """测试默认模板已加载"""
        assert registry.get("intent_recognition") is not None
        assert registry.get("planning") is not None
        assert registry.get("execution") is not None
        assert registry.get("verification") is not None


class TestBuiltinPrompts:
    """内置提示词测试"""

    def test_intent_agent_prompt(self):
        """测试意图识别提示词"""
        assert INTENT_AGENT_PROMPT.name == "intent_recognition"
        assert "意图识别" in INTENT_AGENT_PROMPT.system_prompt
        assert "$user_input" in INTENT_AGENT_PROMPT.user_prompt_template

    def test_plan_agent_prompt(self):
        """测试规划提示词"""
        assert PLAN_AGENT_PROMPT.name == "planning"
        assert "$intent_type" in PLAN_AGENT_PROMPT.user_prompt_template

    def test_intent_prompt_render(self):
        """测试意图提示词渲染"""
        result = render_prompt(
            "intent_recognition",
            user_input="帮我创建订单"
        )

        assert "帮我创建订单" in result
        assert "JSON" in result


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_get_prompt(self):
        """测试获取提示词"""
        template = get_prompt("intent_recognition")

        assert template is not None
        assert template.name == "intent_recognition"

    def test_get_prompt_not_found(self):
        """测试获取不存在的提示词"""
        template = get_prompt("nonexistent")

        assert template is None

    def test_render_prompt(self):
        """测试渲染提示词"""
        result = render_prompt(
            "planning",
            user_input="测试",
            intent_type="create_order",
            entities="{}",
            intent_summary="测试摘要",
            knowledge_context=""
        )

        assert "测试" in result
        assert "create_order" in result

    def test_render_prompt_not_found(self):
        """测试渲染不存在的提示词"""
        result = render_prompt("nonexistent", input="test")

        assert result == ""

