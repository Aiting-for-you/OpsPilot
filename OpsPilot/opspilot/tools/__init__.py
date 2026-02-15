"""
工具模块

按文档要求，使用 LangChain 负责工具封装和 RAG 检索：
- MCP 作为工具协议标准
- LangChain Tool 接口封装
- LangChain Embeddings 用于工具向量化

包含:
- base: 工具基类、路由器、Schema定义
- mcp: MCP Server 实现（ERP、合规等）
- internal: 内部工具（格式化、计算等）
- indexer: 工具索引器（ToolRAG）
- retriever: 工具检索器
- compressor: 工具描述压缩器
- context_manager: 上下文管理器
- healing: 工具自愈机制（创新保留）
- langchain_tools: LangChain 工具适配器（新增）
- embeddings: LangChain Embeddings 适配器（新增）
"""

from opspilot.tools.base import (
    ToolStatus,
    FallbackMode,
    ToolSchema,
    ToolResult,
    ToolContext,
    BaseToolServer,
    ToolRouter,
)

from opspilot.tools.mcp import (
    ERPServer,
    ComplianceServer,
    create_default_router,
)

from opspilot.tools.internal import InternalToolsServer

# 工具调用优化模块
from opspilot.tools.indexer import (
    ToolCategory,
    ToolEmbedding,
    ToolIndex,
    ToolIndexer,
    SimpleTokenizer,
    create_tool_index,
)

from opspilot.tools.retriever import (
    RetrievalStrategy,
    RetrievalResult,
    ToolRetriever,
    ToolContextBudget,
    retrieve_tools,
)

from opspilot.tools.compressor import (
    CompressionLevel,
    CompressedTool,
    ToolCompressor,
    TokenEstimator,
    compress_tools,
    get_compression_stats,
)

from opspilot.tools.context_manager import (
    ToolSelectionResult,
    ToolContextManager,
    DynamicToolLoader,
    create_context_manager,
)

from opspilot.tools.healing import (
    ErrorType,
    RecoveryStrategy,
    ErrorDiagnosis,
    ErrorDiagnoser,
    ToolHealer,
    ToolUnrecoverableError,
    ToolMaxRetriesExceededError,
    create_healer,
)

# LangChain 工具适配 - 按文档要求
try:
    from opspilot.tools.langchain_tools import (
        MCPToolWrapper,
        OpsToolRegistry,
        create_langchain_tool,
        convert_tools_to_langchain,
        LANGCHAIN_AVAILABLE,
    )
except ImportError:
    LANGCHAIN_AVAILABLE = False
    MCPToolWrapper = None
    OpsToolRegistry = None
    create_langchain_tool = None
    convert_tools_to_langchain = None

# LangChain Embeddings 适配
try:
    from opspilot.tools.embeddings import (
        ToolEmbeddingsManager,
        create_embeddings_manager,
        LANGCHAIN_EMBEDDINGS_AVAILABLE,
    )
except ImportError:
    LANGCHAIN_EMBEDDINGS_AVAILABLE = False
    ToolEmbeddingsManager = None
    create_embeddings_manager = None

__all__ = [
    # 基础类
    "ToolStatus",
    "FallbackMode",
    "ToolSchema",
    "ToolResult",
    "ToolContext",
    "BaseToolServer",
    "ToolRouter",
    # MCP Server
    "ERPServer",
    "ComplianceServer",
    "create_default_router",
    # 内部工具
    "InternalToolsServer",
    # 工具索引
    "ToolCategory",
    "ToolEmbedding",
    "ToolIndex",
    "ToolIndexer",
    "SimpleTokenizer",
    "create_tool_index",
    # 工具检索
    "RetrievalStrategy",
    "RetrievalResult",
    "ToolRetriever",
    "ToolContextBudget",
    "retrieve_tools",
    # 工具压缩
    "CompressionLevel",
    "CompressedTool",
    "ToolCompressor",
    "TokenEstimator",
    "compress_tools",
    "get_compression_stats",
    # 上下文管理
    "ToolSelectionResult",
    "ToolContextManager",
    "DynamicToolLoader",
    "create_context_manager",
    # 自愈机制
    "ErrorType",
    "RecoveryStrategy",
    "ErrorDiagnosis",
    "ErrorDiagnoser",
    "ToolHealer",
    "ToolUnrecoverableError",
    "ToolMaxRetriesExceededError",
    "create_healer",
    # LangChain 工具适配
    "MCPToolWrapper",
    "OpsToolRegistry",
    "create_langchain_tool",
    "convert_tools_to_langchain",
    "LANGCHAIN_AVAILABLE",
    # LangChain Embeddings
    "ToolEmbeddingsManager",
    "create_embeddings_manager",
    "LANGCHAIN_EMBEDDINGS_AVAILABLE",
]

