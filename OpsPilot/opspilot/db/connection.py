"""
数据库连接管理

提供异步连接池和查询执行功能
"""
import asyncio
from typing import Optional, List, Dict, Any, Callable
from contextlib import asynccontextmanager
import asyncpg
from asyncpg import Pool, Connection
import yaml
from pathlib import Path

# 配置路径
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "database.yaml"


class DatabasePool:
    """数据库连接池管理器"""
    
    _instance: Optional['DatabasePool'] = None
    _pool: Optional[Pool] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._pool is not None:
            return
        
        self._config = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载数据库配置"""
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get("postgresql", {})
        return {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "cyx0414",
            "database": "opspilot",
        }
    
    async def connect(self) -> Pool:
        """创建连接池"""
        if self._pool is not None:
            return self._pool
        
        pool_config = self._config.get("pool", {})
        
        self._pool = await asyncpg.create_pool(
            host=self._config.get("host", "localhost"),
            port=self._config.get("port", 5432),
            user=self._config.get("user", "postgres"),
            password=self._config.get("password", ""),
            database=self._config.get("database", "opspilot"),
            min_size=pool_config.get("min_size", 5),
            max_size=pool_config.get("max_size", 20),
        )
        
        return self._pool
    
    async def close(self):
        """关闭连接池"""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
    
    @property
    def pool(self) -> Optional[Pool]:
        """获取连接池"""
        return self._pool
    
    async def execute(self, query: str, *args) -> str:
        """执行 SQL 语句"""
        async with self._pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """查询多行"""
        async with self._pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """查询单行"""
        async with self._pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args) -> Any:
        """查询单值"""
        async with self._pool.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    @asynccontextmanager
    async def transaction(self):
        """事务上下文管理器"""
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                yield conn


# 全局实例
_db_pool: Optional[DatabasePool] = None


async def get_database_pool() -> DatabasePool:
    """获取数据库连接池实例"""
    global _db_pool
    if _db_pool is None:
        _db_pool = DatabasePool()
        await _db_pool.connect()
    return _db_pool


async def close_database_pool():
    """关闭数据库连接池"""
    global _db_pool
    if _db_pool is not None:
        await _db_pool.close()
        _db_pool = None


async def execute_query(query: str, *args) -> List[asyncpg.Record]:
    """执行查询并返回结果"""
    pool = await get_database_pool()
    return await pool.fetch(query, *args)


async def execute_transaction(queries: List[tuple]) -> bool:
    """
    执行事务
    
    Args:
        queries: [(query, args), ...] 格式的查询列表
    
    Returns:
        是否成功
    """
    pool = await get_database_pool()
    try:
        async with pool.transaction() as conn:
            for query, args in queries:
                await conn.execute(query, *args)
        return True
    except Exception as e:
        print(f"Transaction failed: {e}")
        return False
