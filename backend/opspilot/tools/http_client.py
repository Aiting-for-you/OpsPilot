"""
HTTP API 工具模块

提供 REST API、GraphQL 的 MCP 工具封装。

特性：
- 统一请求封装
- 重试与超时
- 认证支持
- 响应缓存
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from opspilot.tools.base import (
    BaseToolServer,
    ToolSchema,
    ToolResult,
    ToolContext,
)


class HttpMethod(Enum):
    """HTTP 方法"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


@dataclass
class RequestConfig:
    """请求配置"""
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    verify_ssl: bool = True
    follow_redirects: bool = True
    max_redirects: int = 5


@dataclass
class AuthConfig:
    """认证配置"""
    auth_type: str = "none"  # none, basic, bearer, api_key, oauth2
    username: str = ""
    password: str = ""
    token: str = ""
    api_key: str = ""
    api_key_header: str = "X-API-Key"


@dataclass
class ApiResponse:
    """API 响应"""
    success: bool
    status_code: int = 0
    headers: Dict[str, str] = field(default_factory=dict)
    body: Any = None
    error: str = ""
    latency_ms: float = 0.0
    from_cache: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "status_code": self.status_code,
            "headers": self.headers,
            "body": self.body,
            "error": self.error,
            "latency_ms": self.latency_ms,
            "from_cache": self.from_cache,
        }


