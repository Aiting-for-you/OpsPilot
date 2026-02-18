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


# ==================== MCP Server 配置相关 ====================

class MCPServerStatus(str, Enum):
    """MCP Server 状态"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class MCPServerConfigRequest(BaseModel):
    """MCP Server 配置请求"""
    name: str = Field(..., description="Server 唯一标识", min_length=1, max_length=50)
    command: str = Field(..., description="启动命令，如 npx、python", min_length=1)
    args: List[str] = Field(default_factory=list, description="命令参数")
    env: Dict[str, str] = Field(default_factory=dict, description="环境变量")
    enabled: bool = Field(default=True, description="是否启用")
    auto_connect: bool = Field(default=False, description="是否自动连接")
    description: str = Field(default="", description="Server 描述")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "filesystem",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed"],
                "env": {},
                "enabled": True,
                "auto_connect": True,
                "description": "文件系统操作工具"
            }
        }


class MCPServerConfigResponse(BaseModel):
    """MCP Server 配置响应"""
    name: str = Field(..., description="Server 名称")
    command: str = Field(..., description="启动命令")
    args: List[str] = Field(default_factory=list, description="命令参数")
    enabled: bool = Field(..., description="是否启用")
    auto_connect: bool = Field(..., description="是否自动连接")
    description: str = Field(default="", description="Server 描述")
    status: MCPServerStatus = Field(..., description="连接状态")
    tool_count: int = Field(default=0, description="提供的工具数量")
    error_message: str = Field(default="", description="错误信息")
    connected_at: Optional[str] = Field(default=None, description="连接时间")


class MCPServerListResponse(BaseModel):
    """MCP Server 列表响应"""
    success: bool = True
    servers: List[MCPServerConfigResponse] = Field(default_factory=list, description="Server 列表")


class MCPServerToolResponse(BaseModel):
    """MCP Server 工具响应"""
    success: bool = True
    server_name: str = Field(..., description="Server 名称")
    tools: List[Dict[str, Any]] = Field(default_factory=list, description="工具列表")


class MCPToolCallRequest(BaseModel):
    """MCP 工具调用请求"""
    tool_name: str = Field(..., description="工具名称")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="工具参数")
    server_name: Optional[str] = Field(default=None, description="指定 Server（可选）")

    class Config:
        json_schema_extra = {
            "example": {
                "tool_name": "read_file",
                "arguments": {"path": "/tmp/test.txt"},
                "server_name": "filesystem"
            }
        }


class MCPToolCallResponse(BaseModel):
    """MCP 工具调用响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(default="", description="结果消息")
    tool_name: str = Field(..., description="工具名称")
    server_name: str = Field(..., description="执行的 Server")
    result: Optional[Any] = Field(default=None, description="执行结果")
    error: Optional[str] = Field(default=None, description="错误信息")


class MCPAllToolsResponse(BaseModel):
    """所有 MCP 工具列表响应"""
    success: bool = True
    tools: List[Dict[str, Any]] = Field(default_factory=list, description="所有工具列表")


# ==================== RBAC 权限相关 ====================

class RoleType(str, Enum):
    """角色类型"""
    JUNIOR_BUYER = "junior_buyer"
    SENIOR_BUYER = "senior_buyer"
    FINANCE_AUDITOR = "finance_auditor"
    SYSTEM_ADMIN = "system_admin"


class AssignRoleRequest(BaseModel):
    """分配角色请求"""
    user_id: str = Field(..., description="用户ID")
    role: RoleType = Field(..., description="角色类型")
    department: Optional[str] = Field(default=None, description="部门")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-001",
                "role": "senior_buyer",
                "department": "采购部"
            }
        }


class UserRoleResponse(BaseResponse):
    """用户角色响应"""
    user_id: str
    role: str
    department: Optional[str] = None
    assigned_at: str


class RolePermissionResponse(BaseModel):
    """角色权限响应"""
    role: str
    name: str
    description: str
    amount_limit: float
    permissions: List[str]
    sensitive_actions: List[str]
    can_approve_amount: float
    data_scope: str


class CheckPermissionRequest(BaseModel):
    """检查权限请求"""
    user_id: str = Field(..., description="用户ID")
    permission: str = Field(..., description="权限名称")


