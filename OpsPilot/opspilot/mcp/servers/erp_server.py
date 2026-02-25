"""
ERP MCP Server

提供 ERP 系统相关工具：
- 供应商查询
- 产品查询
- 库存管理
- 订单管理

使用真实数据库连接
"""
import json
from typing import Any, Dict, List, Optional

from opspilot.mcp.base import MCPServerBase
from opspilot.db.crud import (
    SupplierCRUD,
    ProductCRUD,
    InventoryCRUD,
    OrderCRUD,
)
from opspilot.db.connection import get_database_pool


class ERPMCPServer(MCPServerBase):
    """
    ERP 系统 MCP Server

    连接 PostgreSQL 提供 ERP 相关工具
    """

    def __init__(self):
        super().__init__(
            name="erp-tools",
            version="1.0.0",
            description="ERP系统工具集：供应商查询、产品管理、库存管理、订单管理",
        )
        # 注册工具
        self._register_tools()

    def _register_tools(self) -> None:
        """注册所有 ERP 工具"""

        # ==================== 供应商工具 ====================

        @self.tool(
            name="query_supplier",
            description="查询供应商信息，支持按名称、区域、类别筛选",
            input_schema={
                "type": "object",
                "properties": {
                    "supplier_name": {
                        "type": "string",
                        "description": "供应商名称（支持模糊匹配）",
                    },
                    "region": {
                        "type": "string",
                        "description": "区域筛选：华南/华东/华北/西南/东北",
                    },
                    "category": {
                        "type": "string",
                        "description": "产品类别筛选",
                    },
                    "min_rating": {
                        "type": "number",
                        "description": "最低评分筛选",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量限制，默认 10",
                    },
                },
            },
        )
        async def query_supplier(params: Dict[str, Any]) -> Dict[str, Any]:
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

            return {
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
                "total": len(suppliers),
            }

        @self.tool(
            name="get_supplier",
            description="根据ID获取供应商详情",
            input_schema={
                "type": "object",
                "required": ["supplier_id"],
                "properties": {
                    "supplier_id": {
                        "type": "string",
                        "description": "供应商ID",
                    },
                },
            },
        )
        async def get_supplier(params: Dict[str, Any]) -> Dict[str, Any]:
            supplier = await SupplierCRUD.get_by_id(params["supplier_id"])
            if not supplier:
                return {"error": "供应商不存在", "error_code": "NOT_FOUND"}

            return {
                "supplier_id": supplier.supplier_id,
                "name": supplier.name,
                "region": supplier.region,
                "rating": float(supplier.rating),
                "products": supplier.products,
                "contact": supplier.contact,
                "phone": supplier.phone,
                "delivery_days": supplier.delivery_days,
                "status": supplier.status,
            }

        # ==================== 产品工具 ====================

        @self.tool(
            name="query_product",
            description="查询产品信息，支持按SKU、名称、类别筛选",
            input_schema={
                "type": "object",
                "properties": {
                    "sku": {
                        "type": "string",
                        "description": "产品SKU",
                    },
                    "name": {
                        "type": "string",
                        "description": "产品名称（支持模糊匹配）",
                    },
                    "category": {
                        "type": "string",
                        "description": "产品类别",
                    },
                    "status": {
                        "type": "string",
                        "description": "状态：active/inactive",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量限制，默认 20",
                    },
                },
            },
        )
        async def query_product(params: Dict[str, Any]) -> Dict[str, Any]:
            products = await ProductCRUD.get_list(
                category=params.get("category"),
                status=params.get("status"),
                limit=params.get("limit", 20),
            )

            # 按SKU或名称过滤
            sku_filter = params.get("sku", "").lower()
            name_filter = params.get("name", "").lower()

            if sku_filter:
                products = [p for p in products if sku_filter in p.sku.lower()]
            if name_filter:
                products = [p for p in products if name_filter in p.name.lower()]

            return {
                "products": [
                    {
                        "sku": p.sku,
                        "name": p.name,
                        "category": p.category,
                        "base_price": float(p.base_price),
                        "unit": p.unit,
                        "status": p.status,
                    }
                    for p in products
                ],
                "total": len(products),
            }

        @self.tool(
            name="get_product",
            description="根据SKU获取产品详情",
            input_schema={
                "type": "object",
                "required": ["sku"],
                "properties": {
                    "sku": {
                        "type": "string",
                        "description": "产品SKU",
                    },
                },
            },
        )
        async def get_product(params: Dict[str, Any]) -> Dict[str, Any]:
            product = await ProductCRUD.get_by_sku(params["sku"])
            if not product:
                return {"error": "产品不存在", "error_code": "NOT_FOUND"}

            return {
                "sku": product.sku,
                "name": product.name,
                "category": product.category,
                "base_price": float(product.base_price),
                "unit": product.unit,
                "status": product.status,
                "description": product.description,
            }

        # ==================== 库存工具 ====================

        @self.tool(
            name="query_inventory",
            description="查询库存信息，支持按SKU、仓库筛选",
            input_schema={
                "type": "object",
                "properties": {
                    "sku": {
                        "type": "string",
                        "description": "产品SKU",
                    },
                    "warehouse": {
                        "type": "string",
                        "description": "仓库名称或代码",
                    },
                    "low_stock": {
                        "type": "boolean",
                        "description": "是否只显示低库存",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量限制，默认 20",
                    },
                },
            },
        )
        async def query_inventory(params: Dict[str, Any]) -> Dict[str, Any]:
            sku = params.get("sku")
            warehouse_id = params.get("warehouse")  # 前端传 warehouse，映射到 warehouse_id
            low_stock_only = params.get("low_stock", False)

            # 获取库存数据
            if low_stock_only:
                # 获取低库存（返回字典列表）
                raw_data = await InventoryCRUD.get_low_stock()
                inventories = [
                    {
                        "sku": i.get('sku', ''),
                        "warehouse": i.get('warehouse_id', i.get('warehouse', '')),
                        "quantity": i.get('quantity', 0),
                        "safety_stock": i.get('safety_stock', 0),
                    }
                    for i in raw_data
                ]
            elif sku:
                # 按 SKU 查询（返回 Inventory 对象列表）
                raw_data = await InventoryCRUD.get_by_sku(sku, warehouse_id)
                inventories = [
                    {
                        "sku": i.sku,
                        "warehouse": i.warehouse_id,
                        "quantity": i.quantity,
                        "safety_stock": i.safety_stock if hasattr(i, 'safety_stock') else 0,
                    }
                    for i in raw_data
                ]
            else:
                # 返回空结果（没有 sku 时）
                inventories = []

            # 计算状态
            for inv in inventories:
                inv["status"] = "low" if inv["quantity"] <= inv.get("safety_stock", 0) else "normal"

            return {
                "inventories": inventories,
                "total": len(inventories),
            }

        @self.tool(
            name="get_stock_summary",
            description="获取指定SKU的总库存摘要",
            input_schema={
                "type": "object",
                "required": ["sku"],
                "properties": {
                    "sku": {
                        "type": "string",
                        "description": "产品SKU",
                    },
                },
            },
        )
        async def get_stock_summary(params: Dict[str, Any]) -> Dict[str, Any]:
            sku = params["sku"]
            inventories = await InventoryCRUD.get_by_sku(sku)

            total_quantity = sum(i.quantity for i in inventories)
            total_safety = sum(i.safety_stock for i in inventories)

            return {
                "sku": sku,
                "total_quantity": total_quantity,
                "total_safety_stock": total_safety,
                "warehouse_count": len(inventories),
                "warehouses": [
                    {
                        "warehouse": i.warehouse,
                        "quantity": i.quantity,
                        "safety_stock": i.safety_stock,
                    }
                    for i in inventories
                ],
                "status": "low" if total_quantity <= total_safety else "normal",
            }

        # ==================== 订单工具 ====================

        @self.tool(
            name="query_order",
            description="查询采购订单，支持按供应商、状态筛选",
            input_schema={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "订单ID",
                    },
                    "supplier_id": {
                        "type": "string",
                        "description": "供应商ID",
                    },
                    "status": {
                        "type": "string",
                        "description": "订单状态：pending/approved/completed/cancelled",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量限制，默认 20",
                    },
                },
            },
        )
        async def query_order(params: Dict[str, Any]) -> Dict[str, Any]:
            if params.get("order_id"):
                order = await OrderCRUD.get_by_id(params["order_id"])
                if not order:
                    return {"error": "订单不存在", "error_code": "NOT_FOUND"}
                orders = [order]
            else:
                orders = await OrderCRUD.get_list(
                    supplier_id=params.get("supplier_id"),
                    status=params.get("status"),
                    limit=params.get("limit", 20),
                )

            return {
                "orders": [
                    {
                        "order_id": o.order_id,
                        "supplier_id": o.supplier_id,
                        "status": o.status,
                        "priority": o.priority,
                        "total_amount": float(o.total_amount) if o.total_amount else 0,
                        "created_at": o.created_at.isoformat() if o.created_at else None,
                        "approved_at": o.approved_at.isoformat() if o.approved_at else None,
                    }
                    for o in orders
                ],
                "total": len(orders),
            }

        @self.tool(
            name="create_order",
            description="创建采购订单",
            input_schema={
                "type": "object",
                "required": ["supplier_id", "items"],
                "properties": {
                    "supplier_id": {
                        "type": "string",
                        "description": "供应商ID",
                    },
                    "items": {
                        "type": "array",
                        "description": "订单项列表",
                        "items": {
                            "type": "object",
                            "required": ["sku", "quantity"],
                            "properties": {
                                "sku": {"type": "string"},
                                "quantity": {"type": "integer", "minimum": 1},
                            },
                        },
                    },
                    "priority": {
                        "type": "string",
                        "description": "优先级：urgent/high/normal/low",
                    },
                    "created_by": {
                        "type": "string",
                        "description": "创建人",
                    },
                },
            },
        )
        async def create_order(params: Dict[str, Any]) -> Dict[str, Any]:
            from opspilot.db.models import OrderCreate

            supplier_id = params["supplier_id"]
            items_data = params.get("items", [])

            # 验证供应商
            supplier = await SupplierCRUD.get_by_id(supplier_id)
            if not supplier:
                return {"error": "供应商不存在", "error_code": "SUPPLIER_NOT_FOUND"}

            # 构建订单项
            items = []
            for item in items_data:
                product = await ProductCRUD.get_by_sku(item["sku"])
                if not product:
                    return {"error": f"产品不存在: {item['sku']}", "error_code": "PRODUCT_NOT_FOUND"}
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
                created_by=params.get("created_by", "mcp-server"),
            )

            order = await OrderCRUD.create(order_create)

            return {
                "order_id": order.order_id,
                "supplier_id": order.supplier_id,
                "status": order.status,
                "total_amount": float(order.total_amount) if order.total_amount else 0,
                "created_at": order.created_at.isoformat() if order.created_at else None,
            }

        @self.tool(
            name="health_check",
            description="检查服务器健康状态",
            input_schema={
                "type": "object",
                "properties": {},
            },
        )
        async def health_check(params: Dict[str, Any]) -> Dict[str, Any]:
            try:
                pool = await get_database_pool()
                # 简单查询测试连接
                result = await pool.fetchval("SELECT 1")
                return {
                    "status": "healthy",
                    "server": self.name,
                    "version": self.version,
                    "database": "connected",
                }
            except Exception as e:
                return {
                    "status": "unhealthy",
                    "server": self.name,
                    "error": str(e),
                }


# 便捷函数：创建并运行 Server
def run_server(mode: str = "stdio", **kwargs):
    """启动 ERP MCP Server"""
    server = ERPMCPServer()
    server.run(mode=mode, **kwargs)


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    run_server(mode=mode)
