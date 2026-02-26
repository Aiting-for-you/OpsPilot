"""
CRUD 操作封装

提供各数据模型的增删改查操作
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from decimal import Decimal

from opspilot.db.connection import get_database_pool, DatabasePool
from opspilot.db.models import (
    Supplier, SupplierCreate, SupplierUpdate,
    Product, ProductCreate,
    Inventory,
    Warehouse,
    Order, OrderCreate, OrderItem,
    Logistics,
    CustomsDeclaration,
    PlatformOrder,
    Policy,
    ExchangeRate,
)


def _record_to_supplier(record: dict) -> Supplier:
    """将数据库记录转换为 Supplier 模型"""
    return Supplier(
        id=record.get("id"),
        supplier_id=record.get("supplier_id"),
        name=record.get("name"),
        short_name=record.get("short_name"),
        region=record.get("region"),
        province=record.get("province"),
        city=record.get("city"),
        address=record.get("address"),
        rating=record.get("rating") or Decimal("4.0"),
        rating_count=record.get("rating_count") or 0,
        products=list(record.get("products") or []),
        main_category=record.get("main_category"),
        contact=record.get("contact"),
        phone=record.get("phone"),
        email=record.get("email"),
        payment_terms=record.get("payment_terms"),
        min_order_amount=record.get("min_order_amount") or Decimal("0"),
        delivery_days=record.get("delivery_days") or 7,
        certifications=list(record.get("certifications") or []),
        status=record.get("status") or "active",
        cooperation_years=record.get("cooperation_years") or 0,
        created_at=record.get("created_at"),
        updated_at=record.get("updated_at"),
    )


def _record_to_product(record: dict) -> Product:
    """将数据库记录转换为 Product 模型"""
    return Product(
        id=record.get("id"),
        sku=record.get("sku"),
        name=record.get("name"),
        category=record.get("category"),
        sub_category=record.get("sub_category"),
        base_price=record.get("base_price") or Decimal("0"),
        currency=record.get("currency") or "CNY",
        unit=record.get("unit"),
        specifications=dict(record.get("specifications") or {}),
        description=record.get("description"),
        safety_stock=record.get("safety_stock") or 100,
        status=record.get("status") or "active",
        created_at=record.get("created_at"),
        updated_at=record.get("updated_at"),
    )


def _record_to_inventory(record: dict) -> Inventory:
    """将数据库记录转换为 Inventory 模型"""
    return Inventory(
        id=record.get("id"),
        sku=record.get("sku"),
        warehouse_id=record.get("warehouse_id"),
        quantity=record.get("quantity") or 0,
        available=record.get("available") or 0,
        reserved=record.get("reserved") or 0,
        location=record.get("location"),
        batch_number=record.get("batch_number"),
        status=record.get("status") or "normal",
        created_at=record.get("created_at"),
        updated_at=record.get("updated_at"),
    )


def _record_to_order(record: dict) -> Order:
    """将数据库记录转换为 Order 模型"""
    items = []
    for item in (record.get("items") or []):
        items.append(OrderItem(
            sku=item.get("sku"),
            name=item.get("name"),
            quantity=item.get("quantity"),
            unit_price=item.get("unit_price"),
            amount=item.get("amount"),
        ))
    
    return Order(
        id=record.get("id"),
        order_id=record.get("order_id"),
        supplier_id=record.get("supplier_id"),
        supplier_name=record.get("supplier_name"),
        items=items,
        total_quantity=record.get("total_quantity") or 0,
        total_amount=record.get("total_amount") or Decimal("0"),
        currency=record.get("currency") or "CNY",
        status=record.get("status") or "created",
        priority=record.get("priority") or "normal",
        need_approval=record.get("need_approval") or False,
        approved_by=record.get("approved_by"),
        approved_at=record.get("approved_at"),
        created_by=record.get("created_by"),
        created_at=record.get("created_at"),
        updated_at=record.get("updated_at"),
    )


# ============================================
# 供应商 CRUD
# ============================================

class SupplierCRUD:
    """供应商 CRUD 操作"""
    
    @staticmethod
    async def get_by_id(supplier_id: str) -> Optional[Supplier]:
        """根据 ID 获取供应商"""
        pool = await get_database_pool()
        record = await pool.fetchrow(
            "SELECT * FROM suppliers WHERE supplier_id = $1",
            supplier_id
        )
        return _record_to_supplier(dict(record)) if record else None
    
    @staticmethod
    async def get_list(
        region: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        min_rating: Optional[float] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Supplier]:
        """获取供应商列表"""
        pool = await get_database_pool()
        
        conditions = []
        params = []
        param_idx = 1
        
        if region:
            conditions.append(f"region = ${param_idx}")
            params.append(region)
            param_idx += 1
        
        if category:
            conditions.append(f"$${param_idx} = ANY(products)")
            params.append(category)
            param_idx += 1
        
        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1
        
        if min_rating:
            conditions.append(f"rating >= ${param_idx}")
            params.append(min_rating)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        
        query = f"""
            SELECT * FROM suppliers
            WHERE {where_clause}
            ORDER BY rating DESC, created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([limit, offset])
        
        records = await pool.fetch(query, *params)
        return [_record_to_supplier(dict(r)) for r in records]
    
    @staticmethod
    async def create(supplier: SupplierCreate) -> Supplier:
        """创建供应商"""
        pool = await get_database_pool()
        
        record = await pool.fetchrow(
            """
            INSERT INTO suppliers (
                supplier_id, name, short_name, region, province, city, address,
                rating, rating_count, products, main_category, contact, phone, email,
                payment_terms, min_order_amount, delivery_days, certifications, status, cooperation_years
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
            RETURNING *
            """,
            supplier.supplier_id, supplier.name, supplier.short_name, supplier.region,
            supplier.province, supplier.city, supplier.address, supplier.rating,
            supplier.rating_count, supplier.products, supplier.main_category,
            supplier.contact, supplier.phone, supplier.email, supplier.payment_terms,
            supplier.min_order_amount, supplier.delivery_days, supplier.certifications,
            supplier.status, supplier.cooperation_years
        )
        
        return _record_to_supplier(dict(record))
    
    @staticmethod
    async def update(supplier_id: str, data: SupplierUpdate) -> Optional[Supplier]:
        """更新供应商"""
        pool = await get_database_pool()
        
        update_fields = []
        params = []
        param_idx = 1
        
        for field, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = ${param_idx}")
                params.append(value)
                param_idx += 1
        
        if not update_fields:
            return await SupplierCRUD.get_by_id(supplier_id)
        
        params.append(supplier_id)
        query = f"""
            UPDATE suppliers SET {", ".join(update_fields)}
            WHERE supplier_id = ${param_idx}
            RETURNING *
        """
        
        record = await pool.fetchrow(query, *params)
        return _record_to_supplier(dict(record)) if record else None


