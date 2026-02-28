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
    ObservabilityStatusResponse,
    TokenUsageResponse,
    AgentTokenUsageResponse,
    ModelTokenUsageResponse,
    # 数据库信息相关
    DatabaseSummaryResponse,
    SupplierListResponse,
    ProductListResponse,
    InventoryListResponse,
    WarehouseListResponse,
    # Skills相关
    SkillDefinition,
    SkillCreateRequest,
    SkillUpdateRequest,
    SkillListResponse,
    SkillResponse,
    SkillCategoryResponse,
    CloudSkillInfo,
    CloudSkillListResponse,
    CloudSkillDownloadRequest,
    CloudSkillDownloadResponse,
)
from opspilot.core.orchestrator import Orchestrator
from opspilot.core.sop_executor import SOPExecutor, SOPDefinition, create_order_sop, query_supplier_sop
from opspilot.tools.base import ToolRouter, ToolContext
from opspilot.tools.mcp import create_default_router
from opspilot.memory.short_term import ShortTermMemory
from opspilot.memory.knowledge import KnowledgeBase


# ==================== 依赖注入 ====================

_orchestrator_instance = None


def get_orchestrator() -> Orchestrator:
    """获取编排器实例"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = Orchestrator()
    return _orchestrator_instance


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


# ==================== 可观测性 API ====================

@router.get(
    "/observability/status",
    response_model=ObservabilityStatusResponse,
    summary="获取可观测性状态"
)
async def get_observability_status():
    """获取 AgentScope Studio 和 LangSmith 的状态"""
    from opspilot.observability import get_studio, get_langsmith
    
    studio = get_studio()
    langsmith = get_langsmith()
    
    return ObservabilityStatusResponse(
        studio={
            "available": studio.is_available(),
            "initialized": studio._initialized,
            "dashboard_url": studio.get_dashboard_url(),
        },
        langsmith={
            "available": langsmith.is_available(),
            "initialized": langsmith._initialized,
            "project": langsmith.config.project if langsmith.config else None,
            "project_url": langsmith.get_project_url() if langsmith.is_available() else None,
        },
    )


@router.post(
    "/observability/studio/start",
    response_model=BaseResponse,
    summary="启动 AgentScope Studio"
)
async def start_studio():
    """启动 AgentScope Studio"""
    from opspilot.observability import get_studio
    
    studio = get_studio()
    success = studio.start()
    
    return BaseResponse(
        success=success,
        message="Studio started successfully" if success else "Failed to start Studio",
    )


@router.post(
    "/observability/studio/stop",
    response_model=BaseResponse,
    summary="停止 AgentScope Studio"
)
async def stop_studio():
    """停止 AgentScope Studio"""
    from opspilot.observability import get_studio
    
    studio = get_studio()
    studio.stop()
    
    return BaseResponse(
        success=True,
        message="Studio stopped",
    )


@router.post(
    "/observability/langsmith/start",
    response_model=BaseResponse,
    summary="启动 LangSmith"
)
async def start_langsmith():
    """启动 LangSmith 追踪"""
    from opspilot.observability import get_langsmith
    
    langsmith = get_langsmith()
    success = langsmith.start()
    
    return BaseResponse(
        success=success,
        message="LangSmith started successfully" if success else "Failed to start LangSmith",
    )


@router.post(
    "/observability/langsmith/stop",
    response_model=BaseResponse,
    summary="停止 LangSmith"
)
async def stop_langsmith():
    """停止 LangSmith 追踪"""
    from opspilot.observability import get_langsmith
    
    langsmith = get_langsmith()
    langsmith.stop()
    
    return BaseResponse(
        success=True,
        message="LangSmith stopped",
    )


# ==================== Token 使用统计 API ====================

@router.get(
    "/tokens/usage",
    response_model=BaseResponse,
    summary="获取 Token 使用统计"
)
async def get_token_usage():
    """获取 Token 使用统计"""
    # TODO: 实现实际的 token 统计
    return BaseResponse(
        success=True,
        data={
            "total": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "record_count": 0,
            }
        },
    )


@router.get(
    "/tokens/by-agent",
    response_model=BaseResponse,
    summary="获取按 Agent 的 Token 使用统计"
)
async def get_token_by_agent():
    """获取按 Agent 分组的 Token 使用统计"""
    # TODO: 实现实际的 token 统计
    return BaseResponse(
        success=True,
        data={},
    )


@router.get(
    "/tokens/by-model",
    response_model=BaseResponse,
    summary="获取按模型的 Token 使用统计"
)
async def get_token_by_model():
    """获取按模型分组的 Token 使用统计"""
    # TODO: 实现实际的 token 统计
    return BaseResponse(
        success=True,
        data={},
    )


@router.post(
    "/tokens/reset",
    response_model=BaseResponse,
    summary="重置 Token 统计"
)
async def reset_token_stats():
    """重置 Token 统计数据"""
    # TODO: 实现实际的 token 重置
    return BaseResponse(
        success=True,
        message="Token stats reset successfully",
    )


# ============================================
# 数据库信息查询接口
# ============================================

# 模拟数据存储
MOCK_SUPPLIERS = [
    {
        "supplier_id": "SUP001",
        "name": "深圳华强电子",
        "short_name": "华强电子",
        "region": "华南",
        "province": "广东",
        "city": "深圳",
        "address": "深圳市福田区华强北",
        "rating": 4.8,
        "rating_count": 256,
        "main_category": "电子元器件",
        "contact": "张经理",
        "phone": "0755-12345678",
        "email": "hq@supplier.com",
        "payment_terms": "月结30天",
        "min_order_amount": 5000,
        "delivery_days": 3,
        "certifications": ["ISO9001", "CE"],
        "status": "active",
        "cooperation_years": 5,
    },
    {
        "supplier_id": "SUP002",
        "name": "上海中芯供应链",
        "short_name": "中芯供应链",
        "region": "华东",
        "province": "上海",
        "city": "上海",
        "address": "上海市浦东新区张江高科",
        "rating": 4.5,
        "rating_count": 128,
        "main_category": "芯片",
        "contact": "李经理",
        "phone": "021-87654321",
        "email": "supply@supplier.com",
        "payment_terms": "月结60天",
        "min_order_amount": 10000,
        "delivery_days": 7,
        "certifications": ["ISO9001", "ISO14001"],
        "status": "active",
        "cooperation_years": 3,
    },
    {
        "supplier_id": "SUP003",
        "name": "北京东方电子",
        "short_name": "东方电子",
        "region": "华北",
        "province": "北京",
        "city": "北京",
        "address": "北京市海淀区中关村",
        "rating": 4.2,
        "rating_count": 89,
        "main_category": "传感器",
        "contact": "王经理",
        "phone": "010-12345678",
        "email": "east@supplier.com",
        "payment_terms": "预付30%+月结70%",
        "min_order_amount": 8000,
        "delivery_days": 5,
        "certifications": ["CE", "RoHS"],
        "status": "active",
        "cooperation_years": 2,
    },
]

MOCK_PRODUCTS = [
    {
        "sku": "SKU001",
        "name": "电阻 100Ω 0805",
        "category": "被动元件",
        "sub_category": "电阻",
        "base_price": 0.05,
        "currency": "CNY",
        "unit": "个",
        "specifications": {"resistance": "100Ω", "size": "0805", "precision": "1%"},
        "description": "贴片电阻 100Ω 1% 0805",
        "safety_stock": 10000,
        "status": "active",
    },
    {
        "sku": "SKU002",
        "name": "电容 10μF 0805",
        "category": "被动元件",
        "sub_category": "电容",
        "base_price": 0.08,
        "currency": "CNY",
        "unit": "个",
        "specifications": {"capacitance": "10μF", "size": "0805", "voltage": "25V"},
        "description": "贴片电容 10μF 25V 0805",
        "safety_stock": 8000,
        "status": "active",
    },
    {
        "sku": "SKU003",
        "name": "STM32F103C8T6",
        "category": "集成电路",
        "sub_category": "MCU",
        "base_price": 12.5,
        "currency": "CNY",
        "unit": "个",
        "specifications": {"core": "ARM Cortex-M3", "flash": "64KB", "ram": "20KB"},
        "description": "STM32F103C8T6 微控制器",
        "safety_stock": 500,
        "status": "active",
    },
    {
        "sku": "SKU004",
        "name": "ESP32-WROOM-32",
        "category": "集成电路",
        "sub_category": "无线通信",
        "base_price": 18.0,
        "currency": "CNY",
        "unit": "个",
        "specifications": {"wifi": "802.11 b/g/n", "bluetooth": "4.2 BR/LE", "flash": "4MB"},
        "description": "ESP32 WiFi+蓝牙模块",
        "safety_stock": 300,
        "status": "active",
    },
    {
        "sku": "SKU005",
        "name": "LM358 双运放",
        "category": "集成电路",
        "sub_category": "运放",
        "base_price": 0.6,
        "currency": "CNY",
        "unit": "个",
        "specifications": {"channels": 2, "bandwidth": "700kHz", "voltage": "3V-32V"},
        "description": "LM358 双运算放大器",
        "safety_stock": 2000,
        "status": "active",
    },
]

MOCK_INVENTORY = [
    {"sku": "SKU001", "warehouse_id": "WH001", "quantity": 50000, "available": 45000, "reserved": 5000, "location": "A区-01-01", "batch_number": "B20240101", "status": "normal"},
    {"sku": "SKU002", "warehouse_id": "WH001", "quantity": 30000, "available": 28000, "reserved": 2000, "location": "A区-01-02", "batch_number": "B20240102", "status": "normal"},
    {"sku": "SKU003", "warehouse_id": "WH001", "quantity": 2000, "available": 1800, "reserved": 200, "location": "B区-02-01", "batch_number": "B20240103", "status": "normal"},
    {"sku": "SKU004", "warehouse_id": "WH002", "quantity": 1500, "available": 1500, "reserved": 0, "location": "C区-01-01", "batch_number": "B20240104", "status": "normal"},
    {"sku": "SKU005", "warehouse_id": "WH001", "quantity": 10000, "available": 9000, "reserved": 1000, "location": "A区-02-01", "batch_number": "B20240105", "status": "normal"},
]

MOCK_WAREHOUSES = [
    {
        "warehouse_id": "WH001",
        "name": "深圳中心仓",
        "region": "华南",
        "province": "广东",
        "city": "深圳",
        "address": "深圳市宝安区沙井街道",
        "capacity_sqm": 5000,
        "type": "中心仓",
        "manager": "陈主管",
        "phone": "0755-11111111",
        "status": "active",
    },
    {
        "warehouse_id": "WH002",
        "name": "上海分仓",
        "region": "华东",
        "province": "上海",
        "city": "上海",
        "address": "上海市嘉定区",
        "capacity_sqm": 3000,
        "type": "分仓",
        "manager": "刘主管",
        "phone": "021-22222222",
        "status": "active",
    },
    {
        "warehouse_id": "WH003",
        "name": "北京分仓",
        "region": "华北",
        "province": "北京",
        "city": "北京",
        "address": "北京市顺义区",
        "capacity_sqm": 2000,
        "type": "分仓",
        "manager": "赵主管",
        "phone": "010-33333333",
        "status": "active",
    },
]

# Skills 存储
MOCK_SKILLS: Dict[str, Dict[str, Any]] = {}


@router.get(
    "/database/summary",
    response_model=DatabaseSummaryResponse,
    summary="获取数据库概览",
    description="获取供应商、商品、库存、仓库等数据概览"
)
async def get_database_summary():
    """获取数据库概览"""
    return DatabaseSummaryResponse(
        success=True,
        message="获取成功",
        total_suppliers=len(MOCK_SUPPLIERS),
        total_products=len(MOCK_PRODUCTS),
        total_inventory=len(MOCK_INVENTORY),
        total_warehouses=len(MOCK_WAREHOUSES),
        total_orders=15,
        total_logistics=8,
    )


@router.get(
    "/database/suppliers",
    response_model=SupplierListResponse,
    summary="获取供应商列表",
    description="获取所有供应商信息"
)
async def get_suppliers(
    region: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    """获取供应商列表"""
    suppliers = MOCK_SUPPLIERS.copy()
    
    if region:
        suppliers = [s for s in suppliers if s.get("region") == region]
    if status:
        suppliers = [s for s in suppliers if s.get("status") == status]
    
    total = len(suppliers)
    suppliers = suppliers[offset:offset + limit]
    
    return SupplierListResponse(
        success=True,
        message="获取成功",
        suppliers=suppliers,
        total=total,
    )


@router.get(
    "/database/suppliers/{supplier_id}",
    response_model=BaseResponse,
    summary="获取单个供应商详情",
    description="获取指定供应商的详细信息"
)
async def get_supplier_detail(supplier_id: str):
    """获取供应商详情"""
    supplier = next((s for s in MOCK_SUPPLIERS if s["supplier_id"] == supplier_id), None)
    
    if not supplier:
        raise HTTPException(status_code=404, detail=f"供应商不存在: {supplier_id}")
    
    return BaseResponse(
        success=True,
        message="获取成功",
        data=supplier,
    )


@router.get(
    "/database/products",
    response_model=ProductListResponse,
    summary="获取商品列表",
    description="获取所有商品信息"
)
async def get_products(
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    """获取商品列表"""
    products = MOCK_PRODUCTS.copy()
    
    if category:
        products = [p for p in products if p.get("category") == category]
    if status:
        products = [p for p in products if p.get("status") == status]
    
    total = len(products)
    products = products[offset:offset + limit]
    
    return ProductListResponse(
        success=True,
        message="获取成功",
        products=products,
        total=total,
    )


@router.get(
    "/database/products/{sku}",
    response_model=BaseResponse,
    summary="获取单个商品详情",
    description="获取指定商品的详细信息"
)
async def get_product_detail(sku: str):
    """获取商品详情"""
    product = next((p for p in MOCK_PRODUCTS if p["sku"] == sku), None)
    
    if not product:
        raise HTTPException(status_code=404, detail=f"商品不存在: {sku}")
    
    return BaseResponse(
        success=True,
        message="获取成功",
        data=product,
    )


@router.get(
    "/database/inventory",
    response_model=InventoryListResponse,
    summary="获取库存列表",
    description="获取所有库存信息"
)
async def get_inventory(
    warehouse_id: Optional[str] = None,
    sku: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    """获取库存列表"""
    inventory = MOCK_INVENTORY.copy()
    
    if warehouse_id:
        inventory = [i for i in inventory if i.get("warehouse_id") == warehouse_id]
    if sku:
        inventory = [i for i in inventory if i.get("sku") == sku]
    
    total = len(inventory)
    inventory = inventory[offset:offset + limit]
    
    return InventoryListResponse(
        success=True,
        message="获取成功",
        inventory=inventory,
        total=total,
    )


@router.get(
    "/database/warehouses",
    response_model=WarehouseListResponse,
    summary="获取仓库列表",
    description="获取所有仓库信息"
)
async def get_warehouses(
    region: Optional[str] = None,
    status: Optional[str] = None,
):
    """获取仓库列表"""
    warehouses = MOCK_WAREHOUSES.copy()
    
    if region:
        warehouses = [w for w in warehouses if w.get("region") == region]
    if status:
        warehouses = [w for w in warehouses if w.get("status") == status]
    
    return WarehouseListResponse(
        success=True,
        message="获取成功",
        warehouses=warehouses,
        total=len(warehouses),
    )


from opspilot.api.skills_storage import get_skills_storage, SkillsStorage


# Skills 存储管理
def get_skills_storage_dep() -> SkillsStorage:
    """获取 Skills 存储管理器依赖"""
    return get_skills_storage()


# ============================================
# Skills 管理接口
# ============================================

@router.get(
    "/skills",
    response_model=SkillListResponse,
    summary="获取 Skills 列表",
    description="获取所有已配置的 Skills"
)
async def list_skills(
    category: Optional[str] = None,
    enabled: Optional[bool] = None,
    storage: SkillsStorage = Depends(get_skills_storage_dep),
):
    """获取 Skills 列表"""
    skills = list(storage._skills_cache.values())
    
    if category:
        skills = [s for s in skills if s.get("category") == category]
    if enabled is not None:
        skills = [s for s in skills if s.get("enabled") == enabled]
    
    return SkillListResponse(
        success=True,
        message="获取成功",
        skills=skills,
        total=len(skills),
    )


@router.get(
    "/skills/categories",
    response_model=SkillCategoryResponse,
    summary="获取 Skill 分类",
    description="获取所有 Skill 分类及其数量"
)
async def get_skill_categories(
    storage: SkillsStorage = Depends(get_skills_storage_dep),
):
    """获取 Skill 分类"""
    categories = {}
    for skill in storage._skills_cache.values():
        cat = skill.get("category", "未分类")
        if cat not in categories:
            categories[cat] = {"name": cat, "count": 0}
        categories[cat]["count"] += 1
    
    return SkillCategoryResponse(
        success=True,
        message="获取成功",
        categories=list(categories.values()),
    )


# ==================== 云端技能市场路由（需要在 /skills/{skill_id} 之前）====================

@router.get(
    "/skills/cloud",
    response_model=CloudSkillListResponse,
    summary="获取云端技能市场",
    description="从云端获取可下载的技能列表"
)
async def get_cloud_skills(
    category: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    """获取云端技能市场列表"""
    skills = CLOUD_SKILLS_MARKET.copy()
    
    if category:
        skills = [s for s in skills if s.get("category") == category]
    
    if search:
        search_lower = search.lower()
        skills = [
            s for s in skills 
            if search_lower in s.get("name", "").lower() 
            or search_lower in s.get("description", "").lower()
            or any(search_lower in tag.lower() for tag in s.get("tags", []))
        ]
    
    total = len(skills)
    start = (page - 1) * page_size
    end = start + page_size
    skills_page = skills[start:end]
    
    return CloudSkillListResponse(
        success=True,
        message="获取成功",
        skills=skills_page,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/skills/cloud/categories",
    summary="获取云端技能分类",
    description="获取云端技能市场的分类信息"
)
async def get_cloud_skill_categories():
    """获取云端技能分类"""
    categories = {}
    for skill in CLOUD_SKILLS_MARKET:
        cat = skill.get("category", "未分类")
        if cat not in categories:
            categories[cat] = {"name": cat, "count": 0, "downloads": 0}
        categories[cat]["count"] += 1
        categories[cat]["downloads"] += skill.get("downloads", 0)
    
    return {
        "success": True,
        "message": "获取成功",
        "categories": list(categories.values()),
    }


@router.get(
    "/skills/cloud/{skill_id}",
    response_model=CloudSkillInfo,
    summary="获取云端技能详情",
    description="获取指定云端技能的详细信息"
)
async def get_cloud_skill_detail(skill_id: str):
    """获取云端技能详情"""
    for skill in CLOUD_SKILLS_MARKET:
        if skill.get("id") == skill_id:
            return {
                "success": True,
                "message": "获取成功",
                "skill": skill,
            }
    
    raise HTTPException(status_code=404, detail=f"云端技能不存在: {skill_id}")


@router.post(
    "/skills/cloud/download",
    response_model=CloudSkillDownloadResponse,
    summary="从云端下载技能",
    description="从云端市场下载技能到本地"
)
async def download_skill_from_cloud(
    request: CloudSkillDownloadRequest,
    storage: SkillsStorage = Depends(get_skills_storage_dep),
):
    """从云端下载技能"""
    cloud_skill = None
    for skill in CLOUD_SKILLS_MARKET:
        if skill.get("id") == request.skill_id:
            cloud_skill = skill
            break
    
    if not cloud_skill:
        raise HTTPException(status_code=404, detail=f"云端技能不存在: {request.skill_id}")
    
    # 检查是否已存在
    if storage.get_skill(request.skill_id):
        return CloudSkillDownloadResponse(
            success=False,
            message="技能已存在，无需重复下载",
            skill=None,
        )
    
    local_skill = {
        "id": cloud_skill["id"],
        "name": cloud_skill["name"],
        "description": cloud_skill["description"],
        "category": cloud_skill["category"],
        "version": request.version or cloud_skill["version"],
        "author": cloud_skill["author"],
        "input_schema": cloud_skill.get("input_schema", {}),
        "output_schema": cloud_skill.get("output_schema", {}),
        "parameters": cloud_skill.get("parameters", []),
        "examples": cloud_skill.get("examples", []),
        "tags": cloud_skill.get("tags", []),
        "enabled": True,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    
    # 保存到文件系统
    storage.save_skill(request.skill_id, local_skill)
    
    return CloudSkillDownloadResponse(
        success=True,
        message="下载成功",
        skill=local_skill,
    )


# ==================== 本地 Skills 路由 ====================

@router.get(
    "/skills/{skill_id}",
    response_model=SkillResponse,
    summary="获取单个 Skill",
    description="获取指定 Skill 的详细信息"
)
async def get_skill(
    skill_id: str,
    storage: SkillsStorage = Depends(get_skills_storage_dep),
):
    """获取 Skill 详情"""
    skill = storage.get_skill(skill_id)
    
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill 不存在: {skill_id}")
    
    return SkillResponse(
        success=True,
        message="获取成功",
        skill=skill,
    )


@router.post(
    "/skills",
    response_model=SkillResponse,
    summary="创建 Skill",
    description="创建新的 Skill 定义"
)
async def create_skill(
    request: SkillCreateRequest,
    storage: SkillsStorage = Depends(get_skills_storage_dep),
):
    """创建 Skill"""
    import uuid
    from datetime import datetime
    
    skill_id = f"skill_{uuid.uuid4().hex[:8]}"
    now = datetime.now().isoformat()
    
    skill = {
        "id": skill_id,
        "name": request.name,
        "description": request.description,
        "category": request.category,
        "version": request.version,
        "enabled": True,
        "input_schema": request.input_schema,
        "output_schema": request.output_schema,
        "parameters": request.parameters,
        "examples": request.examples,
        "tags": request.tags,
        "author": request.author,
        "created_at": now,
        "updated_at": now,
    }
    
    # 保存到文件系统
    storage.save_skill(skill_id, skill)
    
    return SkillResponse(
        success=True,
        message="创建成功",
        skill=skill,
    )


@router.put(
    "/skills/{skill_id}",
    response_model=SkillResponse,
    summary="更新 Skill",
    description="更新指定 Skill 的定义"
)
async def update_skill(
    skill_id: str,
    request: SkillUpdateRequest,
    storage: SkillsStorage = Depends(get_skills_storage_dep),
):
    """更新 Skill"""
    skill = storage.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill 不存在: {skill_id}")
    
    from datetime import datetime
    
    # 更新字段
    update_data = request.model_dump(exclude_unset=True)
    skill.update(update_data)
    skill["updated_at"] = datetime.now().isoformat()
    
    # 保存到文件系统
    storage.save_skill(skill_id, skill)
    
    return SkillResponse(
        success=True,
        message="更新成功",
        skill=skill,
    )


@router.delete(
    "/skills/{skill_id}",
    response_model=BaseResponse,
    summary="删除 Skill",
    description="删除指定的 Skill"
)
async def delete_skill(
    skill_id: str,
    storage: SkillsStorage = Depends(get_skills_storage_dep),
):
    """删除 Skill"""
    skill = storage.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill 不存在: {skill_id}")
    
    storage.delete_skill(skill_id)
    
    return BaseResponse(
        success=True,
        message="删除成功",
    )


@router.post(
    "/skills/{skill_id}/toggle",
    response_model=SkillResponse,
    summary="启用/禁用 Skill",
    description="切换 Skill 的启用状态"
)
async def toggle_skill(
    skill_id: str,
    storage: SkillsStorage = Depends(get_skills_storage_dep),
):
    """切换 Skill 启用状态"""
    skill = storage.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill 不存在: {skill_id}")
    
    from datetime import datetime
    
    skill["enabled"] = not skill.get("enabled", True)
    skill["updated_at"] = datetime.now().isoformat()
    
    # 保存到文件系统
    storage.save_skill(skill_id, skill)
    
    return SkillResponse(
        success=True,
        message=f"Skill 已{'启用' if skill['enabled'] else '禁用'}",
        skill=skill,
    )


# ============================================
# 云端 Skills 接口
# ============================================

# 模拟云端技能市场数据
CLOUD_SKILLS_MARKET = [
    {
        "id": "cloud-skill-001",
        "name": "电商订单处理",
        "description": "自动处理电商平台订单，包括订单确认、库存检查、发货处理等流程",
        "category": "电商",
        "version": "1.2.0",
        "author": "OpsPilot Team",
        "downloads": 1520,
        "rating": 4.8,
        "tags": ["电商", "订单", "自动化"],
        "created_at": "2024-01-15T10:00:00Z",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "订单ID"},
                "action": {"type": "string", "enum": ["confirm", "cancel", "ship"]}
            },
            "required": ["order_id"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"}
            }
        },
        "parameters": [
            {"name": "order_id", "type": "string", "required": True, "description": "订单ID"},
            {"name": "action", "type": "string", "required": True, "description": "操作类型"}
        ],
        "examples": [
            {"input": {"order_id": "ORD001", "action": "confirm"}, "output": {"success": True}}
        ],
        "enabled": True,
    },
    {
        "id": "cloud-skill-002",
        "name": "物流追踪",
        "description": "查询物流状态，跟踪包裹运输进度，支持多家快递公司",
        "category": "物流",
        "version": "1.0.5",
        "author": "Logistics Pro",
        "downloads": 980,
        "rating": 4.5,
        "tags": ["物流", "追踪", "快递"],
        "created_at": "2024-02-20T10:00:00Z",
        "input_schema": {
            "type": "object",
            "properties": {
                "tracking_no": {"type": "string", "description": "快递单号"},
                "carrier": {"type": "string", "description": "快递公司"}
            },
            "required": ["tracking_no"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "location": {"type": "string"},
                "events": {"type": "array"}
            }
        },
        "parameters": [
            {"name": "tracking_no", "type": "string", "required": True, "description": "快递单号"},
            {"name": "carrier", "type": "string", "required": False, "description": "快递公司"}
        ],
        "examples": [],
        "enabled": True,
    },
    {
        "id": "cloud-skill-003",
        "name": "库存预警",
        "description": "监控商品库存水平，当低于安全库存时自动发送预警通知",
        "category": "库存",
        "version": "2.1.0",
        "author": "Inventory Master",
        "downloads": 2340,
        "rating": 4.9,
        "tags": ["库存", "预警", "监控"],
        "created_at": "2024-01-05T10:00:00Z",
        "input_schema": {
            "type": "object",
            "properties": {
                "sku": {"type": "string", "description": "商品SKU"},
                "threshold": {"type": "number", "description": "预警阈值"}
            },
            "required": ["sku"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "alert": {"type": "boolean"},
                "current_stock": {"type": "number"},
                "recommendation": {"type": "string"}
            }
        },
        "parameters": [
            {"name": "sku", "type": "string", "required": True, "description": "商品SKU"},
            {"name": "threshold", "type": "number", "required": False, "description": "预警阈值"}
        ],
        "examples": [],
        "enabled": True,
    },
    {
        "id": "cloud-skill-004",
        "name": "供应商评估",
        "description": "基于历史合作数据对供应商进行综合评估，包括价格、质量、交货及时性等维度",
        "category": "采购",
        "version": "1.5.2",
        "author": "Procurement AI",
        "downloads": 756,
        "rating": 4.6,
        "tags": ["供应商", "评估", "采购"],
        "created_at": "2024-03-01T10:00:00Z",
        "input_schema": {
            "type": "object",
            "properties": {
                "supplier_id": {"type": "string", "description": "供应商ID"},
                "period": {"type": "string", "description": "评估周期"}
            },
            "required": ["supplier_id"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "score": {"type": "number"},
                "dimensions": {"type": "object"},
                "recommendation": {"type": "string"}
            }
        },
        "parameters": [
            {"name": "supplier_id", "type": "string", "required": True, "description": "供应商ID"},
            {"name": "period", "type": "string", "required": False, "description": "评估周期"}
        ],
        "examples": [],
        "enabled": True,
    },
    {
        "id": "cloud-skill-005",
        "name": "智能客服回复",
        "description": "基于AI大模型生成智能客服回复，支持多种场景和问题类型",
        "category": "客服",
        "version": "3.0.1",
        "author": "AI Support",
        "downloads": 3200,
        "rating": 4.7,
        "tags": ["客服", "AI", "回复"],
        "created_at": "2024-02-10T10:00:00Z",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "客户问题"},
                "context": {"type": "object", "description": "上下文信息"}
            },
            "required": ["query"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "reply": {"type": "string"},
                "confidence": {"type": "number"}
            }
        },
        "parameters": [
            {"name": "query", "type": "string", "required": True, "description": "客户问题"},
            {"name": "context", "type": "object", "required": False, "description": "上下文信息"}
        ],
        "examples": [],
        "enabled": True,
    },
    {
        "id": "cloud-skill-006",
        "name": "价格比价",
        "description": "自动采集多个电商平台的商品价格，进行比价分析",
        "category": "价格",
        "version": "1.8.0",
        "author": "Price Hunter",
        "downloads": 1890,
        "rating": 4.4,
        "tags": ["价格", "比价", "电商"],
        "created_at": "2024-01-25T10:00:00Z",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string", "description": "商品名称"},
                "platforms": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["product_name"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "prices": {"type": "array"},
                "lowest_price": {"type": "number"},
                "recommendation": {"type": "string"}
            }
        },
        "parameters": [
            {"name": "product_name", "type": "string", "required": True, "description": "商品名称"},
            {"name": "platforms", "type": "array", "required": False, "description": "平台列表"}
        ],
        "examples": [],
        "enabled": True,
    },
]


@router.get(
    "/skills/cloud",
    response_model=CloudSkillListResponse,
    summary="获取云端技能市场",
    description="从云端获取可下载的技能列表"
)
async def get_cloud_skills(
    category: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    """获取云端技能市场列表"""
    skills = CLOUD_SKILLS_MARKET.copy()
    
    # 按分类筛选
    if category:
        skills = [s for s in skills if s.get("category") == category]
    
    # 按关键词搜索
    if search:
        search_lower = search.lower()
        skills = [
            s for s in skills 
            if search_lower in s.get("name", "").lower() 
            or search_lower in s.get("description", "").lower()
            or any(search_lower in tag.lower() for tag in s.get("tags", []))
        ]
    
    # 分页
    total = len(skills)
    start = (page - 1) * page_size
    end = start + page_size
    skills_page = skills[start:end]
    
    return CloudSkillListResponse(
        success=True,
        message="获取成功",
        skills=skills_page,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/skills/cloud/categories",
    summary="获取云端技能分类",
    description="获取云端技能市场的分类信息"
)
async def get_cloud_skill_categories():
    """获取云端技能分类"""
    categories = {}
    for skill in CLOUD_SKILLS_MARKET:
        cat = skill.get("category", "未分类")
        if cat not in categories:
            categories[cat] = {"name": cat, "count": 0, "downloads": 0}
        categories[cat]["count"] += 1
        categories[cat]["downloads"] += skill.get("downloads", 0)
    
    return {
        "success": True,
        "message": "获取成功",
        "categories": list(categories.values()),
    }


@router.get(
    "/skills/cloud/{skill_id}",
    response_model=CloudSkillInfo,
    summary="获取云端技能详情",
    description="获取指定云端技能的详细信息"
)
async def get_cloud_skill_detail(skill_id: str):
    """获取云端技能详情"""
    for skill in CLOUD_SKILLS_MARKET:
        if skill.get("id") == skill_id:
            return {
                "success": True,
                "message": "获取成功",
                "skill": skill,
            }
    
    raise HTTPException(status_code=404, detail=f"云端技能不存在: {skill_id}")


@router.post(
    "/skills/cloud/download",
    response_model=CloudSkillDownloadResponse,
    summary="从云端下载技能",
    description="从云端市场下载技能到本地"
)
async def download_skill_from_cloud_2(
    request: CloudSkillDownloadRequest,
    storage: SkillsStorage = Depends(get_skills_storage_dep),
):
    """从云端下载技能"""
    # 查找云端技能
    cloud_skill = None
    for skill in CLOUD_SKILLS_MARKET:
        if skill.get("id") == request.skill_id:
            cloud_skill = skill
            break
    
    if not cloud_skill:
        raise HTTPException(status_code=404, detail=f"云端技能不存在: {request.skill_id}")
    
    # 检查是否已存在
    if storage.get_skill(request.skill_id):
        return CloudSkillDownloadResponse(
            success=False,
            message="技能已存在，无需重复下载",
            skill=None,
        )
    
    # 创建本地技能
    local_skill = {
        "id": cloud_skill["id"],
        "name": cloud_skill["name"],
        "description": cloud_skill["description"],
        "category": cloud_skill["category"],
        "version": request.version or cloud_skill["version"],
        "author": cloud_skill["author"],
        "input_schema": cloud_skill.get("input_schema", {}),
        "output_schema": cloud_skill.get("output_schema", {}),
        "parameters": cloud_skill.get("parameters", []),
        "examples": cloud_skill.get("examples", []),
        "tags": cloud_skill.get("tags", []),
        "enabled": True,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    
    # 保存到文件系统
    storage.save_skill(request.skill_id, local_skill)
    
    return CloudSkillDownloadResponse(
        success=True,
        message=f"成功下载技能: {cloud_skill['name']}",
        skill=local_skill,
    )


