"""
链式执行器模块

使用 LangChain LCEL（LangChain Expression Language）实现确定性逻辑链条。

文档原文：
- "确定性逻辑：固定流程的 Chain 执行"
- "LCEL 链式表达式：灵活组合"
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

from opspilot.chains.prompts import RAG_PROMPT, TOOL_SELECTION_PROMPT, VERIFICATION_PROMPT


# LangChain imports
try:
    from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
    from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
    from langchain_core.runnables import RunnablePassthrough, RunnableParallel
    from langchain_core.language_models import BaseLanguageModel
    from langchain_core.tools import BaseTool
    from langchain_core.documents import Document
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    ChatPromptTemplate = None
    PromptTemplate = None
    StrOutputParser = None
    JsonOutputParser = None
    RunnablePassthrough = None
    RunnableParallel = None
    BaseLanguageModel = None
    BaseTool = None
    Document = None


@dataclass
class ChainResult:
    """链执行结果"""
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class RAGChain:
    """
    RAG 检索链
    
    使用 LangChain LCEL 构建 RAG 管道。
    
    示例:
        >>> chain = RAGChain(retriever=vectorstore.as_retriever(), llm=llm)
        >>> result = await chain.ainvoke("查询供应商信息")
    """
    
    def __init__(
        self,
        retriever,
        llm: "BaseLanguageModel",
        prompt_template: Optional[str] = None,
    ):
        """
        初始化 RAG 链
        
        Args:
            retriever: LangChain Retriever（来自 ChromaDB）
            llm: LangChain 语言模型
            prompt_template: 自定义提示模板
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain 未安装")
        
        self._retriever = retriever
        self._llm = llm
        self._prompt_template = prompt_template or RAG_PROMPT
        
        # 构建 LCEL 链
        self._chain = self._build_chain()
    
    def _build_chain(self):
        """构建 LCEL 链"""
        prompt = ChatPromptTemplate.from_template(self._prompt_template)
        
        chain = (
            {
                "context": self._retriever | self._format_docs,
                "question": RunnablePassthrough(),
            }
            | prompt
            | self._llm
            | StrOutputParser()
        )
        
        return chain
    
    @staticmethod
    def _format_docs(docs: List["Document"]) -> str:
        """格式化文档"""
        return "\n\n".join(doc.page_content for doc in docs)
    
    async def ainvoke(self, query: str) -> ChainResult:
        """异步执行"""
        # 支持测试模式
        if hasattr(self, '_mock_ainvoke') and self._mock_ainvoke is not None:
            return self._mock_ainvoke(query)
        
        try:
            output = await self._chain.ainvoke(query)
            return ChainResult(success=True, output=output)
        except Exception as e:
            return ChainResult(success=False, output=None, error=str(e))
    
    def invoke(self, query: str) -> ChainResult:
        """同步执行"""
        # 支持测试模式
        if hasattr(self, '_mock_invoke') and self._mock_invoke is not None:
            return self._mock_invoke(query)
        
        try:
            output = self._chain.invoke(query)
            return ChainResult(success=True, output=output)
        except Exception as e:
            return ChainResult(success=False, output=None, error=str(e))


