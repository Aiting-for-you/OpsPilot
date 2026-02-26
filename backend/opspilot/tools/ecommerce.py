"""
跨境电商 Mock MCP Server

提供跨境电商业务场景的 Mock 工具：
- 汇率查询
- 物流追踪
- 平台订单
- 报关状态
"""
from typing import Dict, Any, List, Optional
import sys
import os

from opspilot.tools.base import (
    BaseToolServer,
    ToolSchema,
    ToolResult,
    ToolContext,
)

# 添加 fixtures 路径
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_fixtures_path = os.path.join(_project_root, 'tests', 'fixtures')
if _fixtures_path not in sys.path:
    sys.path.insert(0, _fixtures_path)

# 导入 Mock 数据
try:
    from ecommerce_data import (
        MOCK_EXCHANGE_RATES,
        MOCK_LOGISTICS_TRACKING,
        MOCK_PLATFORM_ORDERS,
        MOCK_CUSTOMS_DECLARATIONS,
        get_exchange_rate,
        convert_currency,
        track_logistics,
        get_platform_order,
        get_orders_by_platform,
        get_orders_by_status,
        sync_platform_orders,
        get_customs_declaration,
        get_customs_by_order,
        get_customs_by_status,
        get_logistics_by_status,
        get_ecommerce_summary,
    )
    _ECOMMERCE_DATA_AVAILABLE = True
except ImportError:
    _ECOMMERCE_DATA_AVAILABLE = False
    
    # 内置 Mock 数据
    MOCK_EXCHANGE_RATES = {
        "USD_CNY": {"from_currency": "USD", "to_currency": "CNY", "rate": 7.25, "updated_at": "2026-02-17"},
        "EUR_CNY": {"from_currency": "EUR", "to_currency": "CNY", "rate": 7.85, "updated_at": "2026-02-17"},
    }
    MOCK_LOGISTICS_TRACKING = {
        "SF1234567890123": {"tracking_no": "SF1234567890123", "status": "in_transit", "carrier": "SF Express", "estimated_delivery": "2026-02-20", "timeline": [{"time": "2026-02-15 10:00", "status": "已发出", "location": "深圳"}, {"time": "2026-02-16 14:00", "status": "运输中", "location": "广州"}]},
        "YT9876543210987": {"tracking_no": "YT9876543210987", "status": "delayed", "carrier": "YTO Express", "estimated_delivery": "2026-02-25", "delay_reason": "天气原因", "timeline": [{"time": "2026-02-14 09:00", "status": "已发出", "location": "杭州"}, {"time": "2026-02-15 18:00", "status": "延迟", "location": "上海"}]},
    }
    MOCK_PLATFORM_ORDERS = {
        "AMZ-2026021002": {"order_id": "AMZ-2026021002", "status": "shipped", "platform": "amazon", "amount_usd": 99.99},
    }
    MOCK_CUSTOMS_DECLARATIONS = {
        "CUS2026021501": {"declaration_no": "CUS2026021501", "status": "cleared", "order_id": "AMZ-2026021002"},
    }
    
    def get_exchange_rate(from_curr: str, to_curr: str) -> Optional[Dict]:
        return MOCK_EXCHANGE_RATES.get(f"{from_curr}_{to_curr}")
    
    def convert_currency(amount: float, from_curr: str, to_curr: str) -> Dict:
        rate = get_exchange_rate(from_curr, to_curr)
        if rate:
            return {
                "success": True,
                "original_amount": amount,
                "original_currency": from_curr,
                "converted_currency": to_curr,
                "converted_amount": amount * rate["rate"],
                "rate": rate["rate"]
            }
        return {"success": False, "error": "Unsupported currency pair"}
    
    def track_logistics(tracking_no: str) -> Optional[Dict]:
        return MOCK_LOGISTICS_TRACKING.get(tracking_no)
    
    def get_platform_order(order_id: str) -> Optional[Dict]:
        return MOCK_PLATFORM_ORDERS.get(order_id)
    
    def get_orders_by_platform(platform: str) -> List:
        if platform:
            return [order for order in MOCK_PLATFORM_ORDERS.values() if order.get("platform") == platform]
        return list(MOCK_PLATFORM_ORDERS.values())
    
    def get_orders_by_status(status: str) -> List:
        if status:
            return [order for order in MOCK_PLATFORM_ORDERS.values() if order.get("status") == status]
        return list(MOCK_PLATFORM_ORDERS.values())
    
    def sync_platform_orders(platform: str, days: int = 7) -> Dict:
        orders = get_orders_by_platform(platform) if platform else list(MOCK_PLATFORM_ORDERS.values())
        return {"platform": platform or "all", "orders": orders, "total_orders": len(orders)}
    
    def get_customs_declaration(declaration_no: str) -> Optional[Dict]:
        return MOCK_CUSTOMS_DECLARATIONS.get(declaration_no)
    
    def get_customs_by_order(order_id: str) -> Optional[Dict]:
        for decl in MOCK_CUSTOMS_DECLARATIONS.values():
            if decl.get("order_id") == order_id:
                return decl
        return None
    
    def get_customs_by_status(status: str) -> List:
        if status:
            return [decl for decl in MOCK_CUSTOMS_DECLARATIONS.values() if decl.get("status") == status]
        return list(MOCK_CUSTOMS_DECLARATIONS.values())
    
    def get_logistics_by_status(status: str) -> List:
        if status:
            return [log for log in MOCK_LOGISTICS_TRACKING.values() if log.get("status") == status]
        return list(MOCK_LOGISTICS_TRACKING.values())
    
    def get_ecommerce_summary() -> Dict:
        orders = list(MOCK_PLATFORM_ORDERS.values())
        logistics = list(MOCK_LOGISTICS_TRACKING.values())
        customs = list(MOCK_CUSTOMS_DECLARATIONS.values())
        
        total_amount_usd = sum(order.get("amount_usd", 0) for order in orders)
        
        return {
            "orders": {
                "total": len(orders),
                "total_amount_usd": total_amount_usd,
            },
            "logistics": {
                "total": len(logistics),
            },
            "customs": {
                "total": len(customs),
            },
            "exchange_rates": {
                "total": len(MOCK_EXCHANGE_RATES),
            }
        }


