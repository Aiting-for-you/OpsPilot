"""
跨境电商 Mock 数据

包含：
- 汇率数据
- 物流轨迹
- 平台订单（亚马逊、速卖通）
- 报关状态
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random


# ==================== 汇率数据 ====================

MOCK_EXCHANGE_RATES: Dict[str, Dict[str, Any]] = {
    "USD_CNY": {
        "from_currency": "USD",
        "to_currency": "CNY",
        "rate": 7.2456,
        "rate_date": "2026-02-17",
        "updated_at": "2026-02-17T10:30:00Z",
        "source": "中国银行",
        "buy_rate": 7.2356,
        "sell_rate": 7.2556,
    },
    "EUR_CNY": {
        "from_currency": "EUR",
        "to_currency": "CNY",
        "rate": 7.8234,
        "rate_date": "2026-02-17",
        "updated_at": "2026-02-17T10:30:00Z",
        "source": "中国银行",
        "buy_rate": 7.8134,
        "sell_rate": 7.8334,
    },
    "JPY_CNY": {
        "from_currency": "JPY",
        "to_currency": "CNY",
        "rate": 0.0482,
        "rate_date": "2026-02-17",
        "updated_at": "2026-02-17T10:30:00Z",
        "source": "中国银行",
        "buy_rate": 0.0480,
        "sell_rate": 0.0484,
    },
    "GBP_CNY": {
        "from_currency": "GBP",
        "to_currency": "CNY",
        "rate": 9.1234,
        "rate_date": "2026-02-17",
        "updated_at": "2026-02-17T10:30:00Z",
        "source": "中国银行",
        "buy_rate": 9.1134,
        "sell_rate": 9.1334,
    },
    "CNY_USD": {
        "from_currency": "CNY",
        "to_currency": "USD",
        "rate": 0.1380,
        "rate_date": "2026-02-17",
        "updated_at": "2026-02-17T10:30:00Z",
        "source": "中国银行",
        "buy_rate": 0.1378,
        "sell_rate": 0.1382,
    },
}


def get_exchange_rate(from_currency: str, to_currency: str) -> Optional[Dict[str, Any]]:
    """
    获取汇率
    
    Args:
        from_currency: 源货币
        to_currency: 目标货币
    
    Returns:
        汇率信息
    """
    key = f"{from_currency}_{to_currency}"
    if key in MOCK_EXCHANGE_RATES:
        return MOCK_EXCHANGE_RATES[key]
    return None


def convert_currency(amount: float, from_currency: str, to_currency: str) -> Dict[str, Any]:
    """
    货币换算
    
    Args:
        amount: 金额
        from_currency: 源货币
        to_currency: 目标货币
    
    Returns:
        换算结果
    """
    rate_info = get_exchange_rate(from_currency, to_currency)
    
    if not rate_info:
        return {
            "success": False,
            "error": f"不支持的货币对: {from_currency} -> {to_currency}",
        }
    
    converted_amount = amount * rate_info["rate"]
    
    return {
        "success": True,
        "original_amount": amount,
        "original_currency": from_currency,
        "converted_amount": round(converted_amount, 2),
        "converted_currency": to_currency,
        "exchange_rate": rate_info["rate"],
        "rate_date": rate_info["rate_date"],
        "source": rate_info["source"],
    }


# ==================== 物流轨迹 ====================

MOCK_LOGISTICS_COMPANIES = [
    {"code": "SF", "name": "顺丰速运"},
    {"code": "YTO", "name": "圆通速递"},
    {"code": "ZTO", "name": "中通快递"},
    {"code": "DHL", "name": "DHL国际快递"},
    {"code": "FEDEX", "name": "联邦快递"},
    {"code": "UPS", "name": "UPS联合包裹"},
]

MOCK_LOGISTICS_TRACKING: Dict[str, Dict[str, Any]] = {
    # 正常运输中
    "SF1234567890123": {
        "tracking_no": "SF1234567890123",
        "carrier": "SF",
        "carrier_name": "顺丰速运",
        "status": "in_transit",
        "status_text": "运输中",
        "origin": "深圳市",
        "destination": "上海市",
        "estimated_delivery": "2026-02-19",
        "weight_kg": 2.5,
        "current_location": "杭州转运中心",
        "timeline": [
            {
                "time": "2026-02-17T14:30:00",
                "location": "杭州转运中心",
                "status": "已到达",
                "description": "快件已到达杭州转运中心",
            },
            {
                "time": "2026-02-17T08:15:00",
                "location": "深圳集散中心",
                "status": "已发出",
                "description": "快件已从深圳集散中心发出",
            },
            {
                "time": "2026-02-16T18:00:00",
                "location": "深圳市南山区",
                "status": "已揽收",
                "description": "快递员已揽收",
            },
        ],
    },
    # 已签收
    "DHL9876543210987": {
        "tracking_no": "DHL9876543210987",
        "carrier": "DHL",
        "carrier_name": "DHL国际快递",
        "status": "delivered",
        "status_text": "已签收",
        "origin": "美国洛杉矶",
        "destination": "深圳市",
        "estimated_delivery": "2026-02-15",
        "actual_delivery": "2026-02-15T16:30:00",
        "weight_kg": 5.2,
        "signed_by": "张先生",
        "timeline": [
            {
                "time": "2026-02-15T16:30:00",
                "location": "深圳市南山区",
                "status": "已签收",
                "description": "快件已签收，签收人：张先生",
            },
            {
                "time": "2026-02-15T10:00:00",
                "location": "深圳转运中心",
                "status": "派送中",
                "description": "快件正在派送",
            },
            {
                "time": "2026-02-14T20:00:00",
                "location": "深圳海关",
                "status": "清关完成",
                "description": "海关放行",
            },
            {
                "time": "2026-02-13T08:00:00",
                "location": "香港转运中心",
                "status": "中转",
                "description": "快件到达香港转运中心",
            },
            {
                "time": "2026-02-10T15:00:00",
                "location": "美国洛杉矶",
                "status": "已发出",
                "description": "快件已从洛杉矶发出",
            },
        ],
    },
    # 物流延迟
    "ZTO1122334455667": {
        "tracking_no": "ZTO1122334455667",
        "carrier": "ZTO",
        "carrier_name": "中通快递",
        "status": "delayed",
        "status_text": "运输延迟",
        "origin": "广州市",
        "destination": "北京市",
        "estimated_delivery": "2026-02-16",
        "delayed_delivery": "2026-02-20",
        "weight_kg": 1.8,
        "delay_reason": "因天气原因，航班延误",
        "current_location": "武汉转运中心",
        "timeline": [
            {
                "time": "2026-02-17T10:00:00",
                "location": "武汉转运中心",
                "status": "滞留",
                "description": "因天气原因，快件滞留武汉转运中心",
            },
            {
                "time": "2026-02-16T14:00:00",
                "location": "武汉转运中心",
                "status": "已到达",
                "description": "快件已到达武汉转运中心",
            },
            {
                "time": "2026-02-16T06:00:00",
                "location": "广州集散中心",
                "status": "已发出",
                "description": "快件已从广州集散中心发出",
            },
        ],
    },
    # 海关扣留
    "FEDEX4455667788990": {
        "tracking_no": "FEDEX4455667788990",
        "carrier": "FEDEX",
        "carrier_name": "联邦快递",
        "status": "customs_hold",
        "status_text": "海关扣留",
        "origin": "德国法兰克福",
        "destination": "深圳市",
        "estimated_delivery": "2026-02-18",
        "weight_kg": 8.5,
        "customs_status": "待补充资料",
        "customs_requirement": "需提供产品原产地证明",
        "current_location": "深圳海关",
        "timeline": [
            {
                "time": "2026-02-17T09:00:00",
                "location": "深圳海关",
                "status": "海关扣留",
                "description": "海关要求补充资料：产品原产地证明",
            },
            {
                "time": "2026-02-16T18:00:00",
                "location": "深圳海关",
                "status": "清关中",
                "description": "快件正在清关",
            },
            {
                "time": "2026-02-14T10:00:00",
                "location": "香港转运中心",
                "status": "中转",
                "description": "快件到达香港转运中心",
            },
        ],
    },
    # 派送中
    "YTO7788990011223": {
        "tracking_no": "YTO7788990011223",
        "carrier": "YTO",
        "carrier_name": "圆通速递",
        "status": "out_for_delivery",
        "status_text": "派送中",
        "origin": "杭州市",
        "destination": "深圳市",
        "estimated_delivery": "2026-02-17",
        "weight_kg": 0.8,
        "courier_name": "李师傅",
        "courier_phone": "138****5678",
        "current_location": "深圳市南山区",
        "timeline": [
            {
                "time": "2026-02-17T11:30:00",
                "location": "深圳市南山区",
                "status": "派送中",
                "description": "快递员李师傅正在派送，电话：138****5678",
            },
            {
                "time": "2026-02-17T06:00:00",
                "location": "深圳转运中心",
                "status": "已发出",
                "description": "快件已发出派送",
            },
        ],
    },
}


def track_logistics(tracking_no: str) -> Optional[Dict[str, Any]]:
    """
    查询物流轨迹
    
    Args:
        tracking_no: 快递单号
    
    Returns:
        物流信息
    """
    if tracking_no in MOCK_LOGISTICS_TRACKING:
        return MOCK_LOGISTICS_TRACKING[tracking_no]
    return None


def get_logistics_by_status(status: str) -> List[Dict[str, Any]]:
    """
    按状态获取物流列表
    
    Args:
        status: 状态（in_transit/delivered/delayed/customs_hold/out_for_delivery）
    
    Returns:
        物流列表
    """
    return [
        info for info in MOCK_LOGISTICS_TRACKING.values()
        if info["status"] == status
    ]


# ==================== 平台订单 ====================

MOCK_PLATFORM_ORDERS: Dict[str, Dict[str, Any]] = {
    # 亚马逊订单 - 待发货
    "AMZ-2026021501": {
        "order_id": "AMZ-2026021501",
        "platform": "amazon",
        "platform_name": "亚马逊",
        "marketplace": "Amazon.com",
        "status": "pending_shipment",
        "status_text": "待发货",
        "order_date": "2026-02-15T08:30:00Z",
        "buyer": {
            "name": "John Smith",
            "email": "j***@gmail.com",
            "country": "美国",
            "state": "California",
            "city": "Los Angeles",
        },
        "items": [
            {
                "sku": "SKU003",
                "asin": "B09XXXXXXXXX",
                "title": "STM32F103C8T6 Development Board",
                "quantity": 5,
                "unit_price_usd": 8.50,
                "total_usd": 42.50,
            },
        ],
        "total_amount_usd": 42.50,
        "total_amount_cny": 308.24,
        "shipping_method": "Standard",
        "estimated_delivery": "2026-02-25",
    },
    # 亚马逊订单 - 已发货
    "AMZ-2026021002": {
        "order_id": "AMZ-2026021002",
        "platform": "amazon",
        "platform_name": "亚马逊",
        "marketplace": "Amazon.com",
        "status": "shipped",
        "status_text": "已发货",
        "order_date": "2026-02-10T14:20:00Z",
        "ship_date": "2026-02-12T10:00:00Z",
        "buyer": {
            "name": "Emily Johnson",
            "email": "e***@yahoo.com",
            "country": "美国",
            "state": "Texas",
            "city": "Houston",
        },
        "items": [
            {
                "sku": "SKU004",
                "asin": "B08YYYYYYYYY",
                "title": "DHT11 Temperature Humidity Sensor",
                "quantity": 20,
                "unit_price_usd": 3.80,
                "total_usd": 76.00,
            },
        ],
        "total_amount_usd": 76.00,
        "total_amount_cny": 550.66,
        "shipping_method": "Expedited",
        "tracking_no": "DHL9876543210987",
        "estimated_delivery": "2026-02-15",
    },
    # 速卖通订单 - 待付款
    "AE-2026021701": {
        "order_id": "AE-2026021701",
        "platform": "aliexpress",
        "platform_name": "速卖通",
        "marketplace": "AliExpress",
        "status": "pending_payment",
        "status_text": "待付款",
        "order_date": "2026-02-17T03:45:00Z",
        "buyer": {
            "name": "Marie Dupont",
            "email": "m***@hotmail.fr",
            "country": "法国",
            "city": "Paris",
        },
        "items": [
            {
                "sku": "SKU001",
                "product_id": "1005001234567890",
                "title": "100Ω Resistor Pack (100pcs)",
                "quantity": 100,
                "unit_price_usd": 0.02,
                "total_usd": 2.00,
            },
            {
                "sku": "SKU002",
                "product_id": "1005000987654321",
                "title": "10μF Capacitor Pack (50pcs)",
                "quantity": 50,
                "unit_price_usd": 0.05,
                "total_usd": 2.50,
            },
        ],
        "total_amount_usd": 4.50,
        "total_amount_cny": 32.61,
        "shipping_method": "AliExpress Standard Shipping",
        "payment_deadline": "2026-02-20T03:45:00Z",
    },
    # 速卖通订单 - 运输中
    "AE-2026020801": {
        "order_id": "AE-2026020801",
        "platform": "aliexpress",
        "platform_name": "速卖通",
        "marketplace": "AliExpress",
        "status": "in_transit",
        "status_text": "运输中",
        "order_date": "2026-02-08T16:30:00Z",
        "ship_date": "2026-02-10T09:00:00Z",
        "buyer": {
            "name": "Hans Mueller",
            "email": "h***@gmail.com",
            "country": "德国",
            "city": "Berlin",
        },
        "items": [
            {
                "sku": "SKU005",
                "product_id": "1005005555666677",
                "title": "6205-2RS Bearing (10pcs)",
                "quantity": 10,
                "unit_price_usd": 12.00,
                "total_usd": 120.00,
            },
        ],
        "total_amount_usd": 120.00,
        "total_amount_cny": 869.47,
        "shipping_method": "AliExpress Standard Shipping",
        "tracking_no": "SF1234567890123",
        "estimated_delivery": "2026-02-28",
    },
    # 独立站订单 - 已完成
    "WEB-2026020501": {
        "order_id": "WEB-2026020501",
        "platform": "shopify",
        "platform_name": "独立站",
        "marketplace": "myshop.example.com",
        "status": "completed",
        "status_text": "已完成",
        "order_date": "2026-02-05T22:15:00Z",
        "ship_date": "2026-02-07T11:00:00Z",
        "delivery_date": "2026-02-14T15:30:00Z",
        "buyer": {
            "name": "Tanaka Yuki",
            "email": "t***@gmail.com",
            "country": "日本",
            "city": "Tokyo",
        },
        "items": [
            {
                "sku": "SKU003",
                "title": "STM32F103C8T6 Development Board",
                "quantity": 10,
                "unit_price_usd": 8.50,
                "total_usd": 85.00,
            },
            {
                "sku": "SKU004",
                "title": "DHT11 Temperature Humidity Sensor",
                "quantity": 20,
                "unit_price_usd": 3.80,
                "total_usd": 76.00,
            },
        ],
        "total_amount_usd": 161.00,
        "total_amount_cny": 1166.54,
        "shipping_method": "DHL Express",
        "tracking_no": "DHL1234567890123",
    },
}


def get_platform_order(order_id: str) -> Optional[Dict[str, Any]]:
    """
    获取平台订单
    
    Args:
        order_id: 订单号
    
    Returns:
        订单信息
    """
    if order_id in MOCK_PLATFORM_ORDERS:
        return MOCK_PLATFORM_ORDERS[order_id]
    return None


def get_orders_by_platform(platform: str) -> List[Dict[str, Any]]:
    """
    按平台获取订单列表
    
    Args:
        platform: 平台（amazon/aliexpress/shopify）
    
    Returns:
        订单列表
    """
    return [
        order for order in MOCK_PLATFORM_ORDERS.values()
        if order["platform"] == platform
    ]


def get_orders_by_status(status: str) -> List[Dict[str, Any]]:
    """
    按状态获取订单列表
    
    Args:
        status: 状态
    
    Returns:
        订单列表
    """
    return [
        order for order in MOCK_PLATFORM_ORDERS.values()
        if order["status"] == status
    ]


def sync_platform_orders(platform: str, days: int = 7) -> Dict[str, Any]:
    """
    同步平台订单
    
    Args:
        platform: 平台
        days: 同步天数
    
    Returns:
        同步结果
    """
    orders = get_orders_by_platform(platform)
    
    return {
        "platform": platform,
        "sync_time": datetime.now().isoformat(),
        "total_orders": len(orders),
        "orders": orders,
        "sync_range": f"最近 {days} 天",
    }


# ==================== 报关状态 ====================

MOCK_CUSTOMS_DECLARATIONS: Dict[str, Dict[str, Any]] = {
    "CUS2026021501": {
        "declaration_no": "CUS2026021501",
        "order_id": "AMZ-2026021002",
        "status": "cleared",
        "status_text": "已放行",
        "declaration_type": "出口报关",
        "customs_port": "深圳海关",
        "declaration_date": "2026-02-12",
        "clearance_date": "2026-02-13",
        "hs_code": "8542.31",
        "goods_name": "集成电路开发板",
        "quantity": 20,
        "unit": "个",
        "gross_weight_kg": 0.5,
        "net_weight_kg": 0.3,
        "value_usd": 76.00,
        "value_cny": 550.66,
        "trade_terms": "FOB",
        "declared_by": "深圳XX供应链管理有限公司",
        "timeline": [
            {
                "time": "2026-02-13T16:00:00",
                "status": "放行",
                "description": "海关放行，货物可以提离",
            },
            {
                "time": "2026-02-13T10:00:00",
                "status": "查验",
                "description": "货物查验中",
            },
            {
                "time": "2026-02-12T15:00:00",
                "status": "申报",
                "description": "报关单已提交",
            },
        ],
    },
    "CUS2026021601": {
        "declaration_no": "CUS2026021601",
        "order_id": "AE-2026020801",
        "status": "pending_docs",
        "status_text": "待补充资料",
        "declaration_type": "出口报关",
        "customs_port": "深圳海关",
        "declaration_date": "2026-02-11",
        "hs_code": "8482.10",
        "goods_name": "滚动轴承",
        "quantity": 10,
        "unit": "个",
        "gross_weight_kg": 2.0,
        "net_weight_kg": 1.8,
        "value_usd": 120.00,
        "value_cny": 869.47,
        "trade_terms": "CIF",
        "declared_by": "深圳XX供应链管理有限公司",
        "pending_documents": [
            "产品原产地证明",
            "质量检测报告",
        ],
        "deadline": "2026-02-20",
        "timeline": [
            {
                "time": "2026-02-17T09:00:00",
                "status": "待补充",
                "description": "海关要求补充：产品原产地证明、质量检测报告",
            },
            {
                "time": "2026-02-11T16:00:00",
                "status": "审核中",
                "description": "报关单审核中",
            },
            {
                "time": "2026-02-11T10:00:00",
                "status": "申报",
                "description": "报关单已提交",
            },
        ],
    },
    "CUS2026021701": {
        "declaration_no": "CUS2026021701",
        "order_id": "WEB-2026020501",
        "status": "in_review",
        "status_text": "审核中",
        "declaration_type": "出口报关",
        "customs_port": "深圳海关",
        "declaration_date": "2026-02-17",
        "hs_code": "8542.31",
        "goods_name": "电子元器件",
        "quantity": 30,
        "unit": "个",
        "gross_weight_kg": 1.2,
        "net_weight_kg": 0.8,
        "value_usd": 161.00,
        "value_cny": 1166.54,
        "trade_terms": "DDP",
        "declared_by": "深圳XX供应链管理有限公司",
        "timeline": [
            {
                "time": "2026-02-17T14:00:00",
                "status": "审核中",
                "description": "报关单正在审核",
            },
            {
                "time": "2026-02-17T09:00:00",
                "status": "申报",
                "description": "报关单已提交",
            },
        ],
    },
}


def get_customs_declaration(declaration_no: str) -> Optional[Dict[str, Any]]:
    """
    获取报关单
    
    Args:
        declaration_no: 报关单号
    
    Returns:
        报关单信息
    """
    if declaration_no in MOCK_CUSTOMS_DECLARATIONS:
        return MOCK_CUSTOMS_DECLARATIONS[declaration_no]
    return None


def get_customs_by_order(order_id: str) -> Optional[Dict[str, Any]]:
    """
    根据订单号获取报关单
    
    Args:
        order_id: 订单号
    
    Returns:
        报关单信息
    """
    for decl in MOCK_CUSTOMS_DECLARATIONS.values():
        if decl.get("order_id") == order_id:
            return decl
    return None


def get_customs_by_status(status: str) -> List[Dict[str, Any]]:
    """
    按状态获取报关单列表
    
    Args:
        status: 状态（cleared/pending_docs/in_review）
    
    Returns:
        报关单列表
    """
    return [
        decl for decl in MOCK_CUSTOMS_DECLARATIONS.values()
        if decl["status"] == status
    ]


# ==================== 统计汇总 ====================

def get_ecommerce_summary() -> Dict[str, Any]:
    """
    获取跨境电商汇总统计
    
    Returns:
        统计数据
    """
    total_orders = len(MOCK_PLATFORM_ORDERS)
    total_amount_usd = sum(o["total_amount_usd"] for o in MOCK_PLATFORM_ORDERS.values())
    
    # 按平台统计
    platform_stats = {}
    for order in MOCK_PLATFORM_ORDERS.values():
        platform = order["platform"]
        if platform not in platform_stats:
            platform_stats[platform] = {"count": 0, "amount_usd": 0}
        platform_stats[platform]["count"] += 1
        platform_stats[platform]["amount_usd"] += order["total_amount_usd"]
    
    # 按状态统计
    status_stats = {}
    for order in MOCK_PLATFORM_ORDERS.values():
        status = order["status"]
        status_stats[status] = status_stats.get(status, 0) + 1
    
    # 物流状态统计
    logistics_stats = {}
    for track in MOCK_LOGISTICS_TRACKING.values():
        status = track["status"]
        logistics_stats[status] = logistics_stats.get(status, 0) + 1
    
    # 报关状态统计
    customs_stats = {}
    for decl in MOCK_CUSTOMS_DECLARATIONS.values():
        status = decl["status"]
        customs_stats[status] = customs_stats.get(status, 0) + 1
    
    return {
        "orders": {
            "total": total_orders,
            "total_amount_usd": total_amount_usd,
            "total_amount_cny": round(total_amount_usd * 7.2456, 2),
            "by_platform": platform_stats,
            "by_status": status_stats,
        },
        "logistics": {
            "total": len(MOCK_LOGISTICS_TRACKING),
            "by_status": logistics_stats,
        },
        "customs": {
            "total": len(MOCK_CUSTOMS_DECLARATIONS),
            "by_status": customs_stats,
        },
        "exchange_rates": {
            "USD_CNY": MOCK_EXCHANGE_RATES["USD_CNY"]["rate"],
            "EUR_CNY": MOCK_EXCHANGE_RATES["EUR_CNY"]["rate"],
            "JPY_CNY": MOCK_EXCHANGE_RATES["JPY_CNY"]["rate"],
        },
        "updated_at": datetime.now().isoformat(),
    }