# ============================================
# 产品 CRUD
# ============================================

class ProductCRUD:
    """产品 CRUD 操作"""
    
    @staticmethod
    async def get_by_sku(sku: str) -> Optional[Product]:
        """根据 SKU 获取产品"""
        pool = await get_database_pool()
        record = await pool.fetchrow(
            "SELECT * FROM products WHERE sku = $1",
            sku
        )
        return _record_to_product(dict(record)) if record else None
    
    @staticmethod
    async def get_list(
        category: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Product]:
        """获取产品列表"""
        pool = await get_database_pool()
        
        conditions = []
        params = []
        param_idx = 1
        
        if category:
            conditions.append(f"category = ${param_idx}")
            params.append(category)
            param_idx += 1
        
        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        
        query = f"""
            SELECT * FROM products
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([limit, offset])
        
        records = await pool.fetch(query, *params)
        return [_record_to_product(dict(r)) for r in records]


# ============================================
# 库存 CRUD
# ============================================

class InventoryCRUD:
    """库存 CRUD 操作"""
    
    @staticmethod
    async def get_by_sku(sku: str, warehouse_id: Optional[str] = None) -> List[Inventory]:
        """根据 SKU 获取库存"""
        pool = await get_database_pool()
        
        if warehouse_id:
            records = await pool.fetch(
                "SELECT * FROM inventory WHERE sku = $1 AND warehouse_id = $2",
                sku, warehouse_id
            )
        else:
            records = await pool.fetch(
                "SELECT * FROM inventory WHERE sku = $1",
                sku
            )
        
        return [_record_to_inventory(dict(r)) for r in records]
    
    @staticmethod
    async def get_low_stock(threshold_ratio: float = 0.2) -> List[Dict]:
        """获取低库存产品"""
        pool = await get_database_pool()
        
        records = await pool.fetch(
            """
            SELECT i.*, p.name, p.safety_stock, p.category
            FROM inventory i
            JOIN products p ON i.sku = p.sku
            WHERE i.quantity < p.safety_stock * $1
            ORDER BY i.quantity ASC
            """,
            threshold_ratio
        )
        
        return [dict(r) for r in records]
    
    @staticmethod
    async def update_quantity(sku: str, warehouse_id: str, quantity_delta: int) -> Optional[Inventory]:
        """更新库存数量"""
        pool = await get_database_pool()
        
        record = await pool.fetchrow(
            """
            UPDATE inventory 
            SET quantity = quantity + $1,
                available = available + $1,
                updated_at = CURRENT_TIMESTAMP
            WHERE sku = $2 AND warehouse_id = $3
            RETURNING *
            """,
            quantity_delta, sku, warehouse_id
        )
        
        return _record_to_inventory(dict(record)) if record else None


# ============================================
# 订单 CRUD
# ============================================

class OrderCRUD:
    """订单 CRUD 操作"""
    
    @staticmethod
    async def get_by_id(order_id: str) -> Optional[Order]:
        """根据 ID 获取订单"""
        pool = await get_database_pool()
        record = await pool.fetchrow(
            "SELECT * FROM orders WHERE order_id = $1",
            order_id
        )
        return _record_to_order(dict(record)) if record else None
    
    @staticmethod
    async def get_list(
        status: Optional[str] = None,
        supplier_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Order]:
        """获取订单列表"""
        pool = await get_database_pool()
        
        conditions = []
        params = []
        param_idx = 1
        
        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1
        
        if supplier_id:
            conditions.append(f"supplier_id = ${param_idx}")
            params.append(supplier_id)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        
        query = f"""
            SELECT * FROM orders
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([limit, offset])
        
        records = await pool.fetch(query, *params)
        return [_record_to_order(dict(r)) for r in records]
    
    @staticmethod
    async def create(order_data: OrderCreate) -> Order:
        """创建订单"""
        pool = await get_database_pool()
        
        # 生成订单ID
        order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 计算总金额
        total_amount = sum(
            item.get("quantity", 0) * item.get("unit_price", 0)
            for item in order_data.items
        )
        need_approval = total_amount > 10000
        
        record = await pool.fetchrow(
            """
            INSERT INTO orders (
                order_id, supplier_id, items, total_quantity, total_amount,
                status, priority, need_approval, created_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
            """,
            order_id, order_data.supplier_id, 
            [item.model_dump() for item in order_data.items],
            sum(item.get("quantity", 0) for item in order_data.items),
            total_amount, "created", order_data.priority,
            need_approval, order_data.created_by
        )
        
        return _record_to_order(dict(record))
    
    @staticmethod
    async def update_status(order_id: str, status: str, approved_by: Optional[str] = None) -> Optional[Order]:
        """更新订单状态"""
        pool = await get_database_pool()
        
        if approved_by:
            record = await pool.fetchrow(
                """
                UPDATE orders 
                SET status = $1, approved_by = $2, approved_at = CURRENT_TIMESTAMP
                WHERE order_id = $3
                RETURNING *
                """,
                status, approved_by, order_id
            )
        else:
            record = await pool.fetchrow(
                """
                UPDATE orders SET status = $1 WHERE order_id = $2 RETURNING *
                """,
                status, order_id
            )
        
        return _record_to_order(dict(record)) if record else None


