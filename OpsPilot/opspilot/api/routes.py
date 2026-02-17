"""
API 路由定义

职责：
- 定义 API 端点
- 请求处理
- 响应生成
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks

from opspilot.api.schemas import (
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

