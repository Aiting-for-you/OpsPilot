"""
OpsPilot 数据库完整初始化脚本

执行步骤:
1. 创建数据库和表结构
2. 生成虚拟数据
3. 插入数据到 PostgreSQL
4. 同步到 ChromaDB
"""
import asyncio
import random
import string
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncpg
from opspilot.db.vector_store import get_vector_store, PolicyVectorStore, SupplierVectorStore
from opspilot.db.cache import get_cache

# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "cyx0414",
}


# ============================================
# 数据生成器
# ============================================

class DataGenerator:
    """数据生成器"""
    
    REGIONS = {
        "华南": ["广东省", "福建省", "海南省"],
        "华东": ["上海市", "江苏省", "浙江省"],
        "华北": ["北京市", "天津市", "河北省"],
        "西南": ["四川省", "重庆市", "云南省"],
        "东北": ["辽宁省", "吉林省", "黑龙江省"],
    }
    
    CATEGORIES = {
        "电子元器件": ["电阻", "电容", "芯片", "传感器", "二极管"],
        "机械零件": ["轴承", "齿轮", "螺丝", "弹簧", "密封件"],
        "包装材料": ["纸箱", "木托盘", "塑料薄膜", "泡沫"],
        "化工材料": ["润滑油", "清洗剂", "涂料", "胶粘剂"],
    }
    
    CARRIERS = [("顺丰速运", "SF"), ("中通快递", "ZT"), ("京东物流", "JD")]
    CUSTOMS_OFFICES = [("深圳海关", "5301"), ("上海海关", "2200"), ("广州海关", "5100")]
    PLATFORMS = ["amazon", "aliexpress", "shopify"]
    
    def __init__(self):
        self.suppliers = []
        self.products = []
        self.inventory = []
        self.orders = []
        self.logistics = []
        self.customs = []
        self.platform_orders = []
        self.policies = []
        self.warehouse_ids = ["WH001", "WH002", "WH003", "WH004", "WH005"]
    
    def generate_all(self):
        """生成所有数据"""
        self.generate_suppliers(50)
        self.generate_products(100)
        self.generate_inventory(500)
        self.generate_orders(200)
        self.generate_logistics(200)
        self.generate_customs(100)
        self.generate_platform_orders(50)
        self.generate_policies(50)
    
    def generate_suppliers(self, count: int):
        """生成供应商"""
        for i in range(count):
            region = random.choice(list(self.REGIONS.keys()))
            category = random.choice(list(self.CATEGORIES.keys()))
            
            self.suppliers.append({
                "supplier_id": f"SUP{str(i+1).zfill(3)}",
                "name": f"{region}{category}有限公司",
                "short_name": f"{region[:2]}{category[:2]}",
                "region": region,
                "province": random.choice(self.REGIONS[region]),
                "city": "深圳市",
                "address": f"某某区某某路{random.randint(1, 999)}号",
                "rating": round(random.uniform(3.5, 5.0), 1),
                "rating_count": random.randint(10, 500),
                "products": random.sample(self.CATEGORIES[category], min(2, len(self.CATEGORIES[category]))),
                "main_category": category,
                "contact": f"联系人{random.randint(1, 100)}",
                "phone": f"138****{random.randint(1000, 9999)}",
                "email": f"contact{random.randint(1, 100)}@company.com",
                "payment_terms": random.choice(["月结30天", "月结45天", "款到发货"]),
                "min_order_amount": random.choice([0, 500, 1000, 2000]),
                "delivery_days": random.randint(3, 15),
                "certifications": random.sample(["ISO9001", "ISO14001", "CE"], random.randint(0, 2)),
                "status": random.choices(["active", "inactive"], weights=[90, 10])[0],
                "cooperation_years": random.randint(0, 10),
            })
    
    def generate_products(self, count: int):
        """生成产品"""
        for i in range(count):
            category = random.choice(list(self.CATEGORIES.keys()))
            sub_category = random.choice(self.CATEGORIES[category])
            
            price_ranges = {
                "电子元器件": (0.1, 100),
                "机械零件": (5, 500),
                "包装材料": (1, 200),
                "化工材料": (10, 2000),
            }
            min_p, max_p = price_ranges.get(category, (1, 100))
            
            self.products.append({
                "sku": f"SKU{str(i+1).zfill(4)}",
                "name": f"{sub_category}{random.randint(100, 999)}",
                "category": category,
                "sub_category": sub_category,
                "base_price": round(random.uniform(min_p, max_p), 2),
                "currency": "CNY",
                "unit": random.choice(["个", "件", "箱", "桶"]),
                "specifications": {"weight": round(random.uniform(0.1, 50), 2)},
                "description": f"{category}-{sub_category}类产品",
                "safety_stock": random.randint(50, 1000),
                "status": "active",
            })
    
    def generate_inventory(self, count: int):
        """生成库存"""
        for _ in range(count):
            product = random.choice(self.products)
            
            quantity = random.randint(0, 10000)
            reserved = random.randint(0, quantity // 2)
            
            self.inventory.append({
                "sku": product["sku"],
                "warehouse_id": random.choice(self.warehouse_ids),
                "quantity": quantity,
                "available": quantity - reserved,
                "reserved": reserved,
                "location": f"{random.choice('ABCDEFGH')}-{random.randint(1, 10):02d}",
                "status": random.choices(["normal", "low_stock"], weights=[80, 20])[0],
            })
    
    def generate_orders(self, count: int):
        """生成订单"""
        for i in range(count):
            supplier = random.choice(self.suppliers)
            
            items = []
            total_amount = 0
            for _ in range(random.randint(1, 3)):
                product = random.choice(self.products)
                quantity = random.randint(10, 100)
                price = product["base_price"] * random.uniform(0.9, 1.1)
                amount = quantity * price
                items.append({
                    "sku": product["sku"],
                    "name": product["name"],
                    "quantity": quantity,
                    "unit_price": round(price, 2),
                    "amount": round(amount, 2),
                })
                total_amount += amount
            
            self.orders.append({
                "order_id": f"ORD{datetime.now().strftime('%Y%m%d')}{str(i+1).zfill(4)}",
                "supplier_id": supplier["supplier_id"],
                "supplier_name": supplier["name"],
                "items": items,
                "total_quantity": sum(item["quantity"] for item in items),
                "total_amount": round(total_amount, 2),
                "currency": "CNY",
                "status": random.choice(["created", "approved", "shipping", "completed"]),
                "priority": random.choice(["low", "normal", "high"]),
                "need_approval": total_amount > 10000,
                "created_by": f"用户{random.randint(1, 50)}",
            })
    
    def generate_logistics(self, count: int):
        """生成物流"""
        for i, order in enumerate(self.orders[:count]):
            carrier = random.choice(self.CARRIERS)
            
            self.logistics.append({
                "tracking_no": f"{carrier[1]}{datetime.now().strftime('%Y%m%d')}{str(i+1).zfill(6)}",
                "order_id": order["order_id"],
                "carrier": carrier[0],
                "carrier_code": carrier[1],
                "status": random.choice(["pending", "in_transit", "delivered"]),
                "current_location": random.choice(["深圳", "上海", "北京", "成都"]),
                "estimated_delivery": (datetime.now() + timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d"),
                "tracking_history": [],
                "weight": round(random.uniform(0.5, 50), 2),
            })
    
    def generate_customs(self, count: int):
        """生成报关"""
        for i in range(count):
            order = random.choice(self.orders)
            customs_office = random.choice(self.CUSTOMS_OFFICES)
            
            self.customs.append({
                "declaration_no": f"CUS{datetime.now().strftime('%Y%m%d')}{str(i+1).zfill(5)}",
                "order_id": order["order_id"],
                "customs_office": customs_office[0],
                "customs_code": customs_office[1],
                "status": random.choices(["cleared", "pending", "hold"], weights=[60, 30, 10])[0],
                "declared_value": order["total_amount"],
                "currency": "CNY",
                "hs_codes": [{"code": f"{random.randint(1000000000, 9999999999)}", "description": "商品"}],
                "issue_type": random.choice([None, "文件缺失", "申报价值异常"]) if random.random() > 0.7 else None,
            })
    
    def generate_platform_orders(self, count: int):
        """生成平台订单"""
        for i in range(count):
            platform = random.choice(self.PLATFORMS)
            
            self.platform_orders.append({
                "platform_order_id": f"{platform.upper()}-{str(i+1).zfill(5)}",
                "platform": platform,
                "buyer_info": {"name": f"买家{random.randint(1, 100)}", "country": random.choice(["US", "UK", "DE"])},
                "items": [{"sku": random.choice(self.products)["sku"], "quantity": random.randint(1, 5)}],
                "total_amount": round(random.uniform(50, 1000), 2),
                "currency": "USD",
                "status": random.choice(["pending", "processing", "shipped"]),
                "payment_status": random.choice(["pending", "paid"]),
                "shipping_address": {"country": "US", "city": "New York"},
            })
    
    def generate_policies(self, count: int):
        """生成政策文档"""
        templates = [
            ("采购限额管理规定", "采购限额", "本规定明确了各类采购的审批限额和流程..."),
            ("供应商准入标准", "供应商准入", "供应商准入需满足以下条件..."),
            ("付款条款规范", "付款条款", "付款条款按照供应商等级确定..."),
            ("合同管理规范", "合同管理", "采购合同签订流程和管理要求..."),
            ("紧急采购流程", "紧急采购", "紧急采购的定义和快速审批流程..."),
        ]
        
        for i in range(count):
            template = templates[i % len(templates)]
            
            self.policies.append({
                "policy_id": f"POL{str(i+1).zfill(3)}",
                "title": f"{template[0]}_V{random.randint(1, 3)}.{random.randint(0, 9)}",
                "category": template[1],
                "version": f"{random.randint(1, 3)}.{random.randint(0, 9)}",
                "content": f"{template[2]}\n\n详细内容：适用范围-全公司",
                "effective_date": datetime.now().strftime("%Y-%m-%d"),
                "status": "active",
            })


# ============================================
# 数据库操作
# ============================================

async def create_database():
    """创建数据库"""
    print("[1/4] 创建数据库...")
    
    try:
        conn = await asyncpg.connect(**DB_CONFIG, database="postgres")
        await conn.execute("CREATE DATABASE opspilot")
        print("      ✅ 数据库创建成功")
        await conn.close()
    except asyncpg.DuplicateDatabaseError:
        print("      ⚠️ 数据库已存在")
    except Exception as e:
        print(f"      ❌ 错误: {e}")
        return False
    
    return True


async def create_tables(conn):
    """创建表结构"""
    print("[2/4] 创建表结构...")
    
    tables = [
        ("suppliers", """
            CREATE TABLE IF NOT EXISTS suppliers (
                id SERIAL PRIMARY KEY,
                supplier_id VARCHAR(20) UNIQUE NOT NULL,
                name VARCHAR(200) NOT NULL,
                short_name VARCHAR(50),
                region VARCHAR(50),
                province VARCHAR(50),
                city VARCHAR(50),
                address VARCHAR(500),
                rating DECIMAL(2,1) DEFAULT 4.0,
                rating_count INTEGER DEFAULT 0,
                products TEXT[],
                main_category VARCHAR(100),
                contact VARCHAR(50),
                phone VARCHAR(20),
                email VARCHAR(100),
                payment_terms VARCHAR(50),
                min_order_amount DECIMAL(10,2) DEFAULT 0,
                delivery_days INTEGER DEFAULT 7,
                certifications TEXT[],
                status VARCHAR(20) DEFAULT 'active',
                cooperation_years INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("products", """
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                sku VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(200) NOT NULL,
                category VARCHAR(100),
                sub_category VARCHAR(100),
                base_price DECIMAL(10,2) DEFAULT 0,
                currency VARCHAR(10) DEFAULT 'CNY',
                unit VARCHAR(20),
                specifications JSONB,
                description TEXT,
                safety_stock INTEGER DEFAULT 100,
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("warehouses", """
            CREATE TABLE IF NOT EXISTS warehouses (
                id SERIAL PRIMARY KEY,
                warehouse_id VARCHAR(20) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                region VARCHAR(50),
                province VARCHAR(50),
                city VARCHAR(50),
                capacity_sqm DECIMAL(10,2),
                type VARCHAR(50),
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("inventory", """
            CREATE TABLE IF NOT EXISTS inventory (
                id SERIAL PRIMARY KEY,
                sku VARCHAR(50) NOT NULL,
                warehouse_id VARCHAR(20),
                quantity INTEGER DEFAULT 0,
                available INTEGER DEFAULT 0,
                reserved INTEGER DEFAULT 0,
                location VARCHAR(50),
                status VARCHAR(20) DEFAULT 'normal',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(sku, warehouse_id)
            )
        """),
        ("orders", """
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                order_id VARCHAR(30) UNIQUE NOT NULL,
                supplier_id VARCHAR(20),
                supplier_name VARCHAR(200),
                items JSONB,
                total_quantity INTEGER DEFAULT 0,
                total_amount DECIMAL(12,2) DEFAULT 0,
                currency VARCHAR(10) DEFAULT 'CNY',
                status VARCHAR(30) DEFAULT 'created',
                priority VARCHAR(20) DEFAULT 'normal',
                need_approval BOOLEAN DEFAULT false,
                created_by VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("logistics", """
            CREATE TABLE IF NOT EXISTS logistics (
                id SERIAL PRIMARY KEY,
                tracking_no VARCHAR(50) UNIQUE NOT NULL,
                order_id VARCHAR(30),
                carrier VARCHAR(100),
                carrier_code VARCHAR(20),
                status VARCHAR(30) DEFAULT 'pending',
                current_location VARCHAR(200),
                estimated_delivery DATE,
                tracking_history JSONB,
                weight DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("customs_declarations", """
            CREATE TABLE IF NOT EXISTS customs_declarations (
                id SERIAL PRIMARY KEY,
                declaration_no VARCHAR(30) UNIQUE NOT NULL,
                order_id VARCHAR(30),
                customs_office VARCHAR(100),
                customs_code VARCHAR(20),
                status VARCHAR(30) DEFAULT 'pending',
                declared_value DECIMAL(12,2),
                currency VARCHAR(10) DEFAULT 'CNY',
                hs_codes JSONB,
                issue_type VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("platform_orders", """
            CREATE TABLE IF NOT EXISTS platform_orders (
                id SERIAL PRIMARY KEY,
                platform_order_id VARCHAR(50) UNIQUE NOT NULL,
                platform VARCHAR(50),
                buyer_info JSONB,
                items JSONB,
                total_amount DECIMAL(12,2),
                currency VARCHAR(10) DEFAULT 'USD',
                status VARCHAR(30) DEFAULT 'pending',
                payment_status VARCHAR(30),
                shipping_address JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("policies", """
            CREATE TABLE IF NOT EXISTS policies (
                id SERIAL PRIMARY KEY,
                policy_id VARCHAR(20) UNIQUE NOT NULL,
                title VARCHAR(200) NOT NULL,
                category VARCHAR(50),
                version VARCHAR(20),
                content TEXT,
                effective_date DATE,
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("exchange_rates", """
            CREATE TABLE IF NOT EXISTS exchange_rates (
                id SERIAL PRIMARY KEY,
                from_currency VARCHAR(10) NOT NULL,
                to_currency VARCHAR(10) NOT NULL,
                rate DECIMAL(12,6) NOT NULL,
                source VARCHAR(50),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(from_currency, to_currency)
            )
        """),
    ]
    
    for name, sql in tables:
        try:
            await conn.execute(sql)
            print(f"      ✅ {name}")
        except Exception as e:
            if "already exists" not in str(e):
                print(f"      ❌ {name}: {e}")


async def insert_data(conn, generator: DataGenerator):
    """插入数据"""
    print("[3/4] 插入数据...")
    
    # 仓库
    print("      - 仓库...")
    for wh in [
        ("WH001", "深圳仓库", "华南", "广东省", "深圳市", 50000),
        ("WH002", "上海仓库", "华东", "上海市", "上海市", 30000),
        ("WH003", "北京仓库", "华北", "北京市", "北京市", 20000),
        ("WH004", "成都仓库", "西南", "四川省", "成都市", 15000),
        ("WH005", "广州仓库", "华南", "广东省", "广州市", 25000),
    ]:
        await conn.execute("""
            INSERT INTO warehouses (warehouse_id, name, region, province, city, capacity_sqm)
            VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT DO NOTHING
        """, *wh)
    
    # 供应商
    print("      - 供应商...")
    for s in generator.suppliers:
        await conn.execute("""
            INSERT INTO suppliers (supplier_id, name, short_name, region, province, city, address,
                rating, rating_count, products, main_category, contact, phone, email,
                payment_terms, min_order_amount, delivery_days, certifications, status, cooperation_years)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
            ON CONFLICT (supplier_id) DO NOTHING
        """, s["supplier_id"], s["name"], s["short_name"], s["region"], s["province"],
           s["city"], s["address"], s["rating"], s["rating_count"], s["products"],
           s["main_category"], s["contact"], s["phone"], s["email"], s["payment_terms"],
           s["min_order_amount"], s["delivery_days"], s["certifications"], s["status"], s["cooperation_years"])
    
    # 产品
    print("      - 产品...")
    for p in generator.products:
        await conn.execute("""
            INSERT INTO products (sku, name, category, sub_category, base_price, currency, unit,
                specifications, description, safety_stock, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (sku) DO NOTHING
        """, p["sku"], p["name"], p["category"], p["sub_category"], p["base_price"],
           p["currency"], p["unit"], p["specifications"], p["description"],
           p["safety_stock"], p["status"])
    
    # 库存
    print("      - 库存...")
    for inv in generator.inventory:
        await conn.execute("""
            INSERT INTO inventory (sku, warehouse_id, quantity, available, reserved, location, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (sku, warehouse_id) DO NOTHING
        """, inv["sku"], inv["warehouse_id"], inv["quantity"], inv["available"],
           inv["reserved"], inv["location"], inv["status"])
    
    # 订单
    print("      - 订单...")
    for o in generator.orders:
        await conn.execute("""
            INSERT INTO orders (order_id, supplier_id, supplier_name, items, total_quantity, 
                total_amount, currency, status, priority, need_approval, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (order_id) DO NOTHING
        """, o["order_id"], o["supplier_id"], o["supplier_name"], o["items"],
           o["total_quantity"], o["total_amount"], o["currency"], o["status"],
           o["priority"], o["need_approval"], o["created_by"])
    
    # 物流
    print("      - 物流...")
    for l in generator.logistics:
        await conn.execute("""
            INSERT INTO logistics (tracking_no, order_id, carrier, carrier_code, status,
                current_location, estimated_delivery, tracking_history, weight)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (tracking_no) DO NOTHING
        """, l["tracking_no"], l["order_id"], l["carrier"], l["carrier_code"],
           l["status"], l["current_location"], l["estimated_delivery"],
           l["tracking_history"], l["weight"])
    
    # 报关
    print("      - 报关...")
    for c in generator.customs:
        await conn.execute("""
            INSERT INTO customs_declarations (declaration_no, order_id, customs_office, customs_code,
                status, declared_value, currency, hs_codes, issue_type)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (declaration_no) DO NOTHING
        """, c["declaration_no"], c["order_id"], c["customs_office"], c["customs_code"],
           c["status"], c["declared_value"], c["currency"], c["hs_codes"], c["issue_type"])
    
    # 平台订单
    print("      - 平台订单...")
    for po in generator.platform_orders:
        await conn.execute("""
            INSERT INTO platform_orders (platform_order_id, platform, buyer_info, items,
                total_amount, currency, status, payment_status, shipping_address)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (platform_order_id) DO NOTHING
        """, po["platform_order_id"], po["platform"], po["buyer_info"], po["items"],
           po["total_amount"], po["currency"], po["status"], po["payment_status"],
           po["shipping_address"])
    
    # 政策
    print("      - 政策文档...")
    for p in generator.policies:
        await conn.execute("""
            INSERT INTO policies (policy_id, title, category, version, content, effective_date, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (policy_id) DO NOTHING
        """, p["policy_id"], p["title"], p["category"], p["version"], p["content"],
           p["effective_date"], p["status"])
    
    # 汇率
    print("      - 汇率...")
    for rate in [
        ("USD", "CNY", 7.25), ("CNY", "USD", 0.138),
        ("EUR", "CNY", 7.85), ("CNY", "EUR", 0.127),
        ("JPY", "CNY", 0.048), ("CNY", "JPY", 20.83),
    ]:
        await conn.execute("""
            INSERT INTO exchange_rates (from_currency, to_currency, rate, source)
            VALUES ($1, $2, $3, 'mock')
            ON CONFLICT (from_currency, to_currency) DO UPDATE SET rate = EXCLUDED.rate
        """, *rate)


async def sync_to_vector_store(generator: DataGenerator):
    """同步到向量存储"""
    print("[4/4] 同步到 ChromaDB...")
    
    # 政策文档向量存储
    policy_store = get_vector_store("policy")
    policy_store.add_policies(generator.policies)
    print(f"      ✅ 政策文档: {len(generator.policies)} 条")
    
    # 供应商向量存储
    supplier_store = get_vector_store("supplier")
    for s in generator.suppliers[:20]:  # 只同步前20个
        supplier_store.add_supplier(
            s["supplier_id"], s["name"], s["region"], s["products"], s["main_category"]
        )
    print(f"      ✅ 供应商: 20 条")


async def main():
    """主函数"""
    print("=" * 60)
    print("OpsPilot 数据库初始化")
    print("=" * 60)
    
    # 1. 创建数据库
    if not await create_database():
        return
    
    # 2. 连接数据库
    conn = await asyncpg.connect(**DB_CONFIG, database="opspilot")
    
    # 3. 创建表结构
    await create_tables(conn)
    
    # 4. 生成数据
    print("\n[生成虚拟数据]")
    generator = DataGenerator()
    generator.generate_all()
    
    print(f"  - 供应商: {len(generator.suppliers)}")
    print(f"  - 产品: {len(generator.products)}")
    print(f"  - 库存: {len(generator.inventory)}")
    print(f"  - 订单: {len(generator.orders)}")
    print(f"  - 物流: {len(generator.logistics)}")
    print(f"  - 报关: {len(generator.customs)}")
    print(f"  - 平台订单: {len(generator.platform_orders)}")
    print(f"  - 政策文档: {len(generator.policies)}")
    
    # 5. 插入数据
    await insert_data(conn, generator)
    
    await conn.close()
    
    # 6. 同步到向量存储
    await sync_to_vector_store(generator)
    
    # 7. 测试 Redis
    print("\n[Redis 测试]")
    cache = get_cache()
    if cache.connected:
        cache.set("test_key", {"value": "test"})
        print("      ✅ Redis 连接正常")
    else:
        print("      ⚠️ Redis 未连接")
    
    print("\n" + "=" * 60)
    print("✅ 数据库初始化完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
