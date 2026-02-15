"""
API 模块

包含:
- schemas: 请求/响应模型定义
- routes: API 路由定义
- middleware: 中间件配置
"""

from opspilot.api.schemas import (
    BaseResponse,
    TaskCreateRequest,
    TaskCreateResponse,
    TaskStatus,
    TaskStatusResponse,
    TaskResultResponse,
    ToolCallRequest,
    ToolCallResponse,
    ToolSchemaResponse,
    MemoryStoreRequest,
    MemorySearchRequest,
    MemorySearchResponse,
    SOPExecuteRequest,
    SOPExecuteResponse,
    KnowledgeQueryRequest,
    KnowledgeQueryResponse,
    HealthCheckResponse,
    ErrorResponse,
)

from opspilot.api.routes import (
    router,
    get_orchestrator,
    get_tool_router,
    get_memory,
    get_knowledge,
)

from opspilot.api.middleware import (
    RequestLoggingMiddleware,
    ErrorHandlerMiddleware,
    setup_cors,
    setup_middleware,
)

__all__ = [
    # Schemas
    "BaseResponse",
    "TaskCreateRequest",
    "TaskCreateResponse",
    "TaskStatus",
    "TaskStatusResponse",
    "TaskResultResponse",
    "ToolCallRequest",
    "ToolCallResponse",
    "ToolSchemaResponse",
    "MemoryStoreRequest",
    "MemorySearchRequest",
    "MemorySearchResponse",
    "SOPExecuteRequest",
    "SOPExecuteResponse",
    "KnowledgeQueryRequest",
    "KnowledgeQueryResponse",
    "HealthCheckResponse",
    "ErrorResponse",
    # Routes
    "router",
    "get_orchestrator",
    "get_tool_router",
    "get_memory",
    "get_knowledge",
    # Middleware
    "RequestLoggingMiddleware",
    "ErrorHandlerMiddleware",
    "setup_cors",
    "setup_middleware",
]

