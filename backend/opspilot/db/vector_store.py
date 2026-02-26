"""
向量存储模块

提供 ChromaDB 向量存储功能
"""
from typing import Optional, List, Dict, Any
from pathlib import Path
import chromadb
from chromadb.config import Settings

# 配置路径
CHROMA_PERSIST_DIR = Path(__file__).parent.parent.parent / "data" / "chroma"


class VectorStore:
    """向量存储基类"""
    
    def __init__(
        self,
        collection_name: str = "opspilot",
        persist_directory: Optional[str] = None,
    ):
        self.persist_directory = persist_directory or str(CHROMA_PERSIST_DIR)
        
        # 确保目录存在
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # 初始化 ChromaDB 客户端
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ):
        """添加文档"""
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]
        
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
    
    def query(
        self,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """查询相似文档"""
        return self.collection.query(
            query_texts=query_texts,
            n_results=n_results,
            where=where,
        )
    
    def delete(self, ids: List[str]):
        """删除文档"""
        self.collection.delete(ids=ids)
    
    def count(self) -> int:
        """获取文档数量"""
        return self.collection.count()
    
    def clear(self):
        """清空集合"""
        # 获取所有 ID
        all_items = self.collection.get()
        if all_items["ids"]:
            self.collection.delete(ids=all_items["ids"])


class PolicyVectorStore(VectorStore):
    """政策文档向量存储"""
    
    def __init__(self):
        super().__init__(collection_name="policies")
    
    def add_policy(
        self,
        policy_id: str,
        title: str,
        content: str,
        category: Optional[str] = None,
    ):
        """添加政策文档"""
        # 组合标题和内容作为文档
        document = f"{title}\n\n{content}"
        
        self.collection.add(
            documents=[document],
            metadatas=[{
                "policy_id": policy_id,
                "title": title,
                "category": category or "general",
            }],
            ids=[policy_id],
        )
    
    def add_policies(self, policies: List[Dict[str, Any]]):
        """批量添加政策文档"""
        documents = []
        metadatas = []
        ids = []
        
        for policy in policies:
            document = f"{policy.get('title', '')}\n\n{policy.get('content', '')}"
            documents.append(document)
            metadatas.append({
                "policy_id": policy.get("policy_id"),
                "title": policy.get("title"),
                "category": policy.get("category", "general"),
            })
            ids.append(policy.get("policy_id"))
        
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )
    
    def search_policies(
        self,
        query: str,
        n_results: int = 5,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """搜索政策文档"""
        where_filter = None
        if category:
            where_filter = {"category": category}
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter,
        )
        
        # 格式化结果
        policies = []
        for i, doc in enumerate(results["documents"][0]):
            policies.append({
                "content": doc,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else 0,
            })
        
        return policies
    
    def get_relevant_policy(self, query: str) -> Optional[Dict[str, Any]]:
        """获取最相关的政策"""
        results = self.search_policies(query, n_results=1)
        return results[0] if results else None


class ProductVectorStore(VectorStore):
    """产品向量存储"""
    
    def __init__(self):
        super().__init__(collection_name="products")
    
    def add_product(
        self,
        sku: str,
        name: str,
        description: str,
        category: Optional[str] = None,
        specifications: Optional[Dict] = None,
    ):
        """添加产品文档"""
        # 组合产品信息作为文档
        spec_str = ""
        if specifications:
            spec_str = "\n".join([f"{k}: {v}" for k, v in specifications.items()])
        
        document = f"{name}\n{description}\n{spec_str}"
        
        self.collection.add(
            documents=[document],
            metadatas=[{
                "sku": sku,
                "name": name,
                "category": category or "general",
            }],
            ids=[sku],
        )
    
    def search_products(
        self,
        query: str,
        n_results: int = 10,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """搜索产品"""
        where_filter = None
        if category:
            where_filter = {"category": category}
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter,
        )
        
        products = []
        for i, doc in enumerate(results["documents"][0]):
            products.append({
                "content": doc,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else 0,
            })
        
        return products


class SupplierVectorStore(VectorStore):
    """供应商向量存储"""
    
    def __init__(self):
        super().__init__(collection_name="suppliers")
    
    def add_supplier(
        self,
        supplier_id: str,
        name: str,
        region: Optional[str] = None,
        products: Optional[List[str]] = None,
        main_category: Optional[str] = None,
    ):
        """添加供应商文档"""
        # 组合供应商信息作为文档
        products_str = ", ".join(products) if products else ""
        document = f"{name}\n{region or ''}\n{main_category or ''}\n{products_str}"
        
        self.collection.add(
            documents=[document],
            metadatas=[{
                "supplier_id": supplier_id,
                "name": name,
                "region": region or "",
                "category": main_category or "",
            }],
            ids=[supplier_id],
        )
    
    def search_suppliers(
        self,
        query: str,
        n_results: int = 10,
        region: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """搜索供应商"""
        where_filter = None
        if region:
            where_filter = {"region": region}
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter,
        )
        
        suppliers = []
        for i, doc in enumerate(results["documents"][0]):
            suppliers.append({
                "content": doc,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else 0,
            })
        
        return suppliers


# ============================================
# 全局实例
# ============================================

_policy_store: Optional[PolicyVectorStore] = None
_product_store: Optional[ProductVectorStore] = None
_supplier_store: Optional[SupplierVectorStore] = None


def get_vector_store(store_type: str = "policy") -> VectorStore:
    """获取向量存储实例"""
    global _policy_store, _product_store, _supplier_store
    
    if store_type == "policy":
        if _policy_store is None:
            _policy_store = PolicyVectorStore()
        return _policy_store
    
    elif store_type == "product":
        if _product_store is None:
            _product_store = ProductVectorStore()
        return _product_store
    
    elif store_type == "supplier":
        if _supplier_store is None:
            _supplier_store = SupplierVectorStore()
        return _supplier_store
    
    else:
        raise ValueError(f"Unknown store type: {store_type}")
