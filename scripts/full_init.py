"""
OpsPilot 完整数据初始化
"""
import asyncio
import asyncpg
import random
from datetime import datetime, timedelta

DB = {"host": "localhost", "port": 5432, "user": "postgres", "password": "cyx0414", "database": "opspilot"}

# 数据
REGIONS = ["华南", "华东", "华北", "西南", "东北"]
CATEGORIES = {"电子元器件": ["电阻", "电容", "芯片"], "机械零件": ["轴承", "齿轮"], "包装材料": ["纸箱", "托盘"], "化工材料": ["润滑油", "清洗剂"]}

def gen_suppliers(n=50):
    data = []
    for i in range(n):
        region = random.choice(REGIONS)
        cat = random.choice(list(CATEGORIES.keys()))
        data.append((f"SUP{str(i+1).zfill(3)}", f"{region}{cat}公司", round(random.uniform(3.5, 5.0), 1), region, cat))
    return data

def gen_products(n=100):
    data = []
    for i in range(n):
        cat = random.choice(list(CATEGORIES.keys()))
        sub = random.choice(CATEGORIES[cat])
        price = random.uniform(1, 500)
        data.append((f"SKU{str(i+1).zfill(4)}", f"{sub}{i}", cat, sub, round(price, 2)))
    return data

