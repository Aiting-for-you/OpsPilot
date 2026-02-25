"""
通知 MCP 工具测试

测试 NotificationServer 的所有工具
"""
import pytest

from opspilot.tools.notification import NotificationServer, create_notification_server
from opspilot.tools.base import ToolContext


@pytest.fixture
def notification_server():
    """创建通知 Server"""
    return create_notification_server(default_sender="TestOpsPilot")


@pytest.fixture
def context():
    """创建工具上下文"""
    return ToolContext(task_id="test-task-001", user_id="test-user")


class TestEmailNotification:
    """邮件通知测试"""

    @pytest.mark.asyncio
    async def test_send_email_basic(self, notification_server, context):
        """测试发送基本邮件"""
        result = await notification_server.execute_tool(
            "send_email",
            {
                "to": "test@example.com",
                "subject": "测试邮件",
                "content": "这是一封测试邮件",
            },
            context,
        )
        
        assert result.is_success()
        assert result.data["channel"] == "email"
        assert result.data["to"] == "test@example.com"
        assert result.data["status"] == "sent"
        assert "notification_id" in result.data

    @pytest.mark.asyncio
    async def test_send_email_with_cc(self, notification_server, context):
        """测试发送带抄送的邮件"""
        result = await notification_server.execute_tool(
            "send_email",
            {
                "to": "test@example.com",
                "subject": "测试邮件",
                "content": "这是一封测试邮件",
                "cc": "cc1@example.com,cc2@example.com",
                "priority": "high",
            },
            context,
        )
        
        assert result.is_success()
        assert result.data["cc"] == "cc1@example.com,cc2@example.com"


class TestSMSNotification:
    """短信通知测试"""

    @pytest.mark.asyncio
    async def test_send_sms_basic(self, notification_server, context):
        """测试发送基本短信"""
        result = await notification_server.execute_tool(
            "send_sms",
            {
                "phone": "13800138000",
                "content": "您的验证码是：123456",
            },
            context,
        )
        
        assert result.is_success()
        assert result.data["channel"] == "sms"
        assert result.data["phone"] == "13800138000"
        assert result.data["status"] == "sent"

    @pytest.mark.asyncio
    async def test_send_sms_with_template(self, notification_server, context):
        """测试使用模板发送短信"""
        result = await notification_server.execute_tool(
            "send_sms",
            {
                "phone": "13800138000",
                "content": "",
                "template_code": "SMS_123456",
                "template_params": {"code": "123456"},
            },
            context,
        )
        
        assert result.is_success()


class TestWeComNotification:
    """企业微信通知测试"""

    @pytest.mark.asyncio
    async def test_send_wecom_text(self, notification_server, context):
        """测试发送文本消息"""
        result = await notification_server.execute_tool(
            "send_wecom",
            {
                "to_user": "zhangsan",
                "content": "这是一条企业微信消息",
                "msg_type": "text",
            },
            context,
        )
        
        assert result.is_success()
        assert result.data["channel"] == "wecom"
        assert result.data["to_user"] == "zhangsan"
        assert result.data["msg_type"] == "text"

    @pytest.mark.asyncio
    async def test_send_wecom_markdown(self, notification_server, context):
        """测试发送 Markdown 消息"""
        result = await notification_server.execute_tool(
            "send_wecom",
            {
                "to_user": "lisi",
                "content": "## 标题\n\n这是 Markdown 内容",
                "msg_type": "markdown",
                "mentioned_list": ["@all"],
            },
            context,
        )
        
        assert result.is_success()
        assert result.data["msg_type"] == "markdown"
        assert "@all" in result.data["mentioned_list"]


class TestInboxNotification:
    """站内信测试"""

    @pytest.mark.asyncio
    async def test_send_inbox_message(self, notification_server, context):
        """测试发送站内信"""
        result = await notification_server.execute_tool(
            "send_inbox_message",
            {
                "to_user": "wangwu",
                "title": "系统通知",
                "content": "您有一条新消息",
                "priority": "high",
                "action_url": "/orders/123",
            },
            context,
        )
        
        assert result.is_success()
        assert result.data["channel"] == "inbox"
        assert result.data["to_user"] == "wangwu"
        assert result.data["title"] == "系统通知"