class ToolChain:
    """
    工具调用链
    
    使用 LangChain Tool 执行工具调用。
    
    示例:
        >>> chain = ToolChain(tools=lc_tools, llm=llm)
        >>> result = await chain.ainvoke("查询供应商 SUP001 的库存")
    """
    
    def __init__(
        self,
        tools: List["BaseTool"],
        llm: "BaseLanguageModel",
        prompt_template: Optional[str] = None,
    ):
        """
        初始化工具链
        
        Args:
            tools: LangChain Tool 列表
            llm: LangChain 语言模型
            prompt_template: 自定义提示模板
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain 未安装")
        
        self._tools = tools
        self._llm = llm
        self._prompt_template = prompt_template or TOOL_SELECTION_PROMPT
        
        # 构建工具映射
        self._tool_map = {tool.name: tool for tool in tools}
        
        # 构建选择链
        self._selection_chain = self._build_selection_chain()
    
    def _build_selection_chain(self):
        """构建工具选择链"""
        prompt = ChatPromptTemplate.from_template(self._prompt_template)
        
        chain = (
            {
                "tools": lambda _: self._format_tools(),
                "query": RunnablePassthrough(),
            }
            | prompt
            | self._llm
            | StrOutputParser()
        )
        
        return chain
    
    def _format_tools(self) -> str:
        """格式化工具列表"""
        lines = []
        for tool in self._tools:
            lines.append(f"- {tool.name}: {tool.description}")
        return "\n".join(lines)
    
    async def ainvoke(self, query: str) -> ChainResult:
        """异步执行"""
        # 支持测试模式
        if hasattr(self, '_mock_ainvoke') and self._mock_ainvoke is not None:
            return self._mock_ainvoke(query)
        
        try:
            # 1. 选择工具
            selection = await self._selection_chain.ainvoke(query)
            
            # 2. 解析工具名称（简化实现）
            tool_name = self._parse_tool_name(selection)
            
            if tool_name and tool_name in self._tool_map:
                # 3. 执行工具
                tool = self._tool_map[tool_name]
                result = await tool.ainvoke({"query": query})
                
                return ChainResult(
                    success=True,
                    output=result,
                    metadata={"tool_name": tool_name, "selection": selection},
                )
            
            return ChainResult(
                success=False,
                output=None,
                error="无法确定合适的工具",
                metadata={"selection": selection},
            )
        except Exception as e:
            return ChainResult(success=False, output=None, error=str(e))
    
    def _parse_tool_name(self, selection: str) -> Optional[str]:
        """从选择结果中解析工具名称"""
        import re
        
        # 首先检查是否包含工具名称模式
        tool_pattern = r'(query_|get_|search_|list_|create_|update_|delete_|track_|convert_)\w+'
        
        # 简单实现：查找"工具名称："或"tool_name:"
        for line in selection.split("\n"):
            if "工具名称" in line or "tool_name" in line.lower():
                # 提取名称
                parts = line.split("：") if "：" in line else line.split(":")
                if len(parts) > 1:
                    name = parts[1].strip()
                    # 只返回工具名称，不包含额外描述
                    # 例如："query_supplier 是最合适的" -> "query_supplier"
                    tool_match = re.match(r'^(query_|get_|search_|list_|create_|update_|delete_|track_|convert_)\w+', name)
                    if tool_match:
                        return tool_match.group(0)
                    # 如果不是工具名称格式，不返回
                    return None
        
        # 如果没有找到格式化的输出，尝试直接提取工具名称
        # 常见模式：query_xxx, get_xxx, search_xxx 等
        match = re.search(tool_pattern, selection)
        if match:
            return match.group(0)
        
        # 如果只有一个单词，检查是否匹配工具名称模式
        selection = selection.strip()
        if selection and not '\n' in selection and len(selection) < 50:
            tool_match = re.match(r'^(query_|get_|search_|list_|create_|update_|delete_|track_|convert_)\w+$', selection)
            if tool_match:
                return tool_match.group(0)
        
        return None
    
    def invoke(self, query: str) -> ChainResult:
        """同步执行"""
        import asyncio
        return asyncio.run(self.ainvoke(query))


class DecisionChain:
    """
    决策验证链
    
    使用 LangChain LCEL 构建决策和验证流程。
    
    示例:
        >>> chain = DecisionChain(llm=llm)
        >>> result = await chain.ainvoke(task="查询库存", result="库存充足")
    """
    
    def __init__(
        self,
        llm: "BaseLanguageModel",
        prompt_template: Optional[str] = None,
    ):
        """
        初始化决策链
        
        Args:
            llm: LangChain 语言模型
            prompt_template: 自定义提示模板
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain 未安装")
        
        self._llm = llm
        self._prompt_template = prompt_template or VERIFICATION_PROMPT
        
        # 构建验证链
        self._chain = self._build_chain()
    
    def _build_chain(self):
        """构建验证链"""
        prompt = ChatPromptTemplate.from_template(self._prompt_template)
        
        chain = (
            {
                "task": lambda x: x["task"],
                "result": lambda x: x["result"],
            }
            | prompt
            | self._llm
            | StrOutputParser()
        )
        
        return chain
    
    async def ainvoke(self, task: str, result: str) -> ChainResult:
        """异步执行"""
        # 支持测试模式
        if hasattr(self, '_mock_ainvoke') and self._mock_ainvoke is not None:
            return self._mock_ainvoke(task, result)
        
        try:
            output = await self._chain.ainvoke({"task": task, "result": result})
            return ChainResult(success=True, output=output)
        except Exception as e:
            return ChainResult(success=False, output=None, error=str(e))
    
    def invoke(self, task: str, result: str) -> ChainResult:
        """同步执行"""
        import asyncio
        return asyncio.run(self.ainvoke(task, result))


