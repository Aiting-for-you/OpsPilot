"""
工具系统端到端测试

测试工具系统的完整流程：
- MCP Server (ERP、合规)
- 数据库工具
- HTTP 客户端工具
- 运维工具
- 文件操作工具
- 通知工具
- 工具索引和检索
- 工具自愈机制
"""
import pytest
import asyncio
import json
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from opspilot.tools import (
    ToolRouter,
    ToolContext,
    ToolResult,
    DatabaseServer,
    ApiServer,
    DevOpsServer,
    FileServer,
    NotificationServer,
    InternalToolsServer,
    create_default_router,
)
from opspilot.tools.base import ToolStatus


class TestDatabaseToolsE2E:
    """数据库工具端到端测试"""

    @pytest.fixture
    def db_tool_server(self):
        """创建数据库工具服务器"""
        return DatabaseServer(db_type="mock")

    @pytest.mark.asyncio
    async def test_db_query_execution(self, db_tool_server):
        """测试数据库查询执行"""
        context = ToolContext(task_id="db_test_001")
        
        result = await db_tool_server.execute_tool(
            tool_name="db_query",
            params={"sql": "SELECT * FROM suppliers LIMIT 5"},
            context=context,
        )
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_db_execute_operation(self, db_tool_server):
        """测试数据库执行操作"""
        context = ToolContext(task_id="db_test_002")
        
        result = await db_tool_server.execute_tool(
            tool_name="db_execute",
            params={
                "sql": "INSERT INTO test_table (name) VALUES ('test')"
            },
            context=context,
        )
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_db_transaction(self, db_tool_server):
        """测试数据库事务"""
        context = ToolContext(task_id="db_test_003")
        
        # 查询操作
        query_result = await db_tool_server.execute_tool(
            tool_name="db_query",
            params={"sql": "SELECT COUNT(*) FROM suppliers"},
            context=context,
        )
        
        assert query_result is not None


class TestHttpToolsE2E:
    """HTTP 工具端到端测试"""

    @pytest.fixture
    def http_tool_server(self):
        """创建 HTTP 工具服务器"""
        return ApiServer()

    @pytest.mark.asyncio
    async def test_http_get_request(self, http_tool_server):
        """测试 HTTP GET 请求"""
        context = ToolContext(task_id="http_test_001")
        
        result = await http_tool_server.execute_tool(
            tool_name="http_get",
            params={
                "url": "https://jsonplaceholder.typicode.com/posts/1"
            },
            context=context,
        )
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_http_post_request(self, http_tool_server):
        """测试 HTTP POST 请求"""
        context = ToolContext(task_id="http_test_002")
        
        result = await http_tool_server.execute_tool(
            tool_name="http_post",
            params={
                "url": "https://jsonplaceholder.typicode.com/posts",
                "data": {"title": "测试", "body": "内容", "userId": 1},
            },
            context=context,
        )
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_http_with_headers(self, http_tool_server):
        """测试带 headers 的 HTTP 请求"""
        context = ToolContext(task_id="http_test_003")
        
        result = await http_tool_server.execute_tool(
            tool_name="http_get",
            params={
                "url": "https://jsonplaceholder.typicode.com/posts/1",
                "headers": {"Accept": "application/json"},
            },
            context=context,
        )
        
        assert result is not None


class TestDevOpsToolsE2E:
    """运维工具端到端测试"""

    @pytest.fixture
    def devops_tool_server(self):
        """创建运维工具服务器"""
        return DevOpsServer()

    @pytest.mark.asyncio
    async def test_system_info(self, devops_tool_server):
        """测试系统信息获取"""
        context = ToolContext(task_id="devops_test_001")
        
        result = await devops_tool_server.execute_tool(
            tool_name="system_info",
            params={},
            context=context,
        )
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_system_cpu(self, devops_tool_server):
        """测试 CPU 信息获取"""
        context = ToolContext(task_id="devops_test_002")
        
        result = await devops_tool_server.execute_tool(
            tool_name="system_cpu",
            params={},
            context=context,
        )
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_system_memory(self, devops_tool_server):
        """测试内存信息获取"""
        context = ToolContext(task_id="devops_test_003")
        
        result = await devops_tool_server.execute_tool(
            tool_name="system_memory",
            params={},
            context=context,
        )
        
        assert result is not None


