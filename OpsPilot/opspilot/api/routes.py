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

