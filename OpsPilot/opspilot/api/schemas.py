"""
API Schema 定义

职责：
- 定义请求/响应模型
- 参数验证
- API 文档
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


# ==================== 通用模型 ====================

class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: str = "操作成功"
    error_code: Optional[str] = None


# ==================== 任务相关 ====================

class TaskCreateRequest(BaseModel):
    """创建任务请求"""
    user_input: str = Field(..., description="用户输入", min_length=1, max_length=2000)
    context: Optional[Dict[str, Any]] = Field(default=None, description="额外上下文")

    class Config:
        json_schema_extra = {
            "example": {
                "user_input": "帮我查询华南地区的供应商",
                "context": {"user_id": "user-001"}
            }
        }


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"


class TaskCreateResponse(BaseResponse):
    """创建任务响应"""
    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="任务状态")


class TaskStatusResponse(BaseResponse):
    """任务状态响应"""
    task_id: str
    state: str = Field(..., description="当前状态机状态")
    intent: Optional[str] = Field(default=None, description="识别的意图")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class TaskResultResponse(BaseResponse):
    """任务结果响应"""
    task_id: str
    state: str
    result: Optional[Dict[str, Any]] = Field(default=None, description="执行结果")
    execution_trace: Optional[List[Dict[str, Any]]] = Field(default=None, description="执行轨迹")


# ==================== 工具相关 ====================

class ToolCallRequest(BaseModel):
    """工具调用请求"""
    tool_name: str = Field(..., description="工具名称")
    params: Dict[str, Any] = Field(default_factory=dict, description="工具参数")
    task_id: Optional[str] = Field(default=None, description="关联任务ID")

    class Config:
        json_schema_extra = {
            "example": {
                "tool_name": "query_supplier",
                "params": {"region": "华南"},
                "task_id": "task-001"
            }
        }


class ToolCallResponse(BaseResponse):
    """工具调用响应"""
    tool_name: str
    result: Optional[Dict[str, Any]] = Field(default=None, description="执行结果")
    latency_ms: int = Field(default=0, description="执行耗时（毫秒）")
    fallback_mode: Optional[str] = Field(default=None, description="降级模式")


class ToolSchemaResponse(BaseResponse):
    """工具 Schema 响应"""
    tools: List[Dict[str, Any]] = Field(default_factory=list, description="工具列表")


# ==================== 记忆相关 ====================

class MemoryStoreRequest(BaseModel):
    """存储记忆请求"""
    content: str = Field(..., description="记忆内容", min_length=1)
    memory_type: str = Field(default="short_term", description="记忆类型")
    task_id: Optional[str] = Field(default=None, description="关联任务ID")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class MemorySearchRequest(BaseModel):
    """搜索记忆请求"""
    query: str = Field(..., description="搜索查询", min_length=1)
    memory_type: Optional[str] = Field(default=None, description="记忆类型过滤")
    limit: int = Field(default=10, ge=1, le=100, description="返回数量限制")


class MemorySearchResponse(BaseResponse):
    """搜索记忆响应"""
    results: List[Dict[str, Any]] = Field(default_factory=list, description="搜索结果")
    total: int = Field(default=0, description="结果总数")


# ==================== SOP 相关 ====================

class SOPExecuteRequest(BaseModel):
    """执行 SOP 请求"""
    sop_name: str = Field(..., description="SOP 名称")
    variables: Dict[str, Any] = Field(default_factory=dict, description="变量")

    class Config:
        json_schema_extra = {
            "example": {
                "sop_name": "create_order",
                "variables": {
                    "region": "华南",
                    "sku": "SKU001",
                    "amount": 5000
                }
            }
        }


class SOPExecuteResponse(BaseResponse):
    """执行 SOP 响应"""
    sop_name: str
    steps_executed: int = Field(default=0, description="已执行步骤数")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="步骤结果")


# ==================== 知识库相关 ====================

class KnowledgeQueryRequest(BaseModel):
    """查询知识库请求"""
    query: str = Field(..., description="查询内容", min_length=1)
    category: Optional[str] = Field(default=None, description="类别过滤")
    limit: int = Field(default=5, ge=1, le=20, description="返回数量限制")


class KnowledgeQueryResponse(BaseResponse):
    """查询知识库响应"""
    results: List[Dict[str, Any]] = Field(default_factory=list, description="查询结果")


# ==================== 健康检查 ====================

class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str = "healthy"
    version: str = "0.1.0"
    components: Dict[str, bool] = Field(
        default_factory=lambda: {
            "state_machine": True,
            "memory": True,
            "tools": True,
            "agents": True
        }
    )


# ==================== LLM 配置相关 ====================

class LLMProviderEnum(str, Enum):
    """LLM 提供商枚举"""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    CLAUDE = "claude"
    QWEN = "qwen"
    ERNIE = "ernie"
    ZHIPU = "zhipu"
    DEEPSEEK = "deepseek"
    CUSTOM = "custom"


class LLMProviderConfigRequest(BaseModel):
    """LLM 提供商配置请求"""
    provider: LLMProviderEnum = Field(..., description="提供商类型")
    api_key: str = Field(..., description="API Key")
    api_base: Optional[str] = Field(default=None, description="API 基础 URL")
    model_name: Optional[str] = Field(default=None, description="模型名称")
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2, description="温度参数")
    max_tokens: Optional[int] = Field(default=4096, ge=1, description="最大 Token 数")
    top_p: Optional[float] = Field(default=1.0, ge=0, le=1, description="Top-p 参数")
    is_enabled: Optional[bool] = Field(default=True, description="是否启用")
    is_default: Optional[bool] = Field(default=False, description="是否设为默认")
    available_models: Optional[List[str]] = Field(default=None, description="可用模型列表（自定义提供商）")

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "openai",
                "api_key": "sk-xxxxx",
                "model_name": "gpt-4o",
                "temperature": 0.7,
                "max_tokens": 4096,
                "is_enabled": True,
                "is_default": True
            }
        }


class LLMProviderConfigResponse(BaseModel):
    """LLM 提供商配置响应"""
    provider: str = Field(..., description="提供商类型")
    name: str = Field(..., description="显示名称")
    api_key_masked: Optional[str] = Field(default=None, description="脱敏后的 API Key")
    api_base: str = Field(..., description="API 基础 URL")
    model_name: str = Field(..., description="当前模型")
    default_model: str = Field(..., description="默认模型")
    available_models: List[str] = Field(default_factory=list, description="可用模型列表")
    temperature: float = Field(..., description="温度参数")
    max_tokens: int = Field(..., description="最大 Token 数")
    top_p: float = Field(..., description="Top-p 参数")
    is_enabled: bool = Field(..., description="是否启用")
    is_default: bool = Field(..., description="是否为默认")
    last_used: Optional[str] = Field(default=None, description="最后使用时间")


class LLMConfigListResponse(BaseModel):
    """LLM 配置列表响应"""
    success: bool = True
    providers: List[LLMProviderConfigResponse] = Field(default_factory=list, description="提供商列表")
    default_provider: Optional[str] = Field(default=None, description="默认提供商")


class LLMTestConnectionResponse(BaseModel):
    """LLM 连接测试响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="结果消息")
    latency_ms: Optional[int] = Field(default=None, description="延迟毫秒")