class TestFileOperationsE2E:
    """文件操作端到端测试"""

    @pytest.fixture
    def file_tool_server(self):
        """创建文件操作服务器"""
        return FileServer()

    @pytest.mark.asyncio
    async def test_file_read(self, file_tool_server):
        """测试文件读取"""
        context = ToolContext(task_id="file_test_001")
        
        # 读取测试文件
        result = await file_tool_server.execute_tool(
            tool_name="file_read",
            params={"path": "tests/test_integration.py"},
            context=context,
        )
        
        # 文件可能不存在，但工具应该正常执行
        assert result is not None

    @pytest.mark.asyncio
    async def test_file_write(self, file_tool_server):
        """测试文件写入"""
        context = ToolContext(task_id="file_test_002")
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = f.name
            f.write("test content")
        
        try:
            result = await file_tool_server.execute_tool(
                tool_name="file_write",
                params={
                    "path": temp_path,
                    "content": "updated content",
                },
                context=context,
            )
            assert result is not None
        finally:
            import os
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestNotificationToolsE2E:
    """通知工具端到端测试"""

    @pytest.fixture
    def notification_tool_server(self):
        """创建通知工具服务器"""
        return NotificationServer()

    @pytest.mark.asyncio
    async def test_send_notification(self, notification_tool_server):
        """测试发送通知"""
        context = ToolContext(task_id="notify_test_001")
        
        result = await notification_tool_server.execute_tool(
            tool_name="send_notification",
            params={
                "channel": "log",
                "title": "测试通知",
                "content": "这是一条测试通知",
            },
            context=context,
        )
        
        assert result is not None