class CheckPermissionResponse(BaseResponse):
    """检查权限响应"""
    has_permission: bool


class CheckAmountRequest(BaseModel):
    """检查金额请求"""
    user_id: str = Field(..., description="用户ID")
    amount: float = Field(..., description="金额")


class CheckAmountResponse(BaseResponse):
    """检查金额响应"""
    within_limit: bool
    limit: float
    exceeded_amount: Optional[float] = None


# ==================== 审批工作流相关 ====================

class ApprovalType(str, Enum):
    """审批类型"""
    AMOUNT_EXCEEDED = "amount_exceeded"
    SENSITIVE_ACTION = "sensitive_action"
    PAYMENT = "payment"
    CONTRACT = "contract"
    ORDER_CANCEL = "order_cancel"


class CreateApprovalRequest(BaseModel):
    """创建审批请求"""
    user_id: str = Field(..., description="用户ID")
    approval_type: ApprovalType = Field(..., description="审批类型")
    title: str = Field(..., description="审批标题")
    description: str = Field(..., description="审批描述")
    data: Dict[str, Any] = Field(default_factory=dict, description="审批数据")
    expires_in_hours: Optional[int] = Field(default=None, description="过期时间（小时）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-001",
                "approval_type": "amount_exceeded",
                "title": "超额采购订单审批",
                "description": "采购金额 150,000 元，超过角色上限 100,000 元",
                "data": {
                    "order_id": "order-123",
                    "amount": 150000,
                    "supplier": "供应商A"
                },
                "expires_in_hours": 24
            }
        }


class ApprovalRequestResponse(BaseResponse):
    """审批请求响应"""
    request_id: str
    approval_type: str
    user_id: str
    user_role: str
    title: str
    description: str
    status: str
    created_at: str
    expires_at: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    approval_comment: Optional[str] = None


class ApproveRequest(BaseModel):
    """审批操作请求"""
    request_id: str = Field(..., description="审批请求ID")
    approver_id: str = Field(..., description="审批人ID")
    comment: Optional[str] = Field(default=None, description="审批意见")


class RejectRequest(BaseModel):
    """拒绝操作请求"""
    request_id: str = Field(..., description="审批请求ID")
    approver_id: str = Field(..., description="审批人ID")
    comment: Optional[str] = Field(default=None, description="拒绝原因")


class PendingApprovalsResponse(BaseResponse):
    """待审批列表响应"""
    requests: List[ApprovalRequestResponse]


class UserApprovalsResponse(BaseResponse):
    """用户发起的审批列表响应"""
    requests: List[ApprovalRequestResponse]


# ==================== 任务调度相关 ====================

