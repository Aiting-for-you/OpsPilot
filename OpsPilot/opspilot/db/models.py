"""
数据库模型定义

使用 Pydantic 定义 ORM 模型
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field
from decimal import Decimal


# ============================================
# 供应商模型
# ============================================

class SupplierBase(BaseModel):
    """供应商基础模型"""
    supplier_id: str
    name: str
    short_name: Optional[str] = None
    region: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    rating: Decimal = Field(default=Decimal("4.0"), ge=0, le=5)
    rating_count: int = 0
    products: List[str] = Field(default_factory=list)
    main_category: Optional[str] = None
    contact: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    payment_terms: Optional[str] = None
    min_order_amount: Decimal = Decimal("0")
    delivery_days: int = 7
    certifications: List[str] = Field(default_factory=list)
    status: str = "active"
    cooperation_years: int = 0


class Supplier(SupplierBase):
    """供应商完整模型"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SupplierCreate(SupplierBase):
    """创建供应商"""
    pass


class SupplierUpdate(BaseModel):
    """更新供应商"""
    name: Optional[str] = None
    short_name: Optional[str] = None
    region: Optional[str] = None
    rating: Optional[Decimal] = None
    products: Optional[List[str]] = None
    main_category: Optional[str] = None
    contact: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    payment_terms: Optional[str] = None
    min_order_amount: Optional[Decimal] = None
    delivery_days: Optional[int] = None
    certifications: Optional[List[str]] = None
    status: Optional[str] = None


# ============================================
# 产品模型
# ============================================

class ProductBase(BaseModel):
    """产品基础模型"""
    sku: str
    name: str
    category: Optional[str] = None
    sub_category: Optional[str] = None
    base_price: Decimal = Decimal("0")
    currency: str = "CNY"
    unit: Optional[str] = None
    specifications: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None
    safety_stock: int = 100
    status: str = "active"


class Product(ProductBase):
    """产品完整模型"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProductCreate(ProductBase):
    """创建产品"""
    pass


# ============================================
# 库存模型
# ============================================

class InventoryBase(BaseModel):
    """库存基础模型"""
    sku: str
    warehouse_id: str
    quantity: int = 0
    available: int = 0
    reserved: int = 0
    location: Optional[str] = None
    batch_number: Optional[str] = None
    status: str = "normal"


class Inventory(InventoryBase):
    """库存完整模型"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================
# 仓库模型
# ============================================

class WarehouseBase(BaseModel):
    """仓库基础模型"""
    warehouse_id: str
    name: str
    region: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    capacity_sqm: Optional[Decimal] = None
    type: Optional[str] = None
    manager: Optional[str] = None
    phone: Optional[str] = None
    status: str = "active"


class Warehouse(WarehouseBase):
    """仓库完整模型"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================
# 订单模型
# ============================================

class OrderItem(BaseModel):
    """订单项"""
    sku: str
    name: str
    quantity: int
    unit_price: Decimal
    amount: Decimal


class OrderBase(BaseModel):
    """订单基础模型"""
    order_id: str
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    items: List[OrderItem] = Field(default_factory=list)
    total_quantity: int = 0
    total_amount: Decimal = Decimal("0")
    currency: str = "CNY"
    status: str = "created"
    priority: str = "normal"
    need_approval: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_by: Optional[str] = None


class Order(OrderBase):
    """订单完整模型"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    """创建订单"""
    supplier_id: str
    items: List[Dict[str, Any]]
    priority: str = "normal"
    created_by: Optional[str] = None


# ============================================
# 物流模型
# ============================================

class TrackingEvent(BaseModel):
    """物流轨迹事件"""
    time: str
    location: str
    status: str
    description: str


class LogisticsBase(BaseModel):
    """物流基础模型"""
    tracking_no: str
    order_id: Optional[str] = None
    carrier: Optional[str] = None
    carrier_code: Optional[str] = None
    status: str = "pending"
    current_location: Optional[str] = None
    estimated_delivery: Optional[date] = None
    actual_delivery: Optional[date] = None
    tracking_history: List[TrackingEvent] = Field(default_factory=list)
    weight: Optional[Decimal] = None
    notes: Optional[str] = None


class Logistics(LogisticsBase):
    """物流完整模型"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================
# 报关模型
# ============================================

class HSCode(BaseModel):
    """HS编码"""
    code: str
    description: str


class CustomsDeclarationBase(BaseModel):
    """报关基础模型"""
    declaration_no: str
    order_id: Optional[str] = None
    customs_office: Optional[str] = None
    customs_code: Optional[str] = None
    status: str = "pending"
    declared_value: Optional[Decimal] = None
    currency: str = "CNY"
    hs_codes: List[HSCode] = Field(default_factory=list)
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    issue_type: Optional[str] = None
    issue_description: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None


class CustomsDeclaration(CustomsDeclarationBase):
    """报关完整模型"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================
# 平台订单模型
# ============================================

class PlatformOrderBase(BaseModel):
    """平台订单基础模型"""
    platform_order_id: str
    platform: str
    buyer_info: Dict[str, Any] = Field(default_factory=dict)
    items: List[Dict[str, Any]] = Field(default_factory=list)
    total_amount: Decimal = Decimal("0")
    currency: str = "USD"
    status: str = "pending"
    payment_status: Optional[str] = None
    shipping_address: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    synced_at: Optional[datetime] = None


class PlatformOrder(PlatformOrderBase):
    """平台订单完整模型"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================
# 政策文档模型
# ============================================

class PolicyBase(BaseModel):
    """政策文档基础模型"""
    policy_id: str
    title: str
    category: Optional[str] = None
    version: Optional[str] = None
    content: Optional[str] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    status: str = "active"


class Policy(PolicyBase):
    """政策文档完整模型"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================
# 汇率模型
# ============================================

class ExchangeRateBase(BaseModel):
    """汇率基础模型"""
    from_currency: str
    to_currency: str
    rate: Decimal
    source: Optional[str] = None


class ExchangeRate(ExchangeRateBase):
    """汇率完整模型"""
    id: Optional[int] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
