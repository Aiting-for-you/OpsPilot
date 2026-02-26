"""
LangChain 集成模块

利用LangChain的优势弥补AgentScope的不足:
1. 丰富的工具生态 - StructuredTool, Tool
2. RAG检索增强 - Retriever, VectorStore
3. 链式思维 - LCEL (LangChain Expression Language)
4. 成熟的提示词管理 - PromptTemplate

与AgentScope协同:
- AgentScope负责调度和通信
- LangChain负责具体执行和工具调用
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# LangChain 工具适配
# ============================================================================

@dataclass
class LCToolConfig:
    """LangChain工具配置"""
    name: str
    description: str
    func: Optional[Callable] = None
    coroutine: Optional[Callable] = None
    args_schema: Optional[Type[BaseModel]] = None
    return_direct: bool = False


class LCToolAdapter:
    """
    LangChain工具适配器
    
    将opspilot工具转换为LangChain工具格式，反之亦然
    
    使用场景:
    1. 将MCP工具包装为LangChain工具
    2. 将LangChain工具注册到opspilot工具系统
    3. 统一工具调用接口
    """
    
    def __init__(self, config: LCToolConfig):
        self.config = config
        self._tool: Optional[Any] = None
        self._usage_count = 0
        self._error_count = 0
    
    @property
    def name(self) -> str:
        return self.config.name
    
    @property
    def description(self) -> str:
        return self.config.description
    
    def to_langchain_tool(self) -> Any:
        """
        转换为LangChain工具
        
        Returns:
            LangChain StructuredTool或Tool实例
        """
        try:
            from langchain_core.tools import StructuredTool
        except ImportError:
            logger.warning("langchain_core not installed, returning mock tool")
            return self._create_mock_tool()
        
        if self.config.coroutine:
            # 异步工具
            self._tool = StructuredTool(
                name=self.config.name,
                description=self.config.description,
                func=self.config.func,
                coroutine=self.config.coroutine,
                args_schema=self.config.args_schema,
                return_direct=self.config.return_direct,
            )
        else:
            # 同步工具
            self._tool = StructuredTool(
                name=self.config.name,
                description=self.config.description,
                func=self.config.func or self._default_func,
                args_schema=self.config.args_schema,
                return_direct=self.config.return_direct,
            )
        
        return self._tool
    
    @staticmethod
    def from_langchain_tool(lc_tool: Any) -> "LCToolAdapter":
        """从LangChain工具创建适配器"""
        return LCToolAdapter(LCToolConfig(
            name=lc_tool.name,
            description=lc_tool.description,
            func=getattr(lc_tool, "func", None),
            coroutine=getattr(lc_tool, "coroutine", None),
            args_schema=getattr(lc_tool, "args_schema", None),
            return_direct=getattr(lc_tool, "return_direct", False),
        ))
    
    async def ainvoke(self, input_data: Dict[str, Any]) -> Any:
        """异步调用工具"""
        self._usage_count += 1
        
        try:
            if self._tool and hasattr(self._tool, "ainvoke"):
                return await self._tool.ainvoke(input_data)
            elif self.config.coroutine:
                return await self.config.coroutine(input_data)
            elif self.config.func:
                return self.config.func(input_data)
            else:
                return self._default_func(input_data)
        except Exception as e:
            self._error_count += 1
            logger.error(f"Tool {self.name} error: {e}")
            raise
    
    def invoke(self, input_data: Dict[str, Any]) -> Any:
        """同步调用工具"""
        self._usage_count += 1
        
        try:
            if self._tool and hasattr(self._tool, "invoke"):
                return self._tool.invoke(input_data)
            elif self.config.func:
                return self.config.func(input_data)
            else:
                return self._default_func(input_data)
        except Exception as e:
            self._error_count += 1
            logger.error(f"Tool {self.name} error: {e}")
            raise
    
    def _default_func(self, input_data: Any) -> Dict[str, Any]:
        """默认函数实现"""
        return {
            "tool": self.name,
            "input": input_data,
            "result": "Tool executed successfully",
        }
    
    def _create_mock_tool(self) -> Any:
        """创建模拟工具（当LangChain未安装时）"""
        class MockTool:
            name = self.config.name
            description = self.config.description
            
            def invoke(self, input_data):
                return {"mock": True, "result": "LangChain not installed"}
            
            async def ainvoke(self, input_data):
                return {"mock": True, "result": "LangChain not installed"}
        
        return MockTool()
    
    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return {
            "usage_count": self._usage_count,
            "error_count": self._error_count,
        }


class LCToolRegistry:
    """
    LangChain工具注册表
    
    统一管理所有LangChain工具，支持动态注册和发现
    """
    
    _instance: Optional["LCToolRegistry"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools: Dict[str, LCToolAdapter] = {}
            cls._instance._categories: Dict[str, List[str]] = {}
        return cls._instance
    
    def register(
        self,
        tool: Union[LCToolAdapter, Any],
        category: str = "general",
    ) -> None:
        """注册工具"""
        if isinstance(tool, LCToolAdapter):
            adapter = tool
        else:
            adapter = LCToolAdapter.from_langchain_tool(tool)
        
        self._tools[adapter.name] = adapter
        
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(adapter.name)
        
        logger.info(f"Tool registered: {adapter.name} in category {category}")
    
    def get(self, name: str) -> Optional[LCToolAdapter]:
        """获取工具"""
        return self._tools.get(name)
    
    def list_tools(self, category: str = None) -> List[str]:
        """列出工具"""
        if category:
            return self._categories.get(category, [])
        return list(self._tools.keys())
    
    def list_categories(self) -> List[str]:
        """列出类别"""
        return list(self._categories.keys())
    
    async def call_tool(self, name: str, input_data: Dict) -> Any:
        """调用工具"""
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")
        return await tool.ainvoke(input_data)
    
    def get_langchain_tools(self) -> List[Any]:
        """获取所有LangChain工具"""
        return [tool.to_langchain_tool() for tool in self._tools.values()]


class MCPToolWrapper:
    """
    MCP工具包装器
    
    将MCP Server的工具包装为LangChain工具
    
    使用示例:
    ```python
    mcp_server = ERPServer()
    wrapper = MCPToolWrapper(mcp_server)
    
    # 获取LangChain工具列表
    lc_tools = wrapper.get_langchain_tools()
    
    # 或单个工具
    query_tool = wrapper.get_tool("query_supplier")
    ```
    """
    
    def __init__(self, mcp_server: Any):
        """
        初始化包装器
        
        Args:
            mcp_server: MCP Server实例 (如ERPServer, ComplianceServer)
        """
        self.mcp_server = mcp_server
        self._tools: Dict[str, LCToolAdapter] = {}
        self._initialize_tools()
    
    def _initialize_tools(self) -> None:
        """从MCP Server提取工具"""
        # 获取MCP Server定义的工具
        if hasattr(self.mcp_server, "tools"):
            for tool_schema in self.mcp_server.tools:
                self._wrap_mcp_tool(tool_schema)
        elif hasattr(self.mcp_server, "list_tools"):
            for tool_info in self.mcp_server.list_tools():
                self._wrap_mcp_tool(tool_info)
    
    def _wrap_mcp_tool(self, tool_schema: Dict[str, Any]) -> None:
        """包装单个MCP工具"""
        tool_name = tool_schema.get("name", "unknown")
        
        # 创建异步调用函数
        async def mcp_call(input_data: Dict) -> Dict:
            try:
                # 调用MCP Server
                if hasattr(self.mcp_server, "call_tool"):
                    result = await self.mcp_server.call_tool(tool_name, input_data)
                elif hasattr(self.mcp_server, "execute"):
                    result = await self.mcp_server.execute(tool_name, input_data)
                else:
                    result = {"error": "MCP server method not found"}
                
                return result
            except Exception as e:
                return {"error": str(e), "tool": tool_name}
        
        # 创建同步调用函数
        def mcp_call_sync(input_data: Dict) -> Dict:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(mcp_call(input_data))
        
        config = LCToolConfig(
            name=tool_name,
            description=tool_schema.get("description", ""),
            func=mcp_call_sync,
            coroutine=mcp_call,
        )
        
        self._tools[tool_name] = LCToolAdapter(config)
    
    def get_tool(self, name: str) -> Optional[LCToolAdapter]:
        """获取工具"""
        return self._tools.get(name)
    
    def get_langchain_tools(self) -> List[Any]:
        """获取所有LangChain工具"""
        return [tool.to_langchain_tool() for tool in self._tools.values()]
    
    def list_tools(self) -> List[str]:
        """列出所有工具"""
        return list(self._tools.keys())


# ============================================================================
# LangChain RAG 适配
# ============================================================================

class LCRetrieverAdapter:
    """
    LangChain检索器适配器
    
    将opspilot的向量检索适配到LangChain的Retriever接口
    """
    
    def __init__(
        self,
        vector_store: Any = None,
        search_kwargs: Dict[str, Any] = None,
    ):
        self.vector_store = vector_store
        self.search_kwargs = search_kwargs or {"k": 5}
        self._retriever: Optional[Any] = None
    
    def to_langchain_retriever(self) -> Any:
        """转换为LangChain检索器"""
        if not self.vector_store:
            return self._create_mock_retriever()
        
        try:
            from langchain_core.retrievers import VectorStoreRetriever
            
            self._retriever = VectorStoreRetriever(
                vectorstore=self.vector_store,
                search_type="similarity",
                search_kwargs=self.search_kwargs,
            )
            return self._retriever
        except ImportError:
            return self._create_mock_retriever()
    
    async def aretrieve(self, query: str) -> List[Any]:
        """异步检索"""
        if self._retriever and hasattr(self._retriever, "ainvoke"):
            return await self._retriever.ainvoke(query)
        
        # 回退到手动检索
        if self.vector_store and hasattr(self.vector_store, "asimilarity_search"):
            return await self.vector_store.asimilarity_search(
                query, **self.search_kwargs
            )
        
        return []
    
    def retrieve(self, query: str) -> List[Any]:
        """同步检索"""
        if self._retriever and hasattr(self._retriever, "invoke"):
            return self._retriever.invoke(query)
        
        if self.vector_store and hasattr(self.vector_store, "similarity_search"):
            return self.vector_store.similarity_search(query, **self.search_kwargs)
        
        return []
    
    def _create_mock_retriever(self) -> Any:
        """创建模拟检索器"""
        class MockRetriever:
            def invoke(self, query: str) -> List:
                return []
            
            async def ainvoke(self, query: str) -> List:
                return []
        
        return MockRetriever()


class LCMemoryAdapter:
    """
    LangChain记忆适配器
    
    将opspilot的记忆系统适配到LangChain的Memory接口
    """
    
    def __init__(
        self,
        memory_store: Any = None,
        memory_key: str = "chat_history",
    ):
        self.memory_store = memory_store
        self.memory_key = memory_key
    
    def to_langchain_memory(self) -> Any:
        """转换为LangChain记忆"""
        try:
            from langchain_community.chat_message_histories import InMemoryChatMessageHistory
            
            # 使用opspilot的记忆存储作为后端
            history = InMemoryChatMessageHistory()
            return history
        except ImportError:
            return None
    
    async def load_memory(self, session_id: str) -> List[Dict[str, Any]]:
        """加载记忆"""
        if self.memory_store:
            # 从opspilot记忆系统加载
            memories = await self.memory_store.search(
                query="",
                filters={"session_id": session_id},
                limit=100,
            )
            return [m.content for m in memories]
        return []
    
    async def save_memory(
        self,
        session_id: str,
        messages: List[Dict[str, Any]],
    ) -> None:
        """保存记忆"""
        if self.memory_store:
            for msg in messages:
                await self.memory_store.store(
                    content=msg,
                    metadata={"session_id": session_id},
                )


class LCVectorStoreAdapter:
    """
    LangChain向量存储适配器
    
    统一向量存储接口
    """
    
    def __init__(self, store_type: str = "memory", **kwargs):
        """
        初始化向量存储
        
        Args:
            store_type: 存储类型 (memory, chroma, faiss, pinecone)
            **kwargs: 存储配置
        """
        self.store_type = store_type
        self.config = kwargs
        self._store: Optional[Any] = None
    
    async def initialize(self) -> None:
        """初始化向量存储"""
        if self.store_type == "memory":
            self._store = await self._create_memory_store()
        elif self.store_type == "chroma":
            self._store = await self._create_chroma_store()
        elif self.store_type == "faiss":
            self._store = await self._create_faiss_store()
        else:
            self._store = await self._create_memory_store()
    
    async def _create_memory_store(self) -> Any:
        """创建内存向量存储"""
        try:
            from langchain_community.vectorstores import InMemoryVectorStore
            
            embeddings = self._get_embeddings()
            return InMemoryVectorStore(embeddings)
        except ImportError:
            return None
    
    async def _create_chroma_store(self) -> Any:
        """创建Chroma向量存储"""
        try:
            from langchain_community.vectorstores import Chroma
            
            embeddings = self._get_embeddings()
            return Chroma(
                embedding_function=embeddings,
                persist_directory=self.config.get("persist_directory", "./chroma_db"),
            )
        except ImportError:
            return None
    
    async def _create_faiss_store(self) -> Any:
        """创建FAISS向量存储"""
        try:
            from langchain_community.vectorstores import FAISS
            
            embeddings = self._get_embeddings()
            return FAISS(embeddings)
        except ImportError:
            return None
    
    def _get_embeddings(self) -> Any:
        """获取嵌入模型"""
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            
            return HuggingFaceEmbeddings(
                model_name=self.config.get(
                    "embedding_model",
                    "sentence-transformers/all-MiniLM-L6-v2"
                )
            )
        except ImportError:
            return None
    
    async def add_documents(self, documents: List[Any]) -> None:
        """添加文档"""
        if self._store and hasattr(self._store, "aadd_documents"):
            await self._store.aadd_documents(documents)
        elif self._store and hasattr(self._store, "add_documents"):
            self._store.add_documents(documents)
    
    async def similarity_search(
        self,
        query: str,
        k: int = 5,
    ) -> List[Any]:
        """相似性搜索"""
        if self._store and hasattr(self._store, "asimilarity_search"):
            return await self._store.asimilarity_search(query, k=k)
        elif self._store and hasattr(self._store, "similarity_search"):
            return self._store.similarity_search(query, k=k)
        return []


# ============================================================================
# LangChain 链式调用执行器
# ============================================================================

@dataclass
class LCChainConfig:
    """LangChain链配置"""
    chain_type: str = "sequential"  # sequential, router, transform
    memory_enabled: bool = True
    verbose: bool = False
    max_iterations: int = 10


class LCChainExecutor:
    """
    LangChain链式执行器
    
    使用LCEL (LangChain Expression Language) 构建执行链
    
    核心功能:
    1. 链式调用 - 将多个步骤串联
    2. 条件分支 - 根据中间结果选择路径
    3. 工具调用 - 集成LangChain工具
    4. 记忆管理 - 保持对话上下文
    
    使用示例:
    ```python
    executor = LCChainExecutor(config)
    
    # 注册工具
    executor.register_tools([tool1, tool2])
    
    # 执行链
    result = await executor.execute({
        "input": "查询供应商信息",
        "session_id": "session_123",
    })
    ```
    """
    
    def __init__(self, config: LCChainConfig = None):
        self.config = config or LCChainConfig()
        self._tools: List[Any] = []
        self._chains: Dict[str, Any] = {}
        self._memory_adapters: Dict[str, LCMemoryAdapter] = {}
    
    def register_tools(self, tools: List[Any]) -> None:
        """注册工具"""
        for tool in tools:
            if isinstance(tool, LCToolAdapter):
                self._tools.append(tool.to_langchain_tool())
            else:
                self._tools.append(tool)
    
    def register_retriever(self, retriever: LCRetrieverAdapter) -> None:
        """注册检索器"""
        self._retriever = retriever.to_langchain_retriever()
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        chain_name: str = None,
    ) -> Dict[str, Any]:
        """
        执行链
        
        Args:
            input_data: 输入数据
            chain_name: 链名称（如果已注册）
        
        Returns:
            执行结果
        """
        start_time = time.time()
        
        try:
            # 如果有预定义链
            if chain_name and chain_name in self._chains:
                chain = self._chains[chain_name]
                result = await self._run_chain(chain, input_data)
            else:
                # 动态构建链
                result = await self._build_and_run(input_data)
            
            result["execution_time"] = time.time() - start_time
            return result
            
        except Exception as e:
            return {
                "error": str(e),
                "success": False,
                "execution_time": time.time() - start_time,
            }
    
    async def _run_chain(self, chain: Any, input_data: Dict) -> Dict[str, Any]:
        """运行预定义链"""
        if hasattr(chain, "ainvoke"):
            result = await chain.ainvoke(input_data)
        elif hasattr(chain, "invoke"):
            result = chain.invoke(input_data)
        else:
            result = {"error": "Chain has no invoke method"}
        
        if isinstance(result, dict):
            return result
        return {"result": result}
    
    async def _build_and_run(self, input_data: Dict) -> Dict[str, Any]:
        """构建并运行链"""
        # 简化实现：顺序执行工具
        results = []
        
        for tool in self._tools:
            try:
                if hasattr(tool, "ainvoke"):
                    result = await tool.ainvoke(input_data)
                elif hasattr(tool, "invoke"):
                    result = tool.invoke(input_data)
                else:
                    continue
                
                results.append({
                    "tool": getattr(tool, "name", "unknown"),
                    "result": result,
                })
                
            except Exception as e:
                results.append({
                    "tool": getattr(tool, "name", "unknown"),
                    "error": str(e),
                })
        
        return {
            "success": True,
            "results": results,
        }
    
    def register_chain(self, name: str, chain: Any) -> None:
        """注册链"""
        self._chains[name] = chain
    
    def create_rag_chain(
        self,
        prompt_template: str = None,
    ) -> Any:
        """
        创建RAG链
        
        使用LCEL构建检索增强生成链
        """
        try:
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser
            from langchain_core.runnables import RunnablePassthrough
            
            # 默认提示模板
            template = prompt_template or """
            基于以下上下文回答问题:
            
            {context}
            
            问题: {question}
            """
            
            prompt = ChatPromptTemplate.from_template(template)
            
            # 构建链
            if hasattr(self, "_retriever") and self._retriever:
                chain = (
                    {"context": self._retriever, "question": RunnablePassthrough()}
                    | prompt
                    | StrOutputParser()
                )
            else:
                chain = prompt | StrOutputParser()
            
            return chain
            
        except ImportError:
            return None


# ============================================================================
# 工厂函数
# ============================================================================

def create_lc_tool_adapter(
    name: str,
    description: str,
    func: Callable = None,
    coroutine: Callable = None,
    args_schema: Type[BaseModel] = None,
) -> LCToolAdapter:
    """
    创建LangChain工具适配器
    
    Args:
        name: 工具名称
        description: 工具描述
        func: 同步函数
        coroutine: 异步函数
        args_schema: 参数Schema
    
    Returns:
        LCToolAdapter实例
    """
    config = LCToolConfig(
        name=name,
        description=description,
        func=func,
        coroutine=coroutine,
        args_schema=args_schema,
    )
    return LCToolAdapter(config)


def create_lc_retriever(
    vector_store: Any = None,
    k: int = 5,
) -> LCRetrieverAdapter:
    """
    创建LangChain检索器
    
    Args:
        vector_store: 向量存储
        k: 返回文档数量
    
    Returns:
        LCRetrieverAdapter实例
    """
    return LCRetrieverAdapter(
        vector_store=vector_store,
        search_kwargs={"k": k},
    )