# ============================================
# 物流 CRUD
# ============================================

class LogisticsCRUD:
    """物流 CRUD 操作"""
    
    @staticmethod
    async def get_by_tracking(tracking_no: str) -> Optional[Logistics]:
        """根据运单号获取物流"""
        pool = await get_database_pool()
        record = await pool.fetchrow(
            "SELECT * FROM logistics WHERE tracking_no = $1",
            tracking_no
        )
        return Logistics(**dict(record)) if record else None
    
    @staticmethod
    async def get_by_order(order_id: str) -> Optional[Logistics]:
        """根据订单ID获取物流"""
        pool = await get_database_pool()
        record = await pool.fetchrow(
            "SELECT * FROM logistics WHERE order_id = $1",
            order_id
        )
        return Logistics(**dict(record)) if record else None
    
    @staticmethod
    async def get_by_status(status: str, limit: int = 50) -> List[Logistics]:
        """根据状态获取物流列表"""
        pool = await get_database_pool()
        records = await pool.fetch(
            "SELECT * FROM logistics WHERE status = $1 LIMIT $2",
            status, limit
        )
        return [Logistics(**dict(r)) for r in records]


# ============================================
# 报关 CRUD
# ============================================

class CustomsCRUD:
    """报关 CRUD 操作"""
    
    @staticmethod
    async def get_by_declaration_no(declaration_no: str) -> Optional[CustomsDeclaration]:
        """根据报关单号获取"""
        pool = await get_database_pool()
        record = await pool.fetchrow(
            "SELECT * FROM customs_declarations WHERE declaration_no = $1",
            declaration_no
        )
        return CustomsDeclaration(**dict(record)) if record else None
    
    @staticmethod
    async def get_by_order(order_id: str) -> Optional[CustomsDeclaration]:
        """根据订单ID获取报关"""
        pool = await get_database_pool()
        record = await pool.fetchrow(
            "SELECT * FROM customs_declarations WHERE order_id = $1",
            order_id
        )
        return CustomsDeclaration(**dict(record)) if record else None
    
    @staticmethod
    async def get_issues() -> List[CustomsDeclaration]:
        """获取问题报关单"""
        pool = await get_database_pool()
        records = await pool.fetch(
            "SELECT * FROM customs_declarations WHERE status IN ('hold', 'rejected')"
        )
        return [CustomsDeclaration(**dict(r)) for r in records]


