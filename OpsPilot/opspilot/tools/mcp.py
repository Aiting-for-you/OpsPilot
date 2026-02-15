"""
MCP Server 实现

职责：
- ERP Server 实现
- 合规 Server 实现
- Mock 数据支持
"""
from typing import Dict, Any, List, Optional
from datetime import datetime

from opspilot.tools.base import (
    BaseToolServer,
    ToolSchema,
    ToolResult,
    ToolContext,
    ToolStatus,
    FallbackMode,
)


# ==================== Mock 数据 ====================

MOCK_SUPPLIERS = [
    {
        "id": "SUP001",
        "name": "华南电子科技",
        "region": "华南",
        "rating": 4.8,
        "products": ["电子元件", "芯片", "传感器"],
        "contact": "张经理",
        "phone": "138****1234",
    },
    {
        "id": "SUP002",
        "name": "华东精密制造",
        "region": "华东",
        "rating": 4.5,
        "products": ["机械零件", "模具", "金属加工"],
        "contact": "李经理",
        "phone": "139****5678",
    },
    {
        "id": "SUP003",
        "name": "华北物流供应链",
        "region": "华北",
        "rating": 4.6,
        "products": ["包装材料", "托盘", "仓储设备"],
        "contact": "王经理",
        "phone": "137****9012",
    },
]

MOCK_INVENTORY = {
    "SKU001": {"name": "电阻100Ω", "quantity": 5000, "warehouse": "深圳仓"},
    "SKU002": {"name": "电容10μF", "quantity": 3000, "warehouse": "深圳仓"},
    "SKU003": {"name": "芯片STM32", "quantity": 200, "warehouse": "上海仓"},
    "SKU004": {"name": "传感器DHT11", "quantity": 800, "warehouse": "北京仓"},
}

MOCK_ORDERS: Dict[str, Dict[str, Any]] = {}


# ==================== ERP Server ====================