def gen_inventory(products, warehouses, n=500):
    data = []
    for _ in range(n):
        p = random.choice(products)
        w = random.choice(warehouses)
        q = random.randint(0, 10000)
        data.append((p[0], w, q, q - q//3, q//3))
    return data

def gen_orders(suppliers, products, n=200):
    data = []
    for i in range(n):
        s = random.choice(suppliers)
        items = []
        amount = 0
        for _ in range(random.randint(1, 3)):
            p = random.choice(products)
            qty = random.randint(10, 100)
            price = p[4] * random.uniform(0.9, 1.1)
            items.append({"sku": p[0], "name": p[1], "quantity": qty, "unit_price": round(price, 2)})
            amount += qty * price
        data.append((f"ORD{datetime.now().strftime('%Y%m%d')}{str(i+1).zfill(4)}", s[0], s[1], items, round(amount, 2)))
    return data

def gen_logistics(orders, n=200):
    carriers = [("顺丰", "SF"), ("中通", "ZT"), ("京东", "JD")]
    data = []
    for i, o in enumerate(orders[:n]):
        c = random.choice(carriers)
        data.append((f"{c[1]}{datetime.now().strftime('%Y%m%d')}{str(i+1).zfill(6)}", o[0], c[0], c[1], random.choice(["运输中", "已签收"])))
    return data

def gen_customs(orders, n=100):
    offices = [("深圳海关", "5301"), ("上海海关", "2200")]
    data = []
    for i in range(n):
        o = random.choice(orders)
        office = random.choice(offices)
        data.append((f"CUS{datetime.now().strftime('%Y%m%d')}{str(i+1).zfill(5)}", o[0], office[0], office[1], random.choice(["已放行", "待审核"]), o[4]))
    return data

def gen_platform_orders(n=50):
    platforms = ["amazon", "aliexpress", "shopify"]
    data = []
    for i in range(n):
        p = random.choice(platforms)
        data.append((f"{p.upper()}-{str(i+1).zfill(5)}", p, round(random.uniform(50, 500), 2), random.choice(["待发货", "已发货"])))
    return data

def gen_policies(n=50):
    templates = [("采购限额管理", "采购限额"), ("供应商准入", "供应商"), ("付款条款", "付款"), ("合同管理", "合同")]
    data = []
    for i in range(n):
        t = templates[i % len(templates)]
        data.append((f"POL{str(i+1).zfill(3)}", f"{t[0]}_V{random.randint(1,3)}", t[1], f"{t[0]}详细内容..."))
    return data

async def main():
    print("=" * 60)
    print("OpsPilot 完整数据初始化")
    print("=" * 60)
    
    conn = await asyncpg.connect(**DB)
    
    # 创建表
    print("\n[1/3] 创建表结构...")
    await conn.execute('''CREATE TABLE IF NOT EXISTS suppliers (
        id SERIAL PRIMARY KEY, supplier_id VARCHAR(20) UNIQUE NOT NULL, name VARCHAR(200),
        rating DECIMAL(2,1) DEFAULT 4.0, region VARCHAR(50), main_category VARCHAR(100))''')
    await conn.execute('''CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY, sku VARCHAR(50) UNIQUE NOT NULL, name VARCHAR(200),
        category VARCHAR(100), sub_category VARCHAR(100), base_price DECIMAL(10,2))''')
    await conn.execute('''CREATE TABLE IF NOT EXISTS inventory (
        id SERIAL PRIMARY KEY, sku VARCHAR(50) NOT NULL, warehouse_id VARCHAR(20),
        quantity INTEGER DEFAULT 0, available INTEGER DEFAULT 0, reserved INTEGER DEFAULT 0,
        UNIQUE(sku, warehouse_id))''')
    await conn.execute('''CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY, order_id VARCHAR(30) UNIQUE NOT NULL, supplier_id VARCHAR(20),
        supplier_name VARCHAR(200), items JSONB, total_amount DECIMAL(12,2))''')
    await conn.execute('''CREATE TABLE IF NOT EXISTS logistics (
        id SERIAL PRIMARY KEY, tracking_no VARCHAR(50) UNIQUE NOT NULL, order_id VARCHAR(30),
        carrier VARCHAR(100), carrier_code VARCHAR(20), status VARCHAR(30))''')
    await conn.execute('''CREATE TABLE IF NOT EXISTS customs_declarations (
        id SERIAL PRIMARY KEY, declaration_no VARCHAR(30) UNIQUE NOT NULL, order_id VARCHAR(30),
        customs_office VARCHAR(100), customs_code VARCHAR(20), status VARCHAR(30), declared_value DECIMAL(12,2))''')
    await conn.execute('''CREATE TABLE IF NOT EXISTS platform_orders (
        id SERIAL PRIMARY KEY, platform_order_id VARCHAR(50) UNIQUE NOT NULL, platform VARCHAR(50),
        total_amount DECIMAL(12,2), status VARCHAR(30))''')
    await conn.execute('''CREATE TABLE IF NOT EXISTS policies (
        id SERIAL PRIMARY KEY, policy_id VARCHAR(20) UNIQUE NOT NULL, title VARCHAR(200),
        category VARCHAR(50), content TEXT)''')
    print("      Done")
    
    # 生成数据
    print("[2/3] 生成虚拟数据...")
    suppliers = gen_suppliers(50)
    products = gen_products(100)
    inventory = gen_inventory(products, ["WH001", "WH002", "WH003", "WH004", "WH005"], 500)
    orders = gen_orders(suppliers, products, 200)
    logistics = gen_logistics(orders, 200)
    customs = gen_customs(orders, 100)
    platform = gen_platform_orders(50)
    policies = gen_policies(50)
    print(f"      Suppliers: {len(suppliers)}")
    print(f"      Products: {len(products)}")
    print(f"      Inventory: {len(inventory)}")
    print(f"      Orders: {len(orders)}")
    print(f"      Logistics: {len(logistics)}")
    print(f"      Customs: {len(customs)}")
    print(f"      Platform: {len(platform)}")
    print(f"      Policies: {len(policies)}")
    
    # 插入数据
    print("[3/3] 插入数据...")
    
    print("      - suppliers...")
    for s in suppliers:
        await conn.execute("INSERT INTO suppliers (supplier_id, name, rating, region, main_category) VALUES ($1,$2,$3,$4,$5) ON CONFLICT DO NOTHING", *s)
    
    print("      - products...")
    for p in products:
        await conn.execute("INSERT INTO products (sku, name, category, sub_category, base_price) VALUES ($1,$2,$3,$4,$5) ON CONFLICT DO NOTHING", *p)
    
    print("      - inventory...")
    for i in inventory:
        await conn.execute("INSERT INTO inventory (sku, warehouse_id, quantity, available, reserved) VALUES ($1,$2,$3,$4,$5) ON CONFLICT DO NOTHING", *i)
    
    print("      - orders...")
    for o in orders:
        await conn.execute("INSERT INTO orders (order_id, supplier_id, supplier_name, items, total_amount) VALUES ($1,$2,$3,$4,$5) ON CONFLICT DO NOTHING", *o)
    
    print("      - logistics...")
    for l in logistics:
        await conn.execute("INSERT INTO logistics (tracking_no, order_id, carrier, carrier_code, status) VALUES ($1,$2,$3,$4,$5) ON CONFLICT DO NOTHING", *l)
    
    print("      - customs...")
    for c in customs:
        await conn.execute("INSERT INTO customs_declarations (declaration_no, order_id, customs_office, customs_code, status, declared_value) VALUES ($1,$2,$3,$4,$5,$6) ON CONFLICT DO NOTHING", *c)
    
    print("      - platform...")
    for p in platform:
        await conn.execute("INSERT INTO platform_orders (platform_order_id, platform, total_amount, status) VALUES ($1,$2,$3,$4) ON CONFLICT DO NOTHING", *p)
    
    print("      - policies...")
    for p in policies:
        await conn.execute("INSERT INTO policies (policy_id, title, category, content) VALUES ($1,$2,$3,$4) ON CONFLICT DO NOTHING", *p)
    
    await conn.close()
    
    print("\n" + "=" * 60)
    print("Done! Total: 1270 records")
    print("=" * 60)

asyncio.run(main())
