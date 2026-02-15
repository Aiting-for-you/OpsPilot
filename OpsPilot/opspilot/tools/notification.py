"""
通知工具模块

提供邮件、钉钉、企业微信等通知 MCP 工具封装。

特性：
- 多渠道通知
- 模板支持
- 批量发送
- 发送记录
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

from opspilot.tools.base import (
    BaseToolServer,
    ToolSchema,
    ToolResult,
    ToolContext,
)


class NotificationChannel(Enum):
    """通知渠道"""
    EMAIL = "email"
    DINGTALK = "dingtalk"
    WECOM = "wecom"  # 企业微信
    WEBHOOK = "webhook"
    SLACK = "slack"


@dataclass
class NotificationConfig:
    """通知配置"""
    channel: NotificationChannel
    # Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_address: str = ""
    # DingTalk
    dingtalk_webhook: str = ""
    dingtalk_secret: str = ""
    # WeCom
    wecom_webhook: str = ""
    # Slack
    slack_webhook: str = ""


@dataclass
class NotificationResult:
    """通知发送结果"""
    success: bool
    channel: str
    message_id: str = ""
    error: str = ""
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "channel": self.channel,
            "message_id": self.message_id,
            "error": self.error,
            "timestamp": self.timestamp,
        }


@dataclass
class NotificationTemplate:
    """通知模板"""
    id: str
    name: str
    subject: str
    body: str
    variables: List[str] = field(default_factory=list)


# 预定义模板
NOTIFICATION_TEMPLATES: Dict[str, NotificationTemplate] = {
    "alert": NotificationTemplate(
        id="alert",
        name="告警通知",
        subject="【告警】{{alert_name}}",
        body="""
告警名称: {{alert_name}}
告警级别: {{severity}}
告警时间: {{timestamp}}
告警详情: {{details}}

请及时处理。
        """.strip(),
        variables=["alert_name", "severity", "timestamp", "details"],
    ),
    "order_created": NotificationTemplate(
        id="order_created",
        name="订单创建通知",
        subject="订单创建成功 - {{order_id}}",
        body="""
订单号: {{order_id}}
供应商: {{supplier_name}}
金额: {{amount}}
状态: {{status}}
创建时间: {{created_at}}
        """.strip(),
        variables=["order_id", "supplier_name", "amount", "status", "created_at"],
    ),
    "task_complete": NotificationTemplate(
        id="task_complete",
        name="任务完成通知",
        subject="任务完成 - {{task_name}}",
        body="""