class TestTemplatedNotification:
    """模板通知测试"""

    @pytest.mark.asyncio
    async def test_send_order_created_notification(self, notification_server, context):
        """测试订单创建通知"""
        result = await notification_server.execute_tool(
            "send_templated_notification",
            {
                "template_name": "order_created",
                "recipient": "buyer@example.com",
                "template_params": {
                    "recipient_name": "张先生",
                    "order_id": "ORD2026021701",
                    "supplier_name": "华南电子科技",
                    "total_amount": 8500.00,
                    "status": "待审批",
                    "extra_message": "订单金额超过10000元，需要经理审批",
                },
                "channels": ["email", "wecom"],
            },
            context,
        )
        
        assert result.is_success()
        assert result.data["template_name"] == "order_created"
        assert len(result.data["channels"]) == 2
        assert len(result.data["results"]) == 2

    @pytest.mark.asyncio
    async def test_send_logistics_update_notification(self, notification_server, context):
        """测试物流更新通知"""
        result = await notification_server.execute_tool(
            "send_templated_notification",
            {
                "template_name": "logistics_update",
                "recipient": "13800138000",
                "template_params": {
                    "recipient_name": "李先生",
                    "tracking_no": "SF1234567890123",
                    "carrier": "顺丰速运",
                    "status": "运输中",
                    "location": "杭州转运中心",
                    "timeline_summary": "预计明日送达",
                },
                "channels": ["sms"],
            },
            context,
        )
        
        assert result.is_success()
        assert result.data["template_name"] == "logistics_update"

    @pytest.mark.asyncio
    async def test_send_templated_notification_invalid_template(self, notification_server, context):
        """测试无效模板"""
        result = await notification_server.execute_tool(
            "send_templated_notification",
            {
                "template_name": "invalid_template",
                "recipient": "test@example.com",
                "template_params": {},
                "channels": ["email"],
            },
            context,
        )
        
        assert not result.is_success()
        assert result.error_code == "TEMPLATE_NOT_FOUND"


class TestBatchNotification:
    """批量通知测试"""

    @pytest.mark.asyncio
    async def test_send_batch_notification(self, notification_server, context):
        """测试批量发送通知"""
        result = await notification_server.execute_tool(
            "send_batch_notification",
            {
                "recipients": [
                    "user1@example.com",
                    "user2@example.com",
                    "user3@example.com",
                ],
                "subject": "批量通知测试",
                "content": "这是批量发送的通知",
                "channel": "email",
            },
            context,
        )
        
        assert result.is_success()
        assert result.data["total"] == 3
        assert len(result.data["results"]) == 3


class TestNotificationQuery:
    """通知查询测试"""

    @pytest.mark.asyncio
    async def test_get_notification_status(self, notification_server, context):
        """测试查询通知状态"""
        # 先发送一个通知
        send_result = await notification_server.execute_tool(
            "send_email",
            {
                "to": "query@example.com",
                "subject": "查询测试",
                "content": "测试内容",
            },
            context,
        )
        
        notification_id = send_result.data["notification_id"]
        
        # 查询状态
        result = await notification_server.execute_tool(
            "get_notification_status",
            {"notification_id": notification_id},
            context,
        )
        
        assert result.is_success()
        assert result.data["notification_id"] == notification_id
        assert result.data["status"] == "sent"

    @pytest.mark.asyncio
    async def test_get_notification_not_found(self, notification_server, context):
        """测试查询不存在的通知"""
        result = await notification_server.execute_tool(
            "get_notification_status",
            {"notification_id": "NOT_EXIST"},
            context,
        )
        
        assert not result.is_success()
        assert result.error_code == "NOTIFICATION_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_list_notifications(self, notification_server, context):
        """测试列出通知记录"""
        # 先发送几个通知
        await notification_server.execute_tool(
            "send_email",
            {"to": "list1@example.com", "subject": "测试1", "content": "内容1"},
            context,
        )
        await notification_server.execute_tool(
            "send_sms",
            {"phone": "13900139000", "content": "测试短信"},
            context,
        )
        
        # 列出通知
        result = await notification_server.execute_tool(
            "list_notifications",
            {"limit": 10},
            context,
        )
        
        assert result.is_success()
        assert result.data["total"] > 0

    @pytest.mark.asyncio
    async def test_list_notifications_by_channel(self, notification_server, context):
        """测试按渠道筛选通知"""
        result = await notification_server.execute_tool(
            "list_notifications",
            {"channel": "email", "limit": 10},
            context,
        )
        
        assert result.is_success()
        for notification in result.data["notifications"]:
            assert notification["channel"] == "email"


class TestServerHealth:
    """服务器健康检查测试"""

    @pytest.mark.asyncio
    async def test_health_check(self, notification_server):
        """测试健康检查"""
        result = await notification_server.health_check()
        assert result is True

    def test_server_name(self, notification_server):
        """测试服务器名称"""
        assert notification_server.name == "notification-tools"

    def test_server_has_tools(self, notification_server):
        """测试服务器注册了工具"""
        schemas = notification_server.get_all_schemas()
        assert len(schemas) > 0
        
        # 检查关键工具存在
        tool_names = [s.name for s in schemas]
        assert "send_email" in tool_names
        assert "send_sms" in tool_names
        assert "send_wecom" in tool_names
        assert "send_inbox_message" in tool_names
        assert "send_templated_notification" in tool_names