class FetchModelsRequest(BaseModel):
    """获取模型列表请求"""
    api_base: str = Field(..., description="API 基础 URL")
    api_key: str = Field(..., description="API Key")
    provider_type: str = Field(default="openai", description="提供商类型")

    class Config:
        json_schema_extra = {
            "example": {
                "api_base": "https://api.openai.com/v1",
                "api_key": "sk-xxxxx",
                "provider_type": "openai"
            }
        }


class ModelInfo(BaseModel):
    """模型信息"""
    id: str = Field(..., description="模型 ID")
    name: Optional[str] = Field(default=None, description="模型名称")
    owned_by: Optional[str] = Field(default=None, description="所有者")
    object: Optional[str] = Field(default=None, description="对象类型")


class FetchModelsResponse(BaseModel):
    """获取模型列表响应"""
    success: bool = Field(..., description="是否成功")
    models: List[ModelInfo] = Field(default_factory=list, description="模型列表")
    error: Optional[str] = Field(default=None, description="错误信息")


class BatchAddModelsRequest(BaseModel):
    """批量添加模型请求"""
    provider: LLMProviderEnum = Field(..., description="提供商类型")
    api_key: str = Field(..., description="API Key")
    api_base: str = Field(..., description="API 基础 URL")
    models: List[str] = Field(..., description="模型名称列表")
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2, description="温度参数")
    max_tokens: Optional[int] = Field(default=4096, ge=1, description="最大 Token 数")
    set_default: Optional[str] = Field(default=None, description="设置为默认的模型名称")

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "custom",
                "api_key": "sk-xxxxx",
                "api_base": "https://api.example.com/v1",
                "models": ["gpt-4", "gpt-3.5-turbo", "claude-3"],
                "set_default": "gpt-4"
            }
        }


class BatchAddModelsResponse(BaseModel):
    """批量添加模型响应"""
    success: bool = Field(..., description="是否成功")
    added_count: int = Field(default=0, description="添加的模型数量")
    default_model: Optional[str] = Field(default=None, description="默认模型")
    error: Optional[str] = Field(default=None, description="错误信息")


# ==================== 错误响应 ====================

class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error_code": "TASK_NOT_FOUND",
                "error_message": "任务不存在",
                "details": {"task_id": "nonexistent"}
            }
        }

