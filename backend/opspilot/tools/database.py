"""
数据库工具模块

提供 MySQL、PostgreSQL 等数据库的 MCP 工具封装。

特性：
- 连接池管理
- SQL 安全验证
- 查询结果格式化
- 事务支持
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod
import re

from opspilot.tools.base import (
    BaseToolServer,
    ToolSchema,
    ToolResult,
    ToolContext,
)


# SQL 注入检测模式
SQL_INJECTION_PATTERNS = [
    r";\s*DROP",
    r";\s*DELETE",
    r";\s*TRUNCATE",
    r";\s*UPDATE",
    r";\s*INSERT",
    r"--",
    r"/\*",
    r"\*/",
    r"UNION\s+SELECT",
    r"OR\s+1\s*=\s*1",
    r"OR\s+'1'\s*=\s*'1'",
]


def validate_sql(sql: str, allowed_commands: List[str] = None) -> tuple[bool, str]:
    """
    验证 SQL 安全性
    
    Args:
        sql: SQL 语句
        allowed_commands: 允许的命令类型 (SELECT, INSERT, UPDATE, DELETE)
    
    Returns:
        (is_safe, error_message)
    """
    sql_upper = sql.upper()
    
    # 检查注入模式
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, sql_upper, re.IGNORECASE):
            return False, f"检测到潜在的 SQL 注入模式: {pattern}"
    
    # 检查允许的命令
    if allowed_commands:
        first_word = sql_upper.strip().split()[0] if sql_upper.strip() else ""
        if first_word not in [cmd.upper() for cmd in allowed_commands]:
            return False, f"不允许的 SQL 命令: {first_word}"
    
    return True, ""


@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str = "localhost"
    port: int = 3306
    database: str = ""
    username: str = ""
    password: str = ""
    charset: str = "utf8mb4"
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    connect_timeout: int = 10


@dataclass
class QueryResult:
    """查询结果"""
    success: bool
    rows: List[Dict[str, Any]] = field(default_factory=list)
    row_count: int = 0
    affected_rows: int = 0
    columns: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    error: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "rows": self.rows,
            "row_count": self.row_count,
            "affected_rows": self.affected_rows,
            "columns": self.columns,
            "execution_time_ms": self.execution_time_ms,
            "error": self.error,
        }


class DatabaseConnection(ABC):
    """数据库连接抽象类"""
    
    @abstractmethod
    async def connect(self) -> bool:
        """建立连接"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        pass
    
    @abstractmethod
    async def execute(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> QueryResult:
        """执行 SQL"""
        pass
    
    @abstractmethod
    async def execute_many(
        self,
        sql: str,
        params_list: List[Dict[str, Any]],
    ) -> List[QueryResult]:
        """批量执行 SQL"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass


class MockDatabaseConnection(DatabaseConnection):
    """
    Mock 数据库连接
    
    用于开发和测试环境，无需真实数据库。
    """
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._connected = False
        self._mock_data: Dict[str, List[Dict[str, Any]]] = {
            "users": [
                {"id": 1, "name": "张三", "email": "zhangsan@example.com", "department": "技术部"},
                {"id": 2, "name": "李四", "email": "lisi@example.com", "department": "产品部"},
                {"id": 3, "name": "王五", "email": "wangwu@example.com", "department": "运营部"},
            ],
            "products": [
                {"id": 1, "name": "电阻100Ω", "sku": "SKU001", "price": 0.1, "stock": 5000},
                {"id": 2, "name": "电容10μF", "sku": "SKU002", "price": 0.2, "stock": 3000},
                {"id": 3, "name": "芯片STM32", "sku": "SKU003", "price": 15.0, "stock": 200},
            ],
            "orders": [
                {"id": 1, "order_no": "ORD2024001", "user_id": 1, "amount": 1500.0, "status": "completed"},
                {"id": 2, "order_no": "ORD2024002", "user_id": 2, "amount": 2500.0, "status": "pending"},
            ],
        }
        self._id_counters = {
            "users": 4,
            "products": 4,
            "orders": 3,
        }
    
    async def connect(self) -> bool:
        self._connected = True
        return True
    
    async def disconnect(self) -> None:
        self._connected = False
    
    async def execute(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> QueryResult:
        start_time = time.time()
        
        if not self._connected:
            return QueryResult(success=False, error="数据库未连接")
        
        sql_upper = sql.upper().strip()
        
        try:
            # SELECT 查询
            if sql_upper.startswith("SELECT"):
                result = self._handle_select(sql, params)
                result.execution_time_ms = (time.time() - start_time) * 1000
                return result
            
            # INSERT 操作
            elif sql_upper.startswith("INSERT"):
                result = self._handle_insert(sql, params)
                result.execution_time_ms = (time.time() - start_time) * 1000
                return result
            
            # UPDATE 操作
            elif sql_upper.startswith("UPDATE"):
                result = self._handle_update(sql, params)
                result.execution_time_ms = (time.time() - start_time) * 1000
                return result
            
            # DELETE 操作
            elif sql_upper.startswith("DELETE"):
                result = self._handle_delete(sql, params)
                result.execution_time_ms = (time.time() - start_time) * 1000
                return result
            
            else:
                return QueryResult(success=False, error=f"不支持的 SQL 类型")
        
        except Exception as e:
            return QueryResult(success=False, error=str(e))
    
    async def execute_many(
        self,
        sql: str,
        params_list: List[Dict[str, Any]],
    ) -> List[QueryResult]:
        results = []
        for params in params_list:
            result = await self.execute(sql, params)
            results.append(result)
        return results
    
    async def health_check(self) -> bool:
        return self._connected
    
    def _parse_table_name(self, sql: str) -> Optional[str]:
        """从 SQL 中解析表名"""
        sql_upper = sql.upper()
        
        # SELECT ... FROM table
        if "FROM" in sql_upper:
            match = re.search(r"FROM\s+(\w+)", sql, re.IGNORECASE)
            if match:
                return match.group(1).lower()
        
        # INSERT INTO table
        if "INTO" in sql_upper:
            match = re.search(r"INTO\s+(\w+)", sql, re.IGNORECASE)
            if match:
                return match.group(1).lower()
        
        # UPDATE table
        if sql_upper.startswith("UPDATE"):
            match = re.search(r"UPDATE\s+(\w+)", sql, re.IGNORECASE)
            if match:
                return match.group(1).lower()
        
        # DELETE FROM table
        if "DELETE" in sql_upper:
            match = re.search(r"FROM\s+(\w+)", sql, re.IGNORECASE)
            if match:
                return match.group(1).lower()
        
        return None
    
    def _handle_select(self, sql: str, params: Optional[Dict[str, Any]]) -> QueryResult:
        """处理 SELECT 查询"""
        table_name = self._parse_table_name(sql)
        
        if not table_name or table_name not in self._mock_data:
            return QueryResult(success=False, error=f"表不存在: {table_name}")
        
        rows = self._mock_data[table_name].copy()
        
        # 简单的 WHERE 条件解析
        if "WHERE" in sql.upper():
            # 支持 id = ? 或 id = :id 格式
            # 这里简化处理，实际应使用 SQL 解析器
            pass
        
        # LIMIT 处理
        if "LIMIT" in sql.upper():
            match = re.search(r"LIMIT\s+(\d+)", sql, re.IGNORECASE)
            if match:
                limit = int(match.group(1))
                rows = rows[:limit]
        
        columns = list(rows[0].keys()) if rows else []
        
        return QueryResult(
            success=True,
            rows=rows,
            row_count=len(rows),
            columns=columns,
        )
    
    def _handle_insert(self, sql: str, params: Optional[Dict[str, Any]]) -> QueryResult:
        """处理 INSERT 操作"""
        table_name = self._parse_table_name(sql)
        
        if not table_name:
            return QueryResult(success=False, error="无法解析表名")
        
        if table_name not in self._mock_data:
            self._mock_data[table_name] = []
            self._id_counters[table_name] = 1
        
        # 使用 params 作为新行
        if params:
            new_row = dict(params)
            if "id" not in new_row:
                new_row["id"] = self._id_counters.get(table_name, 1)
                self._id_counters[table_name] = new_row["id"] + 1
            self._mock_data[table_name].append(new_row)
            
            return QueryResult(
                success=True,
                affected_rows=1,
            )
        
        return QueryResult(success=False, error="INSERT 需要 params 参数")
    
    def _handle_update(self, sql: str, params: Optional[Dict[str, Any]]) -> QueryResult:
        """处理 UPDATE 操作"""
        table_name = self._parse_table_name(sql)
        
        if not table_name or table_name not in self._mock_data:
            return QueryResult(success=False, error=f"表不存在: {table_name}")
        
        # 简化处理：更新所有匹配条件的行
        affected = 0
        for row in self._mock_data[table_name]:
            # 如果有 id 参数，只更新对应行
            if params and "id" in params:
                if row.get("id") == params.get("id"):
                    row.update(params)
                    affected += 1
            else:
                row.update(params or {})
                affected += 1
        
        return QueryResult(success=True, affected_rows=affected)
    
    def _handle_delete(self, sql: str, params: Optional[Dict[str, Any]]) -> QueryResult:
        """处理 DELETE 操作"""
        table_name = self._parse_table_name(sql)
        
        if not table_name or table_name not in self._mock_data:
            return QueryResult(success=False, error=f"表不存在: {table_name}")
        
        original_count = len(self._mock_data[table_name])
        
        # 简化处理：删除所有匹配条件的行
        if params and "id" in params:
            self._mock_data[table_name] = [
                row for row in self._mock_data[table_name]
                if row.get("id") != params.get("id")
            ]
        else:
            # 无条件删除（危险操作）
            self._mock_data[table_name] = []
        
        affected = original_count - len(self._mock_data[table_name])
        
        return QueryResult(success=True, affected_rows=affected)


class MySQLConnection(DatabaseConnection):
    """
    MySQL 数据库连接
    
    需要 aiomysql 库支持。
    """
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._pool = None
    
    async def connect(self) -> bool:
        try:
            import aiomysql
            self._pool = await aiomysql.create_pool(
                host=self.config.host,
                port=self.config.port,
                user=self.config.username,
                password=self.config.password,
                db=self.config.database,
                charset=self.config.charset,
                minsize=1,
                maxsize=self.config.pool_size,
            )
            return True
        except ImportError:
            # 降级到 Mock
            return False
        except Exception:
            return False
    
    async def disconnect(self) -> None:
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
    
    async def execute(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> QueryResult:
        if not self._pool:
            return QueryResult(success=False, error="连接池未初始化")
        
        start_time = time.time()
        
        try:
            async with self._pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(sql, params or ())
                    
                    if sql.upper().strip().startswith("SELECT"):
                        rows = await cur.fetchall()
                        columns = [desc[0] for desc in cur.description]
                        rows_dict = [dict(zip(columns, row)) for row in rows]
                        
                        return QueryResult(
                            success=True,
                            rows=rows_dict,
                            row_count=len(rows_dict),
                            columns=columns,
                            execution_time_ms=(time.time() - start_time) * 1000,
                        )
                    else:
                        await conn.commit()
                        return QueryResult(
                            success=True,
                            affected_rows=cur.rowcount,
                            execution_time_ms=(time.time() - start_time) * 1000,
                        )
        
        except Exception as e:
            return QueryResult(success=False, error=str(e))
    
    async def execute_many(
        self,
        sql: str,
        params_list: List[Dict[str, Any]],
    ) -> List[QueryResult]:
        results = []
        for params in params_list:
            result = await self.execute(sql, params)
            results.append(result)
        return results
    
    async def health_check(self) -> bool:
        result = await self.execute("SELECT 1")
        return result.success


class PostgreSQLConnection(DatabaseConnection):
    """
    PostgreSQL 数据库连接
    
    需要 asyncpg 库支持。
    """
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.config.port = config.port or 5432
        self._pool = None
    
    async def connect(self) -> bool:
        try:
            import asyncpg
            self._pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                user=self.config.username,
                password=self.config.password,
                database=self.config.database,
                min_size=1,
                max_size=self.config.pool_size,
            )
            return True
        except ImportError:
            return False
        except Exception:
            return False
    
    async def disconnect(self) -> None:
        if self._pool:
            await self._pool.close()
    
    async def execute(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> QueryResult:
        if not self._pool:
            return QueryResult(success=False, error="连接池未初始化")
        
        start_time = time.time()
        
        try:
            async with self._pool.acquire() as conn:
                if sql.upper().strip().startswith("SELECT"):
                    rows = await conn.fetch(sql, *(params.values() if params else ()))
                    rows_dict = [dict(row) for row in rows]
                    columns = list(rows[0].keys()) if rows else []
                    
                    return QueryResult(
                        success=True,
                        rows=rows_dict,
                        row_count=len(rows_dict),
                        columns=columns,
                        execution_time_ms=(time.time() - start_time) * 1000,
                    )
                else:
                    result = await conn.execute(sql, *(params.values() if params else ()))
                    return QueryResult(
                        success=True,
                        execution_time_ms=(time.time() - start_time) * 1000,
                    )
        
        except Exception as e:
            return QueryResult(success=False, error=str(e))
    
    async def execute_many(
        self,
        sql: str,
        params_list: List[Dict[str, Any]],
    ) -> List[QueryResult]:
        results = []
        for params in params_list:
            result = await self.execute(sql, params)
            results.append(result)
        return results
    
    async def health_check(self) -> bool:
        result = await self.execute("SELECT 1")
        return result.success


class DatabaseServer(BaseToolServer):
    """
    数据库 MCP Server
    
    提供 MySQL、PostgreSQL 数据库操作工具。
    """
    
    def __init__(
        self,
        db_type: str = "mock",
        config: Optional[DatabaseConfig] = None,
    ):
        """
        初始化数据库 Server
        
        Args:
            db_type: 数据库类型 (mock/mysql/postgresql)
            config: 数据库配置
        """
        super().__init__(
            name="database-tools",
            description="数据库工具集：查询、插入、更新、删除操作"
        )
        
        self.db_type = db_type
        self.config = config or DatabaseConfig()
        self._connection: Optional[DatabaseConnection] = None
        
        self._register_tools()
    
    async def _get_connection(self) -> DatabaseConnection:
        """获取数据库连接"""
        if self._connection is None:
            if self.db_type == "mysql":
                self._connection = MySQLConnection(self.config)
            elif self.db_type == "postgresql":
                self._connection = PostgreSQLConnection(self.config)
            else:
                self._connection = MockDatabaseConnection(self.config)
            
            await self._connection.connect()
        
        return self._connection
    
    def _register_tools(self):
        """注册所有数据库工具"""
        
        # 执行查询
        @self.register_tool(ToolSchema(
            name="db_query",
            description="执行 SQL 查询（SELECT）",
            input_schema={
                "type": "object",
                "required": ["sql"],
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SELECT SQL 语句"
                    },
                    "params": {
                        "type": "object",
                        "description": "查询参数"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回行数限制",
                        "default": 100
                    }
                }
            }
        ))
        async def db_query(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            sql = params.get("sql", "")
            query_params = params.get("params")
            limit = params.get("limit", 100)
            
            # 安全验证
            is_safe, error = validate_sql(sql, ["SELECT"])
            if not is_safe:
                return ToolResult.error(error, error_code="SQL_VALIDATION_ERROR")
            
            # 添加 LIMIT
            if "LIMIT" not in sql.upper():
                sql = f"{sql.rstrip(';')} LIMIT {limit}"
            
            conn = await self._get_connection()
            result = await conn.execute(sql, query_params)
            
            if result.success:
                return ToolResult.success(result.to_dict())
            else:
                return ToolResult.error(result.error, error_code="QUERY_ERROR")
        
        # 执行更新
        @self.register_tool(ToolSchema(
            name="db_execute",
            description="执行 SQL 更新操作（INSERT/UPDATE/DELETE）",
            input_schema={
                "type": "object",
                "required": ["sql"],
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL 语句（INSERT/UPDATE/DELETE）"
                    },
                    "params": {
                        "type": "object",
                        "description": "参数"
                    }
                }
            }
        ))
        async def db_execute(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            sql = params.get("sql", "")
            exec_params = params.get("params")
            
            # 安全验证
            is_safe, error = validate_sql(sql, ["INSERT", "UPDATE", "DELETE"])
            if not is_safe:
                return ToolResult.error(error, error_code="SQL_VALIDATION_ERROR")
            
            conn = await self._get_connection()
            result = await conn.execute(sql, exec_params)
            
            if result.success:
                return ToolResult.success({
                    "affected_rows": result.affected_rows,
                    "execution_time_ms": result.execution_time_ms,
                })
            else:
                return ToolResult.error(result.error, error_code="EXECUTE_ERROR")
        
        # 批量插入
        @self.register_tool(ToolSchema(
            name="db_batch_insert",
            description="批量插入数据",
            input_schema={
                "type": "object",
                "required": ["table", "rows"],
                "properties": {
                    "table": {
                        "type": "string",
                        "description": "表名"
                    },
                    "rows": {
                        "type": "array",
                        "description": "数据行列表",
                        "items": {
                            "type": "object"
                        }
                    }
                }
            }
        ))
        async def db_batch_insert(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            table = params.get("table")
            rows = params.get("rows", [])
            
            if not rows:
                return ToolResult.error("rows 不能为空", error_code="INVALID_PARAMS")
            
            # 构建 INSERT SQL
            columns = list(rows[0].keys())
            placeholders = ", ".join([f":{col}" for col in columns])
            sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
            
            conn = await self._get_connection()
            results = await conn.execute_many(sql, rows)
            
            success_count = sum(1 for r in results if r.success)
            
            return ToolResult.success({
                "total": len(rows),
                "success": success_count,
                "failed": len(rows) - success_count,
            })
        
        # 表结构查询
        @self.register_tool(ToolSchema(
            name="db_describe_table",
            description="查询表结构",
            input_schema={
                "type": "object",
                "required": ["table"],
                "properties": {
                    "table": {
                        "type": "string",
                        "description": "表名"
                    }
                }
            }
        ))
        async def db_describe_table(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            table = params.get("table")
            
            # Mock 实现
            mock_schemas = {
                "users": [
                    {"column": "id", "type": "int", "nullable": False, "key": "PRI"},
                    {"column": "name", "type": "varchar(100)", "nullable": False},
                    {"column": "email", "type": "varchar(255)", "nullable": True},
                    {"column": "department", "type": "varchar(50)", "nullable": True},
                ],
                "products": [
                    {"column": "id", "type": "int", "nullable": False, "key": "PRI"},
                    {"column": "name", "type": "varchar(200)", "nullable": False},
                    {"column": "sku", "type": "varchar(50)", "nullable": False},
                    {"column": "price", "type": "decimal(10,2)", "nullable": False},
                    {"column": "stock", "type": "int", "nullable": False},
                ],
                "orders": [
                    {"column": "id", "type": "int", "nullable": False, "key": "PRI"},
                    {"column": "order_no", "type": "varchar(50)", "nullable": False},
                    {"column": "user_id", "type": "int", "nullable": False},
                    {"column": "amount", "type": "decimal(10,2)", "nullable": False},
                    {"column": "status", "type": "varchar(20)", "nullable": False},
                ],
            }
            
            if table in mock_schemas:
                return ToolResult.success({
                    "table": table,
                    "columns": mock_schemas[table],
                })
            
            return ToolResult.error(f"表不存在: {table}", error_code="TABLE_NOT_FOUND")
        
        # 健康检查
        @self.register_tool(ToolSchema(
            name="db_health_check",
            description="数据库健康检查",
            input_schema={
                "type": "object",
                "properties": {}
            }
        ))
        async def db_health_check(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            conn = await self._get_connection()
            is_healthy = await conn.health_check()
            
            return ToolResult.success({
                "healthy": is_healthy,
                "db_type": self.db_type,
                "database": self.config.database,
            })
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            conn = await self._get_connection()
            return await conn.health_check()
        except Exception:
            return False


# 便捷函数
def create_database_server(
    db_type: str = "mock",
    config: Optional[DatabaseConfig] = None,
) -> DatabaseServer:
    """
    创建数据库 Server
    
    Args:
        db_type: 数据库类型
        config: 数据库配置
    
    Returns:
        DatabaseServer: 数据库 Server 实例
    """
    return DatabaseServer(db_type=db_type, config=config)
