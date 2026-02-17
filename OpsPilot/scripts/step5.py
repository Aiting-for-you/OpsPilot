"""Step 5: Platform Orders & Policies"""
import asyncio, asyncpg, random
from datetime import datetime

async def main():
    conn = await asyncpg.connect(host='localhost', port=5432, user='postgres', password='cyx0414', database='opspilot')
    
    # 平台订单
    await conn.execute('''CREATE TABLE IF NOT EXISTS platform_orders (
        id SERIAL PRIMARY KEY, platform_order_id VARCHAR(50) UNIQUE NOT NULL, platform VARCHAR(50),
        total_amount DECIMAL(12,2), status VARCHAR(30))''')
    
    platforms = ['amazon', 'aliexpress', 'shopify', 'ebay']
    for i in range(50):
        p = random.choice(platforms)
        await conn.execute('INSERT INTO platform_orders (platform_order_id, platform, total_amount, status) VALUES ($1,$2,$3,$4) ON CONFLICT DO NOTHING',
            f"{p.upper()}-{str(i+1).zfill(5)}", p, round(random.uniform(50, 500), 2), random.choice(['待发货', '已发货', '已完成']))
    
    print(f'Platform Orders: {await conn.fetchval("SELECT COUNT(*) FROM platform_orders")}')
    
    # 政策文档
    await conn.execute('''CREATE TABLE IF NOT EXISTS policies (
        id SERIAL PRIMARY KEY, policy_id VARCHAR(20) UNIQUE NOT NULL, title VARCHAR(200),
        category VARCHAR(50), content TEXT)''')
    
    templates = [
        ('采购限额管理规定', '采购限额', '本规定明确了各类采购的审批限额和流程，适用于公司所有采购活动。'),
        ('供应商准入标准', '供应商准入', '供应商准入需满足以下条件：企业资质完整、产品质量合格、价格具有竞争力。'),
        ('付款条款规范', '付款条款', '付款条款按照供应商等级和合作年限确定，分为月结30天、45天、60天。'),
        ('合同管理规范', '合同管理', '采购合同签订流程和管理要求，包括合同审批、签署、归档等环节。'),
        ('紧急采购流程', '紧急采购', '紧急采购的定义和快速审批流程，适用于生产急需或突发情况。'),
    ]
    
    for i in range(50):
        t = templates[i % len(templates)]
        await conn.execute('INSERT INTO policies (policy_id, title, category, content) VALUES ($1,$2,$3,$4) ON CONFLICT DO NOTHING',
            f"POL{str(i+1).zfill(3)}", f"{t[0]}_V{random.randint(1,3)}.{random.randint(0,9)}", t[1], t[2])
    
    print(f'Policies: {await conn.fetchval("SELECT COUNT(*) FROM policies")}')
    await conn.close()

asyncio.run(main())
