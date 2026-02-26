"""
通知推送 MCP Server

提供多种通知渠道：
- 邮件通知
- 短信通知
- 企业微信通知
- 站内信
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
import asyncio

from opspilot.tools.base import (
    BaseToolServer,
    ToolSchema,
    ToolResult,
    ToolContext,
)


# ==================== 通知记录存储 ====================

@dataclass
class NotificationRecord:
    """通知记录"""
    notification_id: str
    channel: str
    recipient: str
    subject: str
    content: str
    status: str = "sent"
    sent_at: str = ""
    error: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "notification_id": self.notification_id,
            "channel": self.channel,
            "recipient": self.recipient,
            "subject": self.subject,
            "content": self.content,
            "status": self.status,
            "sent_at": self.sent_at,
            "error": self.error,
        }


# 模拟通知记录存储
MOCK_NOTIFICATIONS: Dict[str, NotificationRecord] = {}


def generate_notification_id() -> str:
    """生成通知 ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"NOTIF{timestamp}{len(MOCK_NOTIFICATIONS) + 1:04d}"


# ==================== 通知模板 ====================

NOTIFICATION_TEMPLATES = {
    # 采购相关
    "order_created": {
        "subject": "采购订单创建成功 - {order_id}",
        "content": """
尊敬的 {recipient_name}：

您的采购订单已创建成功！

订单号：{order_id}
供应商：{supplier_name}
总金额：¥{total_amount:.2f}
状态：{status}

{extra_message}

请及时跟进订单进度。

OpsPilot 智能运维平台
""".strip(),
    },
    "order_approved": {
        "subject": "订单审批通过 - {order_id}",
        "content": """
尊敬的 {recipient_name}：

采购订单 {order_id} 已审批通过！

审批人：{approver}
审批时间：{approved_at}

订单将进入发货流程，请注意查收。

OpsPilot 智能运维平台
""".strip(),
    },
    "order_delayed": {
        "subject": "⚠️ 订单延迟预警 - {order_id}",
        "content": """
尊敬的 {recipient_name}：

采购订单 {order_id} 出现延迟！

原预计到货：{original_date}
新预计到货：{new_date}
延迟原因：{delay_reason}

请及时与供应商沟通或启动备选方案。

OpsPilot 智能运维平台
""".strip(),
    },
    # 合规相关
    "compliance_violation": {
        "subject": "🔴 合规违规预警 - {check_type}",
        "content": """
尊敬的 {recipient_name}：

检测到合规违规情况！

检查类型：{check_type}
违规规则：{violated_rules}
风险等级：{risk_level}

请立即处理，避免业务风险。

OpsPilot 智能运维平台
""".strip(),
    },
    "approval_required": {
        "subject": "📋 待审批通知 - {subject}",
        "content": """
尊敬的 {approver_name}：

您有一个待审批事项：

类型：{approval_type}
发起人：{initiator}
提交时间：{submitted_at}
金额：¥{amount:.2f}

请及时处理：{approval_link}

OpsPilot 智能运维平台
""".strip(),
    },
    # 物流相关
    "logistics_update": {
        "subject": "物流状态更新 - {tracking_no}",
        "content": """
尊敬的 {recipient_name}：

您的物流有新状态：

快递单号：{tracking_no}
快递公司：{carrier}
当前状态：{status}
当前位置：{location}

{timeline_summary}

OpsPilot 智能运维平台
""".strip(),
    },
    "customs_hold": {
        "subject": "⚠️ 海关扣留通知 - {declaration_no}",
        "content": """
尊敬的 {recipient_name}：

报关单 {declaration_no} 被海关扣留！

扣留原因：{hold_reason}
需补充资料：{required_docs}
截止时间：{deadline}

请尽快补充所需资料！

OpsPilot 智能运维平台
""".strip(),
    },
    # 系统通知
    "system_alert": {
        "subject": "系统告警 - {alert_type}",
        "content": """
系统告警通知：

告警类型：{alert_type}
告警级别：{severity}
告警时间：{alert_time}
告警内容：{alert_message}

{action_required}

OpsPilot 智能运维平台
""".strip(),
    },
    # 告警相关
    "alert": {
        "subject": "{alert_name} - 告警通知",
        "content": """
告警名称：{alert_name}
严重程度：{severity}
发生时间：{timestamp}

详细信息：{details}

请及时处理。

OpsPilot 智能运维平台
""".strip(),
    },
}


