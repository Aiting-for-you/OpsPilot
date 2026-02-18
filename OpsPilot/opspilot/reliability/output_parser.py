"""
结构化输出解析模块

使用 LangChain 的 PydanticOutputParser 实现严格的输出格式校验。

特性：
- 自动生成格式说明
- Pydantic 校验
- 重试机制
- 预定义输出模型
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel, Field, field_validator

# LangChain imports
try:
    from langchain_core.output_parsers import PydanticOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.exceptions import OutputParserException
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    PydanticOutputParser = None
    ChatPromptTemplate = None
    OutputParserException = Exception

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


# ============================================================================
# 预定义输出模型
# ============================================================================

class IntentOutput(BaseModel):
    """意图识别输出"""
    intent_type: str = Field(description="意图类型：query, order, alert, analysis, other")
    confidence: float = Field(description="置信度 0-1", ge=0, le=1)
    entities: Dict[str, Any] = Field(default_factory=dict, description="提取的实体")
    suggested_action: str = Field(default="", description="建议的操作")
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not 0 <= v <= 1:
            raise ValueError('置信度必须在 0-1 之间')
        return v
    
    @field_validator('intent_type')
    @classmethod
    def validate_intent_type(cls, v: str) -> str:
        valid_types = {'query', 'order', 'alert', 'analysis', 'other'}
        if v not in valid_types:
            raise ValueError(f'意图类型必须是: {valid_types}')
        return v


class PlanStep(BaseModel):
    """执行步骤"""
    step_id: int = Field(description="步骤序号")
    action: str = Field(description="动作描述")
    tool: str = Field(description="使用的工具名称")
    params: Dict[str, Any] = Field(default_factory=dict, description="参数")
    dependencies: List[int] = Field(default_factory=list, description="依赖的步骤ID")


class PlanOutput(BaseModel):
    """执行计划输出"""
    plan_id: str = Field(description="计划ID")
    description: str = Field(description="计划描述")
    steps: List[PlanStep] = Field(description="执行步骤列表")
    estimated_time: float = Field(default=0.0, description="预估执行时间（秒）")
    risk_level: str = Field(default="low", description="风险等级：low, medium, high")
    
    @field_validator('risk_level')
    @classmethod
    def validate_risk_level(cls, v: str) -> str:
        valid_levels = {'low', 'medium', 'high'}
        if v not in valid_levels:
            raise ValueError(f'风险等级必须是: {valid_levels}')
        return v


class ToolResult(BaseModel):
    """工具执行结果"""
    tool_name: str = Field(description="工具名称")
    success: bool = Field(description="是否成功")
    data: Dict[str, Any] = Field(default_factory=dict, description="返回数据")
    error: Optional[str] = Field(default=None, description="错误信息")


class ExecutionOutput(BaseModel):
    """执行输出"""
    execution_id: str = Field(description="执行ID")
    status: str = Field(description="状态：pending, running, completed, failed")
    results: List[ToolResult] = Field(default_factory=list, description="工具执行结果")
    total_steps: int = Field(default=0, description="总步骤数")
    completed_steps: int = Field(default=0, description="已完成步骤数")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = {'pending', 'running', 'completed', 'failed'}
        if v not in valid_statuses:
            raise ValueError(f'状态必须是: {valid_statuses}')
        return v


class VerificationOutput(BaseModel):
    """验证输出"""
    is_valid: bool = Field(description="结果是否有效")
    score: float = Field(description="质量评分 0-1", ge=0, le=1)
    issues: List[str] = Field(default_factory=list, description="发现的问题")
    suggestions: List[str] = Field(default_factory=list, description="改进建议")
    
    @field_validator('score')
    @classmethod
    def validate_score(cls, v: float) -> float:
        if not 0 <= v <= 1:
            raise ValueError('评分必须在 0-1 之间')
        return v


# ============================================================================
# 结构化输出解析器
# ============================================================================

class StructuredOutputParser:
    """
    结构化输出解析器
    
    整合 Pydantic 校验和重试机制。
    
    示例:
        >>> parser = StructuredOutputParser(IntentOutput)
        >>> 
        >>> # 获取格式说明
        >>> format_instructions = parser.get_format_instructions()
        >>> 
        >>> # 解析输出
        >>> result = await parser.parse(llm_output)
        >>> print(result.intent_type)
    """
    
    def __init__(
        self,
        output_model: Type[BaseModel],
        max_retries: int = 2,
    ):
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain 未安装")
        
        self._output_model = output_model
        self._max_retries = max_retries
        self._parser = PydanticOutputParser(pydantic_object=output_model)
        
        # 统计
        self._stats = {
            "total_parses": 0,
            "successful_parses": 0,
            "failed_parses": 0,
            "retries": 0,
        }
    
    def get_format_instructions(self) -> str:
        """获取格式说明，用于注入到 Prompt"""
        return self._parser.get_format_instructions()
    
    def get_prompt_template(
        self,
        system_prompt: str,
        human_template: str = "{input}",
    ) -> ChatPromptTemplate:
        """
        获取带格式说明的 Prompt 模板
        
        Args:
            system_prompt: 系统提示
            human_template: 用户输入模板
        
        Returns:
            ChatPromptTemplate
        """
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt + "\n\n{format_instructions}"),
            ("human", human_template),
        ]).partial(format_instructions=self.get_format_instructions())
    
    def parse(self, output: str) -> BaseModel:
        """
        解析输出
        
        Args:
            output: LLM 输出字符串
        
        Returns:
            BaseModel: 解析后的模型实例
        
        Raises:
            OutputParserException: 解析失败
        """
        self._stats["total_parses"] += 1
        
        try:
            result = self._parser.parse(output)
            self._stats["successful_parses"] += 1
            return result
            
        except Exception as e:
            self._stats["failed_parses"] += 1
            logger.error(f"Output parsing failed: {e}")
            raise OutputParserException(f"Failed to parse output: {e}")
    
    def parse_with_retry(
        self,
        output: str,
        llm_callable: Optional[callable] = None,
    ) -> BaseModel:
        """
        带重试的解析
        
        如果解析失败，尝试让 LLM 修正输出
        
        Args:
            output: LLM 输出
            llm_callable: 用于修正的 LLM 调用函数
        
        Returns:
            BaseModel: 解析后的模型实例
        """
        for attempt in range(self._max_retries + 1):
            try:
                return self.parse(output)
            except OutputParserException as e:
                if attempt == self._max_retries:
                    raise
                
                self._stats["retries"] += 1
                
                # 尝试让 LLM 修正
                if llm_callable:
                    fix_prompt = f"""
                    以下输出格式不正确，请修正为正确的 JSON 格式：
                    
                    原始输出：
                    {output}
                    
                    错误信息：
                    {str(e)}
                    
                    要求格式：
                    {self.get_format_instructions()}
                    
                    请只输出修正后的 JSON，不要包含其他内容。
                    """
                    output = llm_callable(fix_prompt)
        
        # 不应该到达这里
        raise OutputParserException("Max retries exceeded")
    
    async def aparse(self, output: str) -> BaseModel:
        """异步解析"""
        return self.parse(output)
    
    async def aparse_with_retry(
        self,
        output: str,
        llm_callable: Optional[callable] = None,
    ) -> BaseModel:
        """异步带重试解析"""
        return self.parse_with_retry(output, llm_callable)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        return {
            **self._stats,
            "success_rate": (
                self._stats["successful_parses"] / self._stats["total_parses"]
                if self._stats["total_parses"] > 0 else 0
            ),
        }


# ============================================================================
# 工厂函数
# ============================================================================

def create_output_parser(
    output_model: Type[BaseModel],
    max_retries: int = 2,
) -> StructuredOutputParser:
    """
    创建输出解析器
    
    Args:
        output_model: 输出模型类
        max_retries: 最大重试次数
    
    Returns:
        StructuredOutputParser 实例
    """
    return StructuredOutputParser(output_model, max_retries)


# 预创建的解析器
_intent_parser: Optional[StructuredOutputParser] = None
_plan_parser: Optional[StructuredOutputParser] = None
_execution_parser: Optional[StructuredOutputParser] = None
_verification_parser: Optional[StructuredOutputParser] = None


def get_intent_parser() -> StructuredOutputParser:
    """获取意图解析器"""
    global _intent_parser
    if _intent_parser is None:
        _intent_parser = StructuredOutputParser(IntentOutput)
    return _intent_parser


def get_plan_parser() -> StructuredOutputParser:
    """获取计划解析器"""
    global _plan_parser
    if _plan_parser is None:
        _plan_parser = StructuredOutputParser(PlanOutput)
    return _plan_parser


def get_execution_parser() -> StructuredOutputParser:
    """获取执行解析器"""
    global _execution_parser
    if _execution_parser is None:
        _execution_parser = StructuredOutputParser(ExecutionOutput)
    return _execution_parser


def get_verification_parser() -> StructuredOutputParser:
    """获取验证解析器"""
    global _verification_parser
    if _verification_parser is None:
        _verification_parser = StructuredOutputParser(VerificationOutput)
    return _verification_parser
