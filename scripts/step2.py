"""Step 2: Inventory"""
import asyncio, asyncpg, random

async def main():
    conn = await asyncpg.connect(host='localhost', port=5432, user='postgres', password='cyx0414', database='opspilot')
    await conn.execute('''CREATE TABLE IF NOT EXISTS inventory (
        id SERIAL PRIMARY KEY, sku VARCHAR(50) NOT NULL, warehouse_id VARCHAR(20),
        quantity INTEGER DEFAULT 0, available INTEGER DEFAULT 0, reserved INTEGER DEFAULT 0,
        UNIQUE(sku, warehouse_id))''')
    
    skus = [r['sku'] for r in await conn.fetch('SELECT sku FROM products')]
    whs = ['WH001', 'WH002', 'WH003', 'WH004', 'WH005']
    
    for _ in range(500):
        sku = random.choice(skus)
        wh = random.choice(whs)
        q = random.randint(0, 10000)
        try:
            await conn.execute('INSERT INTO inventory (sku, warehouse_id, quantity, available, reserved) VALUES ($1,$2,$3,$4,$5) ON CONFLICT DO NOTHING',
                sku, wh, q, q - q//3, q//3)
        except:
            pass
    
    print(f'Inventory: {await conn.fetchval("SELECT COUNT(*) FROM inventory")}')
    await conn.close()

asyncio.run(main())