class OpsChainExecutor:
    """
    opspilot 链执行器
    
    整合 RAG、工具调用、决策验证等链式流程。
    
    示例:
        >>> executor = OpsChainExecutor(llm=llm)
        >>> executor.set_retriever(vectorstore.as_retriever())
        >>> executor.register_tools(lc_tools)
        >>> result = await executor.execute(query)
    """
    
    def __init__(
        self,
        llm: "BaseLanguageModel",
    ):
        """
        初始化链执行器
        
        Args:
            llm: LangChain 语言模型
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain 未安装")
        
        self._llm = llm
        self._retriever = None
        self._tools: List["BaseTool"] = []
        self._rag_chain: Optional[RAGChain] = None
        self._tool_chain: Optional[ToolChain] = None
        self._decision_chain: Optional[DecisionChain] = None
    
    def set_retriever(self, retriever) -> None:
        """设置检索器"""
        self._retriever = retriever
        self._rag_chain = RAGChain(retriever=retriever, llm=self._llm)
    
    def register_tools(self, tools: List["BaseTool"]) -> None:
        """注册工具"""
        self._tools = tools
        self._tool_chain = ToolChain(tools=tools, llm=self._llm)
    
    def add_tool(self, tool: "BaseTool") -> None:
        """添加工具"""
        self._tools.append(tool)
        self._tool_chain = ToolChain(tools=self._tools, llm=self._llm)
    
    async def execute_rag(self, query: str) -> ChainResult:
        """执行 RAG 检索"""
        if self._rag_chain is None:
            return ChainResult(
                success=False,
                output=None,
                error="未设置检索器，请先调用 set_retriever()",
            )
        return await self._rag_chain.ainvoke(query)
    
    async def execute_tool(self, query: str) -> ChainResult:
        """执行工具调用"""
        if self._tool_chain is None:
            return ChainResult(
                success=False,
                output=None,
                error="未注册工具，请先调用 register_tools()",
            )
        return await self._tool_chain.ainvoke(query)
    
    async def verify(self, task: str, result: str) -> ChainResult:
        """验证结果"""
        if self._decision_chain is None:
            self._decision_chain = DecisionChain(llm=self._llm)
        return await self._decision_chain.ainvoke(task, result)
    
    async def execute(
        self,
        query: str,
        use_rag: bool = True,
        use_tools: bool = True,
        verify: bool = True,
    ) -> Dict[str, Any]:
        """
        执行完整流程
        
        Args:
            query: 查询
            use_rag: 是否使用 RAG
            use_tools: 是否使用工具
            verify: 是否验证结果
        
        Returns:
            Dict[str, Any]: 执行结果
        """
        results = {
            "query": query,
            "rag_result": None,
            "tool_result": None,
            "verification": None,
        }
        
        # 1. RAG 检索
        if use_rag and self._rag_chain:
            rag_result = await self.execute_rag(query)
            results["rag_result"] = rag_result.output if rag_result.success else None
        
        # 2. 工具调用
        if use_tools and self._tool_chain:
            tool_result = await self.execute_tool(query)
            results["tool_result"] = tool_result.output if tool_result.success else None
        
        # 3. 验证
        if verify and results["tool_result"]:
            verification = await self.verify(query, str(results["tool_result"]))
            results["verification"] = verification.output if verification.success else None
        
        return results


# 便捷函数
def create_rag_chain(
    retriever,
    llm: "BaseLanguageModel",
    prompt_template: Optional[str] = None,
) -> RAGChain:
    """创建 RAG 链"""
    return RAGChain(retriever=retriever, llm=llm, prompt_template=prompt_template)


def create_tool_chain(
    tools: List["BaseTool"],
    llm: "BaseLanguageModel",
    prompt_template: Optional[str] = None,
) -> ToolChain:
    """创建工具链"""
    return ToolChain(tools=tools, llm=llm, prompt_template=prompt_template)


def create_decision_chain(
    llm: "BaseLanguageModel",
    prompt_template: Optional[str] = None,
) -> DecisionChain:
    """创建决策链"""
    return DecisionChain(llm=llm, prompt_template=prompt_template)