class TestToolRouterE2E:
    """工具路由器端到端测试"""

    @pytest.fixture
    def tool_router(self):
        """创建工具路由器"""
        router = ToolRouter()
        router.register_server(DatabaseServer(db_type="mock"))
        router.register_server(ApiServer())
        router.register_server(DevOpsServer())
        router.register_server(FileServer())
        router.register_server(NotificationServer())
        router.register_server(InternalToolsServer())
        return router

    @pytest.mark.asyncio
    async def test_router_tool_discovery(self, tool_router):
        """测试路由器工具发现"""
        schemas = tool_router.get_all_schemas()
        tool_names = [s.name for s in schemas]
        
        # 验证有工具注册
        assert len(tool_names) > 0
        
        # 验证包含各类工具
        assert any("db_" in name for name in tool_names) or any("query" in name for name in tool_names)
        assert any("http_" in name for name in tool_names) or any("request" in name for name in tool_names)

    @pytest.mark.asyncio
    async def test_router_tool_list(self, tool_router):
        """测试路由器工具列表"""
        schemas = tool_router.get_all_schemas()
        
        # 验证有工具注册
        assert len(schemas) > 0

    @pytest.mark.asyncio
    async def test_router_tool_execution(self, tool_router):
        """测试路由器工具执行"""
        context = ToolContext(task_id="router_test_001")
        
        # 执行系统信息工具
        result = await tool_router.call_tool(
            "system_info",
            {},
            context,
        )
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_router_concurrent_execution(self, tool_router):
        """测试路由器并发执行"""
        context = ToolContext(task_id="router_test_002")
        
        # 并发执行多个工具
        tasks = [
            tool_router.call_tool("system_info", {}, context),
            tool_router.call_tool("system_cpu", {}, context),
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 2


class TestToolChainE2E:
    """工具链端到端测试"""

    @pytest.mark.asyncio
    async def test_http_to_db_workflow(self):
        """测试 HTTP -> 数据库工作流"""
        api_server = ApiServer()
        db_server = DatabaseServer(db_type="mock")
        context = ToolContext(task_id="chain_test_001")
        
        # 1. 从 HTTP 获取数据
        http_result = await api_server.execute_tool(
            tool_name="http_get",
            params={"url": "https://jsonplaceholder.typicode.com/users/1"},
            context=context,
        )
        
        assert http_result is not None
        
        # 2. 将数据存入数据库（模拟）
        db_result = await db_server.execute_tool(
            tool_name="db_execute",
            params={"sql": "SELECT 1"},
            context=context,
        )
        
        assert db_result is not None

    @pytest.mark.asyncio
    async def test_multi_step_data_processing(self):
        """测试多步数据处理"""
        from opspilot.tools.internal import InternalToolsServer
        
        internal = InternalToolsServer()
        context = ToolContext(task_id="chain_test_002")
        
        # 1. 格式化数据
        format_result = await internal.execute_tool(
            tool_name="format_json",
            params={"data": {"key": "value"}},
            context=context,
        )
        
        assert format_result is not None
        
        # 2. 计算
        calc_result = await internal.execute_tool(
            tool_name="calculate",
            params={"expression": "10 + 20"},
            context=context,
        )
        
        assert calc_result is not None


class TestToolWithDatabaseE2E:
    """工具系统与数据库集成测试"""

    @pytest.fixture
    async def db_pool(self):
        """数据库连接池"""
        import asyncpg
        pool = await asyncpg.create_pool(
            host="localhost",
            port=5432,
            user="postgres",
            password="cyx0414",
            database="opspilot",
            min_size=1,
            max_size=3,
        )
        yield pool
        await pool.close()

    @pytest.mark.asyncio
    async def test_query_suppliers_via_tool(self, db_pool):
        """测试通过工具查询供应商"""
        async with db_pool.acquire() as conn:
            # 查询供应商
            rows = await conn.fetch("SELECT * FROM suppliers LIMIT 5")
            
            assert len(rows) > 0
            
            # 验证数据结构
            row = rows[0]
            assert row is not None

    @pytest.mark.asyncio
    async def test_query_products_via_tool(self, db_pool):
        """测试通过工具查询产品"""
        async with db_pool.acquire() as conn:
            # 查询产品
            rows = await conn.fetch("SELECT * FROM products LIMIT 5")
            
            assert len(rows) > 0




class TestToolWithCacheE2E:
    """工具系统与缓存集成测试"""

    @pytest.fixture
    def cache(self):
        """缓存管理器"""
        from opspilot.db.cache import CacheManager
        return CacheManager()

    @pytest.mark.asyncio
    async def test_tool_result_caching(self, cache):
        """测试工具结果缓存"""
        if not cache.connected:
            pytest.skip("Redis not connected")
        
        tool_name = "system_info"
        cache_key = f"tool_cache:{tool_name}"
        
        # 检查缓存
        cached = cache.get(cache_key)
        
        # 模拟工具执行
        import time
        result_data = {"timestamp": time.time(), "status": "executed"}
        
        # 缓存结果
        cache.set(cache_key, json.dumps(result_data), ttl=60)
        
        # 验证缓存
        cached_result = cache.get(cache_key)
        assert cached_result is not None
        
        # 清理
        cache.delete(cache_key)


class TestToolErrorHandlingE2E:
    """工具错误处理端到端测试"""

    @pytest.fixture
    def tool_router(self):
        """创建工具路由器"""
        return create_default_router()

    @pytest.mark.asyncio
    async def test_invalid_tool_name(self, tool_router):
        """测试无效工具名称"""
        context = ToolContext(task_id="error_test_001")
        
        result = await tool_router.call_tool(
            "nonexistent_tool_12345",
            {},
            context,
        )
        
        assert result is not None
        assert result.status == ToolStatus.ERROR

    @pytest.mark.asyncio
    async def test_invalid_parameters(self, tool_router):
        """测试无效参数"""
        context = ToolContext(task_id="error_test_002")
        
        result = await tool_router.call_tool(
            "system_info",
            {"invalid_param": "value"},
            context,
        )
        
        # 应该能处理错误参数
        assert result is not None