class ERPServer(BaseToolServer):
    """
    ERP 系统 MCP Server

    提供供应商查询、订单管理、库存管理等功能
    """

    def __init__(self):
        super().__init__(
            name="erp-tools",
            description="ERP系统工具集：供应商查询、订单管理、库存管理"
        )
        self._register_tools()

    def _register_tools(self):
        """注册所有 ERP 工具"""

        # 查询供应商
        @self.register_tool(ToolSchema(
            name="query_supplier",
            description="查询供应商信息，支持按名称、区域模糊查询",
            input_schema={
                "type": "object",
                "properties": {
                    "supplier_name": {
                        "type": "string",
                        "description": "供应商名称（支持模糊匹配）"
                    },
                    "region": {
                        "type": "string",
                        "description": "区域筛选：华南/华东/华北"
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
                                "id": {"type": "string"},
                                "name": {"type": "string"},
                                "region": {"type": "string"},
                                "rating": {"type": "number"},
                                "products": {"type": "array"}
                            }
                        }
                    },
                    "total": {"type": "integer"}
                }
            }
        ))
        async def query_supplier(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            supplier_name = params.get("supplier_name", "")
            region = params.get("region", "")

            # 过滤供应商
            results = []
            for s in MOCK_SUPPLIERS:
                if supplier_name and supplier_name not in s["name"]:
                    continue
                if region and region != s["region"]:
                    continue
                results.append(s)

            return ToolResult.success({
                "suppliers": results,
                "total": len(results)
            })

        # 创建订单
        @self.register_tool(ToolSchema(
            name="create_order",
            description="创建采购订单",
            input_schema={
                "type": "object",
                "required": ["supplier_id", "products"],
                "properties": {
                    "supplier_id": {
                        "type": "string",
                        "description": "供应商ID"
                    },
                    "products": {
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
                    "remark": {
                        "type": "string",
                        "description": "备注"
                    }
                }
            }
        ))
        async def create_order(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            supplier_id = params.get("supplier_id")
            products = params.get("products", [])

            # 验证供应商
            supplier = next((s for s in MOCK_SUPPLIERS if s["id"] == supplier_id), None)
            if not supplier:
                return ToolResult.error(
                    error=f"供应商不存在: {supplier_id}",
                    error_code="SUPPLIER_NOT_FOUND"
                )

            # 计算金额（Mock 价格）
            total_amount = 0
            order_products = []
            for p in products:
                sku = p["sku"]
                qty = p["quantity"]
                # Mock 单价
                unit_price = 10.0 if sku.startswith("SKU") else 100.0
                amount = unit_price * qty
                total_amount += amount
                order_products.append({
                    "sku": sku,
                    "quantity": qty,
                    "unit_price": unit_price,
                    "amount": amount
                })

            # 生成订单号
            order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # 判断是否需要审批（金额超过 10000）
            need_approval = total_amount > 10000
            status = "pending_approval" if need_approval else "created"

            # 创建订单
            order = {
                "order_id": order_id,
                "supplier_id": supplier_id,
                "supplier_name": supplier["name"],
                "products": order_products,
                "total_amount": total_amount,
                "status": status,
                "need_approval": need_approval,
                "created_at": datetime.now().isoformat(),
                "created_by": context.user_id or "system"
            }
            MOCK_ORDERS[order_id] = order

            return ToolResult.success({
                "order_id": order_id,
                "status": status,
                "need_approval": need_approval,
                "total_amount": total_amount,
                "message": "订单创建成功，等待审批" if need_approval else "订单创建成功"
            })

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
                        "description": "产品SKU"
                    }
                }
            }
        ))
        async def query_inventory(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            sku = params.get("sku")

            if sku not in MOCK_INVENTORY:
                return ToolResult.error(
                    error=f"产品不存在: {sku}",
                    error_code="PRODUCT_NOT_FOUND"
                )

            return ToolResult.success({
                "sku": sku,
                **MOCK_INVENTORY[sku]
            })

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
            order_id = params.get("order_id")

            if order_id not in MOCK_ORDERS:
                return ToolResult.error(
                    error=f"订单不存在: {order_id}",
                    error_code="ORDER_NOT_FOUND"
                )

            return ToolResult.success(MOCK_ORDERS[order_id])

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
                    "reason": {
                        "type": "string",
                        "description": "操作原因"
                    }
                }
            }
        ))
        async def update_order_status(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            order_id = params.get("order_id")
            new_status = params.get("status")
            reason = params.get("reason", "")

            if order_id not in MOCK_ORDERS:
                return ToolResult.error(
                    error=f"订单不存在: {order_id}",
                    error_code="ORDER_NOT_FOUND"
                )

            order = MOCK_ORDERS[order_id]
            old_status = order["status"]
            order["status"] = new_status
            order["updated_at"] = datetime.now().isoformat()

            return ToolResult.success({
                "order_id": order_id,
                "old_status": old_status,
                "new_status": new_status,
                "message": f"订单状态已更新为 {new_status}"
            })

    async def health_check(self) -> bool:
        """健康检查"""
        return True


# ==================== 合规 Server ====================

class ComplianceServer(BaseToolServer):
    """
    合规系统 MCP Server

    提供政策查询、合规检查等功能
    """

    def __init__(self):
        super().__init__(
            name="compliance-tools",
            description="合规系统工具集：政策查询、合规检查、合同审核"
        )
        self._register_tools()

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
                        "description": "政策类别：采购限额/供应商准入/付款条款等"
                    },
                    "keywords": {
                        "type": "string",
                        "description": "关键词搜索"
                    }
                }
            }
        ))
        async def query_policy(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            category = params.get("category", "")
            keywords = params.get("keywords", "")

            # Mock 政策数据
            policies = [
                {
                    "id": "POL001",
                    "title": "采购限额管理规定",
                    "category": "采购限额",
                    "content": "单笔采购金额超过10000元需经理审批，超过50000元需总监审批。",
                    "effective_date": "2024-01-01"
                },
                {
                    "id": "POL002",
                    "title": "供应商准入标准",
                    "category": "供应商准入",
                    "content": "供应商评分需达到4.0以上方可合作，新供应商需进行资质审核。",
                    "effective_date": "2024-01-01"
                },
                {
                    "id": "POL003",
                    "title": "付款条款规范",
                    "category": "付款条款",
                    "content": "标准付款条款为月结30天，特殊条款需财务审批。",
                    "effective_date": "2024-01-01"
                }
            ]

            # 过滤
            if category:
                policies = [p for p in policies if category in p["category"]]
            if keywords:
                policies = [p for p in policies if keywords in p["title"] or keywords in p["content"]]

            return ToolResult.success({
                "policies": policies,
                "total": len(policies)
            })

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
                        "description": "检查类型：amount_limit/supplier_rating/payment_terms"
                    },
                    "data": {
                        "type": "object",
                        "description": "待检查数据"
                    }
                }
            }
        ))
        async def check_compliance(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            check_type = params.get("check_type")
            data = params.get("data", {})

            violations = []
            warnings = []

            if check_type == "amount_limit":
                amount = data.get("amount", 0)
                if amount > 50000:
                    violations.append({
                        "rule": "采购限额管理规定",
                        "message": f"金额 {amount} 超过总监审批阈值 50000",
                        "level": "violation"
                    })
                elif amount > 10000:
                    warnings.append({
                        "rule": "采购限额管理规定",
                        "message": f"金额 {amount} 需经理审批",
                        "level": "warning"
                    })

            elif check_type == "supplier_rating":
                rating = data.get("rating", 0)
                if rating < 4.0:
                    violations.append({
                        "rule": "供应商准入标准",
                        "message": f"供应商评分 {rating} 低于准入标准 4.0",
                        "level": "violation"
                    })

            is_compliant = len(violations) == 0

            return ToolResult.success({
                "is_compliant": is_compliant,
                "violations": violations,
                "warnings": warnings,
                "check_type": check_type
            })

    async def health_check(self) -> bool:
        """健康检查"""
        return True


# ==================== 便捷函数 ====================

def create_default_router() -> ToolRouter:
    """
    创建默认工具路由器

    包含所有内置 MCP Server
    """
    from opspilot.tools.base import ToolRouter

    router = ToolRouter()
    router.register_server(ERPServer())
    router.register_server(ComplianceServer())

    return router

