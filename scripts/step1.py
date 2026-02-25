"""Step 1: Products"""
import asyncio, asyncpg, random

async def main():
    conn = await asyncpg.connect(host='localhost', port=5432, user='postgres', password='cyx0414', database='opspilot')
    await conn.execute('''CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY, sku VARCHAR(50) UNIQUE NOT NULL, name VARCHAR(200),
        category VARCHAR(100), sub_category VARCHAR(100), base_price DECIMAL(10,2))''')
    cats = {'电子元器件': ['电阻', '电容', '芯片'], '机械零件': ['轴承', '齿轮', '螺丝'], '包装材料': ['纸箱', '托盘'], '化工材料': ['润滑油', '清洗剂']}
    for i in range(100):
        cat = random.choice(list(cats.keys()))
        sub = random.choice(cats[cat])
        await conn.execute('INSERT INTO products (sku, name, category, sub_category, base_price) VALUES ($1,$2,$3,$4,$5) ON CONFLICT DO NOTHING',
            f'SKU{str(i+1).zfill(4)}', f'{sub}{i}', cat, sub, round(random.uniform(1, 500), 2))
    print(f'Products: {await conn.fetchval("SELECT COUNT(*) FROM products")}')
    await conn.close()

asyncio.run(main())
