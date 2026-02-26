"""
MCP 工具测试模块

测试所有新增的 MCP 工具：
- DatabaseServer
- ApiServer
- DevOpsServer
- FileServer
- NotificationServer
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from opspilot.tools.database import (
    DatabaseServer,
    DatabaseConfig,
    MockDatabaseConnection,
    validate_sql,
)
from opspilot.tools.http_client import (
    ApiServer,
    RequestConfig,
    AuthConfig,
    HttpClient,
    HttpMethod,
)
from opspilot.tools.devops import (
    DevOpsServer,
    CommandExecutor,
)
from opspilot.tools.file_ops import (
    FileServer,
    FileOperations,
    LogParser,
)
from opspilot.tools.notification import (
    NotificationServer,
    NotificationConfig,
    NotificationChannel,
)
from opspilot.tools.base import ToolContext


# ==================== 数据库工具测试 ====================

class TestDatabaseTools:
    """数据库工具测试"""
    
    @pytest.fixture
    def db_server(self):
        """创建数据库 Server"""
        return DatabaseServer(db_type="mock")
    
    @pytest.fixture
    def context(self):
        """创建工具上下文"""
        return ToolContext(task_id="test-task")
    
    @pytest.mark.asyncio
    async def test_validate_sql_safe(self):
        """测试 SQL 安全验证 - 安全 SQL"""
        is_safe, error = validate_sql("SELECT * FROM users", ["SELECT"])
        assert is_safe is True
        assert error == ""
    
    @pytest.mark.asyncio
    async def test_validate_sql_injection(self):
        """测试 SQL 安全验证 - 注入检测"""
        is_safe, error = validate_sql("SELECT * FROM users; DROP TABLE users", ["SELECT"])
        assert is_safe is False
        assert "SQL 注入" in error
    
    @pytest.mark.asyncio
    async def test_validate_sql_blocked_command(self):
        """测试 SQL 安全验证 - 禁止命令"""
        is_safe, error = validate_sql("DELETE FROM users", ["SELECT"])
        assert is_safe is False
        assert "不允许" in error
    
    @pytest.mark.asyncio
    async def test_mock_connection_connect(self):
        """测试 Mock 连接"""
        conn = MockDatabaseConnection(DatabaseConfig())
        result = await conn.connect()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_mock_connection_select(self):
        """测试 Mock 查询"""
        conn = MockDatabaseConnection(DatabaseConfig())
        await conn.connect()
        
        result = await conn.execute("SELECT * FROM users")
        assert result.success is True
        assert result.row_count > 0
        assert "id" in result.columns
    
    @pytest.mark.asyncio
    async def test_mock_connection_insert(self):
        """测试 Mock 插入"""
        conn = MockDatabaseConnection(DatabaseConfig())
        await conn.connect()
        
        result = await conn.execute(
            "INSERT INTO users (name, email) VALUES (:name, :email)",
            {"name": "测试用户", "email": "test@example.com"}
        )
        assert result.success is True
        assert result.affected_rows == 1
    
    @pytest.mark.asyncio
    async def test_db_query_tool(self, db_server, context):
        """测试 db_query 工具"""
        # 获取工具
        tool = db_server.get_tool("db_query")
        assert tool is not None
        
        # 执行查询
        result = await tool.handler({"sql": "SELECT * FROM users"}, context)
        assert result.is_success()
    
    @pytest.mark.asyncio
    async def test_db_execute_tool(self, db_server, context):
        """测试 db_execute 工具"""
        tool = db_server.get_tool("db_execute")
        assert tool is not None
        
        result = await tool.handler(
            {"sql": "INSERT INTO users (name, email) VALUES (:name, :email)", "params": {"name": "测试", "email": "test@test.com"}},
            context
        )
        assert result.is_success()
    
    @pytest.mark.asyncio
    async def test_db_describe_table_tool(self, db_server, context):
        """测试 db_describe_table 工具"""
        tool = db_server.get_tool("db_describe_table")
        assert tool is not None
        
        result = await tool.handler({"table": "users"}, context)
        assert result.is_success()
        data = result.data
        assert "columns" in data


# ==================== HTTP API 工具测试 ====================

class TestHttpTools:
    """HTTP API 工具测试"""
    
    @pytest.fixture
    def api_server(self):
        """创建 API Server"""
        return ApiServer(base_url="https://api.example.com")
    
    @pytest.fixture
    def context(self):
        """创建工具上下文"""
        return ToolContext(task_id="test-task")
    
    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_http_client_mock_get(self, mock_httpx_client):
        """测试 HTTP 客户端 Mock GET"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = [{"id": 1, "name": "test"}]
        
        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_httpx_client.return_value.__aenter__.return_value = mock_client
        
        client = HttpClient(cache_enabled=False)
        response = await client.request(
            method=HttpMethod.GET,
            url="https://api.example.com/users",
        )
        assert response.success is True
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_http_get_tool(self, mock_httpx_client, api_server, context):
        """测试 http_get 工具"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = [{"id": 1, "name": "test"}]
        
        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_httpx_client.return_value.__aenter__.return_value = mock_client
        
        tool = api_server.get_tool("http_get")
        assert tool is not None
        
        result = await tool.handler({"url": "/users"}, context)
        assert result.is_success()
    
    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_http_post_tool(self, mock_httpx_client, api_server, context):
        """测试 http_post 工具"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"id": 1, "name": "测试"}
        
        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_httpx_client.return_value.__aenter__.return_value = mock_client
        
        tool = api_server.get_tool("http_post")
        assert tool is not None
        
        result = await tool.handler(
            {"url": "/users", "body": {"name": "测试"}},
            context
        )
        assert result.is_success()
    
    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_graphql_query_tool(self, mock_httpx_client, api_server, context):
        """测试 graphql_query 工具"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"data": {"users": [{"id": 1, "name": "test"}]}}
        
        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_httpx_client.return_value.__aenter__.return_value = mock_client
        
        tool = api_server.get_tool("graphql_query")
        assert tool is not None
        
        result = await tool.handler(
            {
                "url": "/graphql",
                "query": "{ users { id name } }"
            },
            context
        )
        assert result.is_success()
    
    @pytest.mark.asyncio
    async def test_http_batch_tool(self, api_server, context):
        """测试 http_batch 工具"""
        tool = api_server.get_tool("http_batch")
        assert tool is not None
        
        result = await tool.handler(
            {
                "requests": [
                    {"method": "GET", "url": "/users"},
                    {"method": "GET", "url": "/products"},
                ]
            },
            context
        )
        assert result.is_success()
        data = result.data
        assert data["total"] == 2


# ==================== 运维工具测试 ====================

class TestDevOpsTools:
    """运维工具测试"""
    
    @pytest.fixture
    def devops_server(self):
        """创建运维 Server"""
        return DevOpsServer()
    
    @pytest.fixture
    def context(self):
        """创建工具上下文"""
        return ToolContext(task_id="test-task")
    
    def test_command_validator_safe(self):
        """测试命令验证器 - 安全命令"""
        executor = CommandExecutor()
        is_valid, _ = executor.validate_command("kubectl get pods")
        assert is_valid is True
    
    def test_command_validator_blocked(self):
        """测试命令验证器 - 阻止危险命令"""
        executor = CommandExecutor()
        is_valid, error = executor.validate_command("rm -rf /")
        assert is_valid is False
        assert "禁止" in error
    
    def test_command_validator_not_in_whitelist(self):
        """测试命令验证器 - 白名单外命令"""
        executor = CommandExecutor()
        is_valid, error = executor.validate_command("some-random-command")
        assert is_valid is False
        assert "白名单" in error
    
    @pytest.mark.asyncio
    async def test_system_info_tool(self, devops_server, context):
        """测试 system_info 工具"""
        tool = devops_server.get_tool("system_info")
        assert tool is not None
        
        result = await tool.handler({}, context)
        assert result.is_success()
        data = result.data
        assert "hostname" in data
        assert "os" in data
    
    @pytest.mark.asyncio
    async def test_system_cpu_tool(self, devops_server, context):
        """测试 system_cpu 工具"""
        tool = devops_server.get_tool("system_cpu")
        assert tool is not None
        
        result = await tool.handler({}, context)
        assert result.is_success()
        data = result.data
        assert "usage_percent" in data
    
    @pytest.mark.asyncio
    async def test_system_memory_tool(self, devops_server, context):
        """测试 system_memory 工具"""
        tool = devops_server.get_tool("system_memory")
        assert tool is not None
        
        result = await tool.handler({}, context)
        assert result.is_success()
        data = result.data
        assert "total_mb" in data
        assert "usage_percent" in data


# ==================== 文件工具测试 ====================

class TestFileTools:
    """文件工具测试"""
    
    @pytest.fixture
    def file_server(self, tmp_path):
        """创建文件 Server"""
        return FileServer(base_path=str(tmp_path))
    
    @pytest.fixture
    def context(self):
        """创建工具上下文"""
        return ToolContext(task_id="test-task")
    
    @pytest.mark.asyncio
    async def test_file_write_and_read(self, file_server, context, tmp_path):
        """测试文件写入和读取"""
        # 写入
        write_tool = file_server.get_tool("file_write")
        result = await write_tool.handler(
            {"path": "test.txt", "content": "Hello, World!"},
            context
        )
        assert result.is_success()
        
        # 读取
        read_tool = file_server.get_tool("file_read")
        result = await read_tool.handler({"path": "test.txt"}, context)
        assert result.is_success()
        assert "Hello, World!" in result.data["data"]["content"]
    
    @pytest.mark.asyncio
    async def test_file_list(self, file_server, context, tmp_path):
        """测试文件列表"""
        # 创建测试文件
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        
        tool = file_server.get_tool("file_list")
        result = await tool.handler({"path": "."}, context)
        assert result.is_success()
        assert result.data["total"] >= 2
    
    @pytest.mark.asyncio
    async def test_file_search(self, file_server, context, tmp_path):
        """测试文件搜索"""
        # 创建测试文件
        (tmp_path / "test.txt").write_text("line1\nerror line\nline3\nerror again\nline5")
        
        tool = file_server.get_tool("file_search")
        result = await tool.handler(
            {"path": "test.txt", "pattern": "error"},
            context
        )
        assert result.is_success()
        assert result.data["data"]["total_matches"] == 2
    
    @pytest.mark.asyncio
    async def test_log_parse(self, file_server, context):
        """测试日志解析"""
        tool = file_server.get_tool("log_parse")
        
        log_content = '{"level": "INFO", "message": "test"}\n{"level": "ERROR", "message": "error test"}'
        result = await tool.handler(
            {"content": log_content, "format": "json"},
            context
        )
        assert result.is_success()
        assert result.data["total_lines"] == 2
    
    @pytest.mark.asyncio
    async def test_log_analyze(self, file_server, context):
        """测试日志分析"""
        tool = file_server.get_tool("log_analyze")
        
        log_content = "INFO: started\nERROR: failed\nWARNING: check this\nINFO: done"
        result = await tool.handler({"content": log_content}, context)
        assert result.is_success()
        assert result.data["error_count"] == 1
        assert result.data["warning_count"] == 1


# ==================== 通知工具测试 ====================

class TestNotificationTools:
    """通知工具测试"""
    
    @pytest.fixture
    def notification_server(self):
        """创建通知 Server"""
        return NotificationServer(configs=[
            NotificationConfig(channel=NotificationChannel.DINGTALK, dingtalk_webhook="https://oapi.dingtalk.com/robot/send?access_token=test"),
            NotificationConfig(channel=NotificationChannel.WECOM, wecom_webhook="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test"),
        ])
    
    @pytest.fixture
    def context(self):
        """创建工具上下文"""
        return ToolContext(task_id="test-task")
    
    @pytest.mark.asyncio
    async def test_send_notification(self, notification_server, context):
        """测试发送通知"""
        tool = notification_server.get_tool("send_notification")
        assert tool is not None
        
        result = await tool.handler(
            {
                "channel": "dingtalk",
                "subject": "测试通知",
                "body": "这是一条测试通知"
            },
            context
        )
        assert result.is_success()
    
    @pytest.mark.asyncio
    async def test_send_template_notification(self, notification_server, context):
        """测试模板通知"""
        tool = notification_server.get_tool("send_templated_notification")
        assert tool is not None
        
        result = await tool.handler(
            {
                "template_name": "alert",
                "recipient": "admin@example.com",
                "template_params": {
                    "alert_name": "CPU 告警",
                    "severity": "高",
                    "timestamp": "2024-01-01 12:00:00",
                    "details": "CPU 使用率超过 90%"
                },
                "channels": ["dingtalk"]
            },
            context
        )
        assert result.is_success()
    
    @pytest.mark.asyncio
    async def test_batch_send_notification(self, notification_server, context):
        """测试批量发送"""
        tool = notification_server.get_tool("send_batch_notification")
        assert tool is not None
        
        result = await tool.handler(
            {
                "recipients": ["user1@example.com", "user2@example.com"],
                "subject": "批量通知",
                "content": "这是批量发送的内容"
            },
            context
        )
        assert result.is_success()
        assert result.data["total"] == 2
    
    @pytest.mark.asyncio
    async def test_list_templates(self, notification_server, context):
        """测试模板列表"""
        tool = notification_server.get_tool("list_notification_templates")
        assert tool is not None
        
        result = await tool.handler({}, context)
        assert result.is_success()
        assert result.data["total"] >= 1


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
