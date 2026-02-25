"""Step 3: Orders"""
import asyncio, asyncpg, random, json
from datetime import datetime

async def main():
    conn = await asyncpg.connect(host='localhost', port=5432, user='postgres', password='cyx0414', database='opspilot')
    await conn.execute('''CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY, order_id VARCHAR(30) UNIQUE NOT NULL, supplier_id VARCHAR(20),
        supplier_name VARCHAR(200), items JSONB, total_amount DECIMAL(12,2), status VARCHAR(30))''')
    
    suppliers = await conn.fetch('SELECT supplier_id, name FROM suppliers')
    products = await conn.fetch('SELECT sku, name, base_price FROM products')
    
    for i in range(200):
        s = random.choice(suppliers)
        items = []
        amount = 0
        for _ in range(random.randint(1, 3)):
            p = random.choice(products)
            qty = random.randint(10, 100)
            price = float(p['base_price']) * random.uniform(0.9, 1.1)
            items.append({'sku': p['sku'], 'name': p['name'], 'quantity': qty, 'unit_price': round(price, 2)})
            amount += qty * price
        
        oid = f"ORD{datetime.now().strftime('%Y%m%d')}{str(i+1).zfill(4)}"
        await conn.execute('INSERT INTO orders (order_id, supplier_id, supplier_name, items, total_amount, status) VALUES ($1,$2,$3,$4,$5,$6) ON CONFLICT DO NOTHING',
            oid, s['supplier_id'], s['name'], json.dumps(items), round(amount, 2), random.choice(['created', 'approved', 'shipping', 'completed']))
    
    print(f'Orders: {await conn.fetchval("SELECT COUNT(*) FROM orders")}')
    await conn.close()

asyncio.run(main())