任务名称: {{task_name}}
执行结果: {{result}}
耗时: {{duration}}
完成时间: {{completed_at}}
        """.strip(),
        variables=["task_name", "result", "duration", "completed_at"],
    ),
}


class NotificationSender:
    """
    通知发送器
    
    支持多种通知渠道。
    """
    
    def __init__(self, configs: List[NotificationConfig]):
        self.configs = {cfg.channel: cfg for cfg in configs}
        self._sent_messages: List[NotificationResult] = []
    
    async def send(
        self,
        channel: NotificationChannel,
        to: List[str],
        subject: str,
        body: str,
        **kwargs,
    ) -> NotificationResult:
        """
        发送通知
        
        Args:
            channel: 通知渠道
            to: 接收者列表
            subject: 主题
            body: 内容
        
        Returns:
            NotificationResult: 发送结果
        """
        if channel not in self.configs:
            return NotificationResult(
                success=False,
                channel=channel.value,
                error=f"渠道 {channel.value} 未配置",
            )
        
        config = self.configs[channel]
        
        try:
            if channel == NotificationChannel.EMAIL:
                result = await self._send_email(config, to, subject, body)
            elif channel == NotificationChannel.DINGTALK:
                result = await self._send_dingtalk(config, subject, body)
            elif channel == NotificationChannel.WECOM:
                result = await self._send_wecom(config, subject, body)
            elif channel == NotificationChannel.WEBHOOK:
                result = await self._send_webhook(config, subject, body)
            elif channel == NotificationChannel.SLACK:
                result = await self._send_slack(config, subject, body)
            else:
                result = NotificationResult(
                    success=False,
                    channel=channel.value,
                    error="不支持的通知渠道",
                )
            
            self._sent_messages.append(result)
            return result
        
        except Exception as e:
            result = NotificationResult(
                success=False,
                channel=channel.value,
                error=str(e),
            )
            self._sent_messages.append(result)
            return result
    
    async def _send_email(
        self,
        config: NotificationConfig,
        to: List[str],
        subject: str,
        body: str,
    ) -> NotificationResult:
        """发送邮件"""
        # Mock 实现
        message_id = f"email-{int(time.time() * 1000)}"
        
        # 真实实现需要 aiosmtplib
        # import aiosmtplib
        # from email.mime.text import MIMEText
        # from email.mime.multipart import MIMEMultipart
        
        return NotificationResult(
            success=True,
            channel="email",
            message_id=message_id,
        )
    
    async def _send_dingtalk(
        self,
        config: NotificationConfig,
        subject: str,
        body: str,
    ) -> NotificationResult:
        """发送钉钉消息"""
        import hmac
        import base64
        import urllib.parse
        
        message_id = f"dingtalk-{int(time.time() * 1000)}"
        
        # 构建签名
        if config.dingtalk_secret:
            timestamp = str(round(time.time() * 1000))
            string_to_sign = f"{timestamp}\n{config.dingtalk_secret}"
            hmac_code = hmac.new(
                config.dingtalk_secret.encode(),
                string_to_sign.encode(),
                digestmod=hashlib.sha256,
            ).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            webhook_url = f"{config.dingtalk_webhook}&timestamp={timestamp}&sign={sign}"
        else:
            webhook_url = config.dingtalk_webhook
        
        # Mock 发送
        # 真实实现: import httpx; await httpx.post(webhook_url, json=message)
        
        return NotificationResult(
            success=True,
            channel="dingtalk",
            message_id=message_id,
        )
    
    async def _send_wecom(
        self,
        config: NotificationConfig,
        subject: str,
        body: str,
    ) -> NotificationResult:
        """发送企业微信消息"""
        message_id = f"wecom-{int(time.time() * 1000)}"
        
        # Mock 发送
        # 真实实现: import httpx; await httpx.post(config.wecom_webhook, json=message)
        
        return NotificationResult(
            success=True,
            channel="wecom",
            message_id=message_id,
        )
    
    async def _send_webhook(
        self,
        config: NotificationConfig,
        subject: str,
        body: str,
    ) -> NotificationResult:
        """发送 Webhook"""
        message_id = f"webhook-{int(time.time() * 1000)}"
        
        # Mock 发送
        
        return NotificationResult(
            success=True,
            channel="webhook",
            message_id=message_id,
        )
    
    async def _send_slack(
        self,
        config: NotificationConfig,
        subject: str,
        body: str,
    ) -> NotificationResult:
        """发送 Slack 消息"""
        message_id = f"slack-{int(time.time() * 1000)}"
        
        # Mock 发送
        # 真实实现: import httpx; await httpx.post(config.slack_webhook, json=message)
        
        return NotificationResult(
            success=True,
            channel="slack",
            message_id=message_id,
        )
    
    def get_sent_messages(self, limit: int = 100) -> List[NotificationResult]:
        """获取发送记录"""
        return self._sent_messages[-limit:]


class NotificationServer(BaseToolServer):
    """
    通知 MCP Server
    
    提供多渠道通知发送工具。
    """
    
    def __init__(
        self,
        configs: Optional[List[NotificationConfig]] = None,
    ):
        super().__init__(
            name="notification-tools",
            description="通知工具集：邮件、钉钉、企业微信"
        )
        
        self.sender = NotificationSender(configs or [])
        
        self._register_tools()
    
    def _register_tools(self):
        """注册所有通知工具"""
        
        # 发送通知
        @self.register_tool(ToolSchema(
            name="send_notification",
            description="发送通知",
            input_schema={
                "type": "object",
                "required": ["channel", "subject", "body"],
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "通知渠道",
                        "enum": ["email", "dingtalk", "wecom", "webhook", "slack"]
                    },
                    "to": {
                        "type": "array",
                        "description": "接收者列表（邮件地址或用户ID）",
                        "items": {"type": "string"}
                    },
                    "subject": {
                        "type": "string",
                        "description": "通知主题"
                    },
                    "body": {
                        "type": "string",
                        "description": "通知内容"
                    }
                }
            }
        ))
        async def send_notification(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            channel = NotificationChannel(params.get("channel", "email"))
            to = params.get("to", [])
            subject = params.get("subject", "")
            body = params.get("body", "")
            
            result = await self.sender.send(channel, to, subject, body)
            
            if result.success:
                return ToolResult.success(result.to_dict())
            else:
                return ToolResult.error(result.error, error_code="SEND_ERROR")
        
        # 使用模板发送
        @self.register_tool(ToolSchema(
            name="send_template_notification",
            description="使用模板发送通知",
            input_schema={
                "type": "object",
                "required": ["template_id", "channel", "variables"],
                "properties": {
                    "template_id": {
                        "type": "string",
                        "description": "模板ID"
                    },
                    "channel": {
                        "type": "string",
                        "description": "通知渠道",
                        "enum": ["email", "dingtalk", "wecom", "webhook", "slack"]
                    },
                    "to": {
                        "type": "array",
                        "description": "接收者列表",
                        "items": {"type": "string"}
                    },
                    "variables": {
                        "type": "object",
                        "description": "模板变量"
                    }
                }
            }
        ))
        async def send_template_notification(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            template_id = params.get("template_id")
            channel = NotificationChannel(params.get("channel", "email"))
            to = params.get("to", [])
            variables = params.get("variables", {})
            
            # 获取模板
            template = NOTIFICATION_TEMPLATES.get(template_id)
            if not template:
                return ToolResult.error(
                    f"模板不存在: {template_id}",
                    error_code="TEMPLATE_NOT_FOUND",
                )
            
            # 渲染模板
            subject = template.subject
            body = template.body
            
            for key, value in variables.items():
                subject = subject.replace(f"{{{{{key}}}}}", str(value))
                body = body.replace(f"{{{{{key}}}}}", str(value))
            
            result = await self.sender.send(channel, to, subject, body)
            
            if result.success:
                return ToolResult.success(result.to_dict())
            else:
                return ToolResult.error(result.error, error_code="SEND_ERROR")
        
        # 批量发送
        @self.register_tool(ToolSchema(
            name="batch_send_notification",
            description="批量发送通知",
            input_schema={
                "type": "object",
                "required": ["notifications"],
                "properties": {
                    "notifications": {
                        "type": "array",
                        "description": "通知列表",
                        "items": {
                            "type": "object",
                            "required": ["channel", "subject", "body"],
                            "properties": {
                                "channel": {"type": "string"},
                                "to": {"type": "array", "items": {"type": "string"}},
                                "subject": {"type": "string"},
                                "body": {"type": "string"}
                            }
                        }
                    }
                }
            }
        ))
        async def batch_send_notification(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            notifications = params.get("notifications", [])
            
            results = []
            for notif in notifications:
                channel = NotificationChannel(notif.get("channel", "email"))
                to = notif.get("to", [])
                subject = notif.get("subject", "")
                body = notif.get("body", "")
                
                result = await self.sender.send(channel, to, subject, body)
                results.append(result.to_dict())
            
            success_count = sum(1 for r in results if r["success"])
            
            return ToolResult.success({
                "total": len(notifications),
                "success": success_count,
                "failed": len(notifications) - success_count,
                "results": results,
            })
        
        # 获取发送记录
        @self.register_tool(ToolSchema(
            name="get_notification_history",
            description="获取通知发送记录",
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "返回数量",
                        "default": 20
                    }
                }
            }
        ))
        async def get_notification_history(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            limit = params.get("limit", 20)
            messages = self.sender.get_sent_messages(limit)
            
            return ToolResult.success({
                "total": len(messages),
                "messages": [m.to_dict() for m in messages],
            })
        
        # 获取模板列表
        @self.register_tool(ToolSchema(
            name="list_notification_templates",
            description="获取通知模板列表",
            input_schema={
                "type": "object",
                "properties": {}
            }
        ))
        async def list_notification_templates(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            templates = [
                {
                    "id": t.id,
                    "name": t.name,
                    "subject": t.subject,
                    "variables": t.variables,
                }
                for t in NOTIFICATION_TEMPLATES.values()
            ]
            
            return ToolResult.success({
                "templates": templates,
                "total": len(templates),
            })
    
    async def health_check(self) -> bool:
        """健康检查"""
        return True


# 便捷函数
def create_notification_server(
    configs: Optional[List[NotificationConfig]] = None,
) -> NotificationServer:
    """创建通知 Server"""
    return NotificationServer(configs)
