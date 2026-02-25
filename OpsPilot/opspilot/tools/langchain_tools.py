"""
LangChain 工具适配模块

将 MCP 工具和 opspilot 工具转换为 LangChain Tool，符合文档要求。

文档原文：
- "工具封装：统一的 Tool Schema，对接 MCP"
- "LangChain 负责：原子工具封装与执行"
- "MCP 作为工具协议标准"

职责：
- 将 MCP 工具包装为 LangChain StructuredTool
- 提供工具注册和路由
- 支持工具检索和调用
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional, Type
from dataclasses import dataclass

from opspilot.tools.base import ToolSchema, ToolResult, ToolContext


# LangChain imports
try:
    from langchain_core.tools import BaseTool, StructuredTool, Tool
    from langchain_core.callbacks import CallbackManagerForToolRun
    from pydantic import BaseModel, create_model
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseTool = object
    StructuredTool = None
    Tool = None


def create_args_schema(tool_schema: ToolSchema) -> Optional[Type["BaseModel"]]:
    """
    根据工具 Schema 创建 Pydantic 模型
    
    LangChain StructuredTool 需要一个 Pydantic 模型作为参数 Schema
    """
    if not LANGCHAIN_AVAILABLE:
        return None
    
    if not tool_schema.input_schema:
        return None
    
    # 解析 JSON Schema 构建 Pydantic 字段
    fields = {}
    properties = tool_schema.input_schema.get("properties", {})
    required = set(tool_schema.input_schema.get("required", []))
    
    for name, prop in properties.items():
        prop_type = prop.get("type", "string")
        description = prop.get("description", "")
        
        # 类型映射
        type_map = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        
        python_type = type_map.get(prop_type, str)
        
        # 可选字段
        if name in required:
            fields[name] = (python_type, ...)
        else:
            fields[name] = (Optional[python_type], None)
    
    if not fields:
        return None
    
    # 动态创建 Pydantic 模型
    return create_model(
        f"{tool_schema.name}Args",
        **fields
    )


class MCPToolWrapper(BaseTool if LANGCHAIN_AVAILABLE else object):
    """
    MCP 工具包装器 - 将 MCP 工具包装为 LangChain Tool
    
    按文档要求，使用 MCP 作为工具协议标准，
    通过 LangChain Tool 接口执行。
    
    示例:
        >>> wrapper = MCPToolWrapper(
        ...     name="query_supplier",
        ...     description="查询供应商信息",
        ...     mcp_handler=supplier_handler,
        ... )
        >>> result = await wrapper.ainvoke({"supplier_id": "SUP001"})
    """
    
    name: str = ""
    description: str = ""
    args_schema: Optional[Type["BaseModel"]] = None
    
    def __init__(
        self,
        name: str,
        description: str,
        mcp_handler: Callable,
        tool_schema: Optional[ToolSchema] = None,
        args_schema: Optional[Type["BaseModel"]] = None,
        **kwargs,
    ):
        """
        初始化 MCP 工具包装器
        
        Args:
            name: 工具名称
            description: 工具描述
            mcp_handler: MCP 工具处理函数
            tool_schema: 工具 Schema（可选）
            args_schema: 参数 Schema（可选）
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain 未安装。请运行: pip install langchain-core"
            )
        
        # 生成参数 Schema
        if args_schema is None and tool_schema is not None:
            args_schema = create_args_schema(tool_schema)
        
        super().__init__(
            name=name,
            description=description,
            args_schema=args_schema,
            **kwargs,
        )
        
        self._mcp_handler = mcp_handler
        self._tool_schema = tool_schema
    
    def _run(
        self,
        run_manager: Optional["CallbackManagerForToolRun"] = None,
        **kwargs,
    ) -> str:
        """同步执行（LangChain Tool 接口）"""
        # 创建默认上下文
        context = ToolContext(task_id="default")
        
        # 调用 MCP 处理函数
        result = asyncio.run(self._mcp_handler(kwargs, context))
        
        if result.is_success():
            return str(result.data)
        else:
            return f"Error: {result.error}"
    
    async def _arun(
        self,
        run_manager: Optional["CallbackManagerForToolRun"] = None,
        **kwargs,
    ) -> str:
        """异步执行（LangChain Tool 接口）"""
        context = ToolContext(task_id="default")
        result = await self._mcp_handler(kwargs, context)
        
        if result.is_success():
            return str(result.data)
        else:
            return f"Error: {result.error}"


