"""
持久化存储模块

提供任务、审批、Token追踪的数据库持久化功能
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import json

from opspilot.db.connection import get_database_pool, DatabasePool


# ============================================
# 任务记录持久化
# ============================================

class TaskPersistence:
    """任务记录持久化"""
    
    @staticmethod
    async def create_task(task_data: Dict[str, Any]) -> str:
        """创建任务记录"""
        pool = await get_database_pool()
        
        record = await pool.fetchrow(
            """
            INSERT INTO scheduled_tasks (
                task_id, name, task_type, priority, status,
                scheduled_time, interval_seconds, cron_expression,
                max_retries, retry_count, retry_interval,
                target_module, target_function, args, kwargs, tags, metadata,
                created_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
            RETURNING task_id
            """,
            task_data.get("task_id"),
            task_data.get("name"),
            task_data.get("task_type", "one_time"),
            task_data.get("priority", "normal"),
            task_data.get("status", "pending"),
            task_data.get("scheduled_time"),
            task_data.get("interval_seconds"),
            task_data.get("cron_expression"),
            task_data.get("max_retries", 3),
            task_data.get("retry_count", 0),
            task_data.get("retry_interval", 60),
            task_data.get("target_module"),
            task_data.get("target_function"),
            json.dumps(task_data.get("args", [])),
            json.dumps(task_data.get("kwargs", {})),
            task_data.get("tags", []),
            json.dumps(task_data.get("metadata", {})),
            task_data.get("created_by"),
        )
        
        return record["task_id"]
    
    @staticmethod
    async def update_task_status(
        task_id: str,
        status: str,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        execution_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        result: Optional[Any] = None,
        retry_count: Optional[int] = None,
    ) -> bool:
        """更新任务状态"""
        pool = await get_database_pool()
        
        update_fields = ["status = $2"]
        params = [task_id, status]
        param_idx = 3
        
        if started_at:
            update_fields.append(f"started_at = ${param_idx}")
            params.append(started_at)
            param_idx += 1
        
        if completed_at:
            update_fields.append(f"completed_at = ${param_idx}")
            params.append(completed_at)
            param_idx += 1
        
        if execution_time_ms is not None:
            update_fields.append(f"execution_time_ms = ${param_idx}")
            params.append(execution_time_ms)
            param_idx += 1
        
        if error_message:
            update_fields.append(f"error_message = ${param_idx}")
            params.append(error_message)
            param_idx += 1
        
        if result is not None:
            update_fields.append(f"result = ${param_idx}")
            params.append(json.dumps(result))
            param_idx += 1
        
        if retry_count is not None:
            update_fields.append(f"retry_count = ${param_idx}")
            params.append(retry_count)
            param_idx += 1
        
        query = f"""
            UPDATE scheduled_tasks 
            SET {', '.join(update_fields)}
            WHERE task_id = $1
        """
        
        result = await pool.execute(query, *params)
        return "UPDATE 1" in result
    
    @staticmethod
    async def get_task(task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务详情"""
        pool = await get_database_pool()
        
        record = await pool.fetchrow(
            "SELECT * FROM scheduled_tasks WHERE task_id = $1",
            task_id
        )
        
        return dict(record) if record else None
    
    @staticmethod
    async def get_tasks_by_status(
        status: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """按状态获取任务列表"""
        pool = await get_database_pool()
        
        records = await pool.fetch(
            """
            SELECT * FROM scheduled_tasks 
            WHERE status = $1 
            ORDER BY created_at DESC 
            LIMIT $2 OFFSET $3
            """,
            status, limit, offset
        )
        
        return [dict(r) for r in records]
    
    @staticmethod
    async def get_task_statistics(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """获取任务统计"""
        pool = await get_database_pool()
        
        conditions = []
        params = []
        param_idx = 1
        
        if start_date:
            conditions.append(f"DATE(created_at) >= ${param_idx}")
            params.append(start_date)
            param_idx += 1
        
        if end_date:
            conditions.append(f"DATE(created_at) <= ${param_idx}")
            params.append(end_date)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        
        query = f"""
            SELECT 
                COUNT(*) as total_tasks,
                COUNT(*) FILTER (WHERE status = 'completed') as completed_tasks,
                COUNT(*) FILTER (WHERE status = 'failed') as failed_tasks,
                COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled_tasks,
                AVG(execution_time_ms) FILTER (WHERE status = 'completed') as avg_execution_time_ms
            FROM scheduled_tasks
            WHERE {where_clause}
        """
        
        record = await pool.fetchrow(query, *params)
        
        return dict(record) if record else {}


# ============================================
# 审批记录持久化
# ============================================

class ApprovalPersistence:
    """审批记录持久化"""
    
    @staticmethod
    async def create_request(request_data: Dict[str, Any]) -> str:
        """创建审批请求"""
        pool = await get_database_pool()
        
        record = await pool.fetchrow(
            """
            INSERT INTO approval_requests (
                request_id, approval_type, status,
                user_id, user_role, department,
                title, description, data,
                entity_type, entity_id,
                expires_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING request_id
            """,
            request_data.get("request_id"),
            request_data.get("approval_type"),
            request_data.get("status", "pending"),
            request_data.get("user_id"),
            request_data.get("user_role"),
            request_data.get("department"),
            request_data.get("title"),
            request_data.get("description"),
            json.dumps(request_data.get("data", {})),
            request_data.get("entity_type"),
            request_data.get("entity_id"),
            request_data.get("expires_at"),
        )
        
        return record["request_id"]
    
    @staticmethod
    async def update_request_status(
        request_id: str,
        status: str,
        approved_by: Optional[str] = None,
        approval_comment: Optional[str] = None,
    ) -> bool:
        """更新审批状态"""
        pool = await get_database_pool()
        
        update_fields = ["status = $2"]
        params = [request_id, status]
        param_idx = 3
        
        if approved_by:
            update_fields.append(f"approved_by = ${param_idx}")
            params.append(approved_by)
            param_idx += 1
            
            update_fields.append(f"approved_at = ${param_idx}")
            params.append(datetime.now())
            param_idx += 1
        
        if approval_comment:
            update_fields.append(f"approval_comment = ${param_idx}")
            params.append(approval_comment)
            param_idx += 1
        
        query = f"""
            UPDATE approval_requests 
            SET {', '.join(update_fields)}
            WHERE request_id = $1
        """
        
        result = await pool.execute(query, *params)
        return "UPDATE 1" in result
    
    @staticmethod
    async def add_approval_history(
        request_id: str,
        approver_id: str,
        action: str,
        comment: Optional[str] = None,
        approver_role: Optional[str] = None,
        level: int = 1,
        is_final: bool = False,
    ) -> bool:
        """添加审批历史"""
        pool = await get_database_pool()
        
        result = await pool.execute(
            """
            INSERT INTO approval_history (
                request_id, approver_id, approver_role, action, comment, level, is_final
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            request_id, approver_id, approver_role, action, comment, level, is_final
        )
        
        return "INSERT 0 1" in result
    
    @staticmethod
    async def get_request(request_id: str) -> Optional[Dict[str, Any]]:
        """获取审批请求"""
        pool = await get_database_pool()
        
        record = await pool.fetchrow(
            "SELECT * FROM approval_requests WHERE request_id = $1",
            request_id
        )
        
        return dict(record) if record else None
    
    @staticmethod
    async def get_pending_requests(
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """获取待审批列表"""
        pool = await get_database_pool()
        
        records = await pool.fetch(
            """
            SELECT * FROM approval_requests 
            WHERE status = 'pending' 
            ORDER BY created_at DESC 
            LIMIT $1 OFFSET $2
            """,
            limit, offset
        )
        
        return [dict(r) for r in records]
    
    @staticmethod
    async def get_user_requests(
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """获取用户发起的审批"""
        pool = await get_database_pool()
        
        if status:
            records = await pool.fetch(
                """
                SELECT * FROM approval_requests 
                WHERE user_id = $1 AND status = $2 
                ORDER BY created_at DESC 
                LIMIT $3
                """,
                user_id, status, limit
            )
        else:
            records = await pool.fetch(
                """
                SELECT * FROM approval_requests 
                WHERE user_id = $1 
                ORDER BY created_at DESC 
                LIMIT $2
                """,
                user_id, limit
            )
        
        return [dict(r) for r in records]
    
    @staticmethod
    async def get_approval_history(request_id: str) -> List[Dict[str, Any]]:
        """获取审批历史"""
        pool = await get_database_pool()
        
        records = await pool.fetch(
            """
            SELECT * FROM approval_history 
            WHERE request_id = $1 
            ORDER BY created_at ASC
            """,
            request_id
        )
        
        return [dict(r) for r in records]


# ============================================
# Token 使用追踪持久化
# ============================================

class TokenPersistence:
    """Token 使用追踪持久化"""
    
    @staticmethod
    async def record_usage(usage_data: Dict[str, Any]) -> int:
        """记录 Token 使用"""
        pool = await get_database_pool()
        
        # 计算成本（简单估算）
        model = usage_data.get("model", "")
        prompt_tokens = usage_data.get("prompt_tokens", 0)
        completion_tokens = usage_data.get("completion_tokens", 0)
        
        estimated_cost = TokenPersistence._estimate_cost(
            model, prompt_tokens, completion_tokens
        )
        
        record = await pool.fetchrow(
            """
            INSERT INTO token_usage (
                trace_id, model, provider,
                prompt_tokens, completion_tokens, total_tokens,
                agent_id, agent_name, task_id,
                request_type, latency_ms, estimated_cost, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING id
            """,
            usage_data.get("trace_id"),
            model,
            usage_data.get("provider"),
            prompt_tokens,
            completion_tokens,
            prompt_tokens + completion_tokens,
            usage_data.get("agent_id"),
            usage_data.get("agent_name"),
            usage_data.get("task_id"),
            usage_data.get("request_type"),
            usage_data.get("latency_ms"),
            estimated_cost,
            json.dumps(usage_data.get("metadata", {})),
        )
        
        return record["id"]
    
    @staticmethod
    def _estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> Decimal:
        """估算成本（美元）"""
        # 简化的成本估算
        cost_per_1k_prompt = {
            "gpt-4": Decimal("0.03"),
            "gpt-4o": Decimal("0.005"),
            "gpt-3.5-turbo": Decimal("0.0005"),
            "claude-3-opus": Decimal("0.015"),
            "claude-3-sonnet": Decimal("0.003"),
            "deepseek-chat": Decimal("0.0001"),
            "qwen-max": Decimal("0.002"),
        }
        
        cost_per_1k_completion = {
            "gpt-4": Decimal("0.06"),
            "gpt-4o": Decimal("0.015"),
            "gpt-3.5-turbo": Decimal("0.0015"),
            "claude-3-opus": Decimal("0.075"),
            "claude-3-sonnet": Decimal("0.015"),
            "deepseek-chat": Decimal("0.0002"),
            "qwen-max": Decimal("0.006"),
        }
        
        prompt_cost = cost_per_1k_prompt.get(model, Decimal("0.001")) * prompt_tokens / 1000
        completion_cost = cost_per_1k_completion.get(model, Decimal("0.002")) * completion_tokens / 1000
        
        return prompt_cost + completion_cost
    
    @staticmethod
    async def get_usage_statistics(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        group_by: str = "model",
    ) -> List[Dict[str, Any]]:
        """获取使用统计"""
        pool = await get_database_pool()
        
        conditions = []
        params = []
        param_idx = 1
        
        if start_date:
            conditions.append(f"DATE(created_at) >= ${param_idx}")
            params.append(start_date)
            param_idx += 1
        
        if end_date:
            conditions.append(f"DATE(created_at) <= ${param_idx}")
            params.append(end_date)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        
        if group_by == "model":
            query = f"""
                SELECT 
                    model,
                    provider,
                    COUNT(*) as total_requests,
                    SUM(prompt_tokens) as total_prompt_tokens,
                    SUM(completion_tokens) as total_completion_tokens,
                    SUM(total_tokens) as total_tokens,
                    SUM(estimated_cost) as total_cost,
                    AVG(latency_ms) as avg_latency_ms
                FROM token_usage
                WHERE {where_clause}
                GROUP BY model, provider
                ORDER BY total_tokens DESC
            """
        elif group_by == "agent":
            query = f"""
                SELECT 
                    agent_id,
                    agent_name,
                    COUNT(*) as total_requests,
                    SUM(prompt_tokens) as total_prompt_tokens,
                    SUM(completion_tokens) as total_completion_tokens,
                    SUM(total_tokens) as total_tokens,
                    SUM(estimated_cost) as total_cost
                FROM token_usage
                WHERE {where_clause}
                GROUP BY agent_id, agent_name
                ORDER BY total_tokens DESC
            """
        else:  # daily
            query = f"""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as total_requests,
                    SUM(prompt_tokens) as total_prompt_tokens,
                    SUM(completion_tokens) as total_completion_tokens,
                    SUM(total_tokens) as total_tokens,
                    SUM(estimated_cost) as total_cost
                FROM token_usage
                WHERE {where_clause}
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """
        
        records = await pool.fetch(query, *params)
        
        return [dict(r) for r in records]
    
    @staticmethod
    async def get_recent_usage(
        limit: int = 100,
        agent_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """获取最近的使用记录"""
        pool = await get_database_pool()
        
        if agent_id:
            records = await pool.fetch(
                """
                SELECT * FROM token_usage 
                WHERE agent_id = $1 
                ORDER BY created_at DESC 
                LIMIT $2
                """,
                agent_id, limit
            )
        else:
            records = await pool.fetch(
                """
                SELECT * FROM token_usage 
                ORDER BY created_at DESC 
                LIMIT $1
                """,
                limit
            )
        
        return [dict(r) for r in records]
    
    @staticmethod
    async def aggregate_daily_stats() -> bool:
        """聚合每日统计（定时任务调用）"""
        pool = await get_database_pool()
        
        today = date.today()
        
        result = await pool.execute(
            """
            INSERT INTO token_usage_daily (date, model, provider, total_requests, 
                total_prompt_tokens, total_completion_tokens, total_tokens, total_cost,
                avg_latency_ms, avg_tokens_per_request)
            SELECT 
                DATE(created_at) as date,
                model,
                provider,
                COUNT(*) as total_requests,
                SUM(prompt_tokens) as total_prompt_tokens,
                SUM(completion_tokens) as total_completion_tokens,
                SUM(total_tokens) as total_tokens,
                SUM(estimated_cost) as total_cost,
                AVG(latency_ms) as avg_latency_ms,
                AVG(total_tokens) as avg_tokens_per_request
            FROM token_usage
            WHERE DATE(created_at) = $1
            GROUP BY DATE(created_at), model, provider
            ON CONFLICT (date, model) DO UPDATE SET
                total_requests = EXCLUDED.total_requests,
                total_prompt_tokens = EXCLUDED.total_prompt_tokens,
                total_completion_tokens = EXCLUDED.total_completion_tokens,
                total_tokens = EXCLUDED.total_tokens,
                total_cost = EXCLUDED.total_cost,
                avg_latency_ms = EXCLUDED.avg_latency_ms,
                avg_tokens_per_request = EXCLUDED.avg_tokens_per_request,
                updated_at = CURRENT_TIMESTAMP
            """,
            today
        )
        
        return "INSERT" in result or "UPDATE" in result


# ============================================
# 工单持久化
# ============================================

class TicketPersistence:
    """工单持久化"""
    
    @staticmethod
    async def create_ticket(ticket_data: Dict[str, Any]) -> str:
        """创建工单"""
        pool = await get_database_pool()
        
        record = await pool.fetchrow(
            """
            INSERT INTO tickets (
                ticket_id, customer_id, customer_name, customer_email, customer_phone,
                subject, content, category, priority,
                assigned_department, order_id, product_sku
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING ticket_id
            """,
            ticket_data.get("ticket_id"),
            ticket_data.get("customer_id"),
            ticket_data.get("customer_name"),
            ticket_data.get("customer_email"),
            ticket_data.get("customer_phone"),
            ticket_data.get("subject"),
            ticket_data.get("content"),
            ticket_data.get("category"),
            ticket_data.get("priority", "normal"),
            ticket_data.get("assigned_department"),
            ticket_data.get("order_id"),
            ticket_data.get("product_sku"),
        )
        
        return record["ticket_id"]
    
    @staticmethod
    async def update_ticket(
        ticket_id: str,
        update_data: Dict[str, Any],
    ) -> bool:
        """更新工单"""
        pool = await get_database_pool()
        
        update_fields = []
        params = []
        param_idx = 1
        
        for field, value in update_data.items():
            if value is not None:
                update_fields.append(f"{field} = ${param_idx}")
                params.append(value)
                param_idx += 1
        
        if not update_fields:
            return False
        
        params.append(ticket_id)
        
        query = f"""
            UPDATE tickets 
            SET {', '.join(update_fields)}
            WHERE ticket_id = ${param_idx}
        """
        
        result = await pool.execute(query, *params)
        return "UPDATE 1" in result
    
    @staticmethod
    async def get_ticket(ticket_id: str) -> Optional[Dict[str, Any]]:
        """获取工单"""
        pool = await get_database_pool()
        
        record = await pool.fetchrow(
            "SELECT * FROM tickets WHERE ticket_id = $1",
            ticket_id
        )
        
        return dict(record) if record else None
    
    @staticmethod
    async def get_tickets_by_status(
        status: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """按状态获取工单"""
        pool = await get_database_pool()
        
        records = await pool.fetch(
            """
            SELECT * FROM tickets 
            WHERE status = $1 
            ORDER BY created_at DESC 
            LIMIT $2
            """,
            status, limit
        )
        
        return [dict(r) for r in records]


# 导出
__all__ = [
    "TaskPersistence",
    "ApprovalPersistence",
    "TokenPersistence",
    "TicketPersistence",
]
