"""Step 4: Logistics & Customs"""
import asyncio, asyncpg, random
from datetime import datetime, timedelta

async def main():
    conn = await asyncpg.connect(host='localhost', port=5432, user='postgres', password='cyx0414', database='opspilot')
    
    # 物流表
    await conn.execute('''CREATE TABLE IF NOT EXISTS logistics (
        id SERIAL PRIMARY KEY, tracking_no VARCHAR(50) UNIQUE NOT NULL, order_id VARCHAR(30),
        carrier VARCHAR(100), carrier_code VARCHAR(20), status VARCHAR(30))''')
    
    orders = await conn.fetch('SELECT order_id FROM orders LIMIT 200')
    carriers = [('顺丰速运', 'SF'), ('中通快递', 'ZT'), ('京东物流', 'JD')]
    
    for i, o in enumerate(orders):
        c = random.choice(carriers)
        await conn.execute('INSERT INTO logistics (tracking_no, order_id, carrier, carrier_code, status) VALUES ($1,$2,$3,$4,$5) ON CONFLICT DO NOTHING',
            f"{c[1]}{datetime.now().strftime('%Y%m%d')}{str(i+1).zfill(6)}", o['order_id'], c[0], c[1], random.choice(['运输中', '已签收', '派送中']))
    
    print(f'Logistics: {await conn.fetchval("SELECT COUNT(*) FROM logistics")}')
    
    # 报关表
    await conn.execute('''CREATE TABLE IF NOT EXISTS customs_declarations (
        id SERIAL PRIMARY KEY, declaration_no VARCHAR(30) UNIQUE NOT NULL, order_id VARCHAR(30),
        customs_office VARCHAR(100), customs_code VARCHAR(20), status VARCHAR(30), declared_value DECIMAL(12,2))''')
    
    offices = [('深圳海关', '5301'), ('上海海关', '2200'), ('广州海关', '5100')]
    orders = await conn.fetch('SELECT order_id, total_amount FROM orders LIMIT 100')
    
    for i, o in enumerate(orders):
        office = random.choice(offices)
        await conn.execute('INSERT INTO customs_declarations (declaration_no, order_id, customs_office, customs_code, status, declared_value) VALUES ($1,$2,$3,$4,$5,$6) ON CONFLICT DO NOTHING',
            f"CUS{datetime.now().strftime('%Y%m%d')}{str(i+1).zfill(5)}", o['order_id'], office[0], office[1], random.choice(['已放行', '待审核', '审核中']), float(o['total_amount']))
    
    print(f'Customs: {await conn.fetchval("SELECT COUNT(*) FROM customs_declarations")}')
    await conn.close()

asyncio.run(main())
