"""
Redis 缓存模块

提供缓存管理功能
"""
from typing import Optional, Any, Callable, TypeVar, ParamSpec
from functools import wraps
import json
import redis
from datetime import timedelta

# 类型变量
P = ParamSpec("P")
T = TypeVar("T")

# Redis 配置
REDIS_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "decode_responses": True,
}

# 缓存 TTL 配置
CACHE_TTL = {
    "default": 3600,          # 1 小时
    "exchange_rate": 3600,    # 1 小时
    "session": 86400,         # 24 小时
    "inventory": 300,         # 5 分钟
    "supplier": 1800,         # 30 分钟
    "policy": 7200,           # 2 小时
}


class CacheManager:
    """缓存管理器"""
    
    _instance: Optional["CacheManager"] = None
    _client: Optional[redis.Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is not None:
            return
        
        try:
            self._client = redis.Redis(**REDIS_CONFIG)
            self._client.ping()
            self._connected = True
        except Exception as e:
            print(f"Redis connection failed: {e}")
            self._connected = False
            self._client = None
    
    @property
    def connected(self) -> bool:
        """是否已连接"""
        return self._connected
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self._connected or self._client is None:
            return None
        
        try:
            value = self._client.get(key)
            if value is None:
                return None
            
            # 尝试解析 JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """设置缓存"""
        if not self._connected or self._client is None:
            return False
        
        try:
            # 序列化值
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            elif not isinstance(value, str):
                value = str(value)
            
            # 设置过期时间
            if ttl is None:
                ttl = CACHE_TTL["default"]
            
            self._client.setex(key, ttl, value)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self._connected or self._client is None:
            return False
        
        try:
            self._client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        if not self._connected or self._client is None:
            return False
        
        try:
            return bool(self._client.exists(key))
        except Exception:
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的所有缓存"""
        if not self._connected or self._client is None:
            return 0
        
        try:
            keys = self._client.keys(pattern)
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache clear error: {e}")
            return 0
    
    def get_or_set(
        self,
        key: str,
        func: Callable[[], T],
        ttl: Optional[int] = None,
    ) -> T:
        """获取缓存，不存在则调用函数并缓存结果"""
        # 尝试从缓存获取
        value = self.get(key)
        if value is not None:
            return value
        
        # 调用函数获取数据
        result = func()
        
        # 缓存结果
        self.set(key, result, ttl)
        
        return result
    
    async def aget_or_set(
        self,
        key: str,
        func: Callable[[], T],
        ttl: Optional[int] = None,
    ) -> T:
        """异步获取缓存，不存在则调用函数并缓存结果"""
        # 尝试从缓存获取
        value = self.get(key)
        if value is not None:
            return value
        
        # 调用函数获取数据
        import asyncio
        if asyncio.iscoroutinefunction(func):
            result = await func()
        else:
            result = func()
        
        # 缓存结果
        self.set(key, result, ttl)
        
        return result
    
    # ============================================
    # 业务缓存方法
    # ============================================
    
    def cache_exchange_rate(self, from_currency: str, to_currency: str, rate: float):
        """缓存汇率"""
        key = f"exchange_rate:{from_currency}:{to_currency}"
        self.set(key, rate, CACHE_TTL["exchange_rate"])
    
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """获取汇率缓存"""
        key = f"exchange_rate:{from_currency}:{to_currency}"
        value = self.get(key)
        return float(value) if value is not None else None
    
    def cache_inventory(self, sku: str, warehouse_id: str, data: dict):
        """缓存库存数据"""
        key = f"inventory:{sku}:{warehouse_id}"
        self.set(key, data, CACHE_TTL["inventory"])
    
    def get_inventory(self, sku: str, warehouse_id: str) -> Optional[dict]:
        """获取库存缓存"""
        key = f"inventory:{sku}:{warehouse_id}"
        return self.get(key)
    
    def cache_supplier(self, supplier_id: str, data: dict):
        """缓存供应商数据"""
        key = f"supplier:{supplier_id}"
        self.set(key, data, CACHE_TTL["supplier"])
    
    def get_supplier(self, supplier_id: str) -> Optional[dict]:
        """获取供应商缓存"""
        key = f"supplier:{supplier_id}"
        return self.get(key)
    
    def cache_session(self, session_id: str, data: dict):
        """缓存会话数据"""
        key = f"session:{session_id}"
        self.set(key, data, CACHE_TTL["session"])
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """获取会话缓存"""
        key = f"session:{session_id}"
        return self.get(key)
    
    def invalidate_supplier(self, supplier_id: str):
        """使供应商缓存失效"""
        self.delete(f"supplier:{supplier_id}")
    
    def invalidate_inventory(self, sku: str, warehouse_id: str):
        """使库存缓存失效"""
        self.delete(f"inventory:{sku}:{warehouse_id}")


# ============================================
# 全局实例
# ============================================

_cache: Optional[CacheManager] = None


def get_cache() -> CacheManager:
    """获取缓存管理器实例"""
    global _cache
    if _cache is None:
        _cache = CacheManager()
    return _cache


# ============================================
# 缓存装饰器
# ============================================

def cache_result(
    key_prefix: str,
    ttl: Optional[int] = None,
    key_builder: Optional[Callable] = None,
):
    """
    缓存结果装饰器
    
    Args:
        key_prefix: 缓存键前缀
        ttl: 过期时间（秒）
        key_builder: 自定义键构建函数
    
    Example:
        @cache_result("supplier", ttl=1800)
        async def get_supplier(supplier_id: str):
            ...
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # 构建缓存键
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # 默认使用第一个参数作为键的一部分
                key_parts = [key_prefix]
                if args:
                    key_parts.append(str(args[0]))
                for k, v in kwargs.items():
                    if k != "self":
                        key_parts.append(f"{k}:{v}")
                cache_key = ":".join(key_parts)
            
            # 尝试从缓存获取
            cache = get_cache()
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 调用原函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            cache.set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # 构建缓存键
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                key_parts = [key_prefix]
                if args:
                    key_parts.append(str(args[0]))
                for k, v in kwargs.items():
                    if k != "self":
                        key_parts.append(f"{k}:{v}")
                cache_key = ":".join(key_parts)
            
            # 尝试从缓存获取
            cache = get_cache()
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 调用原函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            cache.set(cache_key, result, ttl)
            
            return result
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
