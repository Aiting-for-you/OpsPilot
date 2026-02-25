"""
MCP Server 实现 - 真实数据库版本

职责：
- ERP Server 实现（连接 PostgreSQL）
- 合规 Server 实现（连接 PostgreSQL + ChromaDB）
- 替代 Mock 数据版本
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal

from opspilot.tools.base import (
    BaseToolServer,
    ToolSchema,
    ToolResult,
    ToolContext,
    ToolStatus,
    FallbackMode,
    ToolRouter,
)

# 导入 CRUD 操作
from opspilot.db.crud import (
    SupplierCRUD,
    ProductCRUD,
    InventoryCRUD,
    OrderCRUD,
    LogisticsCRUD,
    CustomsCRUD,
    PlatformOrderCRUD,
    PolicyCRUD,
    ExchangeRateCRUD,
)

# 导入向量存储（延迟导入，避免 ChromaDB 依赖问题）
# from opspilot.db.vector_store import PolicyVectorStore
PolicyVectorStore = None  # 延迟导入


# ==================== ERP Server (数据库版本) ====================

class ERPServerDB(BaseToolServer):
    """
    ERP 系统 MCP Server - 数据库版本
    
    连接 PostgreSQL 提供真实的业务数据
    """

    def __init__(self):
        super().__init__(
            name="erp-tools-db",
            description="ERP系统工具集（数据库版本）：供应商查询、订单管理、库存管理"
        )
        self._register_tools()

    def _register_tools(self):
        """注册所有 ERP 工具"""

        # 查询供应商
        @self.register_tool(ToolSchema(
            name="query_supplier",
            description="查询供应商信息，支持按名称、区域、类别筛选",
            input_schema={
                "type": "object",
                "properties": {
                    "supplier_name": {
                        "type": "string",
                        "description": "供应商名称（支持模糊匹配）"
                    },
                    "region": {
                        "type": "string",
                        "description": "区域筛选：华南/华东/华北/西南/东北"
                    },
                    "category": {
                        "type": "string",
                        "description": "产品类别筛选"
                    },
                    "min_rating": {
                        "type": "number",
                        "description": "最低评分筛选"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量限制，默认 10"
                    }
                },
            },
            output_schema={
                "type": "object",
                "properties": {
                    "suppliers": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "supplier_id": {"type": "string"},
                                "name": {"type": "string"},
                                "region": {"type": "string"},
                                "rating": {"type": "number"},
                                "products": {"type": "array"},
                                "contact": {"type": "string"},
                                "phone": {"type": "string"}
                            }
                        }
                    },
                    "total": {"type": "integer"}
                }
            }
        ))
        async def query_supplier(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            try:
                suppliers = await SupplierCRUD.get_list(
                    region=params.get("region"),
                    category=params.get("category"),
                    min_rating=params.get("min_rating"),
                    limit=params.get("limit", 10),
                )
                
                # 按名称过滤
                name_filter = params.get("supplier_name", "").lower()
                if name_filter:
                    suppliers = [s for s in suppliers if name_filter in s.name.lower()]
                
                result_data = {
                    "suppliers": [
                        {
                            "supplier_id": s.supplier_id,
                            "name": s.name,
                            "region": s.region,
                            "rating": float(s.rating),
                            "products": s.products,
                            "contact": s.contact,
                            "phone": s.phone,
                            "delivery_days": s.delivery_days,
                            "status": s.status,
                        }
                        for s in suppliers
                    ],
                    "total": len(suppliers)
                }
                
                return ToolResult.success(result_data)
            except Exception as e:
                return ToolResult.error(
                    error=f"查询供应商失败: {str(e)}",
                    error_code="QUERY_ERROR",
                    retry_suggested=True
                )

        # 查询产品
        @self.register_tool(ToolSchema(
            name="query_product",
            description="查询产品信息",
            input_schema={
                "type": "object",
                "properties": {
                    "sku": {
                        "type": "string",
                        "description": "产品 SKU"
                    },
                    "category": {
                        "type": "string",
                        "description": "产品类别"
                    }
                }
            }
        ))
        async def query_product(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            try:
                sku = params.get("sku")
                
                if sku:
                    product = await ProductCRUD.get_by_sku(sku)
                    if not product:
                        return ToolResult.error(
                            error=f"产品不存在: {sku}",
                            error_code="PRODUCT_NOT_FOUND"
                        )
                    return ToolResult.success({
                        "sku": product.sku,
                        "name": product.name,
                        "category": product.category,
                        "base_price": float(product.base_price),
                        "currency": product.currency,
                        "unit": product.unit,
                        "safety_stock": product.safety_stock,
                    })
                else:
                    products = await ProductCRUD.get_list(
                        category=params.get("category"),
                        limit=50
                    )
                    return ToolResult.success({
                        "products": [
                            {
                                "sku": p.sku,
                                "name": p.name,
                                "category": p.category,
                                "base_price": float(p.base_price),
                            }
                            for p in products
                        ],
                        "total": len(products)
                    })
            except Exception as e:
                return ToolResult.error(
                    error=f"查询产品失败: {str(e)}",
                    error_code="QUERY_ERROR"
                )

        # 查询库存
        @self.register_tool(ToolSchema(
            name="query_inventory",
            description="查询产品库存",
            input_schema={
                "type": "object",
                "required": ["sku"],
                "properties": {
                    "sku": {
                        "type": "string",
                        "description": "产品 SKU"
                    },
                    "warehouse_id": {
                        "type": "string",
                        "description": "仓库 ID（可选）"
                    }
                }
            }
        ))
        async def query_inventory(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            try:
                sku = params.get("sku")
                warehouse_id = params.get("warehouse_id")
                
                inventory_list = await InventoryCRUD.get_by_sku(sku, warehouse_id)
                
                if not inventory_list:
                    return ToolResult.error(
                        error=f"库存记录不存在: {sku}",
                        error_code="INVENTORY_NOT_FOUND"
                    )
                
                # 获取产品信息
                product = await ProductCRUD.get_by_sku(sku)
                
                return ToolResult.success({
                    "sku": sku,
                    "product_name": product.name if product else "未知产品",
                    "inventory": [
                        {
                            "warehouse_id": inv.warehouse_id,
                            "quantity": inv.quantity,
                            "available": inv.available,
                            "reserved": inv.reserved,
                            "location": inv.location,
                        }
                        for inv in inventory_list
                    ],
                    "total_quantity": sum(inv.quantity for inv in inventory_list),
                    "total_available": sum(inv.available for inv in inventory_list),
                    "safety_stock": product.safety_stock if product else 100,
                })
            except Exception as e:
                return ToolResult.error(
                    error=f"查询库存失败: {str(e)}",
                    error_code="QUERY_ERROR"
                )

        # 查询低库存
        @self.register_tool(ToolSchema(
            name="query_low_stock",
            description="查询低库存产品列表",
            input_schema={
                "type": "object",
                "properties": {
                    "threshold_ratio": {
                        "type": "number",
                        "description": "阈值比例，默认 0.2（低于安全库存的 20%）"
                    }
                }
            }
        ))
        async def query_low_stock(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            try:
                threshold = params.get("threshold_ratio", 0.2)
                low_stock = await InventoryCRUD.get_low_stock(threshold)
                
                return ToolResult.success({
                    "low_stock_items": [
                        {
                            "sku": item["sku"],
                            "name": item["name"],
                            "current_quantity": item["quantity"],
                            "safety_stock": item["safety_stock"],
                            "warehouse_id": item["warehouse_id"],
                        }
                        for item in low_stock
                    ],
                    "total": len(low_stock)
                })
            except Exception as e:
                return ToolResult.error(
                    error=f"查询低库存失败: {str(e)}",
                    error_code="QUERY_ERROR"
                )

        # 创建订单
        @self.register_tool(ToolSchema(
            name="create_order",
            description="创建采购订单",
            input_schema={
                "type": "object",
                "required": ["supplier_id", "items"],
                "properties": {
                    "supplier_id": {
                        "type": "string",
                        "description": "供应商 ID"
                    },
                    "items": {
                        "type": "array",
                        "description": "产品列表",
                        "items": {
                            "type": "object",
                            "required": ["sku", "quantity"],
                            "properties": {
                                "sku": {"type": "string"},
                                "quantity": {"type": "integer", "minimum": 1}
                            }
                        }
                    },
                    "priority": {
                        "type": "string",
                        "description": "优先级：urgent/high/normal/low",
                        "enum": ["urgent", "high", "normal", "low"]
                    },
                    "created_by": {
                        "type": "string",
                        "description": "创建人"
                    }
                }
            }
        ))
        async def create_order(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            try:
                from opspilot.db.models import OrderCreate
                
                supplier_id = params.get("supplier_id")
                items_data = params.get("items", [])
                
                # 验证供应商
                supplier = await SupplierCRUD.get_by_id(supplier_id)
                if not supplier:
                    return ToolResult.error(
                        error=f"供应商不存在: {supplier_id}",
                        error_code="SUPPLIER_NOT_FOUND"
                    )
                
                # 构建订单项
                items = []
                for item in items_data:
                    product = await ProductCRUD.get_by_sku(item["sku"])
                    if not product:
                        return ToolResult.error(
                            error=f"产品不存在: {item['sku']}",
                            error_code="PRODUCT_NOT_FOUND"
                        )
                    items.append({
                        "sku": item["sku"],
                        "name": product.name,
                        "quantity": item["quantity"],
                        "unit_price": float(product.base_price),
                        "amount": float(product.base_price * item["quantity"]),
                    })
                
                # 创建订单
                order_create = OrderCreate(
                    supplier_id=supplier_id,
                    items=items,
                    priority=params.get("priority", "normal"),
                    created_by=params.get("created_by", context.user_id or "system"),
                )
                
                order = await OrderCRUD.create(order_create)
                
                return ToolResult.success({
                    "order_id": order.order_id,
                    "supplier_name": supplier.name,
                    "total_amount": float(order.total_amount),
                    "status": order.status,
                    "need_approval": order.need_approval,
                    "message": "订单创建成功，等待审批" if order.need_approval else "订单创建成功"
                })
            except Exception as e:
                return ToolResult.error(
                    error=f"创建订单失败: {str(e)}",
                    error_code="CREATE_ERROR"
                )

        # 查询订单
        @self.register_tool(ToolSchema(
            name="query_order",
            description="查询订单详情",
            input_schema={
                "type": "object",
                "required": ["order_id"],
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "订单号"
                    }
                }
            }
        ))
        async def query_order(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            try:
                order_id = params.get("order_id")
                order = await OrderCRUD.get_by_id(order_id)
                
                if not order:
                    return ToolResult.error(
                        error=f"订单不存在: {order_id}",
                        error_code="ORDER_NOT_FOUND"
                    )
                
                return ToolResult.success({
                    "order_id": order.order_id,
                    "supplier_id": order.supplier_id,
                    "supplier_name": order.supplier_name,
                    "items": [item.model_dump() for item in order.items],
                    "total_amount": float(order.total_amount),
                    "status": order.status,
                    "need_approval": order.need_approval,
                    "created_at": order.created_at.isoformat() if order.created_at else None,
                })
            except Exception as e:
                return ToolResult.error(
                    error=f"查询订单失败: {str(e)}",
                    error_code="QUERY_ERROR"
                )

        # 更新订单状态
        @self.register_tool(ToolSchema(
            name="update_order_status",
            description="更新订单状态",
            input_schema={
                "type": "object",
                "required": ["order_id", "status"],
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "订单号"
                    },
                    "status": {
                        "type": "string",
                        "description": "新状态",
                        "enum": ["approved", "rejected", "shipped", "completed", "cancelled"]
                    },
                    "approved_by": {
                        "type": "string",
                        "description": "审批人"
                    }
                }
            }
        ))
        async def update_order_status(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            try:
                order_id = params.get("order_id")
                new_status = params.get("status")
                
                order = await OrderCRUD.update_status(
                    order_id,
                    new_status,
                    params.get("approved_by")
                )
                
                if not order:
                    return ToolResult.error(
                        error=f"订单不存在: {order_id}",
                        error_code="ORDER_NOT_FOUND"
                    )
                
                return ToolResult.success({
                    "order_id": order_id,
                    "status": new_status,
                    "message": f"订单状态已更新为 {new_status}"
                })
            except Exception as e:
                return ToolResult.error(
                    error=f"更新订单状态失败: {str(e)}",
                    error_code="UPDATE_ERROR"
                )

        # 查询汇率
        @self.register_tool(ToolSchema(
            name="query_exchange_rate",
            description="查询汇率",
            input_schema={
                "type": "object",
                "properties": {
                    "from_currency": {
                        "type": "string",
                        "description": "源货币代码，如 USD"
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "目标货币代码，如 CNY"
                    }
                }
            }
        ))
        async def query_exchange_rate(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            try:
                from_curr = params.get("from_currency", "USD")
                to_curr = params.get("to_currency", "CNY")
                
                rate = await ExchangeRateCRUD.get_rate(from_curr, to_curr)
                
                if not rate:
                    return ToolResult.error(
                        error=f"汇率不存在: {from_curr}/{to_curr}",
                        error_code="RATE_NOT_FOUND"
                    )
                
                return ToolResult.success({
                    "from_currency": rate.from_currency,
                    "to_currency": rate.to_currency,
                    "rate": float(rate.rate),
                    "source": rate.source,
                    "updated_at": rate.updated_at.isoformat() if rate.updated_at else None,
                })
            except Exception as e:
                return ToolResult.error(
                    error=f"查询汇率失败: {str(e)}",
                    error_code="QUERY_ERROR"
                )

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            from opspilot.db.connection import get_database_pool
            pool = await get_database_pool()
            await pool.fetchval("SELECT 1")
            return True
        except Exception:
            return False


# ==================== 合规 Server (数据库版本) ====================

class ComplianceServerDB(BaseToolServer):
    """
    合规系统 MCP Server - 数据库版本
    
    连接 PostgreSQL + ChromaDB 提供合规检查
    """

    def __init__(self):
        super().__init__(
            name="compliance-tools-db",
            description="合规系统工具集（数据库版本）：政策查询、合规检查"
        )
        self._vector_store = None
        self._register_tools()

    async def _get_vector_store(self):
        """获取向量存储实例（延迟导入）"""
        if self._vector_store is None:
            try:
                from opspilot.db.vector_store import PolicyVectorStore
                self._vector_store = PolicyVectorStore()
            except Exception as e:
                print(f"Warning: Failed to load PolicyVectorStore: {e}")
                pass
        return self._vector_store

    def _register_tools(self):
        """注册所有合规工具"""

        # 查询政策
        @self.register_tool(ToolSchema(
            name="query_policy",
            description="查询企业采购政策",
            input_schema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "政策类别：采购限额/供应商准入/付款条款/合同管理/紧急采购"
                    },
                    "keywords": {
                        "type": "string",
                        "description": "关键词搜索"
                    },
                    "policy_id": {
                        "type": "string",
                        "description": "政策 ID"
                    }
                }
            }
        ))
        async def query_policy(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            try:
                policy_id = params.get("policy_id")
                category = params.get("category")
                keywords = params.get("keywords")
                
                if policy_id:
                    policy = await PolicyCRUD.get_by_id(policy_id)
                    if not policy:
                        return ToolResult.error(
                            error=f"政策不存在: {policy_id}",
                            error_code="POLICY_NOT_FOUND"
                        )
                    return ToolResult.success({
                        "policies": [{
                            "policy_id": policy.policy_id,
                            "title": policy.title,
                            "category": policy.category,
                            "content": policy.content,
                            "effective_date": policy.effective_date.isoformat() if policy.effective_date else None,
                        }],
                        "total": 1
                    })
                
                if keywords:
                    policies = await PolicyCRUD.search(keywords)
                elif category:
                    policies = await PolicyCRUD.get_by_category(category)
                else:
                    # 返回所有活跃政策
                    policies = await PolicyCRUD.search("")
                
                return ToolResult.success({
                    "policies": [
                        {
                            "policy_id": p.policy_id,
                            "title": p.title,
                            "category": p.category,
                            "content": p.content[:200] + "..." if len(p.content) > 200 else p.content,
                        }
                        for p in policies
                    ],
                    "total": len(policies)
                })
            except Exception as e:
                return ToolResult.error(
                    error=f"查询政策失败: {str(e)}",
                    error_code="QUERY_ERROR"
                )

        # 语义搜索政策（向量检索）
        @self.register_tool(ToolSchema(
            name="search_policy_semantic",
            description="语义搜索政策文档，使用向量检索找到最相关的政策",
            input_schema={
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询，可以是自然语言描述"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回结果数量，默认 5"
                    }
                }
            }
        ))
        async def search_policy_semantic(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            try:
                query = params.get("query")
                top_k = params.get("top_k", 5)
                
                vector_store = await self._get_vector_store()
                if not vector_store:
                    # 降级到数据库搜索
                    policies = await PolicyCRUD.search(query)
                    return ToolResult.success({
                        "policies": [
                            {
                                "policy_id": p.policy_id,
                                "title": p.title,
                                "category": p.category,
                                "content": p.content,
                                "relevance": 0.5,  # 降级模式下默认相关度
                            }
                            for p in policies[:top_k]
                        ],
                        "total": len(policies[:top_k]),
                        "mode": "database_fallback"
                    })
                
                # 使用向量检索
                results = vector_store.search_policies(query, n_results=top_k)
                
                # 格式化结果
                policies = []
                for r in results:
                    policies.append({
                        "policy_id": r.get("metadata", {}).get("policy_id", ""),
                        "title": r.get("metadata", {}).get("title", ""),
                        "category": r.get("metadata", {}).get("category", ""),
                        "content": r.get("content", ""),
                        "relevance": 1 - r.get("distance", 0),  # 转换为相似度
                    })
                
                return ToolResult.success({
                    "policies": policies,
                    "total": len(policies),
                    "mode": "vector_search"
                })
            except Exception as e:
                return ToolResult.error(
                    error=f"语义搜索失败: {str(e)}",
                    error_code="SEARCH_ERROR"
                )

        # 合规检查
        @self.register_tool(ToolSchema(
            name="check_compliance",
            description="检查采购行为是否符合政策规定",
            input_schema={
                "type": "object",
                "required": ["check_type", "data"],
                "properties": {
                    "check_type": {
                        "type": "string",
                        "description": "检查类型：amount_limit/supplier_rating/payment_terms/order_approval"
                    },
                    "data": {
                        "type": "object",
                        "description": "待检查数据"
                    }
                }
            }
        ))
        async def check_compliance(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            try:
                check_type = params.get("check_type")
                data = params.get("data", {})
                
                violations = []
                warnings = []
                
                # 获取相关政策
                policies = await PolicyCRUD.search(check_type.replace("_", " "))
                policy_rules = {p.category: p.content for p in policies}
                
                if check_type == "amount_limit":
                    amount = data.get("amount", 0)
                    
                    # 解析政策中的限额规则
                    limit_policy = policy_rules.get("采购限额", "")
                    
                    if amount > 50000:
                        violations.append({
                            "rule": "采购限额管理规定",
                            "message": f"金额 {amount} 元超过总监审批阈值 50000 元",
                            "level": "violation",
                            "action": "需总监审批"
                        })
                    elif amount > 10000:
                        warnings.append({
                            "rule": "采购限额管理规定",
                            "message": f"金额 {amount} 元需经理审批",
                            "level": "warning",
                            "action": "需经理审批"
                        })
                
                elif check_type == "supplier_rating":
                    rating = data.get("rating", 0)
                    supplier_id = data.get("supplier_id", "")
                    
                    # 获取供应商信息
                    supplier = await SupplierCRUD.get_by_id(supplier_id)
                    if supplier:
                        rating = float(supplier.rating)
                    
                    if rating < 4.0:
                        violations.append({
                            "rule": "供应商准入标准",
                            "message": f"供应商评分 {rating} 低于准入标准 4.0",
                            "level": "violation",
                            "action": "需进行资质审核或选择其他供应商"
                        })
                    elif rating < 4.5:
                        warnings.append({
                            "rule": "供应商准入标准",
                            "message": f"供应商评分 {rating} 较低，建议评估风险",
                            "level": "warning"
                        })
                
                elif check_type == "payment_terms":
                    terms = data.get("payment_terms", "")
                    amount = data.get("amount", 0)
                    
                    # 检查付款条款
                    if terms and "预付" in terms and amount > 50000:
                        warnings.append({
                            "rule": "付款条款规范",
                            "message": f"大额订单使用预付款条款需财务审批",
                            "level": "warning"
                        })
                
                is_compliant = len(violations) == 0
                
                return ToolResult.success({
                    "is_compliant": is_compliant,
                    "violations": violations,
                    "warnings": warnings,
                    "check_type": check_type,
                    "related_policies": list(policy_rules.keys()),
                })
            except Exception as e:
                return ToolResult.error(
                    error=f"合规检查失败: {str(e)}",
                    error_code="CHECK_ERROR"
                )

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            from opspilot.db.connection import get_database_pool
            pool = await get_database_pool()
            await pool.fetchval("SELECT 1")
            return True
        except Exception:
            return False


# ==================== 物流 Server (数据库版本) ====================

class LogisticsServerDB(BaseToolServer):
    """物流系统 MCP Server - 数据库版本"""

    def __init__(self):
        super().__init__(
            name="logistics-tools-db",
            description="物流系统工具集：物流追踪、报关查询"
        )
        self._register_tools()

    def _register_tools(self):
        """注册物流工具"""

        # 查询物流
        @self.register_tool(ToolSchema(
            name="query_logistics",
            description="查询物流信息",
            input_schema={
                "type": "object",
                "properties": {
                    "tracking_no": {
                        "type": "string",
                        "description": "运单号"
                    },
                    "order_id": {
                        "type": "string",
                        "description": "订单号"
                    }
                }
            }
        ))
        async def query_logistics(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            try:
                tracking_no = params.get("tracking_no")
                order_id = params.get("order_id")
                
                if tracking_no:
                    logistics = await LogisticsCRUD.get_by_tracking(tracking_no)
                elif order_id:
                    logistics = await LogisticsCRUD.get_by_order(order_id)
                else:
                    return ToolResult.error(
                        error="请提供运单号或订单号",
                        error_code="MISSING_PARAMS"
                    )
                
                if not logistics:
                    return ToolResult.error(
                        error="物流信息不存在",
                        error_code="LOGISTICS_NOT_FOUND"
                    )
                
                return ToolResult.success({
                    "tracking_no": logistics.tracking_no,
                    "order_id": logistics.order_id,
                    "carrier": logistics.carrier,
                    "status": logistics.status,
                    "current_location": logistics.current_location,
                    "estimated_delivery": logistics.estimated_delivery.isoformat() if logistics.estimated_delivery else None,
                    "tracking_history": logistics.tracking_history,
                })
            except Exception as e:
                return ToolResult.error(
                    error=f"查询物流失败: {str(e)}",
                    error_code="QUERY_ERROR"
                )

        # 查询报关
        @self.register_tool(ToolSchema(
            name="query_customs",
            description="查询报关信息",
            input_schema={
                "type": "object",
                "properties": {
                    "declaration_no": {
                        "type": "string",
                        "description": "报关单号"
                    },
                    "order_id": {
                        "type": "string",
                        "description": "订单号"
                    }
                }
            }
        ))
        async def query_customs(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            try:
                declaration_no = params.get("declaration_no")
                order_id = params.get("order_id")
                
                if declaration_no:
                    customs = await CustomsCRUD.get_by_declaration_no(declaration_no)
                elif order_id:
                    customs = await CustomsCRUD.get_by_order(order_id)
                else:
                    return ToolResult.error(
                        error="请提供报关单号或订单号",
                        error_code="MISSING_PARAMS"
                    )
                
                if not customs:
                    return ToolResult.error(
                        error="报关信息不存在",
                        error_code="CUSTOMS_NOT_FOUND"
                    )
                
                return ToolResult.success({
                    "declaration_no": customs.declaration_no,
                    "order_id": customs.order_id,
                    "status": customs.status,
                    "customs_office": customs.customs_office,
                    "declared_value": float(customs.declared_value) if customs.declared_value else 0,
                    "issue_description": customs.issue_description,
                })
            except Exception as e:
                return ToolResult.error(
                    error=f"查询报关失败: {str(e)}",
                    error_code="QUERY_ERROR"
                )

        # 查询问题报关单
        @self.register_tool(ToolSchema(
            name="query_customs_issues",
            description="查询有问题的报关单列表"
        ))
        async def query_customs_issues(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            try:
                issues = await CustomsCRUD.get_issues()
                
                return ToolResult.success({
                    "issues": [
                        {
                            "declaration_no": c.declaration_no,
                            "order_id": c.order_id,
                            "status": c.status,
                            "customs_office": c.customs_office,
                            "issue_description": c.issue_description,
                        }
                        for c in issues
                    ],
                    "total": len(issues)
                })
            except Exception as e:
                return ToolResult.error(
                    error=f"查询问题报关单失败: {str(e)}",
                    error_code="QUERY_ERROR"
                )

    async def health_check(self) -> bool:
        """健康检查"""
        return True


# ==================== 电商 Server (数据库版本) ====================

class EcommerceServerDB(BaseToolServer):
    """电商系统 MCP Server - 数据库版本"""

    def __init__(self):
        super().__init__(
            name="ecommerce-tools-db",
            description="电商系统工具集：平台订单查询"
        )
        self._register_tools()

    def _register_tools(self):
        """注册电商工具"""

        # 查询平台订单
        @self.register_tool(ToolSchema(
            name="query_platform_orders",
            description="查询电商平台订单",
            input_schema={
                "type": "object",
                "properties": {
                    "platform": {
                        "type": "string",
                        "description": "平台名称：Amazon/AliExpress/Shopify/eBay"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量"
                    }
                }
            }
        ))
        async def query_platform_orders(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            try:
                platform = params.get("platform")
                limit = params.get("limit", 20)
                
                orders = await PlatformOrderCRUD.get_by_platform(platform, limit) if platform else []
                
                return ToolResult.success({
                    "orders": [
                        {
                            "order_id": o.order_id,
                            "platform": o.platform,
                            "status": o.status,
                            "payment_status": o.payment_status,
                            "total_amount": float(o.total_amount),
                            "currency": o.currency,
                        }
                        for o in orders
                    ],
                    "total": len(orders)
                })
            except Exception as e:
                return ToolResult.error(
                    error=f"查询平台订单失败: {str(e)}",
                    error_code="QUERY_ERROR"
                )

        # 查询待发货订单
        @self.register_tool(ToolSchema(
            name="query_pending_shipments",
            description="查询待发货的平台订单"
        ))
        async def query_pending_shipments(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            try:
                orders = await PlatformOrderCRUD.get_pending_shipments()
                
                return ToolResult.success({
                    "pending_orders": [
                        {
                            "order_id": o.order_id,
                            "platform": o.platform,
                            "total_amount": float(o.total_amount),
                            "created_at": o.created_at.isoformat() if o.created_at else None,
                        }
                        for o in orders
                    ],
                    "total": len(orders)
                })
            except Exception as e:
                return ToolResult.error(
                    error=f"查询待发货订单失败: {str(e)}",
                    error_code="QUERY_ERROR"
                )

    async def health_check(self) -> bool:
        """健康检查"""
        return True


# ==================== 便捷函数 ====================

def create_db_router() -> ToolRouter:
    """
    创建数据库版本工具路由器
    
    包含所有连接真实数据库的 MCP Server
    """
    router = ToolRouter()
    
    # 核心业务 Server
    router.register_server(ERPServerDB())
    router.register_server(ComplianceServerDB())
    router.register_server(LogisticsServerDB())
    router.register_server(EcommerceServerDB())
    
    return router