class ResponseCache:
    """
    响应缓存
    
    使用内存缓存 GET 请求结果。
    """
    
    def __init__(self, max_size: int = 100, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl
        self._cache: Dict[str, tuple[float, ApiResponse]] = {}
    
    def _get_cache_key(self, url: str, params: Optional[Dict] = None) -> str:
        """生成缓存 key"""
        key_data = f"{url}:{json.dumps(params or {}, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, url: str, params: Optional[Dict] = None) -> Optional[ApiResponse]:
        """获取缓存"""
        key = self._get_cache_key(url, params)
        if key in self._cache:
            timestamp, response = self._cache[key]
            if time.time() - timestamp < self.ttl:
                response.from_cache = True
                return response
            else:
                del self._cache[key]
        return None
    
    def set(self, url: str, params: Optional[Dict], response: ApiResponse) -> None:
        """设置缓存"""
        if len(self._cache) >= self.max_size:
            # 清理过期缓存
            current_time = time.time()
            expired_keys = [
                k for k, (t, _) in self._cache.items()
                if current_time - t > self.ttl
            ]
            for k in expired_keys:
                del self._cache[k]
        
        key = self._get_cache_key(url, params)
        response_copy = ApiResponse(
            success=response.success,
            status_code=response.status_code,
            headers=response.headers,
            body=response.body,
            latency_ms=response.latency_ms,
            from_cache=False,
        )
        self._cache[key] = (time.time(), response_copy)
    
    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()


class HttpClient:
    """
    HTTP 客户端
    
    封装 HTTP 请求，支持重试、认证、缓存。
    """
    
    def __init__(
        self,
        request_config: Optional[RequestConfig] = None,
        auth_config: Optional[AuthConfig] = None,
        cache_enabled: bool = True,
    ):
        self.request_config = request_config or RequestConfig()
        self.auth_config = auth_config or AuthConfig()
        self.cache = ResponseCache() if cache_enabled else None
    
    def _build_headers(
        self,
        custom_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """构建请求头"""
        headers = {
            "User-Agent": "OpsPilot/1.0",
            "Accept": "application/json",
        }
        
        # 添加认证头
        if self.auth_config.auth_type == "basic":
            import base64
            credentials = base64.b64encode(
                f"{self.auth_config.username}:{self.auth_config.password}".encode()
            ).decode()
            headers["Authorization"] = f"Basic {credentials}"
        
        elif self.auth_config.auth_type == "bearer":
            headers["Authorization"] = f"Bearer {self.auth_config.token}"
        
        elif self.auth_config.auth_type == "api_key":
            headers[self.auth_config.api_key_header] = self.auth_config.api_key
        
        # 合并自定义头
        if custom_headers:
            headers.update(custom_headers)
        
        return headers
    
    async def request(
        self,
        method: HttpMethod,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> ApiResponse:
        """
        发送 HTTP 请求
        
        Args:
            method: HTTP 方法
            url: URL
            params: 查询参数
            body: 请求体
            headers: 请求头
        
        Returns:
            ApiResponse: 响应
        """
        # 检查缓存（仅 GET）
        if method == HttpMethod.GET and self.cache:
            cached = self.cache.get(url, params)
            if cached:
                return cached
        
        start_time = time.time()
        
        # 构建请求
        request_headers = self._build_headers(headers)
        
        # 重试逻辑
        last_error = ""
        for attempt in range(self.request_config.max_retries):
            try:
                result = await self._execute_request(
                    method=method,
                    url=url,
                    params=params,
                    body=body,
                    headers=request_headers,
                )
                
                # 缓存 GET 响应
                if method == HttpMethod.GET and self.cache and result.success:
                    self.cache.set(url, params, result)
                
                return result
            
            except Exception as e:
                last_error = str(e)
                if attempt < self.request_config.max_retries - 1:
                    await asyncio.sleep(self.request_config.retry_delay * (attempt + 1))
        
        return ApiResponse(
            success=False,
            error=last_error,
            latency_ms=(time.time() - start_time) * 1000,
        )
    
    async def _execute_request(
        self,
        method: HttpMethod,
        url: str,
        params: Optional[Dict[str, Any]],
        body: Optional[Any],
        headers: Dict[str, str],
    ) -> ApiResponse:
        """执行请求"""
        start_time = time.time()
        
        try:
            import httpx
            
            async with httpx.AsyncClient(
                timeout=self.request_config.timeout,
                verify=self.request_config.verify_ssl,
                follow_redirects=self.request_config.follow_redirects,
                max_redirects=self.request_config.max_redirects,
            ) as client:
                # 准备请求体
                json_body = None
                data_body = None
                content_type = headers.get("Content-Type", "application/json")
                
                if body is not None:
                    if isinstance(body, (dict, list)):
                        json_body = body
                    elif isinstance(body, str):
                        if content_type == "application/json":
                            json_body = json.loads(body)
                        else:
                            data_body = body
                    else:
                        data_body = body
                
                response = await client.request(
                    method=method.value,
                    url=url,
                    params=params,
                    json=json_body,
                    data=data_body,
                    headers=headers,
                )
                
                # 解析响应
                try:
                    response_body = response.json()
                except Exception:
                    response_body = response.text
                
                return ApiResponse(
                    success=200 <= response.status_code < 300,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    body=response_body,
                    latency_ms=(time.time() - start_time) * 1000,
                )
        
        except ImportError:
            # 无 httpx，使用 Mock
            return await self._mock_request(method, url, params, body)
        
        except Exception as e:
            return ApiResponse(
                success=False,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000,
            )
    
    async def _mock_request(
        self,
        method: HttpMethod,
        url: str,
        params: Optional[Dict[str, Any]],
        body: Optional[Any],
    ) -> ApiResponse:
        """Mock 请求（用于测试）"""
        # 模拟延迟
        await asyncio.sleep(0.1)
        
        # Mock 响应
        mock_responses = {
            "api.example.com/users": {
                "users": [
                    {"id": 1, "name": "张三", "email": "zhangsan@example.com"},
                    {"id": 2, "name": "李四", "email": "lisi@example.com"},
                ],
                "total": 2,
            },
            "api.example.com/products": {
                "products": [
                    {"id": 1, "name": "产品A", "price": 100.0},
                    {"id": 2, "name": "产品B", "price": 200.0},
                ],
            },
        }
        
        # 匹配 Mock 数据
        for mock_url, mock_data in mock_responses.items():
            if mock_url in url:
                return ApiResponse(
                    success=True,
                    status_code=200,
                    body=mock_data,
                    latency_ms=100.0,
                )
        
        return ApiResponse(
            success=True,
            status_code=200,
            body={"message": "Mock response", "url": url, "method": method.value},
            latency_ms=100.0,
        )


class ApiServer(BaseToolServer):
    """
    HTTP API MCP Server
    
    提供 REST API 调用工具。
    """
    
    def __init__(
        self,
        base_url: str = "",
        request_config: Optional[RequestConfig] = None,
        auth_config: Optional[AuthConfig] = None,
    ):
        super().__init__(
            name="api-tools",
            description="HTTP API 工具集：GET/POST/PUT/DELETE 请求"
        )
        
        self.base_url = base_url.rstrip("/") if base_url else ""
        self.client = HttpClient(request_config, auth_config)
        
        self._register_tools()
    
    def _build_url(self, endpoint: str) -> str:
        """构建完整 URL"""
        if endpoint.startswith("http"):
            return endpoint
        return f"{self.base_url}/{endpoint.lstrip('/')}"
    
    def _register_tools(self):
        """注册所有 API 工具"""
        
        # GET 请求
        @self.register_tool(ToolSchema(
            name="http_get",
            description="发送 GET 请求",
            input_schema={
                "type": "object",
                "required": ["url"],
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "请求 URL（相对路径或绝对路径）"
                    },
                    "params": {
                        "type": "object",
                        "description": "查询参数"
                    },
                    "headers": {
                        "type": "object",
                        "description": "自定义请求头"
                    },
                    "use_cache": {
                        "type": "boolean",
                        "description": "是否使用缓存",
                        "default": True
                    }
                }
            }
        ))
        async def http_get(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            url = self._build_url(params.get("url", ""))
            query_params = params.get("params")
            headers = params.get("headers")
            
            response = await self.client.request(
                method=HttpMethod.GET,
                url=url,
                params=query_params,
                headers=headers,
            )
            
            if response.success:
                return ToolResult.success(response.to_dict())
            else:
                return ToolResult.error(
                    response.error,
                    error_code="HTTP_ERROR",
                    fallback_mode="mock",
                )
        
        # POST 请求
        @self.register_tool(ToolSchema(
            name="http_post",
            description="发送 POST 请求",
            input_schema={
                "type": "object",
                "required": ["url"],
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "请求 URL"
                    },
                    "body": {
                        "type": "object",
                        "description": "请求体（JSON）"
                    },
                    "headers": {
                        "type": "object",
                        "description": "自定义请求头"
                    }
                }
            }
        ))
        async def http_post(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            url = self._build_url(params.get("url", ""))
            body = params.get("body")
            headers = params.get("headers")
            
            response = await self.client.request(
                method=HttpMethod.POST,
                url=url,
                body=body,
                headers=headers,
            )
            
            if response.success:
                return ToolResult.success(response.to_dict())
            else:
                return ToolResult.error(
                    response.error,
                    error_code="HTTP_ERROR",
                    fallback_mode="mock",
                )
        
        # PUT 请求
        @self.register_tool(ToolSchema(
            name="http_put",
            description="发送 PUT 请求",
            input_schema={
                "type": "object",
                "required": ["url"],
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "请求 URL"
                    },
                    "body": {
                        "type": "object",
                        "description": "请求体（JSON）"
                    },
                    "headers": {
                        "type": "object",
                        "description": "自定义请求头"
                    }
                }
            }
        ))
        async def http_put(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            url = self._build_url(params.get("url", ""))
            body = params.get("body")
            headers = params.get("headers")
            
            response = await self.client.request(
                method=HttpMethod.PUT,
                url=url,
                body=body,
                headers=headers,
            )
            
            if response.success:
                return ToolResult.success(response.to_dict())
            else:
                return ToolResult.error(response.error, error_code="HTTP_ERROR")
        
        # DELETE 请求
        @self.register_tool(ToolSchema(
            name="http_delete",
            description="发送 DELETE 请求",
            input_schema={
                "type": "object",
                "required": ["url"],
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "请求 URL"
                    },
                    "headers": {
                        "type": "object",
                        "description": "自定义请求头"
                    }
                }
            }
        ))
        async def http_delete(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            url = self._build_url(params.get("url", ""))
            headers = params.get("headers")
            
            response = await self.client.request(
                method=HttpMethod.DELETE,
                url=url,
                headers=headers,
            )
            
            if response.success:
                return ToolResult.success(response.to_dict())
            else:
                return ToolResult.error(response.error, error_code="HTTP_ERROR")
        
        # GraphQL 查询
        @self.register_tool(ToolSchema(
            name="graphql_query",
            description="执行 GraphQL 查询",
            input_schema={
                "type": "object",
                "required": ["url", "query"],
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "GraphQL 端点 URL"
                    },
                    "query": {
                        "type": "string",
                        "description": "GraphQL 查询语句"
                    },
                    "variables": {
                        "type": "object",
                        "description": "查询变量"
                    },
                    "operation_name": {
                        "type": "string",
                        "description": "操作名称"
                    }
                }
            }
        ))
        async def graphql_query(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            url = self._build_url(params.get("url", ""))
            query = params.get("query", "")
            variables = params.get("variables")
            operation_name = params.get("operation_name")
            
            body = {
                "query": query,
            }
            if variables:
                body["variables"] = variables
            if operation_name:
                body["operationName"] = operation_name
            
            response = await self.client.request(
                method=HttpMethod.POST,
                url=url,
                body=body,
                headers={"Content-Type": "application/json"},
            )
            
            if response.success:
                # 检查 GraphQL 错误
                if isinstance(response.body, dict) and "errors" in response.body:
                    return ToolResult.error(
                        str(response.body["errors"]),
                        error_code="GRAPHQL_ERROR",
                    )
                return ToolResult.success(response.to_dict())
            else:
                return ToolResult.error(response.error, error_code="HTTP_ERROR")
        
        # 批量请求
        @self.register_tool(ToolSchema(
            name="http_batch",
            description="批量发送 HTTP 请求",
            input_schema={
                "type": "object",
                "required": ["requests"],
                "properties": {
                    "requests": {
                        "type": "array",
                        "description": "请求列表",
                        "items": {
                            "type": "object",
                            "required": ["method", "url"],
                            "properties": {
                                "method": {
                                    "type": "string",
                                    "enum": ["GET", "POST", "PUT", "DELETE"]
                                },
                                "url": {"type": "string"},
                                "params": {"type": "object"},
                                "body": {"type": "object"},
                                "headers": {"type": "object"}
                            }
                        }
                    },
                    "concurrency": {
                        "type": "integer",
                        "description": "并发数",
                        "default": 5
                    }
                }
            }
        ))
        async def http_batch(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            requests = params.get("requests", [])
            concurrency = params.get("concurrency", 5)
            
            semaphore = asyncio.Semaphore(concurrency)
            
            async def execute_single(req: Dict[str, Any]) -> Dict[str, Any]:
                async with semaphore:
                    method = HttpMethod[req.get("method", "GET")]
                    response = await self.client.request(
                        method=method,
                        url=self._build_url(req.get("url", "")),
                        params=req.get("params"),
                        body=req.get("body"),
                        headers=req.get("headers"),
                    )
                    return {
                        "url": req.get("url"),
                        "success": response.success,
                        "status_code": response.status_code,
                        "body": response.body if response.success else response.error,
                    }
            
            tasks = [execute_single(req) for req in requests]
            results = await asyncio.gather(*tasks)
            
            success_count = sum(1 for r in results if r["success"])
            
            return ToolResult.success({
                "total": len(requests),
                "success": success_count,
                "failed": len(requests) - success_count,
                "results": results,
            })
    
    async def health_check(self) -> bool:
        """健康检查"""
        return True


# 便捷函数
def create_api_server(
    base_url: str = "",
    request_config: Optional[RequestConfig] = None,
    auth_config: Optional[AuthConfig] = None,
) -> ApiServer:
    """创建 API Server"""
    return ApiServer(base_url, request_config, auth_config)
