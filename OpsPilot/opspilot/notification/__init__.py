"""
通知模块

支持多种通知方式：
- Webhook通知
- Slack通知
- 邮件通知（可选）
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import aiohttp

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """通知类型"""
    APPROVAL_REQUEST = "approval_request"     # 审批请求
    APPROVAL_APPROVED = "approval_approved"   # 审批通过
    APPROVAL_REJECTED = "approval_rejected"   # 审批拒绝
    SYSTEM_ALERT = "system_alert"             # 系统告警
    TASK_COMPLETED = "task_completed"         # 任务完成


@dataclass
class NotificationMessage:
    """通知消息"""
    type: NotificationType
    title: str
    content: str
    request_id: Optional[str] = None
    tool_name: Optional[str] = None
    requester: Optional[str] = None
    approver: Optional[str] = None
    level: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class NotificationService:
    """
    通知服务
    
    支持Webhook和Slack通知
    """
    
    def __init__(
        self,
        webhook_url: Optional[str] = None,
        slack_token: Optional[str] = None,
        slack_channel: Optional[str] = None,
        smtp_config: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化通知服务
        
        Args:
            webhook_url: Webhook URL
            slack_token: Slack Bot User OAuth Token
            slack_channel: Slack频道ID
            smtp_config: SMTP配置 {host, port, username, password, from_addr}
        """
        self.webhook_url = webhook_url
        self.slack_token = slack_token
        self.slack_channel = slack_channel
        self.smtp_config = smtp_config
    
    def is_configured(self) -> bool:
        """检查是否配置了任何通知方式"""
        return bool(
            self.webhook_url or 
            self.slack_token or 
            self.smtp_config
        )
    
    async def send_notification(self, message: NotificationMessage) -> bool:
        """
        发送通知
        
        Args:
            message: 通知消息
            
        Returns:
            是否发送成功
        """
        if not self.is_configured():
            logger.debug("通知服务未配置，跳过发送")
            return False
        
        success = True
        
        # 发送Webhook通知
        if self.webhook_url:
            try:
                await self._send_webhook(message)
            except Exception as e:
                logger.error(f"Webhook通知发送失败: {e}")
                success = False
        
        # 发送Slack通知
        if self.slack_token:
            try:
                await self._send_slack(message)
            except Exception as e:
                logger.error(f"Slack通知发送失败: {e}")
                success = False
        
        # 发送邮件通知
        if self.smtp_config:
            try:
                await self._send_email(message)
            except Exception as e:
                logger.error(f"邮件通知发送失败: {e}")
                success = False
        
        return success
    
    async def _send_webhook(self, message: NotificationMessage) -> bool:
        """发送Webhook通知"""
        if not self.webhook_url:
            return False
        
        payload = {
            "type": message.type.value,
            "title": message.title,
            "content": message.content,
            "request_id": message.request_id,
            "tool_name": message.tool_name,
            "requester": message.requester,
            "timestamp": message.created_at.isoformat(),
            "metadata": message.metadata,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status < 400:
                        logger.info(f"Webhook通知发送成功: {message.title}")
                        return True
                    else:
                        logger.warning(f"Webhook响应状态码: {response.status}")
                        return False
        except asyncio.TimeoutError:
            logger.error("Webhook通知超时")
            return False
        except Exception as e:
            logger.error(f"Webhook通知发送错误: {e}")
            return False
    
    async def _send_slack(self, message: NotificationMessage) -> bool:
        """发送Slack通知"""
        if not self.slack_token or not self.slack_channel:
            return False
        
        # 构建Slack消息
        color = self._get_color_for_type(message.type)
        fields = self._build_slack_fields(message)
        
        payload = {
            "channel": self.slack_channel,
            "attachments": [{
                "color": color,
                "title": message.title,
                "text": message.content,
                "fields": fields,
                "footer": "OpsPilot Notification",
                "ts": int(message.created_at.timestamp()),
            }]
        }
        
        headers = {
            "Authorization": f"Bearer {self.slack_token}",
            "Content-Type": "application/json",
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://slack.com/api/chat.postMessage",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    result = await response.json()
                    if result.get("ok"):
                        logger.info(f"Slack通知发送成功: {message.title}")
                        return True
                    else:
                        logger.warning(f"Slack API错误: {result.get('error')}")
                        return False
        except Exception as e:
            logger.error(f"Slack通知发送错误: {e}")
            return False
    
    def _get_color_for_type(self, notification_type: NotificationType) -> str:
        """根据通知类型获取颜色"""
        color_map = {
            NotificationType.APPROVAL_REQUEST: "#FFA500",   # 橙色
            NotificationType.APPROVAL_APPROVED: "#00FF00",   # 绿色
            NotificationType.APPROVAL_REJECTED: "#FF0000",   # 红色
            NotificationType.SYSTEM_ALERT: "#FF0000",        # 红色
            NotificationType.TASK_COMPLETED: "#00FF00",      # 绿色
        }
        return color_map.get(notification_type, "#808080")
    
    def _build_slack_fields(self, message: NotificationMessage) -> List[Dict[str, str]]:
        """构建Slack消息字段"""
        fields = []
        
        if message.tool_name:
            fields.append({"title": "工具", "value": message.tool_name, "short": True})
        if message.requester:
            fields.append({"title": "请求人", "value": message.requester, "short": True})
        if message.approver:
            fields.append({"title": "审批人", "value": message.approver, "short": True})
        if message.level:
            fields.append({"title": "级别", "value": message.level, "short": True})
        if message.request_id:
            fields.append({"title": "请求ID", "value": message.request_id, "short": False})
        
        return fields
    
    async def _send_email(self, message: NotificationMessage) -> bool:
        """发送邮件通知"""
        if not self.smtp_config:
            return False
        
        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg["From"] = self.smtp_config.get("from_addr", "opsilot@example.com")
            msg["To"] = self.smtp_config.get("to_addrs", "")
            msg["Subject"] = f"[OpsPilot] {message.title}"
            
            body = f"""
{message.title}
{'=' * 40}

{message.content}

---
类型: {message.type.value}
时间: {message.created_at.strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            if message.tool_name:
                body += f"工具: {message.tool_name}\n"
            if message.requester:
                body += f"请求人: {message.requester}\n"
            if message.approver:
                body += f"审批人: {message.approver}\n"
            
            msg.attach(MIMEText(body, "plain", "utf-8"))
            
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_config.get("host", "smtp.example.com"),
                port=self.smtp_config.get("port", 587),
                username=self.smtp_config.get("username"),
                password=self.smtp_config.get("password"),
                start_tls=True,
            )
            
            logger.info(f"邮件通知发送成功: {message.title}")
            return True
            
        except ImportError:
            logger.warning("aiosmtplib未安装，邮件通知不可用")
            return False
        except Exception as e:
            logger.error(f"邮件通知发送错误: {e}")
            return False


# 全局通知服务实例
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> Optional[NotificationService]:
    """获取全局通知服务实例"""
    return _notification_service


def init_notification_service(
    webhook_url: Optional[str] = None,
    slack_token: Optional[str] = None,
    slack_channel: Optional[str] = None,
    smtp_config: Optional[Dict[str, Any]] = None,
) -> NotificationService:
    """
    初始化全局通知服务
    
    Args:
        webhook_url: Webhook URL
        slack_token: Slack Bot User OAuth Token
        slack_channel: Slack频道ID
        smtp_config: SMTP配置
        
    Returns:
        通知服务实例
    """
    global _notification_service
    
    _notification_service = NotificationService(
        webhook_url=webhook_url,
        slack_token=slack_token,
        slack_channel=slack_channel,
        smtp_config=smtp_config,
    )
    
    logger.info("通知服务初始化完成")
    return _notification_service


async def send_approval_notification(
    notification_type: NotificationType,
    request_id: str,
    tool_name: str,
    requester: str,
    approver: Optional[str] = None,
    level: str = "medium",
    reason: str = "",
) -> bool:
    """
    发送审批通知的便捷函数
    
    Args:
        notification_type: 通知类型
        request_id: 请求ID
        tool_name: 工具名称
        requester: 请求人
        approver: 审批人
        level: 审批级别
        reason: 原因
        
    Returns:
        是否发送成功
    """
    service = get_notification_service()
    if not service:
        return False
    
    title_map = {
        NotificationType.APPROVAL_REQUEST: f"新的审批请求: {tool_name}",
        NotificationType.APPROVAL_APPROVED: f"审批已通过: {tool_name}",
        NotificationType.APPROVAL_REJECTED: f"审批已拒绝: {tool_name}",
    }
    
    content_map = {
        NotificationType.APPROVAL_REQUEST: f"请求人 {requester} 请求执行 {tool_name}，请尽快审批。\n原因: {reason}",
        NotificationType.APPROVAL_APPROVED: f"工具 {tool_name} 的审批请求已通过。\n审批人: {approver}",
        NotificationType.APPROVAL_REJECTED: f"工具 {tool_name} 的审批请求已被拒绝。\n审批人: {approver}\n原因: {reason}",
    }
    
    message = NotificationMessage(
        type=notification_type,
        title=title_map.get(notification_type, "审批通知"),
        content=content_map.get(notification_type, ""),
        request_id=request_id,
        tool_name=tool_name,
        requester=requester,
        approver=approver,
        level=level,
    )
    
    return await service.send_notification(message)
