"""
ERP 系统模拟数据

模拟电商/供应链场景的 ERP 数据，包括：
- 供应商管理
- 产品库存
- 仓库管理
- 采购订单
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random
import string


# ==================== 供应商数据 ====================

MOCK_SUPPLIERS: List[Dict[str, Any]] = [
    {
        "id": "SUP001",
        "name": "华南电子科技有限公司",
        "short_name": "华南电子",
        "region": "华南",
        "province": "广东省",
        "city": "深圳市",
        "address": "南山区科技园南区",
        "rating": 4.8,
        "rating_count": 256,
        "products": ["电子元件", "芯片", "传感器", "连接器"],
        "main_category": "电子元器件",
        "contact": "张伟",
        "phone": "138****1234",
        "email": "zhang.wei@huanan-elec.com",
        "payment_terms": "月结30天",
        "min_order_amount": 500.0,
        "delivery_days": 3,
        "certifications": ["ISO9001", "ISO14001", "ROHS"],
        "status": "active",
        "cooperation_years": 5,
    },
    {
        "id": "SUP002",
        "name": "华东精密制造有限公司",
        "short_name": "华东精密",
        "region": "华东",
        "province": "江苏省",
        "city": "苏州市",
        "address": "工业园区金鸡湖大道",
        "rating": 4.5,
        "rating_count": 189,
        "products": ["机械零件", "模具", "金属加工", "钣金件"],
        "main_category": "机械加工",
        "contact": "李明",
        "phone": "139****5678",
        "email": "li.ming@huadong-precision.com",
        "payment_terms": "月结45天",
        "min_order_amount": 1000.0,
        "delivery_days": 5,
        "certifications": ["ISO9001", "IATF16949"],
        "status": "active",
        "cooperation_years": 3,
    },
    {
        "id": "SUP003",
        "name": "华北物流供应链股份有限公司",
        "short_name": "华北物流",
        "region": "华北",
        "province": "北京市",
        "city": "北京市",
        "address": "大兴区物流基地",
        "rating": 4.6,
        "rating_count": 312,
        "products": ["包装材料", "托盘", "仓储设备", "周转箱"],
        "main_category": "物流包装",
        "contact": "王芳",
        "phone": "137****9012",
        "email": "wang.fang@huabei-logistics.com",
        "payment_terms": "月结30天",
        "min_order_amount": 300.0,
        "delivery_days": 2,
        "certifications": ["ISO9001"],
        "status": "active",
        "cooperation_years": 7,
    },
    {
        "id": "SUP004",
        "name": "西南化工材料有限公司",
        "short_name": "西南化工",
        "region": "西南",
        "province": "四川省",
        "city": "成都市",
        "address": "高新区天府大道",
        "rating": 4.2,
        "rating_count": 98,
        "products": ["化工原料", "润滑剂", "清洗剂", "胶粘剂"],
        "main_category": "化工材料",
        "contact": "陈强",
        "phone": "136****3456",
        "email": "chen.qiang@xinan-chem.com",
        "payment_terms": "月结30天",
        "min_order_amount": 800.0,
        "delivery_days": 4,
        "certifications": ["ISO9001", "ISO14001"],
        "status": "active",
        "cooperation_years": 2,
    },
    {
        "id": "SUP005",
        "name": "东北机械装备集团",
        "short_name": "东北机械",
        "region": "东北",
        "province": "辽宁省",
        "city": "沈阳市",
        "address": "铁西区装备制造园",
        "rating": 4.0,
        "rating_count": 145,
        "products": ["重型机械", "传动设备", "液压系统", "轴承"],
        "main_category": "重型装备",
        "contact": "赵刚",
        "phone": "135****7890",
        "email": "zhao.gang@dongbei-machine.com",
        "payment_terms": "月结60天",
        "min_order_amount": 5000.0,
        "delivery_days": 10,
        "certifications": ["ISO9001", "ISO14001", "OHSAS18001"],
        "status": "active",
        "cooperation_years": 4,
    },
]


# ==================== 产品与库存数据 ====================

MOCK_PRODUCTS: Dict[str, Dict[str, Any]] = {
    # 电子元器件类
    "SKU001": {
        "name": "电阻100Ω ±1%",
        "category": "电子元器件",
        "subcategory": "电阻",
        "specification": "0805封装 1/8W",
        "unit": "个",
        "unit_price": 0.02,
        "currency": "CNY",
        "min_pack_qty": 1000,
        "safety_stock": 10000,
        "supplier_id": "SUP001",
        "lead_time_days": 7,
    },
    "SKU002": {
        "name": "电容10μF 16V",
        "category": "电子元器件",
        "subcategory": "电容",
        "specification": "1206封装 X5R",
        "unit": "个",
        "unit_price": 0.05,
        "currency": "CNY",
        "min_pack_qty": 500,
        "safety_stock": 5000,
        "supplier_id": "SUP001",
        "lead_time_days": 7,
    },
    "SKU003": {
        "name": "芯片STM32F103C8T6",
        "category": "电子元器件",
        "subcategory": "MCU芯片",
        "specification": "ARM Cortex-M3 72MHz",
        "unit": "个",
        "unit_price": 8.50,
        "currency": "CNY",
        "min_pack_qty": 10,
        "safety_stock": 200,
        "supplier_id": "SUP001",
        "lead_time_days": 14,
    },
    "SKU004": {
        "name": "温湿度传感器DHT11",
        "category": "电子元器件",
        "subcategory": "传感器",
        "specification": "温度0-50°C 湿度20-90%RH",
        "unit": "个",
        "unit_price": 3.80,
        "currency": "CNY",
        "min_pack_qty": 10,
        "safety_stock": 500,
        "supplier_id": "SUP001",
        "lead_time_days": 5,
    },
    # 机械零件类
    "SKU005": {
        "name": "轴承6205-2RS",
        "category": "机械零件",
        "subcategory": "轴承",
        "specification": "深沟球轴承 25×52×15mm",
        "unit": "个",
        "unit_price": 12.00,
        "currency": "CNY",
        "min_pack_qty": 10,
        "safety_stock": 100,
        "supplier_id": "SUP002",
        "lead_time_days": 10,
    },
    "SKU006": {
        "name": "铝合金型材4040",
        "category": "机械零件",
        "subcategory": "型材",
        "specification": "欧标40×40mm 6米/根",
        "unit": "根",
        "unit_price": 85.00,
        "currency": "CNY",
        "min_pack_qty": 1,
        "safety_stock": 50,
        "supplier_id": "SUP002",
        "lead_time_days": 5,
    },
    # 包装材料类
    "SKU007": {
        "name": "瓦楞纸箱400×300×200",
        "category": "包装材料",
        "subcategory": "纸箱",
        "specification": "5层瓦楞纸板",
        "unit": "个",
        "unit_price": 4.50,
        "currency": "CNY",
        "min_pack_qty": 50,
        "safety_stock": 500,
        "supplier_id": "SUP003",
        "lead_time_days": 3,
    },
    "SKU008": {
        "name": "木托盘1200×1000",
        "category": "包装材料",
        "subcategory": "托盘",
        "specification": "实木四向进叉",
        "unit": "个",
        "unit_price": 120.00,
        "currency": "CNY",
        "min_pack_qty": 10,
        "safety_stock": 100,
        "supplier_id": "SUP003",
        "lead_time_days": 5,
    },
    # 化工材料类
    "SKU009": {
        "name": "工业润滑油L-HM46",
        "category": "化工材料",
        "subcategory": "润滑油",
        "specification": "抗磨液压油 200L/桶",
        "unit": "桶",
        "unit_price": 1800.00,
        "currency": "CNY",
        "min_pack_qty": 1,
        "safety_stock": 10,
        "supplier_id": "SUP004",
        "lead_time_days": 7,
    },
    "SKU010": {
        "name": "清洗剂WD-40",
        "category": "化工材料",
        "subcategory": "清洗剂",
        "specification": "多功能清洗润滑剂 400ml",
        "unit": "瓶",
        "unit_price": 25.00,
        "currency": "CNY",
        "min_pack_qty": 24,
        "safety_stock": 100,
        "supplier_id": "SUP004",
        "lead_time_days": 5,
    },
}

MOCK_INVENTORY: Dict[str, Dict[str, Any]] = {
    "SKU001": {
        "quantity": 50000,
        "available": 48000,
        "reserved": 2000,
        "warehouse": "WH001",
        "location": "A-01-01",
        "last_updated": "2026-02-15T10:00:00",
    },
    "SKU002": {
        "quantity": 30000,
        "available": 28500,
        "reserved": 1500,
        "warehouse": "WH001",
        "location": "A-01-02",
        "last_updated": "2026-02-15T10:00:00",
    },
    "SKU003": {
        "quantity": 200,
        "available": 180,
        "reserved": 20,
        "warehouse": "WH002",
        "location": "B-02-01",
        "last_updated": "2026-02-15T10:00:00",
    },
    "SKU004": {
        "quantity": 800,
        "available": 750,
        "reserved": 50,
        "warehouse": "WH002",
        "location": "B-02-02",
        "last_updated": "2026-02-15T10:00:00",
    },
    "SKU005": {
        "quantity": 150,
        "available": 120,
        "reserved": 30,
        "warehouse": "WH001",
        "location": "A-03-01",
        "last_updated": "2026-02-15T10:00:00",
    },
    "SKU006": {
        "quantity": 80,
        "available": 60,
        "reserved": 20,
        "warehouse": "WH001",
        "location": "A-03-02",
        "last_updated": "2026-02-15T10:00:00",
    },
    "SKU007": {
        "quantity": 1000,
        "available": 950,
        "reserved": 50,
        "warehouse": "WH003",
        "location": "C-01-01",
        "last_updated": "2026-02-15T10:00:00",
    },
    "SKU008": {
        "quantity": 200,
        "available": 180,
        "reserved": 20,
        "warehouse": "WH003",
        "location": "C-01-02",
        "last_updated": "2026-02-15T10:00:00",
    },
    "SKU009": {
        "quantity": 15,
        "available": 12,
        "reserved": 3,
        "warehouse": "WH002",
        "location": "B-04-01",
        "last_updated": "2026-02-15T10:00:00",
    },
    "SKU010": {
        "quantity": 200,
        "available": 180,
        "reserved": 20,
        "warehouse": "WH002",
        "location": "B-04-02",
        "last_updated": "2026-02-15T10:00:00",
    },
}


# ==================== 仓库数据 ====================

MOCK_WAREHOUSES: List[Dict[str, Any]] = [
    {
        "id": "WH001",
        "name": "深圳仓库",
        "region": "华南",
        "province": "广东省",
        "city": "深圳市",
        "address": "宝安区福永街道物流园",
        "capacity": 50000,  # 平方米
        "used": 35000,
        "manager": "刘经理",
        "phone": "139****0001",
        "type": "原材料仓",
        "status": "active",
    },
    {
        "id": "WH002",
        "name": "上海仓库",
        "region": "华东",
        "province": "上海市",
        "city": "上海市",
        "address": "浦东新区外高桥保税区",
        "capacity": 30000,
        "used": 22000,
        "manager": "周经理",
        "phone": "138****0002",
        "type": "成品仓",
        "status": "active",
    },
    {
        "id": "WH003",
        "name": "北京仓库",
        "region": "华北",
        "province": "北京市",
        "city": "北京市",
        "address": "顺义区空港物流基地",
        "capacity": 20000,
        "used": 15000,
        "manager": "吴经理",
        "phone": "137****0003",
        "type": "包装材料仓",
        "status": "active",
    },
]


# ==================== 采购订单数据 ====================

MOCK_PURCHASE_ORDERS: Dict[str, Dict[str, Any]] = {}

def generate_mock_order(
    supplier_id: str = "SUP001",
    products: Optional[List[Dict[str, Any]]] = None,
    status: str = "created",
    created_by: str = "test_user",
) -> Dict[str, Any]:
    """
    生成模拟采购订单

    Args:
        supplier_id: 供应商ID
        products: 产品列表 [{"sku": "SKU001", "quantity": 100}, ...]
        status: 订单状态
        created_by: 创建人

    Returns:
        订单数据字典
    """
    if products is None:
        products = [{"sku": "SKU001", "quantity": 1000}]

    supplier = next((s for s in MOCK_SUPPLIERS if s["id"] == supplier_id), None)
    if not supplier:
        raise ValueError(f"供应商不存在: {supplier_id}")

    # 计算金额
    total_amount = 0
    order_products = []
    for p in products:
        sku = p["sku"]
        qty = p["quantity"]
        product = MOCK_PRODUCTS.get(sku)
        if not product:
            continue
        unit_price = product["unit_price"]
        amount = unit_price * qty
        total_amount += amount
        order_products.append({
            "sku": sku,
            "name": product["name"],
            "quantity": qty,
            "unit_price": unit_price,
            "amount": round(amount, 2),
        })

    # 生成订单号
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = ''.join(random.choices(string.digits, k=4))
    order_id = f"PO{timestamp}{random_suffix}"

    # 判断审批级别
    need_approval = total_amount > 10000
    approval_level = "manager" if total_amount <= 50000 else "director"
    
    # 如果需要审批且未指定状态，默认设置为pending_approval
    if need_approval and status == "created":
        status = "pending_approval"

    order = {
        "order_id": order_id,
        "supplier_id": supplier_id,
        "supplier_name": supplier["name"],
        "products": order_products,
        "total_amount": round(total_amount, 2),
        "currency": "CNY",
        "status": status,
        "need_approval": need_approval,
        "approval_level": approval_level if need_approval else None,
        "payment_terms": supplier["payment_terms"],
        "expected_delivery": (datetime.now() + timedelta(days=supplier["delivery_days"])).strftime("%Y-%m-%d"),
        "created_at": datetime.now().isoformat(),
        "created_by": created_by,
        "updated_at": None,
        "approved_by": None,
        "approved_at": None,
    }

    MOCK_PURCHASE_ORDERS[order_id] = order
    return order


def get_low_stock_products(threshold_ratio: float = 0.2) -> List[Dict[str, Any]]:
    """
    获取库存预警产品

    Args:
        threshold_ratio: 库存低于安全库存的比例阈值

    Returns:
        低库存产品列表
    """
    low_stock = []
    for sku, inv in MOCK_INVENTORY.items():
        product = MOCK_PRODUCTS.get(sku)
        if not product:
            continue
        safety_stock = product["safety_stock"]
        if inv["quantity"] < safety_stock * threshold_ratio:
            low_stock.append({
                "sku": sku,
                "name": product["name"],
                "current_quantity": inv["quantity"],
                "safety_stock": safety_stock,
                "shortage": safety_stock - inv["quantity"],
                "warehouse": inv["warehouse"],
            })
    return low_stock
