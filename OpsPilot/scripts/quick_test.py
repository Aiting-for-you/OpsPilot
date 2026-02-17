"""快速测试数据库"""
import asyncio
import asyncpg

async def main():
    # 创建数据库
    try:
        conn = await asyncpg.connect(
            host='localhost', port=5432, user='postgres', 
            password='cyx0414', database='postgres'
        )
        await conn.execute('CREATE DATABASE opspilot')
        print('Database created')
        await conn.close()
    except:
        print('Database exists')
    
    # 连接
    conn = await asyncpg.connect(
        host='localhost', port=5432, user='postgres', 
        password='cyx0414', database='opspilot'
    )
    
    # 创建表
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id SERIAL PRIMARY KEY,
            supplier_id VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(200),
            rating DECIMAL(2,1) DEFAULT 4.0,
            region VARCHAR(50)
        )
    ''')
    
    # 插入
    for i in range(5):
        await conn.execute(f'''
            INSERT INTO suppliers (supplier_id, name, rating, region)
            VALUES ('SUP00{i+1}', 'Supplier {i+1}', 4.{i}, 'Region {i}')
            ON CONFLICT (supplier_id) DO NOTHING
        ''')
    
    # 查询
    rows = await conn.fetch('SELECT * FROM suppliers')
    print(f'Found {len(rows)} suppliers')
    
    await conn.close()
    print('OK')

asyncio.run(main())
