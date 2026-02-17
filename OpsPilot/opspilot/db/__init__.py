"""
OpsPilot 数据库层

提供数据库连接、CRUD 操作、向量存储和缓存功能
"""
from opspilot.db.connection import (
    DatabasePool,
    get_database_pool,
    close_database_pool,
    execute_query,
    execute_transaction,
)
from opspilot.db.models import (
    Supplier,
    Product,
    Inventory,
    Warehouse,
    Order,
    Logistics,
    CustomsDeclaration,
    PlatformOrder,
    Policy,
    ExchangeRate,
)
from opspilot.db.crud import (
    SupplierCRUD,
    ProductCRUD,
    InventoryCRUD,
    OrderCRUD,
    LogisticsCRUD,
    CustomsCRUD,
    PlatformOrderCRUD,
    PolicyCRUD,
)
from opspilot.db.vector_store import (
    VectorStore,
    PolicyVectorStore,
    get_vector_store,
)
from opspilot.db.cache import (
    CacheManager,
    get_cache,
    cache_result,
)

__all__ = [
    # 连接管理
    "DatabasePool",
    "get_database_pool",
    "close_database_pool",
    "execute_query",
    "execute_transaction",
    # 模型
    "Supplier",
    "Product",
    "Inventory",
    "Warehouse",
    "Order",
    "Logistics",
    "CustomsDeclaration",
    "PlatformOrder",
    "Policy",
    "ExchangeRate",
    # CRUD
    "SupplierCRUD",
    "ProductCRUD",
    "InventoryCRUD",
    "OrderCRUD",
    "LogisticsCRUD",
    "CustomsCRUD",
    "PlatformOrderCRUD",
    "PolicyCRUD",
    # 向量存储
    "VectorStore",
    "PolicyVectorStore",
    "get_vector_store",
    # 缓存
    "CacheManager",
    "get_cache",
    "cache_result",
]
