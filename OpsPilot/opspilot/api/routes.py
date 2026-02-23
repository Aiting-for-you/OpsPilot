"""
API 路由定义

职责：
- 定义 API 端点
- 请求处理
- 响应生成
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks

from opspilot.api.schemas import (
    BaseResponse,
    TaskCreateRequest,
    TaskCreateResponse,
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
    TaskStatus,
    LLMProviderConfigRequest,
    LLMProviderConfigResponse,
    LLMConfigListResponse,
    LLMTestConnectionResponse,
    LLMProviderEnum,
    FetchModelsRequest,
    FetchModelsResponse,
    ModelInfo,
    BatchAddModelsRequest,
    BatchAddModelsResponse,
    MCPServerConfigRequest,
    MCPServerConfigResponse,
    MCPServerListResponse,
    MCPServerToolResponse,
    MCPToolCallRequest,
    MCPToolCallResponse,
    MCPAllToolsResponse,
    # RBAC 相关
    AssignRoleRequest,
    UserRoleResponse,
    RolePermissionResponse,
    CheckPermissionRequest,
    CheckPermissionResponse,
    CheckAmountRequest,
    CheckAmountResponse,
    # 审批相关
    CreateApprovalRequest,
    ApprovalRequestResponse,
    ApproveRequest,
    RejectRequest,
    PendingApprovalsResponse,
    UserApprovalsResponse,
    # 任务调度相关
    CreateScheduledTaskRequest,
    ScheduledTaskResponse,
    ScheduledTaskListResponse,
    SchedulerStatsResponse,
    TaskPriority,
    TaskType,
    # 数据分析相关
    TaskStatisticsResponse,
    AgentPerformanceResponse,
    ToolAnalyticsResponse,
    SystemMetricsResponse,
    DashboardDataResponse,
    # 工具优化相关
    ToolIndexRequest,
    ToolIndexResponse,
    ToolRetrievalRequest,
    ToolRetrievalResponse,
    ToolCompressRequest,
    ToolCompressResponse,
    ToolHealingRequest,
    ToolHealingResponse,
    ToolContextManagerRequest,
    ToolContextManagerResponse,
    # 记忆优化相关
    MemoryWeightRequest,
    MemoryWeightResponse,
    MemoryConflictRequest,
    MemoryConflictResponse,
    MemoryConsolidationRequest,
    MemoryConsolidationResponse,
    MemoryStatsResponse,
    # 提供者管理相关
    SetProviderRequest,
    ProviderStatusResponse,
    ProviderInfo,
    ProviderListResponse,
)
# 定价模块导入
from opspilot.pricing.api import (
    PricingNegotiateRequest,
    PricingNegotiateResponse,
    PricingHistoryRequest,
    PricingHistoryResponse,
    AgentStatusResponse as PricingAgentStatusResponse,
    pricing_api,
)
# 客服模块导入
from opspilot.customer_service.api import (
    TicketCreateRequest,
    TicketCreateResponse,
    TicketProcessRequest,
    TicketProcessResponse,
    TicketListResponse,
    AgentStatusResponse,
    customer_service_api,
    QueueStatusResponse,
    KnowledgeQueryRequest,
    KnowledgeQueryResponse,
    TicketAnalyticsResponse,
    AgentListResponse,
    AssignmentRequest,
    AssignmentResponse,
    EscalationRequest,
    EscalationResponse,
    FollowUpRequest,
    FollowUpResponse,
    TicketLifecycleResponse,
)
from opspilot.core.orchestrator import Orchestrator
from opspilot.core.sop_executor import SOPExecutor, SOPDefinition, create_order_sop, query_supplier_sop
from opspilot.tools.base import ToolRouter, ToolContext
from opspilot.tools.mcp import create_default_router
from opspilot.memory.short_term import ShortTermMemory
from opspilot.memory.knowledge import KnowledgeBase


# ==================== 依赖注入 ====================

def get_orchestrator() -> Orchestrator:
    """获取编排器实例"""
    return Orchestrator()


def get_tool_router() -> ToolRouter:
    """获取工具路由器"""
    return create_default_router()


def get_memory() -> ShortTermMemory:
    """获取记忆管理器"""
    return ShortTermMemory()


def get_knowledge() -> KnowledgeBase:
    """获取知识库"""
    return KnowledgeBase()


# ==================== 路由定义 ====================

# 创建路由器
router = APIRouter()


# ==================== 任务接口 ====================

@router.post(
    "/tasks",
    response_model=TaskCreateResponse,
    summary="创建任务",
    description="创建新的处理任务"
)
async def create_task(
    request: TaskCreateRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """创建新任务"""
    try:
        result = await orchestrator.process(request.user_input)

        return TaskCreateResponse(
            success=True,
            message="任务创建成功",
            task_id=result["task_id"],
            status=TaskStatus.PROCESSING if result["success"] else TaskStatus.FAILED
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/tasks/{task_id}",
    response_model=TaskStatusResponse,
    summary="查询任务状态",
    description="查询指定任务的状态"
)
async def get_task_status(
    task_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """查询任务状态"""
    status = orchestrator.get_task_status(task_id)

    if not status:
        raise HTTPException(status_code=404, detail="任务不存在")

    return TaskStatusResponse(
        success=True,
        task_id=status["task_id"],
        state=status["state"],
        intent=status.get("intent"),
        created_at=status["created_at"],
        updated_at=status["updated_at"]
    )


@router.get(
    "/tasks/{task_id}/result",
    response_model=TaskResultResponse,
    summary="获取任务结果",
    description="获取任务的执行结果"
)
async def get_task_result(
    task_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """获取任务结果"""
    context = orchestrator.get_task_context(task_id)

    if not context:
        raise HTTPException(status_code=404, detail="任务不存在")

    return TaskResultResponse(
        success=True,
        task_id=task_id,
        state=context.state_context.current_state.value,
        result=context.final_result,
        execution_trace=[
            t.to_dict() for t in context.state_context.history
        ] if context.state_context.history else None
    )


# ==================== 工具接口 ====================

@router.post(
    "/tools/call",
    response_model=ToolCallResponse,
    summary="调用工具",
    description="直接调用指定工具"
)
async def call_tool(
    request: ToolCallRequest,
    tool_router: ToolRouter = Depends(get_tool_router)
):
    """调用工具"""
    if not tool_router.has_tool(request.tool_name):
        raise HTTPException(status_code=404, detail=f"工具不存在: {request.tool_name}")

    context = ToolContext(
        task_id=request.task_id or "direct-call"
    )

    result = await tool_router.call_tool_with_retry(
        tool_name=request.tool_name,
        params=request.params,
        context=context
    )

    return ToolCallResponse(
        success=result.is_success(),
        message="工具调用成功" if result.is_success() else result.error,
        tool_name=request.tool_name,
        result=result.data,
        latency_ms=result.latency_ms,
        fallback_mode=result.fallback_mode.value if result.fallback_mode else None
    )


@router.get(
    "/tools",
    response_model=ToolSchemaResponse,
    summary="获取工具列表",
    description="获取所有可用工具的 Schema"
)
async def list_tools(
    tool_router: ToolRouter = Depends(get_tool_router)
):
    """获取工具列表"""
    schemas = tool_router.get_all_schemas()

    return ToolSchemaResponse(
        success=True,
        tools=[s.to_mcp_format() for s in schemas]
    )


# ==================== 记忆接口 ====================

@router.post(
    "/memory/store",
    summary="存储记忆",
    description="存储一条记忆"
)
async def store_memory(
    request: MemoryStoreRequest,
    memory: ShortTermMemory = Depends(get_memory)
):
    """存储记忆"""
    entry = await memory.remember(
        content=request.content,
        task_id=request.task_id,
        metadata=request.metadata
    )

    return {
        "success": True,
        "entry_id": entry.id
    }


@router.post(
    "/memory/search",
    response_model=MemorySearchResponse,
    summary="搜索记忆",
    description="搜索记忆内容"
)
async def search_memory(
    request: MemorySearchRequest,
    memory: ShortTermMemory = Depends(get_memory)
):
    """搜索记忆"""
    results = await memory.recall(
        query=request.query,
        limit=request.limit
    )

    return MemorySearchResponse(
        success=True,
        results=[r.to_dict() for r in results],
        total=len(results)
    )


# ==================== SOP 接口 ====================

# SOP 注册表
SOP_REGISTRY: dict = {
    "create_order": create_order_sop,
    "query_supplier": query_supplier_sop,
}


@router.post(
    "/sop/execute",
    response_model=SOPExecuteResponse,
    summary="执行 SOP",
    description="执行标准操作流程"
)
async def execute_sop(
    request: SOPExecuteRequest,
    tool_router: ToolRouter = Depends(get_tool_router)
):
    """执行 SOP"""
    if request.sop_name not in SOP_REGISTRY:
        raise HTTPException(status_code=404, detail=f"SOP 不存在: {request.sop_name}")

    # 获取 SOP 定义
    sop = SOP_REGISTRY[request.sop_name]()

    # 创建执行器
    executor = SOPExecutor(tool_router=tool_router)

    # 执行
    result = await executor.execute(sop, request.variables)

    return SOPExecuteResponse(
        success=result["success"],
        message="SOP 执行成功" if result["success"] else result.get("error", "执行失败"),
        sop_name=request.sop_name,
        steps_executed=result.get("steps_executed", 0),
        results=result.get("results", [])
    )


@router.get(
    "/sop/list",
    summary="获取 SOP 列表",
    description="获取所有可用的 SOP"
)
async def list_sops():
    """获取 SOP 列表"""
    return {
        "success": True,
        "sops": list(SOP_REGISTRY.keys())
    }


# ==================== 知识库接口 ====================

@router.post(
    "/knowledge/query",
    response_model=KnowledgeQueryResponse,
    summary="查询知识库",
    description="查询知识库内容"
)
async def query_knowledge(
    request: KnowledgeQueryRequest,
    knowledge: KnowledgeBase = Depends(get_knowledge)
):
    """查询知识库"""
    results = await knowledge.query(
        question=request.query,
        limit=request.limit
    )

    return KnowledgeQueryResponse(
        success=True,
        results=[r.to_dict() for r in results]
    )


# ==================== 健康检查 ====================

@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="健康检查",
    description="检查服务健康状态"
)
async def health_check():
    """健康检查"""
    return HealthCheckResponse()


# ==================== LLM 配置接口 ====================

from opspilot.core.llm_config import (
    get_llm_config_manager,
    fetch_available_models,
    batch_add_custom_models,
    LLMProvider,
)


def get_llm_config():
    """获取 LLM 配置管理器"""
    return get_llm_config_manager()


@router.get(
    "/llm/config",
    response_model=LLMConfigListResponse,
    summary="获取 LLM 配置列表",
    description="获取所有 LLM 提供商的配置信息"
)
async def get_llm_configs(
    manager = Depends(get_llm_config)
):
    """获取所有 LLM 配置"""
    providers = []
    default_provider = None
    
    for provider, config in manager.get_all_providers().items():
        config_dict = config.to_dict()
        providers.append(LLMProviderConfigResponse(
            provider=config_dict["provider"],
            name=config_dict["name"],
            api_key_masked=config_dict.get("api_key_masked"),
            api_base=config_dict["api_base"],
            model_name=config_dict["model_name"],
            default_model=config_dict["default_model"],
            available_models=config_dict["available_models"],
            temperature=config_dict["temperature"],
            max_tokens=config_dict["max_tokens"],
            top_p=config_dict["top_p"],
            is_enabled=config_dict["is_enabled"],
            is_default=config_dict["is_default"],
            last_used=config_dict["last_used"],
        ))
        
        if config.is_default:
            default_provider = config.provider.value
    
    return LLMConfigListResponse(
        success=True,
        providers=providers,
        default_provider=default_provider
    )


@router.get(
    "/llm/config/{provider}",
    response_model=LLMProviderConfigResponse,
    summary="获取单个 LLM 配置",
    description="获取指定提供商的配置信息"
)
async def get_llm_provider_config(
    provider: LLMProviderEnum,
    manager = Depends(get_llm_config)
):
    """获取单个 LLM 配置"""
    try:
        p = LLMProvider(provider.value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的提供商: {provider}")
    
    config = manager.get_provider_config(p)
    if not config:
        raise HTTPException(status_code=404, detail=f"提供商配置不存在: {provider}")
    
    config_dict = config.to_dict()
    return LLMProviderConfigResponse(
        provider=config_dict["provider"],
        name=config_dict["name"],
        api_key_masked=config_dict.get("api_key_masked"),
        api_base=config_dict["api_base"],
        model_name=config_dict["model_name"],
        default_model=config_dict["default_model"],
        available_models=config_dict["available_models"],
        temperature=config_dict["temperature"],
        max_tokens=config_dict["max_tokens"],
        top_p=config_dict["top_p"],
        is_enabled=config_dict["is_enabled"],
        is_default=config_dict["is_default"],
        last_used=config_dict["last_used"],
    )


@router.put(
    "/llm/config/{provider}",
    response_model=LLMProviderConfigResponse,
    summary="更新 LLM 配置",
    description="更新指定提供商的配置，包括 API Key、模型选择等"
)
async def update_llm_config(
    provider: LLMProviderEnum,
    request: LLMProviderConfigRequest,
    manager = Depends(get_llm_config)
):
    """更新 LLM 配置"""
    try:
        p = LLMProvider(provider.value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的提供商: {provider}")
    
    try:
        config = manager.update_provider_config(
            provider=p,
            api_key=request.api_key,
            api_base=request.api_base,
            model_name=request.model_name,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            is_enabled=request.is_enabled,
            is_default=request.is_default,
            available_models=request.available_models,
        )
        
        config_dict = config.to_dict()
        return LLMProviderConfigResponse(
            provider=config_dict["provider"],
            name=config_dict["name"],
            api_key_masked=config_dict.get("api_key_masked"),
            api_base=config_dict["api_base"],
            model_name=config_dict["model_name"],
            default_model=config_dict["default_model"],
            available_models=config_dict["available_models"],
            temperature=config_dict["temperature"],
            max_tokens=config_dict["max_tokens"],
            top_p=config_dict["top_p"],
            is_enabled=config_dict["is_enabled"],
            is_default=config_dict["is_default"],
            last_used=config_dict["last_used"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@router.post(
    "/llm/config/{provider}/test",
    response_model=LLMTestConnectionResponse,
    summary="测试 LLM 连接",
    description="测试指定提供商的 API 连接是否正常"
)
async def test_llm_connection(
    provider: LLMProviderEnum,
    manager = Depends(get_llm_config)
):
    """测试 LLM 连接"""
    try:
        p = LLMProvider(provider.value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的提供商: {provider}")
    
    result = manager.test_provider_connection(p)
    
    return LLMTestConnectionResponse(
        success=result["success"],
        message=result["message"],
        latency_ms=result.get("latency_ms")
    )


@router.post(
    "/llm/config/{provider}/set-default",
    summary="设置默认 LLM",
    description="将指定提供商设置为默认"
)
async def set_default_llm(
    provider: LLMProviderEnum,
    manager = Depends(get_llm_config)
):
    """设置默认 LLM"""
    try:
        p = LLMProvider(provider.value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的提供商: {provider}")
    
    success = manager.set_default_provider(p)
    
    if not success:
        raise HTTPException(
            status_code=400, 
            detail="设置失败，请确保提供商已启用"
        )
    
    return {"success": True, "message": f"已将 {provider.value} 设为默认提供商"}


@router.post(
    "/llm/models/fetch",
    response_model=FetchModelsResponse,
    summary="获取可用模型列表",
    description="从 API 端点获取支持的模型列表（OpenAI 兼容格式）"
)
async def fetch_models(request: FetchModelsRequest):
    """
    获取 API 端点支持的模型列表
    
    支持 OpenAI 兼容格式的 API，如：
    - OpenAI
    - DeepSeek
    - 通义千问（兼容模式）
    - 其他 OpenAI 兼容服务
    """
    result = fetch_available_models(
        api_base=request.api_base,
        api_key=request.api_key,
        provider_type=request.provider_type,
    )
    
    return FetchModelsResponse(
        success=result["success"],
        models=[ModelInfo(**m) for m in result["models"]],
        error=result.get("error"),
    )


@router.post(
    "/llm/models/batch-add",
    response_model=BatchAddModelsResponse,
    summary="批量添加模型",
    description="批量添加模型到指定提供商配置"
)
async def batch_add_models(request: BatchAddModelsRequest):
    """
    批量添加模型配置
    
    用于快速配置多个模型，适用于：
    - 自定义 API 端点
    - 批量导入模型列表
    """
    try:
        p = LLMProvider(request.provider.value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的提供商: {request.provider}")
    
    result = batch_add_custom_models(
        provider=p,
        api_key=request.api_key,
        api_base=request.api_base,
        models=request.models,
        temperature=request.temperature or 0.7,
        max_tokens=request.max_tokens or 4096,
        set_default=request.set_default,
    )
    
    return BatchAddModelsResponse(
        success=result["success"],
        added_count=result["added_count"],
        default_model=result["default_model"],
        error=result.get("error"),
    )


# ==================== MCP Server 配置接口 ====================

from opspilot.mcp.external_manager import get_external_mcp_manager, ExternalMCPManager
from opspilot.api.schemas import (
    MCPServerConfigRequest,
    MCPServerConfigResponse,
    MCPServerListResponse,
    MCPServerStatus,
    MCPServerToolResponse,
    MCPToolCallRequest,
    MCPToolCallResponse,
    MCPAllToolsResponse,
)


def get_mcp_manager() -> ExternalMCPManager:
    """获取 MCP 管理器实例"""
    return get_external_mcp_manager()


@router.get(
    "/mcp/servers",
    response_model=MCPServerListResponse,
    summary="获取 MCP Server 列表",
    description="获取所有已配置的外部 MCP Server"
)
async def list_mcp_servers(
    manager: ExternalMCPManager = Depends(get_mcp_manager)
):
    """获取所有 MCP Server 配置"""
    servers = manager.list_servers()
    return MCPServerListResponse(
        success=True,
        servers=[
            MCPServerConfigResponse(
                name=s["name"],
                command=s["command"],
                args=s["args"],
                enabled=s["enabled"],
                auto_connect=s["auto_connect"],
                description=s.get("description", ""),
                status=MCPServerStatus(s["status"]),
                tool_count=s["tool_count"],
                error_message=s.get("error_message", ""),
                connected_at=s.get("connected_at"),
            )
            for s in servers
        ]
    )


@router.post(
    "/mcp/servers",
    response_model=MCPServerConfigResponse,
    summary="添加 MCP Server",
    description="添加新的外部 MCP Server 配置"
)
async def add_mcp_server(
    request: MCPServerConfigRequest,
    manager: ExternalMCPManager = Depends(get_mcp_manager)
):
    """添加新的 MCP Server"""
    from opspilot.utils.config import MCPServerConfig
    
    config = MCPServerConfig(
        name=request.name,
        command=request.command,
        args=request.args,
        env=request.env,
        enabled=request.enabled,
        auto_connect=request.auto_connect,
        description=request.description,
    )
    
    try:
        result = manager.add_server(config)
        return MCPServerConfigResponse(
            name=result["name"],
            command=result["command"],
            args=result["args"],
            enabled=result["enabled"],
            auto_connect=result["auto_connect"],
            description=result.get("description", ""),
            status=MCPServerStatus(result["status"]),
            tool_count=result["tool_count"],
            error_message=result.get("error_message", ""),
            connected_at=result.get("connected_at"),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/mcp/servers/{name}",
    response_model=MCPServerConfigResponse,
    summary="获取单个 MCP Server",
    description="获取指定 MCP Server 的配置信息"
)
async def get_mcp_server(
    name: str,
    manager: ExternalMCPManager = Depends(get_mcp_manager)
):
    """获取单个 MCP Server 配置"""
    result = manager.get_server(name)
    if not result:
        raise HTTPException(status_code=404, detail=f"Server '{name}' not found")
    
    return MCPServerConfigResponse(
        name=result["name"],
        command=result["command"],
        args=result["args"],
        enabled=result["enabled"],
        auto_connect=result["auto_connect"],
        description=result.get("description", ""),
        status=MCPServerStatus(result["status"]),
        tool_count=result["tool_count"],
        error_message=result.get("error_message", ""),
        connected_at=result.get("connected_at"),
    )


@router.put(
    "/mcp/servers/{name}",
    response_model=MCPServerConfigResponse,
    summary="更新 MCP Server",
    description="更新指定 MCP Server 的配置"
)
async def update_mcp_server(
    name: str,
    request: MCPServerConfigRequest,
    manager: ExternalMCPManager = Depends(get_mcp_manager)
):
    """更新 MCP Server 配置"""
    from opspilot.utils.config import MCPServerConfig
    
    config = MCPServerConfig(
        name=request.name,
        command=request.command,
        args=request.args,
        env=request.env,
        enabled=request.enabled,
        auto_connect=request.auto_connect,
        description=request.description,
    )
    
    try:
        result = manager.update_server(name, config)
        return MCPServerConfigResponse(
            name=result["name"],
            command=result["command"],
            args=result["args"],
            enabled=result["enabled"],
            auto_connect=result["auto_connect"],
            description=result.get("description", ""),
            status=MCPServerStatus(result["status"]),
            tool_count=result["tool_count"],
            error_message=result.get("error_message", ""),
            connected_at=result.get("connected_at"),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/mcp/servers/{name}",
    summary="删除 MCP Server",
    description="删除指定的 MCP Server 配置"
)
async def delete_mcp_server(
    name: str,
    manager: ExternalMCPManager = Depends(get_mcp_manager)
):
    """删除 MCP Server 配置"""
    if not manager.remove_server(name):
        raise HTTPException(status_code=404, detail=f"Server '{name}' not found")
    
    return {"success": True, "message": f"Server '{name}' deleted"}


@router.post(
    "/mcp/servers/{name}/connect",
    response_model=MCPServerConfigResponse,
    summary="连接 MCP Server",
    description="连接到指定的 MCP Server"
)
async def connect_mcp_server(
    name: str,
    manager: ExternalMCPManager = Depends(get_mcp_manager)
):
    """连接到 MCP Server"""
    try:
        result = await manager.connect(name)
        return MCPServerConfigResponse(
            name=result["name"],
            command=result["command"],
            args=result["args"],
            enabled=result["enabled"],
            auto_connect=result["auto_connect"],
            description=result.get("description", ""),
            status=MCPServerStatus(result["status"]),
            tool_count=result["tool_count"],
            error_message=result.get("error_message", ""),
            connected_at=result.get("connected_at"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/mcp/servers/{name}/disconnect",
    response_model=MCPServerConfigResponse,
    summary="断开 MCP Server",
    description="断开与指定 MCP Server 的连接"
)
async def disconnect_mcp_server(
    name: str,
    manager: ExternalMCPManager = Depends(get_mcp_manager)
):
    """断开 MCP Server 连接"""
    try:
        result = await manager.disconnect(name)
        return MCPServerConfigResponse(
            name=result["name"],
            command=result["command"],
            args=result["args"],
            enabled=result["enabled"],
            auto_connect=result["auto_connect"],
            description=result.get("description", ""),
            status=MCPServerStatus(result["status"]),
            tool_count=result["tool_count"],
            error_message=result.get("error_message", ""),
            connected_at=result.get("connected_at"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/mcp/servers/{name}/tools",
    response_model=MCPServerToolResponse,
    summary="获取 MCP Server 工具列表",
    description="获取指定 MCP Server 提供的所有工具"
)
async def get_mcp_server_tools(
    name: str,
    manager: ExternalMCPManager = Depends(get_mcp_manager)
):
    """获取 MCP Server 的工具列表"""
    try:
        tools = await manager.list_tools(name)
        return MCPServerToolResponse(
            success=True,
            server_name=name,
            tools=tools,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/mcp/tools",
    response_model=MCPAllToolsResponse,
    summary="获取所有 MCP 工具",
    description="获取所有已连接 MCP Server 提供的工具"
)
async def list_all_mcp_tools(
    manager: ExternalMCPManager = Depends(get_mcp_manager)
):
    """获取所有 MCP 工具"""
    tools = manager.list_all_tools()
    return MCPAllToolsResponse(
        success=True,
        tools=tools,
    )


@router.post(
    "/mcp/tools/call",
    response_model=MCPToolCallResponse,
    summary="调用 MCP 工具",
    description="调用指定的 MCP 工具（自动路由到对应的 Server）"
)
async def call_mcp_tool(
    request: MCPToolCallRequest,
    manager: ExternalMCPManager = Depends(get_mcp_manager)
):
    """调用 MCP 工具"""
    try:
        if request.server_name:
            # 在指定 Server 上调用
            result = await manager.call_tool_on_server(
                server_name=request.server_name,
                tool_name=request.tool_name,
                arguments=request.arguments,
            )
            server_name = request.server_name
        else:
            # 自动路由
            result = await manager.call_tool(
                tool_name=request.tool_name,
                arguments=request.arguments,
            )
            # 查找工具所属的 Server
            server_name = manager._tool_to_server.get(request.tool_name, "unknown")
        
        return MCPToolCallResponse(
            success=True,
            message="工具调用成功",
            tool_name=request.tool_name,
            server_name=server_name,
            result=result,
        )
    except Exception as e:
        # 查找工具所属的 Server
        server_name = manager._tool_to_server.get(request.tool_name, "unknown")
        return MCPToolCallResponse(
            success=False,
            message="工具调用失败",
            tool_name=request.tool_name,
            server_name=server_name,
            error=str(e),
        )


# ==================== RBAC 权限接口 ====================

@router.post(
    "/rbac/assign-role",
    response_model=UserRoleResponse,
    summary="分配用户角色",
    description="为用户分配角色（需要管理员权限）"
)
async def assign_role(request: AssignRoleRequest):
    """分配用户角色"""
    try:
        from opspilot.auth.rbac import get_rbac_manager, Role
        
        rbac = get_rbac_manager()
        role = Role(request.role.value)
        
        user_role = rbac.assign_role(
            user_id=request.user_id,
            role=role,
            department=request.department,
        )
        
        return UserRoleResponse(
            success=True,
            message="角色分配成功",
            user_id=user_role.user_id,
            role=user_role.role.value,
            department=user_role.department,
            assigned_at=user_role.assigned_at.isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/rbac/user/{user_id}/role",
    response_model=UserRoleResponse,
    summary="获取用户角色"
)
async def get_user_role(user_id: str):
    """获取用户角色信息"""
    from opspilot.auth.rbac import get_rbac_manager
    
    rbac = get_rbac_manager()
    user_role = rbac.get_user_role(user_id)
    
    if not user_role:
        raise HTTPException(status_code=404, detail="用户角色不存在")
    
    return UserRoleResponse(
        success=True,
        message="获取成功",
        user_id=user_role.user_id,
        role=user_role.role.value,
        department=user_role.department,
        assigned_at=user_role.assigned_at.isoformat(),
    )


@router.get(
    "/rbac/role/{role}/permissions",
    response_model=RolePermissionResponse,
    summary="获取角色权限"
)
async def get_role_permissions(role: str):
    """获取角色权限配置"""
    from opspilot.auth.rbac import get_rbac_manager, Role
    
    try:
        rbac = get_rbac_manager()
        role_enum = Role(role)
        role_perm = rbac.get_role_permission(role_enum)
        
        return RolePermissionResponse(
            role=role_perm.role.value,
            name=role_perm.name,
            description=role_perm.description,
            amount_limit=role_perm.amount_limit,
            permissions=[p.value for p in role_perm.permissions],
            sensitive_actions=list(role_perm.sensitive_actions),
            can_approve_amount=role_perm.can_approve_amount,
            data_scope=role_perm.data_scope,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/rbac/check-permission",
    response_model=CheckPermissionResponse,
    summary="检查用户权限"
)
async def check_permission(request: CheckPermissionRequest):
    """检查用户是否有指定权限"""
    from opspilot.auth.rbac import get_rbac_manager, Permission
    
    try:
        rbac = get_rbac_manager()
        permission = Permission(request.permission)
        has_permission = rbac.has_permission(request.user_id, permission)
        
        return CheckPermissionResponse(
            success=True,
            message="检查完成",
            has_permission=has_permission,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/rbac/check-amount",
    response_model=CheckAmountResponse,
    summary="检查金额上限"
)
async def check_amount_limit(request: CheckAmountRequest):
    """检查金额是否在用户角色上限内"""
    from opspilot.auth.rbac import get_rbac_manager
    
    try:
        rbac = get_rbac_manager()
        user_role = rbac.get_user_role(request.user_id)
        
        if not user_role:
            raise HTTPException(status_code=404, detail="用户角色不存在")
        
        role_perm = rbac.get_role_permission(user_role.role)
        limit = role_perm.amount_limit
        
        # 0 表示无限制
        within_limit = (limit == 0) or (request.amount <= limit)
        exceeded = None if within_limit else (request.amount - limit)
        
        return CheckAmountResponse(
            success=True,
            message="检查完成",
            within_limit=within_limit,
            limit=limit,
            exceeded_amount=exceeded,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 审批工作流接口 ====================

@router.post(
    "/approval/create",
    response_model=ApprovalRequestResponse,
    summary="创建审批请求",
    description="创建审批请求（敏感操作、超额订单等）"
)
async def create_approval(request: CreateApprovalRequest):
    """创建审批请求"""
    try:
        from opspilot.auth.approval import get_approval_workflow, ApprovalType
        
        workflow = get_approval_workflow()
        approval_type = ApprovalType(request.approval_type.value)
        
        approval = workflow.create_approval_request(
            user_id=request.user_id,
            approval_type=approval_type,
            title=request.title,
            description=request.description,
            data=request.data,
            expires_in_hours=request.expires_in_hours,
        )
        
        return ApprovalRequestResponse(
            success=True,
            message="审批请求创建成功",
            request_id=approval.request_id,
            approval_type=approval.approval_type.value,
            user_id=approval.user_id,
            user_role=approval.user_role,
            title=approval.title,
            description=approval.description,
            status=approval.status.value,
            created_at=approval.created_at.isoformat(),
            expires_at=approval.expires_at.isoformat() if approval.expires_at else None,
            approved_by=approval.approved_by,
            approved_at=approval.approved_at.isoformat() if approval.approved_at else None,
            approval_comment=approval.approval_comment,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/approval/approve",
    response_model=ApprovalRequestResponse,
    summary="审批通过"
)
async def approve_request(request: ApproveRequest):
    """审批通过"""
    try:
        from opspilot.auth.approval import get_approval_workflow
        
        workflow = get_approval_workflow()
        approval = workflow.approve(
            request_id=request.request_id,
            approver_id=request.approver_id,
            comment=request.comment,
        )
        
        return ApprovalRequestResponse(
            success=True,
            message="审批通过",
            request_id=approval.request_id,
            approval_type=approval.approval_type.value,
            user_id=approval.user_id,
            user_role=approval.user_role,
            title=approval.title,
            description=approval.description,
            status=approval.status.value,
            created_at=approval.created_at.isoformat(),
            expires_at=approval.expires_at.isoformat() if approval.expires_at else None,
            approved_by=approval.approved_by,
            approved_at=approval.approved_at.isoformat() if approval.approved_at else None,
            approval_comment=approval.approval_comment,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/approval/reject",
    response_model=ApprovalRequestResponse,
    summary="审批拒绝"
)
async def reject_request(request: RejectRequest):
    """审批拒绝"""
    try:
        from opspilot.auth.approval import get_approval_workflow
        
        workflow = get_approval_workflow()
        approval = workflow.reject(
            request_id=request.request_id,
            approver_id=request.approver_id,
            comment=request.comment,
        )
        
        return ApprovalRequestResponse(
            success=True,
            message="审批拒绝",
            request_id=approval.request_id,
            approval_type=approval.approval_type.value,
            user_id=approval.user_id,
            user_role=approval.user_role,
            title=approval.title,
            description=approval.description,
            status=approval.status.value,
            created_at=approval.created_at.isoformat(),
            expires_at=approval.expires_at.isoformat() if approval.expires_at else None,
            approved_by=approval.approved_by,
            approved_at=approval.approved_at.isoformat() if approval.approved_at else None,
            approval_comment=approval.approval_comment,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/approval/pending/{user_id}",
    response_model=PendingApprovalsResponse,
    summary="获取待审批列表"
)
async def get_pending_approvals(user_id: str):
    """获取用户待审批的请求列表"""
    from opspilot.auth.approval import get_approval_workflow
    
    workflow = get_approval_workflow()
    requests = workflow.get_pending_requests(user_id)
    
    return PendingApprovalsResponse(
        success=True,
        message="获取成功",
        requests=[
            ApprovalRequestResponse(
                success=True,
                message="",
                request_id=req.request_id,
                approval_type=req.approval_type.value,
                user_id=req.user_id,
                user_role=req.user_role,
                title=req.title,
                description=req.description,
                status=req.status.value,
                created_at=req.created_at.isoformat(),
                expires_at=req.expires_at.isoformat() if req.expires_at else None,
                approved_by=req.approved_by,
                approved_at=req.approved_at.isoformat() if req.approved_at else None,
                approval_comment=req.approval_comment,
            )
            for req in requests
        ],
    )


@router.get(
    "/approval/user/{user_id}",
    response_model=UserApprovalsResponse,
    summary="获取用户发起的审批"
)
async def get_user_approvals(user_id: str):
    """获取用户发起的审批请求列表"""
    from opspilot.auth.approval import get_approval_workflow
    
    workflow = get_approval_workflow()
    requests = workflow.get_user_requests(user_id)
    
    return UserApprovalsResponse(
        success=True,
        message="获取成功",
        requests=[
            ApprovalRequestResponse(
                success=True,
                message="",
                request_id=req.request_id,
                approval_type=req.approval_type.value,
                user_id=req.user_id,
                user_role=req.user_role,
                title=req.title,
                description=req.description,
                status=req.status.value,
                created_at=req.created_at.isoformat(),
                expires_at=req.expires_at.isoformat() if req.expires_at else None,
                approved_by=req.approved_by,
                approved_at=req.approved_at.isoformat() if req.approved_at else None,
                approval_comment=req.approval_comment,
            )
            for req in requests
        ],
    )


@router.get(
    "/approval/{request_id}",
    response_model=ApprovalRequestResponse,
    summary="获取审批详情"
)
async def get_approval_detail(request_id: str):
    """获取审批请求详情"""
    from opspilot.auth.approval import get_approval_workflow
    
    workflow = get_approval_workflow()
    approval = workflow.get_approval_request(request_id)
    
    if not approval:
        raise HTTPException(status_code=404, detail="审批请求不存在")
    
    return ApprovalRequestResponse(
        success=True,
        message="获取成功",
        request_id=approval.request_id,
        approval_type=approval.approval_type.value,
        user_id=approval.user_id,
        user_role=approval.user_role,
        title=approval.title,
        description=approval.description,
        status=approval.status.value,
        created_at=approval.created_at.isoformat(),
        expires_at=approval.expires_at.isoformat() if approval.expires_at else None,
        approved_by=approval.approved_by,
        approved_at=approval.approved_at.isoformat() if approval.approved_at else None,
        approval_comment=approval.approval_comment,
    )


# ==================== 任务调度接口 ====================

@router.post(
    "/scheduler/tasks",
    response_model=ScheduledTaskResponse,
    summary="创建调度任务"
)
async def create_scheduled_task(request: CreateScheduledTaskRequest):
    """创建调度任务"""
    from opspilot.scheduler import get_scheduler, TaskPriority as TP, TaskType as TT
    
    try:
        scheduler = get_scheduler()
        
        # 转换优先级
        priority_map = {
            TaskPriority.LOW: TP.LOW,
            TaskPriority.NORMAL: TP.NORMAL,
            TaskPriority.HIGH: TP.HIGH,
            TaskPriority.URGENT: TP.URGENT,
        }
        
        # 转换任务类型
        type_map = {
            TaskType.ONE_TIME: TT.ONE_TIME,
            TaskType.SCHEDULED: TT.SCHEDULED,
            TaskType.RECURRING: TT.RECURRING,
        }
        
        # 解析定时时间
        scheduled_time = None
        if request.scheduled_time:
            scheduled_time = datetime.fromisoformat(request.scheduled_time)
        
        # 示例目标函数（实际应用中应从注册表中获取）
        async def sample_task(*args, **kwargs):
            return {"status": "executed", "args": args, "kwargs": kwargs}
        
        task_id = scheduler.add_task(
            name=request.name,
            target=sample_task,
            args=tuple(request.args),
            kwargs=request.kwargs,
            priority=priority_map[request.priority],
            task_type=type_map[request.task_type],
            scheduled_time=scheduled_time,
            interval=request.interval,
            max_retries=request.max_retries,
            retry_interval=request.retry_interval,
            tags=request.tags,
        )
        
        task = scheduler.get_task(task_id)
        
        return ScheduledTaskResponse(
            success=True,
            message="任务创建成功",
            task_id=task.task_id,
            name=task.name,
            task_type=task.task_type.value,
            priority=task.priority.value,
            status=task.status.value,
            created_at=task.created_at.isoformat(),
            scheduled_time=task.scheduled_time.isoformat() if task.scheduled_time else None,
            started_at=task.started_at.isoformat() if task.started_at else None,
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
            retry_count=task.retry_count,
            error_message=task.error_message,
            tags=task.tags,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/scheduler/tasks",
    response_model=ScheduledTaskListResponse,
    summary="获取任务列表"
)
async def get_scheduled_tasks(
    status: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 100,
):
    """获取调度任务列表"""
    from opspilot.scheduler import get_scheduler, TaskStatus as TS
    
    scheduler = get_scheduler()
    
    # 转换状态
    status_enum = None
    if status:
        try:
            status_enum = TS(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的任务状态: {status}")
    
    tasks = scheduler.get_all_tasks(status=status_enum, tag=tag, limit=limit)
    
    return ScheduledTaskListResponse(
        success=True,
        message="获取成功",
        tasks=[
            ScheduledTaskResponse(
                success=True,
                message="",
                task_id=task.task_id,
                name=task.name,
                task_type=task.task_type.value,
                priority=task.priority.value,
                status=task.status.value,
                created_at=task.created_at.isoformat(),
                scheduled_time=task.scheduled_time.isoformat() if task.scheduled_time else None,
                started_at=task.started_at.isoformat() if task.started_at else None,
                completed_at=task.completed_at.isoformat() if task.completed_at else None,
                retry_count=task.retry_count,
                error_message=task.error_message,
                tags=task.tags,
            )
            for task in tasks
        ],
        total=len(tasks),
    )


@router.get(
    "/scheduler/tasks/{task_id}",
    response_model=ScheduledTaskResponse,
    summary="获取任务详情"
)
async def get_scheduled_task(task_id: str):
    """获取调度任务详情"""
    from opspilot.scheduler import get_scheduler
    
    scheduler = get_scheduler()
    task = scheduler.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return ScheduledTaskResponse(
        success=True,
        message="获取成功",
        task_id=task.task_id,
        name=task.name,
        task_type=task.task_type.value,
        priority=task.priority.value,
        status=task.status.value,
        created_at=task.created_at.isoformat(),
        scheduled_time=task.scheduled_time.isoformat() if task.scheduled_time else None,
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        retry_count=task.retry_count,
        error_message=task.error_message,
        tags=task.tags,
    )


@router.delete(
    "/scheduler/tasks/{task_id}",
    response_model=BaseResponse,
    summary="取消任务"
)
async def cancel_scheduled_task(task_id: str):
    """取消调度任务"""
    from opspilot.scheduler import get_scheduler
    
    scheduler = get_scheduler()
    success = scheduler.cancel_task(task_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="无法取消任务")
    
    return BaseResponse(
        success=True,
        message="任务已取消",
    )


@router.get(
    "/scheduler/stats",
    response_model=SchedulerStatsResponse,
    summary="获取调度器统计"
)
async def get_scheduler_stats():
    """获取调度器统计信息"""
    from opspilot.scheduler import get_scheduler
    
    scheduler = get_scheduler()
    stats = scheduler.get_stats()
    
    return SchedulerStatsResponse(
        success=True,
        message="获取成功",
        **stats,
    )


@router.post(
    "/scheduler/start",
    response_model=BaseResponse,
    summary="启动调度器"
)
async def start_scheduler():
    """启动任务调度器"""
    from opspilot.scheduler import get_scheduler
    
    scheduler = get_scheduler()
    await scheduler.start()
    
    return BaseResponse(
        success=True,
        message="调度器已启动",
    )


@router.post(
    "/scheduler/stop",
    response_model=BaseResponse,
    summary="停止调度器"
)
async def stop_scheduler():
    """停止任务调度器"""
    from opspilot.scheduler import get_scheduler
    
    scheduler = get_scheduler()
    await scheduler.stop()
    
    return BaseResponse(
        success=True,
        message="调度器已停止",
    )


# ==================== 数据分析接口 ====================

@router.get(
    "/analytics/dashboard",
    response_model=DashboardDataResponse,
    summary="获取看板数据"
)
async def get_dashboard_data(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
):
    """获取数据看板汇总数据"""
    from opspilot.analytics import get_analytics_engine
    
    engine = get_analytics_engine()
    
    # 解析时间
    start = datetime.fromisoformat(start_time) if start_time else None
    end = datetime.fromisoformat(end_time) if end_time else None
    
    data = engine.get_dashboard_data(start, end)
    
    # 转换为响应格式
    task_stats = data["task_statistics"]
    return DashboardDataResponse(
        task_statistics=TaskStatisticsResponse(
            total_tasks=task_stats.total_tasks,
            completed_tasks=task_stats.completed_tasks,
            failed_tasks=task_stats.failed_tasks,
            cancelled_tasks=task_stats.cancelled_tasks,
            pending_tasks=task_stats.pending_tasks,
            running_tasks=task_stats.running_tasks,
            success_rate=task_stats.success_rate,
            avg_execution_time=task_stats.avg_execution_time,
            tasks_by_status=task_stats.tasks_by_status,
            tasks_by_day=task_stats.tasks_by_day,
            tasks_by_hour=task_stats.tasks_by_hour,
            daily_completion_trend=task_stats.daily_completion_trend,
            daily_failure_trend=task_stats.daily_failure_trend,
        ),
        agent_performance=[
            AgentPerformanceResponse(
                agent_id=perf.agent_id,
                agent_name=perf.agent_name,
                total_tasks=perf.total_tasks,
                successful_tasks=perf.successful_tasks,
                failed_tasks=perf.failed_tasks,
                success_rate=perf.success_rate,
                avg_execution_time=perf.avg_execution_time,
                total_tool_calls=perf.total_tool_calls,
                successful_tool_calls=perf.successful_tool_calls,
            )
            for perf in data["agent_performance"]
        ],
        tool_analytics=[
            ToolAnalyticsResponse(
                tool_name=analytics.tool_name,
                total_calls=analytics.total_calls,
                successful_calls=analytics.successful_calls,
                failed_calls=analytics.failed_calls,
                success_rate=analytics.success_rate,
                avg_execution_time=analytics.avg_execution_time,
                calls_by_day=analytics.calls_by_day,
                calls_by_hour=analytics.calls_by_hour,
                common_errors=analytics.common_errors,
            )
            for analytics in data["tool_analytics"]
        ],
        system_metrics=SystemMetricsResponse(
            task_queue_size=data["system_metrics"].task_queue_size,
            active_tasks=data["system_metrics"].active_tasks,
            active_agents=data["system_metrics"].active_agents,
            total_agents=data["system_metrics"].total_agents,
            available_tools=data["system_metrics"].available_tools,
            system_load=data["system_metrics"].system_load,
            timestamp=data["system_metrics"].timestamp.isoformat(),
        ),
        generated_at=data["generated_at"],
    )


@router.get(
    "/analytics/tasks",
    response_model=TaskStatisticsResponse,
    summary="获取任务统计"
)
async def get_task_statistics(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
):
    """获取任务统计数据"""
    from opspilot.analytics import get_analytics_engine
    
    engine = get_analytics_engine()
    
    start = datetime.fromisoformat(start_time) if start_time else None
    end = datetime.fromisoformat(end_time) if end_time else None
    
    stats = engine.get_task_statistics(start, end)
    
    return TaskStatisticsResponse(
        total_tasks=stats.total_tasks,
        completed_tasks=stats.completed_tasks,
        failed_tasks=stats.failed_tasks,
        cancelled_tasks=stats.cancelled_tasks,
        pending_tasks=stats.pending_tasks,
        running_tasks=stats.running_tasks,
        success_rate=stats.success_rate,
        avg_execution_time=stats.avg_execution_time,
        tasks_by_status=stats.tasks_by_status,
        tasks_by_day=stats.tasks_by_day,
        tasks_by_hour=stats.tasks_by_hour,
        daily_completion_trend=stats.daily_completion_trend,
        daily_failure_trend=stats.daily_failure_trend,
    )


@router.get(
    "/analytics/agents",
    response_model=List[AgentPerformanceResponse],
    summary="获取Agent性能"
)
async def get_agent_performance(
    agent_id: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
):
    """获取Agent性能统计"""
    from opspilot.analytics import get_analytics_engine
    
    engine = get_analytics_engine()
    
    start = datetime.fromisoformat(start_time) if start_time else None
    end = datetime.fromisoformat(end_time) if end_time else None
    
    performances = engine.get_agent_performance(agent_id, start, end)
    
    return [
        AgentPerformanceResponse(
            agent_id=perf.agent_id,
            agent_name=perf.agent_name,
            total_tasks=perf.total_tasks,
            successful_tasks=perf.successful_tasks,
            failed_tasks=perf.failed_tasks,
            success_rate=perf.success_rate,
            avg_execution_time=perf.avg_execution_time,
            total_tool_calls=perf.total_tool_calls,
            successful_tool_calls=perf.successful_tool_calls,
        )
        for perf in performances
    ]


@router.get(
    "/analytics/tools",
    response_model=List[ToolAnalyticsResponse],
    summary="获取工具调用分析"
)
async def get_tool_analytics(
    tool_name: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
):
    """获取工具调用分析"""
    from opspilot.analytics import get_analytics_engine
    
    engine = get_analytics_engine()
    
    start = datetime.fromisoformat(start_time) if start_time else None
    end = datetime.fromisoformat(end_time) if end_time else None
    
    analytics_list = engine.get_tool_analytics(tool_name, start, end)
    
    return [
        ToolAnalyticsResponse(
            tool_name=analytics.tool_name,
            total_calls=analytics.total_calls,
            successful_calls=analytics.successful_calls,
            failed_calls=analytics.failed_calls,
            success_rate=analytics.success_rate,
            avg_execution_time=analytics.avg_execution_time,
            calls_by_day=analytics.calls_by_day,
            calls_by_hour=analytics.calls_by_hour,
            common_errors=analytics.common_errors,
        )
        for analytics in analytics_list
    ]


@router.get(
    "/analytics/system",
    response_model=SystemMetricsResponse,
    summary="获取系统指标"
)
async def get_system_metrics():
    """获取系统实时指标"""
    from opspilot.analytics import get_analytics_engine
    
    engine = get_analytics_engine()
    metrics = engine.get_system_metrics()
    
    return SystemMetricsResponse(
        task_queue_size=metrics.task_queue_size,
        active_tasks=metrics.active_tasks,
        active_agents=metrics.active_agents,
        total_agents=metrics.total_agents,
        available_tools=metrics.available_tools,
        system_load=metrics.system_load,
        timestamp=metrics.timestamp.isoformat(),
    )


# ==================== Token 追踪 API ====================

@router.get(
    "/tokens/usage",
    summary="获取 Token 使用统计"
)
async def get_token_usage():
    """获取 Token 使用统计"""
    from opspilot.reliability import get_token_tracker
    
    tracker = get_token_tracker()
    return {
        "success": True,
        "data": tracker.get_usage_summary(),
    }


@router.get(
    "/tokens/by-agent",
    summary="按 Agent 分组获取 Token 使用"
)
async def get_token_usage_by_agent():
    """按 Agent 分组获取 Token 使用"""
    from opspilot.reliability import get_token_tracker
    
    tracker = get_token_tracker()
    return {
        "success": True,
        "data": tracker.get_usage_by_agent(),
    }


@router.get(
    "/tokens/by-model",
    summary="按模型分组获取 Token 使用"
)
async def get_token_usage_by_model():
    """按模型分组获取 Token 使用"""
    from opspilot.reliability import get_token_tracker
    
    tracker = get_token_tracker()
    return {
        "success": True,
        "data": tracker.get_usage_by_model(),
    }


@router.get(
    "/tokens/recent",
    summary="获取最近 Token 使用记录"
)
async def get_recent_token_usage(limit: int = 20):
    """获取最近 Token 使用记录"""
    from opspilot.reliability import get_token_tracker
    
    tracker = get_token_tracker()
    return {
        "success": True,
        "data": tracker.get_recent_usage(limit),
    }


@router.post(
    "/tokens/reset",
    summary="重置 Token 统计"
)
async def reset_token_usage():
    """重置 Token 统计"""
    from opspilot.reliability import get_token_tracker
    
    tracker = get_token_tracker()
    tracker.reset()
    return {
        "success": True,
        "message": "Token 统计已重置",
    }


# ==================== 可观测性 API ====================

@router.get(
    "/observability/status",
    summary="获取可观测性状态"
)
async def get_observability_status():
    """获取可观测性系统状态"""
    from opspilot.observability import get_studio, get_langsmith
    
    studio = get_studio()
    langsmith = get_langsmith()
    
    return {
        "success": True,
        "data": {
            "studio": {
                "available": studio.is_available(),
                "initialized": studio._initialized,
                "dashboard_url": studio.get_dashboard_url(),
            },
            "langsmith": {
                "available": langsmith.is_available(),
                "initialized": langsmith._initialized,
                "project": langsmith.config.project if langsmith._initialized else None,
                "project_url": langsmith.get_project_url(),
            },
        },
    }


@router.post(
    "/observability/studio/start",
    summary="启动 AgentScope Studio"
)
async def start_studio():
    """启动 AgentScope Studio"""
    from opspilot.observability import get_studio
    
    studio = get_studio()
    success = studio.start()
    
    return {
        "success": success,
        "message": "Studio 已启动" if success else "Studio 启动失败",
        "dashboard_url": studio.get_dashboard_url(),
    }


@router.post(
    "/observability/studio/stop",
    summary="停止 AgentScope Studio"
)
async def stop_studio():
    """停止 AgentScope Studio"""
    from opspilot.observability import get_studio
    
    studio = get_studio()
    studio.stop()
    
    return {
        "success": True,
        "message": "Studio 已停止",
    }


@router.post(
    "/observability/langsmith/start",
    summary="启动 LangSmith 追踪"
)
async def start_langsmith():
    """启动 LangSmith 追踪"""
    from opspilot.observability import get_langsmith
    
    langsmith = get_langsmith()
    success = langsmith.start()
    
    return {
        "success": success,
        "message": "LangSmith 已启动" if success else "LangSmith 启动失败",
        "project_url": langsmith.get_project_url(),
    }


@router.post(
    "/observability/langsmith/stop",
    summary="停止 LangSmith 追踪"
)
async def stop_langsmith():
    """停止 LangSmith 追踪"""
    from opspilot.observability import get_langsmith
    
    langsmith = get_langsmith()
    langsmith.stop()
    
    return {
        "success": True,
        "message": "LangSmith 已停止",
    }


# ==================== Pipeline API ====================

@router.get(
    "/pipeline/status",
    summary="获取 Pipeline 状态"
)
async def get_pipeline_status():
    """获取 Pipeline 执行状态"""
    from opspilot.observability import get_tracing
    
    tracing = get_tracing()
    
    return {
        "success": True,
        "data": {
            "active_spans": len(tracing._spans),
            "current_span": tracing._current_span.to_dict() if tracing._current_span else None,
        },
    }


@router.get(
    "/pipeline/trace/{trace_id}",
    summary="获取 Trace 详情"
)
async def get_trace_detail(trace_id: str):
    """获取 Trace 详情"""
    from opspilot.observability import get_tracing
    
    tracing = get_tracing()
    spans = tracing.get_trace(trace_id)
    
    return {
        "success": True,
        "data": {
            "trace_id": trace_id,
            "spans": [s.to_dict() for s in spans],
        },
    }


# ==================== 可靠性 API ====================

@router.get(
    "/reliability/stats",
    summary="获取可靠性统计"
)
async def get_reliability_stats():
    """获取可靠性模块统计"""
    from opspilot.reliability import get_token_tracker, ParallelToolExecutor
    
    tracker = get_token_tracker()
    
    return {
        "success": True,
        "data": {
            "token_tracker": tracker.get_total_usage(),
            "output_parsers": {
                "intent": get_intent_parser().get_stats() if _intent_parser else None,
                "plan": get_plan_parser().get_stats() if _plan_parser else None,
                "execution": get_execution_parser().get_stats() if _execution_parser else None,
                "verification": get_verification_parser().get_stats() if _verification_parser else None,
            },
        },
    }


# 导入解析器全局变量
from opspilot.reliability.output_parser import (
    _intent_parser,
    _plan_parser,
    _execution_parser,
    _verification_parser,
    get_intent_parser,
    get_plan_parser,
    get_execution_parser,
    get_verification_parser,
)


# ==================== 工具优化 API ====================

@router.post(
    "/tools/index",
    response_model=ToolIndexResponse,
    summary="构建工具索引",
    description="将工具定义向量化并构建索引"
)
async def build_tool_index(request: ToolIndexRequest):
    """构建工具索引"""
    from opspilot.tools import create_tool_index
    
    try:
        indexer = create_tool_index()
        indexed_count = indexer.build_index(request.tools)
        
        # 统计各类别工具数量
        categories = {}
        for tool in request.tools:
            category = tool.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1
        
        return ToolIndexResponse(
            success=True,
            message=f"成功索引 {indexed_count} 个工具",
            indexed_count=indexed_count,
            categories=categories,
        )
    except Exception as e:
        return ToolIndexResponse(
            success=False,
            message=f"索引构建失败: {str(e)}",
            indexed_count=0,
            categories={},
        )


@router.post(
    "/tools/retrieve",
    response_model=ToolRetrievalResponse,
    summary="检索相关工具",
    description="基于查询文本检索相关工具"
)
async def retrieve_tools(request: ToolRetrievalRequest):
    """检索相关工具"""
    import time
    from opspilot.tools import retrieve_tools as do_retrieve
    
    try:
        start_time = time.time()
        result = do_retrieve(
            query=request.query,
            max_tools=request.max_tools,
            max_tokens=request.max_tokens,
            strategy=request.strategy,
        )
        retrieval_time_ms = int((time.time() - start_time) * 1000)
        
        return ToolRetrievalResponse(
            success=True,
            message=f"检索到 {len(result.tools)} 个工具",
            tools=[tool.to_dict() for tool in result.tools],
            total_tokens=result.total_tokens,
            retrieval_time_ms=retrieval_time_ms,
        )
    except Exception as e:
        return ToolRetrievalResponse(
            success=False,
            message=f"检索失败: {str(e)}",
            tools=[],
            total_tokens=0,
            retrieval_time_ms=0,
        )


@router.post(
    "/tools/compress",
    response_model=ToolCompressResponse,
    summary="压缩工具描述",
    description="压缩工具描述以节省上下文空间"
)
async def compress_tools(request: ToolCompressRequest):
    """压缩工具描述"""
    from opspilot.tools import compress_tools as do_compress
    
    try:
        result = do_compress(
            tools=request.tools,
            level=request.level,
            max_tokens_per_tool=request.max_tokens_per_tool,
        )
        
        return ToolCompressResponse(
            success=True,
            message=f"压缩完成，压缩率: {result['compression_ratio']:.2%}",
            compressed_tools=result["compressed_tools"],
            original_tokens=result["original_tokens"],
            compressed_tokens=result["compressed_tokens"],
            compression_ratio=result["compression_ratio"],
        )
    except Exception as e:
        return ToolCompressResponse(
            success=False,
            message=f"压缩失败: {str(e)}",
            compressed_tools=[],
            original_tokens=0,
            compressed_tokens=0,
            compression_ratio=0.0,
        )


@router.post(
    "/tools/heal",
    response_model=ToolHealingResponse,
    summary="工具自愈",
    description="尝试自动恢复工具调用失败"
)
async def heal_tool_call(request: ToolHealingRequest):
    """工具自愈"""
    from opspilot.tools import create_healer
    from opspilot.tools.base import ToolContext
    
    try:
        healer = create_healer()
        context = ToolContext(
            task_id=None,
            tool_name=request.tool_name,
            params=request.params,
        )
        
        result = await healer.heal(
            context=context,
            error=request.error_info,
            max_retries=request.max_retries,
        )
        
        return ToolHealingResponse(
            success=result["success"],
            message="自愈成功" if result["success"] else "自愈失败",
            result=result.get("result"),
            strategy_used=result.get("strategy", ""),
            retry_count=result.get("retry_count", 0),
        )
    except Exception as e:
        return ToolHealingResponse(
            success=False,
            message=f"自愈失败: {str(e)}",
            result=None,
            strategy_used="",
            retry_count=0,
        )


@router.post(
    "/tools/context/select",
    response_model=ToolContextManagerResponse,
    summary="上下文管理",
    description="基于上下文预算选择合适的工具"
)
async def select_tools_for_context(request: ToolContextManagerRequest):
    """上下文管理"""
    from opspilot.tools import create_context_manager
    
    try:
        manager = create_context_manager()
        result = manager.select_tools(
            query=request.query,
            available_tools=request.available_tools,
            context_budget=request.context_budget,
        )
        
        return ToolContextManagerResponse(
            success=True,
            message=f"选择了 {len(result.selected_tools)} 个工具",
            selected_tools=result.selected_tools,
            total_tokens=result.total_tokens,
            selection_strategy=result.strategy,
        )
    except Exception as e:
        return ToolContextManagerResponse(
            success=False,
            message=f"选择失败: {str(e)}",
            selected_tools=[],
            total_tokens=0,
            selection_strategy="",
        )


# ==================== 记忆优化 API ====================

@router.post(
    "/memory/weight",
    response_model=MemoryWeightResponse,
    summary="计算记忆权重",
    description="计算记忆的重要性权重"
)
async def calculate_memory_weight(request: MemoryWeightRequest):
    """计算记忆权重"""
    from opspilot.memory import calculate_memory_weight as do_calculate
    
    try:
        weight, factors = do_calculate(
            content=request.content,
            metadata=request.metadata,
        )
        
        return MemoryWeightResponse(
            success=True,
            message=f"权重计算完成: {weight:.4f}",
            memory_id=request.memory_id,
            weight=weight,
            factors=factors,
        )
    except Exception as e:
        return MemoryWeightResponse(
            success=False,
            message=f"权重计算失败: {str(e)}",
            memory_id=request.memory_id,
            weight=0.0,
            factors={},
        )


@router.post(
    "/memory/conflict",
    response_model=MemoryConflictResponse,
    summary="检测记忆冲突",
    description="检测并解决记忆冲突"
)
async def detect_memory_conflicts(request: MemoryConflictRequest):
    """检测记忆冲突"""
    from opspilot.memory import resolve_memory_conflict as do_resolve
    
    try:
        result = do_resolve(
            memories=request.memories,
            check_type=request.check_type,
        )
        
        return MemoryConflictResponse(
            success=True,
            message=f"检测到 {len(result['conflicts'])} 个冲突",
            conflicts=result["conflicts"],
            resolutions=result["resolutions"],
            conflict_count=len(result["conflicts"]),
        )
    except Exception as e:
        return MemoryConflictResponse(
            success=False,
            message=f"冲突检测失败: {str(e)}",
            conflicts=[],
            resolutions=[],
            conflict_count=0,
        )


@router.post(
    "/memory/consolidate",
    response_model=MemoryConsolidationResponse,
    summary="记忆巩固",
    description="整合记忆并提取知识模式"
)
async def consolidate_memories(request: MemoryConsolidationRequest):
    """记忆巩固"""
    from opspilot.memory import consolidate_memories as do_consolidate
    
    try:
        result = do_consolidate(
            memories=request.memories,
            consolidation_type=request.consolidation_type,
            min_cluster_size=request.min_cluster_size,
        )
        
        return MemoryConsolidationResponse(
            success=True,
            message=f"巩固完成，压缩率: {result['reduction_ratio']:.2%}",
            clusters=result["clusters"],
            patterns=result["patterns"],
            consolidated_count=result["consolidated_count"],
            reduction_ratio=result["reduction_ratio"],
        )
    except Exception as e:
        return MemoryConsolidationResponse(
            success=False,
            message=f"巩固失败: {str(e)}",
            clusters=[],
            patterns=[],
            consolidated_count=0,
            reduction_ratio=0.0,
        )


@router.get(
    "/memory/stats",
    response_model=MemoryStatsResponse,
    summary="获取记忆统计",
    description="获取记忆系统的统计信息"
)
async def get_memory_stats():
    """获取记忆统计"""
    from opspilot.memory import MemoryManager
    
    try:
        manager = MemoryManager()
        # 这里应该从实际的记忆存储中获取统计数据
        # 目前返回示例数据
        return MemoryStatsResponse(
            success=True,
            message="统计获取成功",
            total_memories=100,
            weighted_memories=80,
            conflict_count=5,
            consolidated_memories=20,
            patterns_extracted=15,
        )
    except Exception as e:
        return MemoryStatsResponse(
            success=False,
            message=f"统计获取失败: {str(e)}",
            total_memories=0,
            weighted_memories=0,
            conflict_count=0,
            consolidated_memories=0,
            patterns_extracted=0,
        )


# ==================== 提供者管理 API ====================

@router.get(
    "/providers/status",
    response_model=ProviderStatusResponse,
    summary="获取提供者状态",
    description="获取当前所有提供者的配置状态"
)
async def get_provider_status():
    """获取提供者状态"""
    from opspilot.approval import ApprovalFactory, ApprovalProvider
    from opspilot.memory import MemoryFactory, MemoryProvider
    from opspilot.evaluation import EvaluationFactory, EvaluationProvider
    
    return ProviderStatusResponse(
        success=True,
        message="获取成功",
        approval_provider=ApprovalFactory.get_current_provider().value,
        memory_provider=MemoryFactory.get_current_provider().value,
        evaluation_provider=EvaluationFactory.get_current_provider().value,
    )


@router.post(
    "/providers/set",
    response_model=BaseResponse,
    summary="设置提供者",
    description="动态切换提供者"
)
async def set_provider(request: SetProviderRequest):
    """设置提供者"""
    try:
        if request.provider_type == "approval":
            from opspilot.approval import ApprovalFactory, ApprovalProvider
            provider_enum = ApprovalProvider(request.provider)
            ApprovalFactory.set_provider(provider_enum)
            message = f"审批提供者已切换为: {request.provider}"
        
        elif request.provider_type == "memory":
            from opspilot.memory import MemoryFactory, MemoryProvider
            provider_enum = MemoryProvider(request.provider)
            MemoryFactory.set_provider(provider_enum)
            message = f"记忆提供者已切换为: {request.provider}"
        
        elif request.provider_type == "evaluation":
            from opspilot.evaluation import EvaluationFactory, EvaluationProvider
            provider_enum = EvaluationProvider(request.provider)
            EvaluationFactory.set_provider(provider_enum)
            message = f"评估提供者已切换为: {request.provider}"
        
        else:
            return BaseResponse(
                success=False,
                message=f"不支持的提供者类型: {request.provider_type}",
            )
        
        return BaseResponse(
            success=True,
            message=message,
        )
    except Exception as e:
        return BaseResponse(
            success=False,
            message=f"设置失败: {str(e)}",
        )


@router.get(
    "/providers/list",
    response_model=ProviderListResponse,
    summary="获取提供者列表",
    description="获取所有可用的提供者及其信息"
)
async def list_providers():
    """获取提供者列表"""
    from opspilot.approval import ApprovalProvider
    from opspilot.approval.langchain_approval import LangChainApprovalHandler
    from opspilot.memory import MemoryProvider
    from opspilot.memory.reme_memory import ReMeMemory
    from opspilot.evaluation import EvaluationProvider
    from opspilot.evaluation.agentscope_evaluator import AgentScopeEvaluator
    
    # 检查框架可用性
    langchain_approval_available = LangChainApprovalHandler.is_available()
    reme_memory_available = ReMeMemory.is_available()
    agentscope_evaluator_available = AgentScopeEvaluator.is_available()
    
    # 审批提供者
    approval_providers = [
        ProviderInfo(
            name=ApprovalProvider.OPSPILOT.value,
            type="approval",
            available=True,
            description="OpsPilot自研审批系统",
            features=["审批规则配置", "超时自动批准", "多级审批"],
        ),
        ProviderInfo(
            name=ApprovalProvider.LANGCHAIN.value,
            type="approval",
            available=langchain_approval_available,
            description="LangChain人工审批回调",
            features=["工具调用拦截", "人工确认", "审批日志"],
        ),
    ]
    
    # 记忆提供者
    memory_providers = [
        ProviderInfo(
            name=MemoryProvider.OPSPILOT.value,
            type="memory",
            available=True,
            description="OpsPilot记忆管理",
            features=["权重计算", "冲突检测", "记忆巩固", "知识提取"],
        ),
        ProviderInfo(
            name=MemoryProvider.REME.value,
            type="memory",
            available=reme_memory_available,
            description="AgentScope ReMe记忆管理",
            features=["短期记忆", "长期记忆", "向量检索", "知识图谱"],
        ),
    ]
    
    # 评估提供者
    evaluation_providers = [
        ProviderInfo(
            name=EvaluationProvider.OPSPILOT.value,
            type="evaluation",
            available=True,
            description="OpsPilot评估器",
            features=["任务评估", "Agent评估", "性能统计"],
        ),
        ProviderInfo(
            name=EvaluationProvider.AGENTSCOPE.value,
            type="evaluation",
            available=agentscope_evaluator_available,
            description="AgentScope评估框架",
            features=["专业评估", "排行榜", "评估报告", "优化建议"],
        ),
    ]
    
    return ProviderListResponse(
        success=True,
        message="获取成功",
        approval_providers=approval_providers,
        memory_providers=memory_providers,
        evaluation_providers=evaluation_providers,
    )


# ==================== 定价博弈 API ====================

@router.post(
    "/pricing/negotiate",
    response_model=PricingNegotiateResponse,
    summary="定价博弈协商",
    description="启动多Agent博弈定价协商"
)
async def pricing_negotiate(request: PricingNegotiateRequest):
    """
    启动定价博弈协商
    
    通过CostAgent、MarketAgent、ProfitAgent三方博弈，生成最优定价
    """
    try:
        result = await pricing_api.negotiate(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"定价协商失败: {str(e)}")


@router.get(
    "/pricing/history",
    response_model=PricingHistoryResponse,
    summary="查询定价历史",
    description="查询定价博弈历史记录"
)
async def get_pricing_history(
    product_id: Optional[str] = None,
    limit: int = 20
):
    """查询定价历史记录"""
    request = PricingHistoryRequest(
        product_id=product_id,
        limit=limit
    )
    return await pricing_api.get_history(request)


@router.get(
    "/pricing/agents/status",
    response_model=PricingAgentStatusResponse,
    summary="获取Agent状态",
    description="获取定价Agent的状态信息"
)
async def get_pricing_agent_status():
    """获取定价Agent状态"""
    return await pricing_api.get_agent_status()


# ==================== 客服工单 API ====================

@router.post(
    "/customer-service/tickets",
    response_model=TicketCreateResponse,
    summary="创建工单",
    description="创建新的客服工单"
)
async def create_ticket(request: TicketCreateRequest):
    """创建客服工单"""
    try:
        result = await customer_service_api.create_ticket(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建工单失败: {str(e)}")


@router.post(
    "/customer-service/tickets/process",
    response_model=TicketProcessResponse,
    summary="处理工单",
    description="启动多Agent协作处理工单"
)
async def process_ticket(request: TicketProcessRequest):
    """
    处理工单（完整流程）
    
    通过Classifier、Router、Solver、Reviewer四个Agent协作处理
    """
    try:
        result = await customer_service_api.process_ticket(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理工单失败: {str(e)}")


@router.get(
    "/customer-service/tickets",
    response_model=TicketListResponse,
    summary="查询工单列表",
    description="查询工单列表"
)
async def list_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 20
):
    """查询工单列表"""
    return await customer_service_api.list_tickets(
        status=status,
        priority=priority,
        limit=limit
    )


@router.get(
    "/customer-service/tickets/{ticket_id}",
    summary="查询工单详情",
    description="查询指定工单的详细信息"
)
async def get_ticket(ticket_id: str):
    """查询工单详情"""
    result = await customer_service_api.get_ticket(ticket_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="工单不存在")
    return result


@router.get(


    "/customer-service/agents/status",


    response_model=AgentStatusResponse,


    summary="获取Agent状态",


    description="获取客服Agent的状态信息"


)


async def get_customer_service_agent_status():


    """获取客服Agent状态"""


    return await customer_service_api.get_agent_status()








# ==================== 队列管理 API ====================





@router.get(


    "/customer-service/queue/status",


    response_model=QueueStatusResponse,


    summary="获取队列状态",


    description="获取各队列的状态信息"


)


async def get_queue_status():


    """获取队列状态"""


    return await customer_service_api.get_queue_status()








# ==================== 生命周期管理 API ====================





@router.get(


    "/customer-service/tickets/{ticket_id}/lifecycle",


    response_model=TicketLifecycleResponse,


    summary="获取工单生命周期",


    description="获取工单的生命周期信息"


)


async def get_ticket_lifecycle(ticket_id: str):


    """获取工单生命周期"""


    return await customer_service_api.get_ticket_lifecycle(ticket_id)








# ==================== 知识库 API ====================





@router.post(


    "/customer-service/knowledge/query",


    response_model=KnowledgeQueryResponse,


    summary="查询知识库",


    description="从知识库中搜索相关解决方案"


)


async def query_knowledge(request: KnowledgeQueryRequest):


    """查询知识库"""


    return await customer_service_api.query_knowledge(request)








# ==================== 统计分析 API ====================





@router.get(


    "/customer-service/analytics",


    response_model=TicketAnalyticsResponse,


    summary="获取工单统计分析",


    description="获取工单的统计分析和报表数据"


)


async def get_ticket_analytics(


    start_date: Optional[str] = None,


    end_date: Optional[str] = None


):


    """获取工单统计分析"""


    return await customer_service_api.get_analytics(start_date, end_date)








# ==================== 智能分配 API ====================





@router.get(


    "/customer-service/agents",


    response_model=AgentListResponse,


    summary="获取Agent列表",


    description="获取所有可用的客服Agent"


)


async def get_agent_list():


    """获取Agent列表"""


    return await customer_service_api.get_agents()








@router.post(


    "/customer-service/tickets/assign",


    response_model=AssignmentResponse,


    summary="分配工单",


    description="将工单分配给合适的Agent"


)


async def assign_ticket(request: AssignmentRequest):


    """分配工单"""


    return await customer_service_api.assign_ticket(request)








# ==================== 升级 API ====================





@router.post(


    "/customer-service/tickets/escalate",


    response_model=EscalationResponse,


    summary="升级工单",


    description="将工单升级给专家处理"


)


async def escalate_ticket(request: EscalationRequest):


    """升级工单"""


    return await customer_service_api.escalate_ticket(request)








# ==================== 跟进 API ====================





@router.post(


    "/customer-service/tickets/followup",


    response_model=FollowUpResponse,


    summary="创建跟进",


    description="创建工单跟进记录"


)


async def create_followup(request: FollowUpRequest):


    """创建跟进"""


    return await customer_service_api.create_followup(request)








# ==================== 通知配置 API ====================


class BaseRequestModel(BaseResponse):
        """基础请求模型"""
    
        pass


class NotificationConfigRequest(BaseRequestModel):


    """通知配置请求"""


    webhook_url: Optional[str] = None


    slack_token: Optional[str] = None


    slack_channel: Optional[str] = None


    smtp_host: Optional[str] = None


    smtp_port: Optional[int] = None


    smtp_username: Optional[str] = None


    smtp_password: Optional[str] = None


    smtp_from_addr: Optional[str] = None








class NotificationStatusResponse(BaseResponse):


    """通知状态响应"""


    configured: bool = False


    webhook_enabled: bool = False


    slack_enabled: bool = False


    email_enabled: bool = False








@router.post(


    "/notification/config",


    response_model=BaseResponse,


    summary="配置通知服务",


    description="配置Webhook、Slack或邮件通知服务"


)


async def configure_notification(config: NotificationConfigRequest):


    """配置通知服务"""


    try:


        from opspilot.notification import init_notification_service


        


        smtp_config = None


        if config.smtp_host and config.smtp_username:


            smtp_config = {


                "host": config.smtp_host,


                "port": config.smtp_port or 587,


                "username": config.smtp_username,


                "password": config.smtp_password,


                "from_addr": config.smtp_from_addr or config.smtp_username,


            }


        


        init_notification_service(


            webhook_url=config.webhook_url,


            slack_token=config.slack_token,


            slack_channel=config.slack_channel,


            smtp_config=smtp_config,


        )


        


        return BaseResponse(


            success=True,


            message="通知服务配置成功"


        )


    except Exception as e:


        return BaseResponse(


            success=False,


            message=f"配置失败: {str(e)}"


        )








@router.get(


    "/notification/status",


    response_model=NotificationStatusResponse,


    summary="获取通知状态",


    description="获取当前通知服务配置状态"


)


async def get_notification_status():


    """获取通知服务状态"""


    from opspilot.notification import get_notification_service


    


    service = get_notification_service()


    if not service:


        return NotificationStatusResponse(configured=False)


    


    return NotificationStatusResponse(


        configured=service.is_configured(),


        webhook_enabled=bool(service.webhook_url),


        slack_enabled=bool(service.slack_token and service.slack_channel),


        email_enabled=bool(service.smtp_config),


    )








# Pydantic基础模型


class BaseRequestModel(BaseResponse):


    """基础请求模型"""


    pass