class TaskPriority(str, Enum):
    """任务优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TaskType(str, Enum):
    """任务类型"""
    ONE_TIME = "one_time"
    SCHEDULED = "scheduled"
    RECURRING = "recurring"


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class CreateScheduledTaskRequest(BaseModel):
    """创建调度任务请求"""
    name: str = Field(..., description="任务名称")
    target: str = Field(..., description="目标函数名")
    args: List[Any] = Field(default_factory=list, description="位置参数")
    kwargs: Dict[str, Any] = Field(default_factory=dict, description="关键字参数")
    priority: TaskPriority = Field(default=TaskPriority.NORMAL, description="优先级")
    task_type: TaskType = Field(default=TaskType.ONE_TIME, description="任务类型")
    scheduled_time: Optional[str] = Field(default=None, description="定时执行时间（ISO格式）")
    interval: Optional[int] = Field(default=None, description="周期性任务间隔（秒）")
    max_retries: int = Field(default=3, description="最大重试次数")
    retry_interval: int = Field(default=60, description="重试间隔（秒）")
    tags: List[str] = Field(default_factory=list, description="标签")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "库存检查任务",
                "target": "check_inventory",
                "args": [],
                "kwargs": {"threshold": 100},
                "priority": "high",
                "task_type": "recurring",
                "interval": 3600,
                "max_retries": 3,
                "tags": ["inventory", "monitoring"]
            }
        }


class ScheduledTaskResponse(BaseResponse):
    """调度任务响应"""
    task_id: str
    name: str
    task_type: str
    priority: str
    status: str
    created_at: str
    scheduled_time: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    tags: List[str] = []


class ScheduledTaskListResponse(BaseResponse):
    """任务列表响应"""
    tasks: List[ScheduledTaskResponse]
    total: int


class SchedulerStatsResponse(BaseResponse):
    """调度器统计响应"""
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    cancelled_tasks: int
    running_tasks: int
    queued_tasks: int


# ==================== 数据分析相关 ====================

class TaskStatisticsResponse(BaseModel):
    """任务统计响应"""
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    cancelled_tasks: int
    pending_tasks: int
    running_tasks: int
    success_rate: float
    avg_execution_time: float
    tasks_by_status: Dict[str, int]
    tasks_by_day: Dict[str, int]
    tasks_by_hour: Dict[int, int]
    daily_completion_trend: List[Dict[str, Any]]
    daily_failure_trend: List[Dict[str, Any]]


class AgentPerformanceResponse(BaseModel):
    """Agent性能响应"""
    agent_id: str
    agent_name: str
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    success_rate: float
    avg_execution_time: float
    total_tool_calls: int
    successful_tool_calls: int


class ToolAnalyticsResponse(BaseModel):
    """工具调用分析响应"""
    tool_name: str
    total_calls: int
    successful_calls: int
    failed_calls: int
    success_rate: float
    avg_execution_time: float
    calls_by_day: Dict[str, int]
    calls_by_hour: Dict[int, int]
    common_errors: List[Dict[str, Any]]


class SystemMetricsResponse(BaseModel):
    """系统指标响应"""
    task_queue_size: int
    active_tasks: int
    active_agents: int
    total_agents: int
    available_tools: int
    system_load: float
    timestamp: str


class DashboardDataResponse(BaseModel):
    """看板数据响应"""
    task_statistics: TaskStatisticsResponse
    agent_performance: List[AgentPerformanceResponse]
    tool_analytics: List[ToolAnalyticsResponse]
    system_metrics: SystemMetricsResponse
    generated_at: str


# ==================== 工具优化相关 ====================

class ToolIndexRequest(BaseModel):
    """工具索引请求"""
    tools: List[Dict[str, Any]] = Field(..., description="工具列表")
    force_rebuild: bool = Field(default=False, description="是否强制重建索引")


class ToolIndexResponse(BaseResponse):
    """工具索引响应"""
    indexed_count: int = Field(..., description="已索引工具数量")
    categories: Dict[str, int] = Field(default_factory=dict, description="各类别工具数量")


class ToolRetrievalRequest(BaseModel):
    """工具检索请求"""
    query: str = Field(..., description="查询文本", min_length=1)
    max_tools: int = Field(default=10, description="最大返回工具数")
    max_tokens: int = Field(default=2000, description="最大Token预算")
    strategy: str = Field(default="hybrid", description="检索策略: semantic/keyword/hybrid")


class ToolRetrievalResponse(BaseResponse):
    """工具检索响应"""
    tools: List[Dict[str, Any]] = Field(default_factory=list, description="检索到的工具")
    total_tokens: int = Field(default=0, description="总Token数")
    retrieval_time_ms: int = Field(default=0, description="检索耗时")


class ToolCompressRequest(BaseModel):
    """工具压缩请求"""
    tools: List[Dict[str, Any]] = Field(..., description="待压缩工具列表")
    level: str = Field(default="medium", description="压缩级别: low/medium/high")
    max_tokens_per_tool: int = Field(default=100, description="每个工具最大Token数")


class ToolCompressResponse(BaseResponse):
    """工具压缩响应"""
    compressed_tools: List[Dict[str, Any]] = Field(default_factory=list, description="压缩后的工具")
    original_tokens: int = Field(default=0, description="原始Token数")
    compressed_tokens: int = Field(default=0, description="压缩后Token数")
    compression_ratio: float = Field(default=0.0, description="压缩比率")


class ToolHealingRequest(BaseModel):
    """工具自愈请求"""
    tool_name: str = Field(..., description="工具名称")
    params: Dict[str, Any] = Field(default_factory=dict, description="工具参数")
    error_info: Dict[str, Any] = Field(..., description="错误信息")
    max_retries: int = Field(default=3, description="最大重试次数")


class ToolHealingResponse(BaseResponse):
    """工具自愈响应"""
    success: bool = Field(..., description="是否成功")
    result: Optional[Dict[str, Any]] = Field(default=None, description="执行结果")
    strategy_used: str = Field(default="", description="使用的恢复策略")
    retry_count: int = Field(default=0, description="重试次数")


class ToolContextManagerRequest(BaseModel):
    """上下文管理请求"""
    query: str = Field(..., description="查询文本")
    available_tools: List[str] = Field(default_factory=list, description="可用工具列表")
    context_budget: int = Field(default=2000, description="上下文预算")


class ToolContextManagerResponse(BaseResponse):
    """上下文管理响应"""
    selected_tools: List[str] = Field(default_factory=list, description="选中的工具")
    total_tokens: int = Field(default=0, description="总Token数")
    selection_strategy: str = Field(default="", description="选择策略")


# ==================== 记忆优化相关 ====================

class MemoryWeightRequest(BaseModel):
    """记忆权重计算请求"""
    memory_id: str = Field(..., description="记忆ID")
    content: str = Field(..., description="记忆内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="记忆元数据")


class MemoryWeightResponse(BaseResponse):
    """记忆权重响应"""
    memory_id: str
    weight: float = Field(..., description="权重值(0-1)")
    factors: Dict[str, float] = Field(default_factory=dict, description="权重因子")


class MemoryConflictRequest(BaseModel):
    """记忆冲突检测请求"""
    memories: List[Dict[str, Any]] = Field(..., description="记忆列表")
    check_type: str = Field(default="all", description="检查类型: all/contradiction/duplicate")


class MemoryConflictResponse(BaseResponse):
    """记忆冲突响应"""
    conflicts: List[Dict[str, Any]] = Field(default_factory=list, description="检测到的冲突")
    resolutions: List[Dict[str, Any]] = Field(default_factory=list, description="解决方案")
    conflict_count: int = Field(default=0, description="冲突数量")


class MemoryConsolidationRequest(BaseModel):
    """记忆巩固请求"""
    memories: List[Dict[str, Any]] = Field(..., description="待巩固记忆列表")
    consolidation_type: str = Field(default="auto", description="巩固类型: auto/cluster/pattern")
    min_cluster_size: int = Field(default=3, description="最小簇大小")


class MemoryConsolidationResponse(BaseResponse):
    """记忆巩固响应"""
    clusters: List[Dict[str, Any]] = Field(default_factory=list, description="记忆簇")
    patterns: List[Dict[str, Any]] = Field(default_factory=list, description="提取的模式")
    consolidated_count: int = Field(default=0, description="巩固的记忆数")
    reduction_ratio: float = Field(default=0.0, description="压缩比率")


class MemoryStatsResponse(BaseResponse):
    """记忆统计响应"""
    total_memories: int = Field(default=0, description="总记忆数")
    weighted_memories: int = Field(default=0, description="已加权记忆数")
    conflict_count: int = Field(default=0, description="冲突数")
    consolidated_memories: int = Field(default=0, description="已巩固记忆数")
    patterns_extracted: int = Field(default=0, description="提取的模式数")


# ==================== 提供者管理相关 ====================

class ProviderType(str, Enum):
    """提供者类型"""
    OPSPILOT = "opspilot"
    LANGCHAIN = "langchain"
    AGENTSCOPE = "agentscope"
    REME = "reme"


class SetProviderRequest(BaseModel):
    """设置提供者请求"""
    provider_type: str = Field(..., description="提供者类型: approval/memory/evaluation")
    provider: str = Field(..., description="提供者名称")


class ProviderStatusResponse(BaseResponse):
    """提供者状态响应"""
    approval_provider: str = Field(default="langchain", description="审批提供者")
    memory_provider: str = Field(default="opspilot", description="记忆提供者")
    evaluation_provider: str = Field(default="agentscope", description="评估提供者")


class ProviderInfo(BaseModel):
    """提供者信息"""
    name: str
    type: str
    available: bool = Field(default=True)
    description: str = ""
    features: List[str] = Field(default_factory=list)


class ProviderListResponse(BaseResponse):
    """提供者列表响应"""
    approval_providers: List[ProviderInfo] = Field(default_factory=list)
    memory_providers: List[ProviderInfo] = Field(default_factory=list)
    evaluation_providers: List[ProviderInfo] = Field(default_factory=list)