class OpsToolRegistry:
    """
    opspilot 工具注册表
    
    统一管理 MCP 工具，并提供 LangChain Tool 列表。
    
    示例:
        >>> registry = OpsToolRegistry()
        >>> registry.register_mcp_tool(tool_schema, handler)
        >>> lc_tools = registry.get_langchain_tools()
        >>> # lc_tools 可直接传给 LangChain Agent
    """
    
    def __init__(self):
        """初始化工具注册表"""
        self._tools: Dict[str, ToolSchema] = {}
        self._handlers: Dict[str, Callable] = {}
        self._lc_tools: Dict[str, "BaseTool"] = {}
    
    def register_mcp_tool(
        self,
        tool_schema: ToolSchema,
        handler: Callable,
    ) -> "MCPToolWrapper":
        """
        注册 MCP 工具
        
        Args:
            tool_schema: 工具 Schema
            handler: 工具处理函数
        
        Returns:
            MCPToolWrapper: LangChain Tool 包装器
        """
        self._tools[tool_schema.name] = tool_schema
        self._handlers[tool_schema.name] = handler
        
        # 创建 LangChain Tool
        if LANGCHAIN_AVAILABLE:
            lc_tool = MCPToolWrapper(
                name=tool_schema.name,
                description=tool_schema.description,
                mcp_handler=handler,
                tool_schema=tool_schema,
            )
            self._lc_tools[tool_schema.name] = lc_tool
            return lc_tool
        
        return None
    
    def register_from_server(self, server) -> List["BaseTool"]:
        """
        从 opspilot ToolServer 注册所有工具
        
        Args:
            server: BaseToolServer 实例
        
        Returns:
            List[BaseTool]: LangChain Tool 列表
        """
        lc_tools = []
        
        for schema in server.get_all_schemas():
            handler = server._handlers.get(schema.name)
            if handler:
                lc_tool = self.register_mcp_tool(schema, handler)
                if lc_tool:
                    lc_tools.append(lc_tool)
        
        return lc_tools
    
    def get_langchain_tools(self) -> List["BaseTool"]:
        """
        获取所有 LangChain Tool
        
        返回可直接传给 LangChain Agent 的工具列表
        
        Returns:
            List[BaseTool]: LangChain Tool 列表
        """
        return list(self._lc_tools.values())
    
    def get_tool(self, name: str) -> Optional["BaseTool"]:
        """获取指定工具"""
        return self._lc_tools.get(name)
    
    def has_tool(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self._tools
    
    def get_tool_schema(self, name: str) -> Optional[ToolSchema]:
        """获取工具 Schema"""
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """列出所有工具名称"""
        return list(self._tools.keys())


def create_langchain_tool(
    tool_schema: ToolSchema,
    handler: Callable,
) -> Optional["BaseTool"]:
    """
    创建 LangChain Tool 的便捷函数
    
    Args:
        tool_schema: 工具 Schema
        handler: 工具处理函数
    
    Returns:
        BaseTool: LangChain Tool 实例
    """
    if not LANGCHAIN_AVAILABLE:
        return None
    
    return MCPToolWrapper(
        name=tool_schema.name,
        description=tool_schema.description,
        mcp_handler=handler,
        tool_schema=tool_schema,
    )


def convert_tools_to_langchain(
    tools: Dict[str, ToolSchema],
    handlers: Dict[str, Callable],
) -> List["BaseTool"]:
    """
    批量转换工具为 LangChain Tool
    
    Args:
        tools: 工具 Schema 字典
        handlers: 处理函数字典
    
    Returns:
        List[BaseTool]: LangChain Tool 列表
    """
    lc_tools = []
    
    for name, schema in tools.items():
        handler = handlers.get(name)
        if handler:
            lc_tool = create_langchain_tool(schema, handler)
            if lc_tool:
                lc_tools.append(lc_tool)
    
    return lc_tools

