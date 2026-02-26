"""
链式执行模块

按文档要求，使用 LangChain LCEL 实现确定性逻辑链条。

文档原文：
- "确定性逻辑：固定流程的 Chain 执行"
- "LangChain 负责：确定性逻辑链条执行"

职责：
- RAG 检索链
- 工具调用链
- 决策验证链
- 自定义工作流链
"""

from opspilot.chains.executor import (
    OpsChainExecutor,
    RAGChain,
    ToolChain,
    DecisionChain,
    create_rag_chain,
    create_tool_chain,
    create_decision_chain,
)

from opspilot.chains.prompts import (
    SYSTEM_PROMPT,
    RAG_PROMPT,
    TOOL_SELECTION_PROMPT,
    VERIFICATION_PROMPT,
)

__all__ = [
    # 链执行器
    "OpsChainExecutor",
    "RAGChain",
    "ToolChain",
    "DecisionChain",
    # 便捷函数
    "create_rag_chain",
    "create_tool_chain",
    "create_decision_chain",
    # 提示模板
    "SYSTEM_PROMPT",
    "RAG_PROMPT",
    "TOOL_SELECTION_PROMPT",
    "VERIFICATION_PROMPT",
]