# ============================================
# 平台订单 CRUD
# ============================================

class PlatformOrderCRUD:
    """平台订单 CRUD 操作"""
    
    @staticmethod
    async def get_by_platform(platform: str, limit: int = 50) -> List[PlatformOrder]:
        """根据平台获取订单"""
        pool = await get_database_pool()
        records = await pool.fetch(
            "SELECT * FROM platform_orders WHERE platform = $1 ORDER BY created_at DESC LIMIT $2",
            platform, limit
        )
        return [PlatformOrder(**dict(r)) for r in records]
    
    @staticmethod
    async def get_pending_shipments() -> List[PlatformOrder]:
        """获取待发货订单"""
        pool = await get_database_pool()
        records = await pool.fetch(
            "SELECT * FROM platform_orders WHERE status = 'pending' AND payment_status = 'paid'"
        )
        return [PlatformOrder(**dict(r)) for r in records]


# ============================================
# 政策文档 CRUD
# ============================================

class PolicyCRUD:
    """政策文档 CRUD 操作"""
    
    @staticmethod
    async def get_by_id(policy_id: str) -> Optional[Policy]:
        """根据 ID 获取政策"""
        pool = await get_database_pool()
        record = await pool.fetchrow(
            "SELECT * FROM policies WHERE policy_id = $1",
            policy_id
        )
        return Policy(**dict(record)) if record else None
    
    @staticmethod
    async def get_by_category(category: str) -> List[Policy]:
        """根据类别获取政策"""
        pool = await get_database_pool()
        records = await pool.fetch(
            "SELECT * FROM policies WHERE category = $1 AND status = 'active'",
            category
        )
        return [Policy(**dict(r)) for r in records]
    
    @staticmethod
    async def search(query: str, limit: int = 10) -> List[Policy]:
        """搜索政策"""
        pool = await get_database_pool()
        records = await pool.fetch(
            """
            SELECT * FROM policies 
            WHERE title ILIKE $1 OR content ILIKE $1
            AND status = 'active'
            LIMIT $2
            """,
            f"%{query}%", limit
        )
        return [Policy(**dict(r)) for r in records]


# ============================================
# 汇率 CRUD
# ============================================

class ExchangeRateCRUD:
    """汇率 CRUD 操作"""
    
    @staticmethod
    async def get_rate(from_currency: str, to_currency: str) -> Optional[ExchangeRate]:
        """获取汇率"""
        pool = await get_database_pool()
        record = await pool.fetchrow(
            "SELECT * FROM exchange_rates WHERE from_currency = $1 AND to_currency = $2",
            from_currency, to_currency
        )
        return ExchangeRate(**dict(record)) if record else None
    
    @staticmethod
    async def get_all() -> List[ExchangeRate]:
        """获取所有汇率"""
        pool = await get_database_pool()
        records = await pool.fetch("SELECT * FROM exchange_rates")
        return [ExchangeRate(**dict(r)) for r in records]
    
    @staticmethod
    async def update_rate(from_currency: str, to_currency: str, rate: float) -> ExchangeRate:
        """更新汇率"""
        pool = await get_database_pool()
        record = await pool.fetchrow(
            """
            INSERT INTO exchange_rates (from_currency, to_currency, rate, source)
            VALUES ($1, $2, $3, 'api')
            ON CONFLICT (from_currency, to_currency) 
            DO UPDATE SET rate = $3, updated_at = CURRENT_TIMESTAMP
            RETURNING *
            """,
            from_currency, to_currency, rate
        )
        return ExchangeRate(**dict(record))
