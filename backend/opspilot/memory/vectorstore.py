"""
向量存储模块 - Vector Store

使用 LangChain ChromaDB 作为向量存储后端，符合文档要求。

职责：
- 文档加载、分割、向量化、检索（LangChain RAG管道）
- 提供统一的向量存储接口
- 支持语义相似度检索
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime

from opspilot.memory.base import (
    BaseMemoryStore,
    MemoryEntry,
    MemoryType,
    SearchResult,
)


# LangChain imports - 按文档要求使用 ChromaDB
try:
    from langchain_chroma import Chroma
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_core.documents import Document
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    Chroma = None
    HuggingFaceEmbeddings = None
    Document = None


class ChromaDBStore(BaseMemoryStore):
    """
    ChromaDB 向量存储 - 按文档要求使用 LangChain ChromaDB
    
    文档原文：
    "向量存储：ChromaDB - 轻量级，适合中小规模"
    "RAG 管道：文档加载、分割、向量化、检索"
    """
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        collection_name: str = "opspilot_memory",
    ):
        """
        初始化 ChromaDB 存储
        
        Args:
            persist_directory: 持久化目录
            embedding_model: 嵌入模型名称
            collection_name: 集合名称
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain 未安装。请运行: pip install langchain-chroma langchain-community"
            )
        
        self._persist_directory = persist_directory
        self._collection_name = collection_name
        
        # 初始化嵌入模型 - 使用 LangChain HuggingFaceEmbeddings
        self._embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True},
        )
        
        # 初始化 Chroma 向量存储 - 按文档要求
        self._vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=self._embeddings,
            collection_name=collection_name,
        )
        
        # 内存索引，用于快速查找
        self._entries: Dict[str, MemoryEntry] = {}
    
    async def store(self, entry: MemoryEntry) -> bool:
        """存储记忆条目到 ChromaDB"""
        try:
            # 创建 LangChain Document
            doc = Document(
                page_content=entry.content,
                metadata={
                    "entry_id": entry.id,
                    "memory_type": entry.memory_type.value,
                    "priority": entry.priority.value,
                    "created_at": entry.created_at.isoformat(),
                    "agent_name": entry.agent_name or "",
                    "task_id": entry.task_id or "",
                    **entry.metadata,
                },
            )
            
            # 添加到向量存储
            self._vectorstore.add_documents([doc])
            
            # 内存索引
            self._entries[entry.id] = entry
            
            return True
        except Exception as e:
            print(f"ChromaDB 存储错误: {e}")
            return False
    
    async def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """获取记忆条目"""
        return self._entries.get(entry_id)
    
    async def delete(self, entry_id: str) -> bool:
        """删除记忆条目"""
        if entry_id in self._entries:
            del self._entries[entry_id]
            # ChromaDB 删除需要通过 metadata 过滤
            try:
                self._vectorstore.delete(
                    filter={"entry_id": entry_id}
                )
            except Exception:
                pass  # ChromaDB 可能不支持单条删除
            return True
        return False
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        向量相似度搜索
        
        使用 LangChain Retriever 进行语义检索
        """
        results = []
        
        try:
            # 构建 Chroma 过滤条件
            where_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    if key == "memory_type":
                        conditions.append({"memory_type": value})
                    else:
                        conditions.append({key: value})
                if len(conditions) == 1:
                    where_filter = conditions[0]
                elif len(conditions) > 1:
                    where_filter = {"$and": conditions}
            
            # 使用 LangChain Retriever 进行相似度搜索
            docs = self._vectorstore.similarity_search(
                query,
                k=limit,
                filter=where_filter,
            )
            
            for doc in docs:
                entry_id = doc.metadata.get("entry_id")
                if entry_id and entry_id in self._entries:
                    entry = self._entries[entry_id]
                else:
                    # 从 Document 重建 MemoryEntry
                    entry = MemoryEntry(
                        id=entry_id or doc.metadata.get("entry_id", ""),
                        content=doc.page_content,
                        memory_type=MemoryType(doc.metadata.get("memory_type", "long_term")),
                        created_at=datetime.fromisoformat(
                            doc.metadata.get("created_at", datetime.now().isoformat())
                        ),
                        metadata={k: v for k, v in doc.metadata.items() 
                                 if k not in ["entry_id", "memory_type", "created_at"]},
                    )
                
                # 计算相似度分数（LangChain 相似度搜索返回的文档没有分数）
                # 使用嵌入相似度
                score = await self._compute_similarity(query, doc.page_content)
                
                results.append(SearchResult(entry=entry, score=score))
        
        except Exception as e:
            print(f"ChromaDB 搜索错误: {e}")
        
        return results[:limit]
    
    async def _compute_similarity(self, query: str, content: str) -> float:
        """计算查询和内容的相似度"""
        try:
            query_embedding = self._embeddings.embed_query(query)
            content_embedding = self._embeddings.embed_query(content)
            
            # 余弦相似度
            dot = sum(a * b for a, b in zip(query_embedding, content_embedding))
            norm1 = sum(a * a for a in query_embedding) ** 0.5
            norm2 = sum(b * b for b in content_embedding) ** 0.5
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot / (norm1 * norm2)
        except Exception:
            return 0.5
    
    async def clear(self) -> bool:
        """清空所有记忆"""
        self._entries.clear()
        try:
            # ChromaDB 清空集合
            self._vectorstore.delete_collection()
            self._vectorstore = Chroma(
                persist_directory=self._persist_directory,
                embedding_function=self._embeddings,
                collection_name=self._collection_name,
            )
        except Exception:
            pass
        return True
    
    async def count(self) -> int:
        """获取记忆条目数量"""
        return len(self._entries)
    
    def as_retriever(self, **kwargs):
        """
        返回 LangChain Retriever
        
        按文档要求，LangChain 负责 RAG 检索
        """
        return self._vectorstore.as_retriever(**kwargs)


def create_vectorstore(
    persist_directory: Optional[str] = None,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    collection_name: str = "opspilot_memory",
) -> ChromaDBStore:
    """
    创建向量存储的便捷函数
    
    Args:
        persist_directory: 持久化目录
        embedding_model: 嵌入模型名称
        collection_name: 集合名称
    
    Returns:
        ChromaDBStore: 向量存储实例
    """
    return ChromaDBStore(
        persist_directory=persist_directory,
        embedding_model=embedding_model,
        collection_name=collection_name,
    )