class NotificationServer(BaseToolServer):
    """
    通知推送 MCP Server
    
    提供邮件、短信、企业微信、站内信等通知渠道
    """
    
    def __init__(self, default_sender: str = "OpsPilot", configs: "Optional[List[NotificationConfig]]" = None):
        """
        初始化通知 Server
        
        Args:
            default_sender: 默认发送者名称
            configs: 通知配置列表
        """
        super().__init__(
            name="notification-tools",
            description="通知推送工具集：邮件、短信、企业微信、站内信"
        )
        self.default_sender = default_sender
        self.configs = configs or []
        self._register_tools()
    
    def _register_tools(self):
        """注册所有通知工具"""
        
        # ==================== 邮件通知 ====================
        
        @self.register_tool(ToolSchema(
            name="send_email",
            description="发送邮件通知",
            input_schema={
                "type": "object",
                "required": ["to", "subject", "content"],
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "收件人邮箱"
                    },
                    "subject": {
                        "type": "string",
                        "description": "邮件主题"
                    },
                    "content": {
                        "type": "string",
                        "description": "邮件内容"
                    },
                    "cc": {
                        "type": "string",
                        "description": "抄送人（多个用逗号分隔）"
                    },
                    "priority": {
                        "type": "string",
                        "description": "优先级：high/normal/low",
                        "default": "normal"
                    },
                    "attachments": {
                        "type": "array",
                        "description": "附件列表",
                        "items": {"type": "string"}
                    }
                }
            }
        ))
        async def send_email_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            to = params.get("to", "")
            subject = params.get("subject", "")
            content = params.get("content", "")
            cc = params.get("cc", "")
            priority = params.get("priority", "normal")
            
            # 模拟发送延迟
            await asyncio.sleep(0.1)
            
            # 生成通知记录
            notification_id = generate_notification_id()
            record = NotificationRecord(
                notification_id=notification_id,
                channel="email",
                recipient=to,
                subject=subject,
                content=content,
                status="sent",
                sent_at=datetime.now().isoformat(),
            )
            MOCK_NOTIFICATIONS[notification_id] = record
            
            return ToolResult.success({
                "notification_id": notification_id,
                "channel": "email",
                "to": to,
                "cc": cc,
                "subject": subject,
                "status": "sent",
                "sent_at": record.sent_at,
                "message": f"邮件已发送至 {to}",
            })
        
        # ==================== 短信通知 ====================
        
        @self.register_tool(ToolSchema(
            name="send_sms",
            description="发送短信通知",
            input_schema={
                "type": "object",
                "required": ["phone", "content"],
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "手机号码"
                    },
                    "content": {
                        "type": "string",
                        "description": "短信内容（最多500字）"
                    },
                    "template_code": {
                        "type": "string",
                        "description": "短信模板代码"
                    },
                    "template_params": {
                        "type": "object",
                        "description": "模板参数"
                    }
                }
            }
        ))
        async def send_sms_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            phone = params.get("phone", "")
            content = params.get("content", "")
            template_code = params.get("template_code", "")
            
            # 模拟发送延迟
            await asyncio.sleep(0.05)
            
            # 生成通知记录
            notification_id = generate_notification_id()
            record = NotificationRecord(
                notification_id=notification_id,
                channel="sms",
                recipient=phone,
                subject=f"短信模板: {template_code}" if template_code else "直接短信",
                content=content,
                status="sent",
                sent_at=datetime.now().isoformat(),
            )
            MOCK_NOTIFICATIONS[notification_id] = record
            
            return ToolResult.success({
                "notification_id": notification_id,
                "channel": "sms",
                "phone": phone,
                "status": "sent",
                "sent_at": record.sent_at,
                "message": f"短信已发送至 {phone}",
            })
        
        # ==================== 企业微信通知 ====================
        
        @self.register_tool(ToolSchema(
            name="send_wecom",
            description="发送企业微信消息",
            input_schema={
                "type": "object",
                "required": ["to_user", "content"],
                "properties": {
                    "to_user": {
                        "type": "string",
                        "description": "接收人用户ID或群聊webhook"
                    },
                    "content": {
                        "type": "string",
                        "description": "消息内容"
                    },
                    "msg_type": {
                        "type": "string",
                        "description": "消息类型：text/markdown/card",
                        "default": "markdown"
                    },
                    "mentioned_list": {
                        "type": "array",
                        "description": "@人员列表",
                        "items": {"type": "string"}
                    }
                }
            }
        ))
        async def send_wecom_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            to_user = params.get("to_user", "")
            content = params.get("content", "")
            msg_type = params.get("msg_type", "markdown")
            mentioned_list = params.get("mentioned_list", [])
            
            # 模拟发送延迟
            await asyncio.sleep(0.08)
            
            # 生成通知记录
            notification_id = generate_notification_id()
            record = NotificationRecord(
                notification_id=notification_id,
                channel="wecom",
                recipient=to_user,
                subject=f"企业微信-{msg_type}",
                content=content,
                status="sent",
                sent_at=datetime.now().isoformat(),
            )
            MOCK_NOTIFICATIONS[notification_id] = record
            
            return ToolResult.success({
                "notification_id": notification_id,
                "channel": "wecom",
                "to_user": to_user,
                "msg_type": msg_type,
                "mentioned_list": mentioned_list,
                "status": "sent",
                "sent_at": record.sent_at,
                "message": f"企业微信消息已发送至 {to_user}",
            })
        
        # ==================== 站内信 ====================
        
        @self.register_tool(ToolSchema(
            name="send_inbox_message",
            description="发送站内信",
            input_schema={
                "type": "object",
                "required": ["to_user", "title", "content"],
                "properties": {
                    "to_user": {
                        "type": "string",
                        "description": "接收用户ID"
                    },
                    "title": {
                        "type": "string",
                        "description": "消息标题"
                    },
                    "content": {
                        "type": "string",
                        "description": "消息内容"
                    },
                    "priority": {
                        "type": "string",
                        "description": "优先级：high/normal/low",
                        "default": "normal"
                    },
                    "action_url": {
                        "type": "string",
                        "description": "关联操作链接"
                    }
                }
            }
        ))
        async def send_inbox_message_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            to_user = params.get("to_user", "")
            title = params.get("title", "")
            content = params.get("content", "")
            priority = params.get("priority", "normal")
            action_url = params.get("action_url", "")
            
            # 模拟发送延迟
            await asyncio.sleep(0.02)
            
            # 生成通知记录
            notification_id = generate_notification_id()
            record = NotificationRecord(
                notification_id=notification_id,
                channel="inbox",
                recipient=to_user,
                subject=title,
                content=content,
                status="sent",
                sent_at=datetime.now().isoformat(),
            )
            MOCK_NOTIFICATIONS[notification_id] = record
            
            return ToolResult.success({
                "notification_id": notification_id,
                "channel": "inbox",
                "to_user": to_user,
                "title": title,
                "priority": priority,
                "action_url": action_url,
                "status": "sent",
                "sent_at": record.sent_at,
                "message": f"站内信已发送至 {to_user}",
            })
        
        # ==================== 模板通知 ====================
        
        @self.register_tool(ToolSchema(
            name="send_templated_notification",
            description="使用模板发送通知",
            input_schema={
                "type": "object",
                "required": ["template_name", "recipient", "template_params"],
                "properties": {
                    "template_name": {
                        "type": "string",
                        "description": "模板名称：order_created/order_approved/order_delayed/compliance_violation/approval_required/logistics_update/customs_hold/system_alert"
                    },
                    "recipient": {
                        "type": "string",
                        "description": "接收人（邮箱/手机/用户ID）"
                    },
                    "template_params": {
                        "type": "object",
                        "description": "模板参数"
                    },
                    "channels": {
                        "type": "array",
                        "description": "发送渠道：email/sms/wecom/inbox",
                        "items": {"type": "string"},
                        "default": ["email"]
                    }
                }
            }
        ))
        async def send_templated_notification_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            template_name = params.get("template_name", "")
            recipient = params.get("recipient", "")
            template_params = params.get("template_params", {})
            channels = params.get("channels", ["email"])
            
            # 获取模板
            template = NOTIFICATION_TEMPLATES.get(template_name)
            if not template:
                return ToolResult.error(
                    error=f"模板不存在: {template_name}",
                    error_code="TEMPLATE_NOT_FOUND"
                )
            
            # 填充模板
            subject = template["subject"].format(**template_params)
            content = template["content"].format(**template_params)
            
            # 发送到各渠道
            results = []
            for channel in channels:
                notification_id = generate_notification_id()
                record = NotificationRecord(
                    notification_id=notification_id,
                    channel=channel,
                    recipient=recipient,
                    subject=subject,
                    content=content,
                    status="sent",
                    sent_at=datetime.now().isoformat(),
                )
                MOCK_NOTIFICATIONS[notification_id] = record
                
                results.append({
                    "notification_id": notification_id,
                    "channel": channel,
                    "status": "sent",
                })
            
            return ToolResult.success({
                "template_name": template_name,
                "recipient": recipient,
                "subject": subject,
                "channels": channels,
                "results": results,
                "message": f"通知已通过 {len(channels)} 个渠道发送",
            })
        
        # ==================== 批量通知 ====================
        
        @self.register_tool(ToolSchema(
            name="send_batch_notification",
            description="批量发送通知",
            input_schema={
                "type": "object",
                "required": ["recipients", "subject", "content"],
                "properties": {
                    "recipients": {
                        "type": "array",
                        "description": "接收人列表",
                        "items": {"type": "string"}
                    },
                    "subject": {
                        "type": "string",
                        "description": "通知主题"
                    },
                    "content": {
                        "type": "string",
                        "description": "通知内容"
                    },
                    "channel": {
                        "type": "string",
                        "description": "发送渠道",
                        "default": "email"
                    }
                }
            }
        ))
        async def send_batch_notification_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            recipients = params.get("recipients", [])
            subject = params.get("subject", "")
            content = params.get("content", "")
            channel = params.get("channel", "email")
            
            # 模拟批量发送延迟
            await asyncio.sleep(0.1 * len(recipients))
            
            results = []
            for recipient in recipients:
                notification_id = generate_notification_id()
                record = NotificationRecord(
                    notification_id=notification_id,
                    channel=channel,
                    recipient=recipient,
                    subject=subject,
                    content=content,
                    status="sent",
                    sent_at=datetime.now().isoformat(),
                )
                MOCK_NOTIFICATIONS[notification_id] = record
                
                results.append({
                    "notification_id": notification_id,
                    "recipient": recipient,
                    "status": "sent",
                })
            
            return ToolResult.success({
                "total": len(recipients),
                "channel": channel,
                "subject": subject,
                "results": results,
                "message": f"已发送 {len(recipients)} 条通知",
            })
        
        # ==================== 通知查询 ====================
        
        @self.register_tool(ToolSchema(
            name="get_notification_status",
            description="查询通知发送状态",
            input_schema={
                "type": "object",
                "required": ["notification_id"],
                "properties": {
                    "notification_id": {
                        "type": "string",
                        "description": "通知ID"
                    }
                }
            }
        ))
        async def get_notification_status_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            notification_id = params.get("notification_id", "")
            
            if notification_id in MOCK_NOTIFICATIONS:
                return ToolResult.success(MOCK_NOTIFICATIONS[notification_id].to_dict())
            else:
                return ToolResult.error(
                    error=f"通知不存在: {notification_id}",
                    error_code="NOTIFICATION_NOT_FOUND"
                )
        
        # ==================== 通用通知 ====================
        
        @self.register_tool(ToolSchema(
            name="send_notification",
            description="发送通用通知，支持多种渠道",
            input_schema={
                "type": "object",
                "required": ["channel", "subject", "body"],
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "通知渠道：email/sms/dingtalk/wecom/inbox/webhook"
                    },
                    "subject": {
                        "type": "string",
                        "description": "通知主题/标题"
                    },
                    "body": {
                        "type": "string",
                        "description": "通知内容"
                    },
                    "to": {
                        "type": "string",
                        "description": "接收人（邮箱/手机/用户ID）"
                    },
                    "priority": {
                        "type": "string",
                        "description": "优先级：high/normal/low",
                        "default": "normal"
                    }
                }
            }
        ))
        async def send_notification_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            channel = params.get("channel", "")
            subject = params.get("subject", "")
            body = params.get("body", "")
            to = params.get("to", "")
            priority = params.get("priority", "normal")
            
            # 映射渠道
            channel_map = {
                "email": "email",
                "sms": "sms",
                "dingtalk": "webhook",
                "wecom": "wecom",
                "inbox": "inbox",
                "webhook": "webhook",
            }
            actual_channel = channel_map.get(channel.lower(), channel)
            
            # 模拟发送延迟
            await asyncio.sleep(0.05)
            
            # 生成通知记录
            notification_id = generate_notification_id()
            record = NotificationRecord(
                notification_id=notification_id,
                channel=actual_channel,
                recipient=to or "broadcast",
                subject=subject,
                content=body,
                status="sent",
                sent_at=datetime.now().isoformat(),
            )
            MOCK_NOTIFICATIONS[notification_id] = record
            
            return ToolResult.success({
                "notification_id": notification_id,
                "channel": actual_channel,
                "subject": subject,
                "status": "sent",
                "sent_at": record.sent_at,
                "message": f"通知已通过 {channel} 渠道发送",
            })
        
        @self.register_tool(ToolSchema(
            name="list_notifications",
            description="查询通知记录列表",
            input_schema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "渠道筛选：email/sms/wecom/inbox"
                    },
                    "status": {
                        "type": "string",
                        "description": "状态筛选：sent/failed"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量限制",
                        "default": 20
                    }
                }
            }
        ))
        async def list_notifications_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            channel = params.get("channel", "")
            status = params.get("status", "")
            limit = params.get("limit", 20)
            
            # 筛选
            results = []
            for record in MOCK_NOTIFICATIONS.values():
                if channel and record.channel != channel:
                    continue
                if status and record.status != status:
                    continue
                results.append(record.to_dict())
            
            # 按时间倒序
            results.sort(key=lambda x: x["sent_at"], reverse=True)
            results = results[:limit]
            
            return ToolResult.success({
                "notifications": results,
                "total": len(results),
                "filters": {
                    "channel": channel or None,
                    "status": status or None,
                }
            })
        
        @self.register_tool(ToolSchema(
            name="list_notification_templates",
            description="查询通知模板列表",
            input_schema={
                "type": "object",
                "properties": {}
            }
        ))
        async def list_notification_templates_tool(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            templates = [
                {"id": "tpl_001", "name": "任务完成通知", "channel": "email", "subject": "任务完成: {task_name}"},
                {"id": "tpl_002", "name": "告警通知", "channel": "dingtalk", "content": "告警: {alert_message}"},
                {"id": "tpl_003", "name": "订单通知", "channel": "wecom", "content": "新订单: {order_id}"},
            ]
            return ToolResult.success({
                "templates": templates,
                "total": len(templates),
            })
    
    async def health_check(self) -> bool:
        """健康检查"""
        return True


# ==================== 便捷函数 ====================

def create_notification_server(default_sender: str = "OpsPilot") -> NotificationServer:
    """创建通知 Server"""
    return NotificationServer(default_sender)


# ==================== 通知配置和渠道 ====================

from enum import Enum


class NotificationChannel(str, Enum):
    """通知渠道"""
    EMAIL = "email"
    SMS = "sms"
    WECHAT = "wechat"
    WECOM = "wecom"
    WEBHOOK = "webhook"
    INBOX = "inbox"
    DINGTALK = "dingtalk"


@dataclass
class NotificationConfig:
    """通知配置"""
    channel: NotificationChannel
    enabled: bool = True
    sender: str = ""
    recipients: List[str] = field(default_factory=list)
    webhook_url: str = ""
    template: str = ""
    dingtalk_webhook: str = ""
    wecom_webhook: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "channel": self.channel.value if isinstance(self.channel, Enum) else self.channel,
            "enabled": self.enabled,
            "sender": self.sender,
            "recipients": self.recipients,
            "webhook_url": self.webhook_url,
            "template": self.template,
            "dingtalk_webhook": self.dingtalk_webhook,
            "wecom_webhook": self.wecom_webhook,
        }
