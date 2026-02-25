"""
可靠性模块

整合 LangChain 和 AgentScope 的可靠性特性：
- with_retry: 自动重试机制（LangChain）
- with_fallbacks: 多模型降级（LangChain）
- get_openai_callback: Token 追踪（LangChain）
- PydanticOutputParser: 结构化输出（LangChain）
- ParallelToolExecutor: 并行工具执行（AgentScope + asyncio）

职责：
- LLM 调用的可靠性保证
- Token 使用追踪和成本控制
- 输出格式规范化
- 工具并行执行优化
"""

from opspilot.reliability.llm_reliability import (
    ReliableLLMChain,
    FallbackConfig,
    RetryConfig,
    FallbackStrategy,
    create_reliable_chain,
    with_retry,
    with_fallbacks,
)

from opspilot.reliability.token_tracker import (
    TokenTracker,
    TokenUsage,
    TokenBudgetExceeded,
    get_token_tracker,
    track_tokens,
)

from opspilot.reliability.output_parser import (
    StructuredOutputParser,
    IntentOutput,
    PlanOutput,
    PlanStep,
    ExecutionOutput,
    VerificationOutput,
    ToolResult as OutputToolResult,
    create_output_parser,
    get_intent_parser,
    get_plan_parser,
    get_execution_parser,
    get_verification_parser,
)

from opspilot.reliability.parallel_executor import (
    ParallelToolExecutor,
    ToolCall,
    ToolResult,
    ExecutionStatus,
    ParallelExecutionResult,
    execute_tools_parallel,
)

__all__ = [
    # LLM 可靠性
    "ReliableLLMChain",
    "FallbackConfig",
    "RetryConfig",
    "FallbackStrategy",
    "create_reliable_chain",
    "with_retry",
    "with_fallbacks",
    # Token 追踪
    "TokenTracker",
    "TokenUsage",
    "TokenBudgetExceeded",
    "get_token_tracker",
    "track_tokens",
    # 输出解析
    "StructuredOutputParser",
    "IntentOutput",
    "PlanOutput",
    "PlanStep",
    "ExecutionOutput",
    "VerificationOutput",
    "OutputToolResult",
    "create_output_parser",
    "get_intent_parser",
    "get_plan_parser",
    "get_execution_parser",
    "get_verification_parser",
    # 并行执行
    "ParallelToolExecutor",
    "ToolCall",
    "ToolResult",
    "ExecutionStatus",
    "ParallelExecutionResult",
    "execute_tools_parallel",
]
