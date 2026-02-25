"""
工具嵌入模块 - Tool Embeddings

使用 LangChain Embeddings 进行工具向量化，符合文档要求。

文档原文：
- "RAG 管道：文档加载、分割、向量化、检索"
- "LangChain 负责：工具封装、RAG 检索"

职责：
- 工具描述向量化
- 语义相似度计算
- 支持多种嵌入模型
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from opspilot.tools.base import ToolSchema


# LangChain imports
try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_core.embeddings import Embeddings
    LANGCHAIN_EMBEDDINGS_AVAILABLE = True
except ImportError:
    LANGCHAIN_EMBEDDINGS_AVAILABLE = False
    HuggingFaceEmbeddings = None
    Embeddings = None


@dataclass
class ToolEmbedding:
    """工具嵌入向量"""
    tool_name: str
    embedding: List[float]
    description: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ToolEmbeddingsManager:
    """
    工具嵌入管理器
    
    使用 LangChain Embeddings 进行工具描述的向量化，
    用于 ToolRAG 的语义检索。
    
    示例:
        >>> manager = ToolEmbeddingsManager()
        >>> embedding = await manager.embed_tool(tool_schema)
        >>> similar = await manager.find_similar("查询供应商", top_k=5)
    """
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu",
    ):
        """
        初始化嵌入管理器
        
        Args:
            model_name: 嵌入模型名称
            device: 计算设备
        """
        self._model_name = model_name
        self._device = device
        
        # 初始化 LangChain Embeddings
        if LANGCHAIN_EMBEDDINGS_AVAILABLE:
            self._embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={'device': device},
                encode_kwargs={'normalize_embeddings': True},
            )
        else:
            self._embeddings = None
        
        # 工具嵌入缓存
        self._tool_embeddings: Dict[str, ToolEmbedding] = {}
    
    @property
    def embeddings(self) -> Optional["Embeddings"]:
        """获取 LangChain Embeddings 对象"""
        return self._embeddings
    
    @property
    def is_available(self) -> bool:
        """检查嵌入模型是否可用"""
        return self._embeddings is not None
    
    async def embed_text(self, text: str) -> List[float]:
        """
        嵌入文本
        
        Args:
            text: 要嵌入的文本
        
        Returns:
            List[float]: 嵌入向量
        """
        if self._embeddings is None:
            # 降级：返回简单向量
            return self._simple_embedding(text)
        
        return self._embeddings.embed_query(text)
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量嵌入文本
        
        Args:
            texts: 文本列表
        
        Returns:
            List[List[float]]: 嵌入向量列表
        """
        if self._embeddings is None:
            return [self._simple_embedding(t) for t in texts]
        
        return self._embeddings.embed_documents(texts)
    
    async def embed_tool(self, tool_schema: ToolSchema) -> ToolEmbedding:
        """
        嵌入工具描述
        
        构建完整的工具描述文本并嵌入
        
        Args:
            tool_schema: 工具 Schema
        
        Returns:
            ToolEmbedding: 工具嵌入
        """
        # 构建描述文本
        description_parts = [
            f"工具名称: {tool_schema.name}",
            f"描述: {tool_schema.description}",
        ]
        
        # 添加参数描述
        if tool_schema.input_schema:
            properties = tool_schema.input_schema.get("properties", {})
            for param_name, param_info in properties.items():
                param_desc = param_info.get("description", "")
                description_parts.append(f"参数 {param_name}: {param_desc}")
        
        full_description = "\n".join(description_parts)
        
        # 嵌入
        embedding = await self.embed_text(full_description)
        
        tool_embedding = ToolEmbedding(
            tool_name=tool_schema.name,
            embedding=embedding,
            description=full_description,
            metadata={
                "timeout": tool_schema.timeout_seconds,
                "retryable": tool_schema.retryable,
            },
        )
        
        # 缓存
        self._tool_embeddings[tool_schema.name] = tool_embedding
        
        return tool_embedding
    
    async def embed_tools(self, tools: List[ToolSchema]) -> Dict[str, ToolEmbedding]:
        """
        批量嵌入工具
        
        Args:
            tools: 工具 Schema 列表
        
        Returns:
            Dict[str, ToolEmbedding]: 工具名到嵌入的映射
        """
        # 构建描述列表
        descriptions = []
        for tool in tools:
            desc_parts = [
                f"工具名称: {tool.name}",
                f"描述: {tool.description}",
            ]
            if tool.input_schema:
                properties = tool.input_schema.get("properties", {})
                for param_name, param_info in properties.items():
                    param_desc = param_info.get("description", "")
                    desc_parts.append(f"参数 {param_name}: {param_desc}")
            descriptions.append("\n".join(desc_parts))
        
        # 批量嵌入
        embeddings = await self.embed_texts(descriptions)
        
        # 构建结果
        result = {}
        for tool, embedding, desc in zip(tools, embeddings, descriptions):
            tool_embedding = ToolEmbedding(
                tool_name=tool.name,
                embedding=embedding,
                description=desc,
            )
            result[tool.name] = tool_embedding
            self._tool_embeddings[tool.name] = tool_embedding
        
        return result
    
    def get_embedding(self, tool_name: str) -> Optional[ToolEmbedding]:
        """获取工具嵌入"""
        return self._tool_embeddings.get(tool_name)
    
    def get_all_embeddings(self) -> Dict[str, ToolEmbedding]:
        """获取所有工具嵌入"""
        return self._tool_embeddings
    
    async def similarity(
        self,
        query: str,
        tool_name: str,
    ) -> float:
        """
        计算查询与工具的相似度
        
        Args:
            query: 查询文本
            tool_name: 工具名称
        
        Returns:
            float: 相似度分数 (0-1)
        """
        tool_embedding = self._tool_embeddings.get(tool_name)
        if tool_embedding is None:
            return 0.0
        
        query_embedding = await self.embed_text(query)
        
        return self._cosine_similarity(query_embedding, tool_embedding.embedding)
    
    async def find_similar(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[tuple]:
        """
        查找相似工具
        
        Args:
            query: 查询文本
            top_k: 返回数量
        
        Returns:
            List[tuple]: (tool_name, similarity_score) 列表
        """
        if not self._tool_embeddings:
            return []
        
        query_embedding = await self.embed_text(query)
        
        results = []
        for tool_name, tool_emb in self._tool_embeddings.items():
            score = self._cosine_similarity(query_embedding, tool_emb.embedding)
            results.append((tool_name, score))
        
        # 排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]
    
    def _simple_embedding(self, text: str) -> List[float]:
        """简单嵌入（降级实现）"""
        import math
        
        vec = [0.0] * 128
        for i, char in enumerate(text[:128]):
            vec[i % 128] += ord(char) % 100 / 100.0
        
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]
    
    def _cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float],
    ) -> float:
        """计算余弦相似度"""
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot / (norm1 * norm2)


def create_embeddings_manager(
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    device: str = "cpu",
) -> ToolEmbeddingsManager:
    """
    创建嵌入管理器的便捷函数
    
    Args:
        model_name: 嵌入模型名称
        device: 计算设备
    
    Returns:
        ToolEmbeddingsManager: 嵌入管理器
    """
    return ToolEmbeddingsManager(
        model_name=model_name,
        device=device,
    )

