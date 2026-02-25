"""检查数据库状态"""
import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(
        host='localhost', port=5432, user='postgres', 
        password='cyx0414', database='opspilot'
    )
    
    tables = [
        'suppliers', 'products', 'inventory', 'orders', 
        'logistics', 'customs_declarations', 'platform_orders', 
        'policies', 'warehouses', 'exchange_rates'
    ]
    
    print('Database Statistics:')
    print('=' * 50)
    
    total = 0
    for table in tables:
        try:
            count = await conn.fetchval(f'SELECT COUNT(*) FROM {table}')
            print(f'{table:25} {count:>5} records')
            total += count
        except Exception as e:
            print(f'{table:25} ERROR')
    
    print('=' * 50)
    print(f'{"TOTAL":25} {total:>5} records')
    
    await conn.close()

asyncio.run(main())