class EcommerceMockServer(BaseToolServer):
    """
    跨境电商 Mock MCP Server
    
    提供跨境电商业务场景的模拟工具调用
    """
    
    def __init__(self, latency_ms: int = 100):
        """
        初始化电商 Mock Server
        
        Args:
            latency_ms: 模拟延迟（毫秒）
        """
        super().__init__(
            name="ecommerce-tools",
            description="跨境电商工具集：汇率查询、物流追踪、平台订单、报关状态"
        )
        self.latency_ms = latency_ms
        self._register_tools()
    
    def _register_tools(self):
        """注册所有电商工具"""
        
        # ==================== 汇率工具 ====================
        
        @self.register_tool(ToolSchema(
            name="get_exchange_rate",
            description="查询实时汇率",
            input_schema={
                "type": "object",
                "required": ["from_currency", "to_currency"],
                "properties": {
                    "from_currency": {
                        "type": "string",
                        "description": "源货币代码（USD/EUR/JPY/GBP/CNY）"
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "目标货币代码（USD/EUR/JPY/GBP/CNY）"
                    }
                }
            }
        ))
        async def get_exchange_rate_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            from_currency = params.get("from_currency", "").upper()
            to_currency = params.get("to_currency", "").upper()
            
            rate_info = get_exchange_rate(from_currency, to_currency)
            
            if rate_info:
                return ToolResult.success(rate_info)
            else:
                return ToolResult.error(
                    error=f"不支持的货币对: {from_currency} -> {to_currency}",
                    error_code="UNSUPPORTED_CURRENCY_PAIR"
                )
        
        @self.register_tool(ToolSchema(
            name="convert_currency",
            description="货币换算",
            input_schema={
                "type": "object",
                "required": ["amount", "from_currency", "to_currency"],
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "换算金额"
                    },
                    "from_currency": {
                        "type": "string",
                        "description": "源货币代码"
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "目标货币代码"
                    }
                }
            }
        ))
        async def convert_currency_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            amount = params.get("amount", 0)
            from_currency = params.get("from_currency", "").upper()
            to_currency = params.get("to_currency", "").upper()
            
            result = convert_currency(amount, from_currency, to_currency)
            
            if result.get("success"):
                return ToolResult.success(result)
            else:
                return ToolResult.error(
                    error=result.get("error", "换算失败"),
                    error_code="CONVERSION_ERROR"
                )
        
        @self.register_tool(ToolSchema(
            name="list_exchange_rates",
            description="获取所有支持货币的汇率列表",
            input_schema={
                "type": "object",
                "properties": {}
            }
        ))
        async def list_exchange_rates_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            rates = []
            for key, info in MOCK_EXCHANGE_RATES.items():
                rates.append({
                    "pair": key,
                    "from": info["from_currency"],
                    "to": info["to_currency"],
                    "rate": info["rate"],
                    "updated_at": info.get("updated_at", ""),
                })
            
            return ToolResult.success({
                "rates": rates,
                "total": len(rates),
            })
        
        # ==================== 物流工具 ====================
        
        @self.register_tool(ToolSchema(
            name="track_logistics",
            description="查询物流轨迹",
            input_schema={
                "type": "object",
                "required": ["tracking_no"],
                "properties": {
                    "tracking_no": {
                        "type": "string",
                        "description": "快递单号"
                    }
                }
            }
        ))
        async def track_logistics_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            tracking_no = params.get("tracking_no", "")
            
            result = track_logistics(tracking_no)
            
            if result:
                return ToolResult.success(result)
            else:
                return ToolResult.error(
                    error=f"快递单号不存在: {tracking_no}",
                    error_code="TRACKING_NOT_FOUND"
                )
        
        @self.register_tool(ToolSchema(
            name="list_logistics_by_status",
            description="按状态查询物流列表",
            input_schema={
                "type": "object",
                "required": ["status"],
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "物流状态：in_transit(运输中)/delivered(已签收)/delayed(延迟)/customs_hold(海关扣留)/out_for_delivery(派送中)"
                    }
                }
            }
        ))
        async def list_logistics_by_status_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            status = params.get("status", "")
            
            results = get_logistics_by_status(status)
            
            return ToolResult.success({
                "status": status,
                "items": results,
                "total": len(results),
            })
        
        @self.register_tool(ToolSchema(
            name="get_delayed_shipments",
            description="获取延迟的物流列表",
            input_schema={
                "type": "object",
                "properties": {}
            }
        ))
        async def get_delayed_shipments_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            delayed = get_logistics_by_status("delayed")
            customs_hold = get_logistics_by_status("customs_hold")
            
            all_issues = delayed + customs_hold
            
            return ToolResult.success({
                "delayed": delayed,
                "customs_hold": customs_hold,
                "total_issues": len(all_issues),
                "summary": {
                    "delayed_count": len(delayed),
                    "customs_hold_count": len(customs_hold),
                }
            })
        
        # ==================== 平台订单工具 ====================
        
        @self.register_tool(ToolSchema(
            name="get_platform_order",
            description="查询平台订单详情",
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
        async def get_platform_order_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            order_id = params.get("order_id", "")
            
            result = get_platform_order(order_id)
            
            if result:
                return ToolResult.success(result)
            else:
                return ToolResult.error(
                    error=f"订单不存在: {order_id}",
                    error_code="ORDER_NOT_FOUND"
                )
        
        @self.register_tool(ToolSchema(
            name="list_platform_orders",
            description="查询平台订单列表",
            input_schema={
                "type": "object",
                "properties": {
                    "platform": {
                        "type": "string",
                        "description": "平台：amazon/aliexpress/shopify"
                    },
                    "status": {
                        "type": "string",
                        "description": "订单状态筛选"
                    }
                }
            }
        ))
        async def list_platform_orders_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            platform = params.get("platform", "")
            status = params.get("status", "")
            
            if platform:
                results = get_orders_by_platform(platform)
            elif status:
                results = get_orders_by_status(status)
            else:
                results = list(MOCK_PLATFORM_ORDERS.values())
            
            return ToolResult.success({
                "orders": results,
                "total": len(results),
                "filters": {
                    "platform": platform or None,
                    "status": status or None,
                }
            })
        
        @self.register_tool(ToolSchema(
            name="sync_platform_orders",
            description="同步平台订单",
            input_schema={
                "type": "object",
                "required": ["platform"],
                "properties": {
                    "platform": {
                        "type": "string",
                        "description": "平台：amazon/aliexpress/shopify"
                    },
                    "days": {
                        "type": "integer",
                        "description": "同步天数",
                        "default": 7
                    }
                }
            }
        ))
        async def sync_platform_orders_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            platform = params.get("platform", "")
            days = params.get("days", 7)
            
            result = sync_platform_orders(platform, days)
            
            return ToolResult.success(result)
        
        @self.register_tool(ToolSchema(
            name="get_pending_shipments",
            description="获取待发货订单列表",
            input_schema={
                "type": "object",
                "properties": {}
            }
        ))
        async def get_pending_shipments_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            pending = get_orders_by_status("pending_shipment")
            pending_payment = get_orders_by_status("pending_payment")
            
            return ToolResult.success({
                "pending_shipment": pending,
                "pending_payment": pending_payment,
                "total_pending": len(pending),
                "total_unpaid": len(pending_payment),
            })
        
        # ==================== 报关工具 ====================
        
        @self.register_tool(ToolSchema(
            name="get_customs_declaration",
            description="查询报关单详情",
            input_schema={
                "type": "object",
                "properties": {
                    "declaration_no": {
                        "type": "string",
                        "description": "报关单号"
                    },
                    "order_id": {
                        "type": "string",
                        "description": "订单号（二选一）"
                    }
                }
            }
        ))
        async def get_customs_declaration_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            declaration_no = params.get("declaration_no", "")
            order_id = params.get("order_id", "")
            
            if declaration_no:
                result = get_customs_declaration(declaration_no)
            elif order_id:
                result = get_customs_by_order(order_id)
            else:
                return ToolResult.error(
                    error="请提供报关单号或订单号",
                    error_code="MISSING_PARAMETER"
                )
            
            if result:
                return ToolResult.success(result)
            else:
                return ToolResult.error(
                    error="报关单不存在",
                    error_code="DECLARATION_NOT_FOUND"
                )
        
        @self.register_tool(ToolSchema(
            name="list_customs_by_status",
            description="按状态查询报关单列表",
            input_schema={
                "type": "object",
                "required": ["status"],
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "报关状态：cleared(已放行)/pending_docs(待补充资料)/in_review(审核中)"
                    }
                }
            }
        ))
        async def list_customs_by_status_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            status = params.get("status", "")
            
            results = get_customs_by_status(status)
            
            return ToolResult.success({
                "status": status,
                "items": results,
                "total": len(results),
            })
        
        @self.register_tool(ToolSchema(
            name="get_customs_issues",
            description="获取有问题的报关单（需补充资料）",
            input_schema={
                "type": "object",
                "properties": {}
            }
        ))
        async def get_customs_issues_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            pending_docs = get_customs_by_status("pending_docs")
            
            return ToolResult.success({
                "pending_documents": pending_docs,
                "total": len(pending_docs),
                "requires_action": len(pending_docs) > 0,
            })
        
        # ==================== 统计工具 ====================
        
        @self.register_tool(ToolSchema(
            name="get_ecommerce_summary",
            description="获取跨境电商汇总统计",
            input_schema={
                "type": "object",
                "properties": {}
            }
        ))
        async def get_ecommerce_summary_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            result = get_ecommerce_summary()
            return ToolResult.success(result)
    
    async def health_check(self) -> bool:
        """健康检查"""
        return True


# ==================== 便捷函数 ====================

def create_ecommerce_server(latency_ms: int = 100) -> EcommerceMockServer:
    """创建电商 Mock Server"""
    return EcommerceMockServer(latency_ms)
