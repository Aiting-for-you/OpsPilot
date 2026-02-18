# OpsPilot API 文档

## 目录

- [概述](#概述)
- [认证](#认证)
- [基础接口](#基础接口)
- [任务管理](#任务管理)
- [工具调用](#工具调用)
- [MCP工具管理](#mcp工具管理)
- [记忆管理](#记忆管理)
- [SOP执行](#sop执行)
- [知识库查询](#知识库查询)
- [LLM配置管理](#llm配置管理)
- [权限与审批](#权限与审批)
- [任务调度](#任务调度)
- [数据分析](#数据分析)
- [工具优化](#工具优化)
- [记忆优化](#记忆优化)
- [提供者管理](#提供者管理)
- [错误处理](#错误处理)

---

## 概述

OpsPilot提供RESTful API接口，支持任务管理、工具调用、Agent协作等功能。

**基础URL**: `http://localhost:8000/api/v1`

**API文档**: `http://localhost:8000/docs` (Swagger UI)

---

## 认证

目前API无需认证即可访问（生产环境建议添加JWT认证）。

---

## 基础接口

### 健康检查

检查服务健康状态。

**请求**:
```http
GET /api/v1/health
```

**响应**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "components": {
    "state_machine": true,
    "memory": true,
    "tools": true,
    "agents": true
  }
}
```

---

## 任务管理

### 1. 创建任务

创建新的处理任务。

**请求**:
```http
POST /api/v1/tasks
Content-Type: application/json

{
  "user_input": "帮我查询华南地区的供应商",
  "context": {
    "user_id": "user-001",
    "role": "采购员"
  }
}
```

**参数说明**:
- `user_input` (string, 必填): 用户输入，1-2000字符
- `context` (object, 可选): 额外上下文信息

**响应**:
```json
{
  "success": true,
  "message": "任务创建成功",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing"
}
```

---

### 2. 查询任务状态

查询指定任务的状态。

**请求**:
```http
GET /api/v1/tasks/{task_id}
```

**响应**:
```json
{
  "success": true,
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "state": "SUCCESS",
  "intent": "query_supplier",
  "created_at": "2026-02-18T10:00:00Z",
  "updated_at": "2026-02-18T10:05:00Z"
}
```

**任务状态**:
- `PENDING`: 等待处理
- `PROCESSING`: 处理中
- `SUCCESS`: 成功
- `FAILED`: 失败
- `RETRY`: 重试中

---

### 3. 获取任务结果

获取任务的执行结果。

**请求**:
```http
GET /api/v1/tasks/{task_id}/result
```

**响应**:
```json
{
  "success": true,
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "state": "SUCCESS",
  "result": {
    "suppliers": [
      {"name": "供应商A", "region": "华南", "rating": 4.5}
    ]
  },
  "execution_trace": [
    {
      "state": "INTENT",
      "timestamp": "2026-02-18T10:00:01Z",
      "action": "intent_recognition"
    }
  ]
}
```

---

## 工具调用

### 1. 获取工具列表

获取所有可用工具的Schema。

**请求**:
```http
GET /api/v1/tools
```

**响应**:
```json
{
  "success": true,
  "tools": [
    {
      "name": "query_supplier",
      "description": "查询供应商信息",
      "inputSchema": {
        "type": "object",
        "properties": {
          "region": {"type": "string"}
        }
      }
    }
  ]
}
```

---

### 2. 调用工具

直接调用指定工具。

**请求**:
```http
POST /api/v1/tools/call
Content-Type: application/json

{
  "tool_name": "query_supplier",
  "params": {
    "region": "华南"
  },
  "task_id": "task-001"
}
```

**参数说明**:
- `tool_name` (string, 必填): 工具名称
- `params` (object, 可选): 工具参数
- `task_id` (string, 可选): 关联任务ID

**响应**:
```json
{
  "success": true,
  "message": "工具调用成功",
  "tool_name": "query_supplier",
  "result": {
    "suppliers": [...]
  },
  "latency_ms": 150,
  "fallback_mode": null
}
```

---

## MCP工具管理

### 1. 获取MCP Server列表

获取所有已配置的外部MCP Server。

**请求**:
```http
GET /api/v1/mcp/servers
```

**响应**:
```json
{
  "success": true,
  "servers": [
    {
      "name": "filesystem",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"],
      "enabled": true,
      "auto_connect": true,
      "description": "文件系统操作工具",
      "status": "connected",
      "tool_count": 5,
      "error_message": "",
      "connected_at": "2026-02-18T10:00:00Z"
    }
  ]
}
```

**Server状态**:
- `disconnected`: 未连接
- `connecting`: 连接中
- `connected`: 已连接
- `error`: 错误

---

### 2. 添加MCP Server

添加新的外部MCP Server配置。

**请求**:
```http
POST /api/v1/mcp/servers
Content-Type: application/json

{
  "name": "filesystem",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed"],
  "env": {},
  "enabled": true,
  "auto_connect": true,
  "description": "文件系统操作工具"
}
```

**参数说明**:
- `name` (string, 必填): Server唯一标识，1-50字符
- `command` (string, 必填): 启动命令（如npx、python）
- `args` (array, 可选): 命令参数
- `env` (object, 可选): 环境变量
- `enabled` (boolean, 可选): 是否启用，默认true
- `auto_connect` (boolean, 可选): 是否自动连接，默认false
- `description` (string, 可选): Server描述

---

### 3. 连接MCP Server

连接到指定的MCP Server。

**请求**:
```http
POST /api/v1/mcp/servers/{name}/connect
```

**响应**:
```json
{
  "name": "filesystem",
  "status": "connected",
  "tool_count": 5,
  "connected_at": "2026-02-18T10:00:00Z"
}
```

---

### 4. 断开MCP Server

断开与指定MCP Server的连接。

**请求**:
```http
POST /api/v1/mcp/servers/{name}/disconnect
```

---

### 5. 获取MCP Server工具列表

获取指定MCP Server提供的所有工具。

**请求**:
```http
GET /api/v1/mcp/servers/{name}/tools
```

**响应**:
```json
{
  "success": true,
  "server_name": "filesystem",
  "tools": [
    {
      "name": "read_file",
      "description": "读取文件内容",
      "inputSchema": {...}
    }
  ]
}
```

---

### 6. 获取所有MCP工具

获取所有已连接MCP Server提供的工具。

**请求**:
```http
GET /api/v1/mcp/tools
```

---

### 7. 调用MCP工具

调用指定的MCP工具（自动路由到对应的Server）。

**请求**:
```http
POST /api/v1/mcp/tools/call
Content-Type: application/json

{
  "tool_name": "read_file",
  "arguments": {
    "path": "/tmp/test.txt"
  },
  "server_name": "filesystem"
}
```

**参数说明**:
- `tool_name` (string, 必填): 工具名称
- `arguments` (object, 可选): 工具参数
- `server_name` (string, 可选): 指定Server（可选，不指定则自动路由）

**响应**:
```json
{
  "success": true,
  "message": "工具调用成功",
  "tool_name": "read_file",
  "server_name": "filesystem",
  "result": "文件内容..."
}
```

---

### 8. 删除MCP Server

删除指定的MCP Server配置。

**请求**:
```http
DELETE /api/v1/mcp/servers/{name}
```

---

## 记忆管理

### 1. 存储记忆

存储一条记忆。

**请求**:
```http
POST /api/v1/memory/store
Content-Type: application/json

{
  "content": "供应商A的交货周期为7天",
  "memory_type": "short_term",
  "task_id": "task-001",
  "metadata": {
    "source": "user_input",
    "confidence": 0.9
  }
}
```

**参数说明**:
- `content` (string, 必填): 记忆内容
- `memory_type` (string, 可选): 记忆类型，默认"short_term"
- `task_id` (string, 可选): 关联任务ID
- `metadata` (object, 可选): 元数据

**响应**:
```json
{
  "success": true,
  "entry_id": "memory-001"
}
```

---

### 2. 搜索记忆

搜索记忆内容。

**请求**:
```http
POST /api/v1/memory/search
Content-Type: application/json

{
  "query": "供应商交货周期",
  "memory_type": null,
  "limit": 10
}
```

**参数说明**:
- `query` (string, 必填): 搜索查询
- `memory_type` (string, 可选): 记忆类型过滤
- `limit` (integer, 可选): 返回数量限制，1-100，默认10

**响应**:
```json
{
  "success": true,
  "results": [
    {
      "content": "供应商A的交货周期为7天",
      "score": 0.95,
      "created_at": "2026-02-18T10:00:00Z"
    }
  ],
  "total": 1
}
```

---

## SOP执行

### 1. 执行SOP

执行标准操作流程。

**请求**:
```http
POST /api/v1/sop/execute
Content-Type: application/json

{
  "sop_name": "create_order",
  "variables": {
    "region": "华南",
    "sku": "SKU001",
    "amount": 5000
  }
}
```

**参数说明**:
- `sop_name` (string, 必填): SOP名称
- `variables` (object, 可选): 变量

**响应**:
```json
{
  "success": true,
  "message": "SOP 执行成功",
  "sop_name": "create_order",
  "steps_executed": 5,
  "results": [
    {"step": 1, "action": "validate_input", "status": "success"},
    {"step": 2, "action": "check_inventory", "status": "success"}
  ]
}
```

---

### 2. 获取SOP列表

获取所有可用的SOP。

**请求**:
```http
GET /api/v1/sop/list
```

**响应**:
```json
{
  "success": true,
  "sops": ["create_order", "query_supplier"]
}
```

---

## 知识库查询

### 查询知识库

查询知识库内容。

**请求**:
```http
POST /api/v1/knowledge/query
Content-Type: application/json

{
  "query": "跨境电商税收政策",
  "category": null,
  "limit": 5
}
```

**参数说明**:
- `query` (string, 必填): 查询内容
- `category` (string, 可选): 类别过滤
- `limit` (integer, 可选): 返回数量限制，1-20，默认5

**响应**:
```json
{
  "success": true,
  "results": [
    {
      "content": "跨境电商综合税率...",
      "source": "policy_doc.pdf",
      "score": 0.92
    }
  ]
}
```

---

## LLM配置管理

### 1. 获取LLM配置列表

获取所有LLM提供商的配置信息。

**请求**:
```http
GET /api/v1/llm/config
```

**响应**:
```json
{
  "success": true,
  "providers": [
    {
      "provider": "openai",
      "name": "OpenAI",
      "api_key_masked": "sk-***xxx",
      "api_base": "https://api.openai.com/v1",
      "model_name": "gpt-4o",
      "default_model": "gpt-4o",
      "available_models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
      "temperature": 0.7,
      "max_tokens": 4096,
      "top_p": 1.0,
      "is_enabled": true,
      "is_default": true,
      "last_used": "2026-02-18T10:00:00Z"
    }
  ],
  "default_provider": "openai"
}
```

---

### 2. 获取单个LLM配置

获取指定提供商的配置信息。

**请求**:
```http
GET /api/v1/llm/config/{provider}
```

**路径参数**:
- `provider`: 提供商类型 (openai/azure_openai/claude/qwen/ernie/zhipu/deepseek/custom)

---

### 3. 更新LLM配置

更新指定提供商的配置。

**请求**:
```http
PUT /api/v1/llm/config/{provider}
Content-Type: application/json

{
  "provider": "openai",
  "api_key": "sk-xxxxx",
  "api_base": "https://api.openai.com/v1",
  "model_name": "gpt-4o",
  "temperature": 0.7,
  "max_tokens": 4096,
  "top_p": 1.0,
  "is_enabled": true,
  "is_default": true,
  "available_models": ["gpt-4o", "gpt-3.5-turbo"]
}
```

**参数说明**:
- `provider` (enum, 必填): 提供商类型
- `api_key` (string, 必填): API Key
- `api_base` (string, 可选): API基础URL
- `model_name` (string, 可选): 模型名称
- `temperature` (float, 可选): 温度参数，0-2，默认0.7
- `max_tokens` (integer, 可选): 最大Token数，默认4096
- `top_p` (float, 可选): Top-p参数，0-1，默认1.0
- `is_enabled` (boolean, 可选): 是否启用，默认true
- `is_default` (boolean, 可选): 是否设为默认，默认false
- `available_models` (array, 可选): 可用模型列表（自定义提供商）

---

### 4. 测试LLM连接

测试指定提供商的API连接是否正常。

**请求**:
```http
POST /api/v1/llm/config/{provider}/test
```

**响应**:
```json
{
  "success": true,
  "message": "连接成功",
  "latency_ms": 150
}
```

---

### 5. 设置默认LLM

将指定提供商设置为默认。

**请求**:
```http
POST /api/v1/llm/config/{provider}/set-default
```

---

### 6. 获取可用模型列表

从API端点获取支持的模型列表（OpenAI兼容格式）。

**请求**:
```http
POST /api/v1/llm/models/fetch
Content-Type: application/json

{
  "api_base": "https://api.openai.com/v1",
  "api_key": "sk-xxxxx",
  "provider_type": "openai"
}
```

**响应**:
```json
{
  "success": true,
  "models": [
    {
      "id": "gpt-4o",
      "name": "GPT-4 Omni",
      "owned_by": "openai",
      "object": "model"
    }
  ]
}
```

---

### 7. 批量添加模型

批量添加模型到指定提供商配置。

**请求**:
```http
POST /api/v1/llm/models/batch-add
Content-Type: application/json

{
  "provider": "custom",
  "api_key": "sk-xxxxx",
  "api_base": "https://api.example.com/v1",
  "models": ["gpt-4", "gpt-3.5-turbo", "claude-3"],
  "temperature": 0.7,
  "max_tokens": 4096,
  "set_default": "gpt-4"
}
```

**响应**:
```json
{
  "success": true,
  "added_count": 3,
  "default_model": "gpt-4"
}
```

---

## 权限与审批

### RBAC权限管理

#### 1. 分配用户角色

为用户分配角色（需要管理员权限）。

**请求**:
```http
POST /api/v1/rbac/assign-role
Content-Type: application/json

{
  "user_id": "user-001",
  "role": "senior_buyer",
  "department": "采购部"
}
```

**角色类型**:
- `junior_buyer`: 初级采购员
- `senior_buyer`: 高级采购员
- `finance_auditor`: 财务审核员
- `system_admin`: 系统管理员

**响应**:
```json
{
  "success": true,
  "message": "角色分配成功",
  "user_id": "user-001",
  "role": "senior_buyer",
  "department": "采购部",
  "assigned_at": "2026-02-18T10:00:00Z"
}
```

---

#### 2. 获取用户角色

**请求**:
```http
GET /api/v1/rbac/user/{user_id}/role
```

---

#### 3. 获取角色权限

**请求**:
```http
GET /api/v1/rbac/role/{role}/permissions
```

**响应**:
```json
{
  "role": "senior_buyer",
  "name": "高级采购员",
  "description": "可处理高额订单，查看供应商信息",
  "amount_limit": 500000,
  "permissions": ["view_supplier", "create_order", "update_order"],
  "sensitive_actions": ["payment", "contract_sign"],
  "can_approve_amount": 100000,
  "data_scope": "department"
}
```

---

#### 4. 检查用户权限

**请求**:
```http
POST /api/v1/rbac/check-permission
Content-Type: application/json

{
  "user_id": "user-001",
  "permission": "create_order"
}
```

**响应**:
```json
{
  "success": true,
  "message": "检查完成",
  "has_permission": true
}
```

---

#### 5. 检查金额上限

**请求**:
```http
POST /api/v1/rbac/check-amount
Content-Type: application/json

{
  "user_id": "user-001",
  "amount": 150000
}
```

**响应**:
```json
{
  "success": true,
  "message": "检查完成",
  "within_limit": false,
  "limit": 100000,
  "exceeded_amount": 50000
}
```

---

### 审批工作流

#### 1. 创建审批请求

**请求**:
```http
POST /api/v1/approval/create
Content-Type: application/json

{
  "user_id": "user-001",
  "approval_type": "amount_exceeded",
  "title": "超额采购订单审批",
  "description": "采购金额 150,000 元，超过角色上限 100,000 元",
  "data": {
    "order_id": "order-123",
    "amount": 150000,
    "supplier": "供应商A"
  },
  "expires_in_hours": 24
}
```

**审批类型**:
- `amount_exceeded`: 超额订单
- `sensitive_action`: 敏感操作
- `payment`: 支付
- `contract`: 合同
- `order_cancel`: 订单取消

**响应**:
```json
{
  "success": true,
  "message": "审批请求创建成功",
  "request_id": "approval-001",
  "approval_type": "amount_exceeded",
  "user_id": "user-001",
  "user_role": "senior_buyer",
  "title": "超额采购订单审批",
  "description": "采购金额 150,000 元...",
  "status": "pending",
  "created_at": "2026-02-18T10:00:00Z",
  "expires_at": "2026-02-19T10:00:00Z"
}
```

---

#### 2. 审批通过

**请求**:
```http
POST /api/v1/approval/approve
Content-Type: application/json

{
  "request_id": "approval-001",
  "approver_id": "user-002",
  "comment": "审批通过，供应商可靠"
}
```

---

#### 3. 审批拒绝

**请求**:
```http
POST /api/v1/approval/reject
Content-Type: application/json

{
  "request_id": "approval-001",
  "approver_id": "user-002",
  "comment": "金额过大，需要重新评估"
}
```

---

#### 4. 获取待审批列表

**请求**:
```http
GET /api/v1/approval/pending/{user_id}
```

---

#### 5. 获取用户发起的审批

**请求**:
```http
GET /api/v1/approval/user/{user_id}
```

---

#### 6. 获取审批详情

**请求**:
```http
GET /api/v1/approval/{request_id}
```

---

## 任务调度

### 1. 创建调度任务

**请求**:
```http
POST /api/v1/scheduler/tasks
Content-Type: application/json

{
  "name": "库存检查任务",
  "target": "check_inventory",
  "args": [],
  "kwargs": {"threshold": 100},
  "priority": "high",
  "task_type": "recurring",
  "scheduled_time": null,
  "interval": 3600,
  "max_retries": 3,
  "retry_interval": 60,
  "tags": ["inventory", "monitoring"]
}
```

**参数说明**:
- `name` (string, 必填): 任务名称
- `target` (string, 必填): 目标函数名
- `args` (array, 可选): 位置参数
- `kwargs` (object, 可选): 关键字参数
- `priority` (enum, 可选): 优先级 (low/normal/high/urgent)，默认normal
- `task_type` (enum, 可选): 任务类型 (one_time/scheduled/recurring)，默认one_time
- `scheduled_time` (string, 可选): 定时执行时间（ISO格式）
- `interval` (integer, 可选): 周期性任务间隔（秒）
- `max_retries` (integer, 可选): 最大重试次数，默认3
- `retry_interval` (integer, 可选): 重试间隔（秒），默认60
- `tags` (array, 可选): 标签

**响应**:
```json
{
  "success": true,
  "message": "任务创建成功",
  "task_id": "task-001",
  "name": "库存检查任务",
  "task_type": "recurring",
  "priority": "high",
  "status": "pending",
  "created_at": "2026-02-18T10:00:00Z"
}
```

---

### 2. 获取任务列表

**请求**:
```http
GET /api/v1/scheduler/tasks?status=running&tag=inventory&limit=100
```

**查询参数**:
- `status` (string, 可选): 任务状态过滤
- `tag` (string, 可选): 标签过滤
- `limit` (integer, 可选): 返回数量限制，默认100

---

### 3. 获取任务详情

**请求**:
```http
GET /api/v1/scheduler/tasks/{task_id}
```

---

### 4. 取消任务

**请求**:
```http
DELETE /api/v1/scheduler/tasks/{task_id}
```

---

### 5. 获取调度器统计

**请求**:
```http
GET /api/v1/scheduler/stats
```

**响应**:
```json
{
  "success": true,
  "message": "获取成功",
  "total_tasks": 100,
  "completed_tasks": 85,
  "failed_tasks": 5,
  "cancelled_tasks": 3,
  "running_tasks": 7,
  "queued_tasks": 0
}
```

---

### 6. 启动调度器

**请求**:
```http
POST /api/v1/scheduler/start
```

---

### 7. 停止调度器

**请求**:
```http
POST /api/v1/scheduler/stop
```

---

## 数据分析

### 1. 获取看板数据

获取数据看板汇总数据。

**请求**:
```http
GET /api/v1/analytics/dashboard?start_time=2026-02-01T00:00:00Z&end_time=2026-02-18T23:59:59Z
```

**响应**:
```json
{
  "task_statistics": {
    "total_tasks": 100,
    "completed_tasks": 85,
    "failed_tasks": 5,
    "success_rate": 0.94,
    "avg_execution_time": 2.5
  },
  "agent_performance": [
    {
      "agent_id": "intent-agent",
      "agent_name": "IntentAgent",
      "total_tasks": 100,
      "successful_tasks": 98,
      "success_rate": 0.98
    }
  ],
  "tool_analytics": [
    {
      "tool_name": "query_supplier",
      "total_calls": 150,
      "successful_calls": 145,
      "success_rate": 0.97
    }
  ],
  "system_metrics": {
    "task_queue_size": 5,
    "active_tasks": 3,
    "active_agents": 4,
    "system_load": 0.65
  },
  "generated_at": "2026-02-18T10:00:00Z"
}
```

---

### 2. 获取任务统计

**请求**:
```http
GET /api/v1/analytics/tasks
```

---

### 3. 获取Agent性能

**请求**:
```http
GET /api/v1/analytics/agents?agent_id=intent-agent
```

---

### 4. 获取工具调用分析

**请求**:
```http
GET /api/v1/analytics/tools?tool_name=query_supplier
```

---

### 5. 获取系统指标

**请求**:
```http
GET /api/v1/analytics/system
```

---

## Token追踪

### 1. 获取Token使用统计

**请求**:
```http
GET /api/v1/tokens/usage
```

**响应**:
```json
{
  "success": true,
  "data": {
    "total_tokens": 100000,
    "prompt_tokens": 60000,
    "completion_tokens": 40000,
    "by_model": {
      "gpt-4o": 80000,
      "gpt-3.5-turbo": 20000
    }
  }
}
```

---

### 2. 按Agent分组获取Token使用

**请求**:
```http
GET /api/v1/tokens/by-agent
```

---

### 3. 按模型分组获取Token使用

**请求**:
```http
GET /api/v1/tokens/by-model
```

---

### 4. 获取最近Token使用记录

**请求**:
```http
GET /api/v1/tokens/recent?limit=20
```

---

### 5. 重置Token统计

**请求**:
```http
POST /api/v1/tokens/reset
```

---

## 工具优化

### 1. 构建工具索引

将工具定义向量化并构建索引。

**请求**:
```http
POST /api/v1/tools/index
Content-Type: application/json

{
  "tools": [
    {
      "name": "query_supplier",
      "description": "查询供应商信息",
      "category": "database"
    }
  ],
  "force_rebuild": false
}
```

**响应**:
```json
{
  "success": true,
  "message": "成功索引 10 个工具",
  "indexed_count": 10,
  "categories": {
    "database": 5,
    "api": 3,
    "notification": 2
  }
}
```

---

### 2. 检索相关工具

基于查询文本检索相关工具。

**请求**:
```http
POST /api/v1/tools/retrieve
Content-Type: application/json

{
  "query": "查询供应商信息",
  "max_tools": 10,
  "max_tokens": 2000,
  "strategy": "hybrid"
}
```

**参数说明**:
- `query` (string, 必填): 查询文本
- `max_tools` (integer, 可选): 最大返回工具数，默认10
- `max_tokens` (integer, 可选): 最大Token预算，默认2000
- `strategy` (string, 可选): 检索策略 (semantic/keyword/hybrid)，默认hybrid

**响应**:
```json
{
  "success": true,
  "message": "检索到 5 个工具",
  "tools": [...],
  "total_tokens": 1500,
  "retrieval_time_ms": 50
}
```

---

### 3. 压缩工具描述

压缩工具描述以节省上下文空间。

**请求**:
```http
POST /api/v1/tools/compress
Content-Type: application/json

{
  "tools": [...],
  "level": "medium",
  "max_tokens_per_tool": 100
}
```

**参数说明**:
- `level` (string, 可选): 压缩级别 (low/medium/high)，默认medium
- `max_tokens_per_tool` (integer, 可选): 每个工具最大Token数，默认100

**响应**:
```json
{
  "success": true,
  "message": "压缩完成，压缩率: 45.50%",
  "compressed_tools": [...],
  "original_tokens": 5000,
  "compressed_tokens": 2725,
  "compression_ratio": 0.455
}
```

---

### 4. 工具自愈

尝试自动恢复工具调用失败。

**请求**:
```http
POST /api/v1/tools/heal
Content-Type: application/json

{
  "tool_name": "query_supplier",
  "params": {"region": "华南"},
  "error_info": {
    "type": "ConnectionError",
    "message": "数据库连接失败"
  },
  "max_retries": 3
}
```

**响应**:
```json
{
  "success": true,
  "message": "自愈成功",
  "result": {...},
  "strategy_used": "retry_with_backoff",
  "retry_count": 2
}
```

---

### 5. 上下文管理

基于上下文预算选择合适的工具。

**请求**:
```http
POST /api/v1/tools/context/select
Content-Type: application/json

{
  "query": "查询供应商",
  "available_tools": ["query_supplier", "update_supplier", "delete_supplier"],
  "context_budget": 2000
}
```

**响应**:
```json
{
  "success": true,
  "message": "选择了 2 个工具",
  "selected_tools": ["query_supplier", "update_supplier"],
  "total_tokens": 1500,
  "selection_strategy": "relevance_first"
}
```

---

## 记忆优化

### 1. 计算记忆权重

计算记忆的重要性权重。

**请求**:
```http
POST /api/v1/memory/weight
Content-Type: application/json

{
  "memory_id": "memory-001",
  "content": "供应商A的交货周期为7天",
  "metadata": {
    "created_at": "2026-02-01T10:00:00Z",
    "access_count": 5
  }
}
```

**响应**:
```json
{
  "success": true,
  "message": "权重计算完成: 0.8520",
  "memory_id": "memory-001",
  "weight": 0.852,
  "factors": {
    "time_decay": 0.9,
    "frequency": 0.8,
    "relevance": 0.9,
    "timeliness": 0.85,
    "credibility": 0.85
  }
}
```

---

### 2. 检测记忆冲突

检测并解决记忆冲突。

**请求**:
```http
POST /api/v1/memory/conflict
Content-Type: application/json

{
  "memories": [
    {"content": "供应商A交货周期7天", "source": "user1"},
    {"content": "供应商A交货周期10天", "source": "user2"}
  ],
  "check_type": "all"
}
```

**参数说明**:
- `check_type` (string, 可选): 检查类型 (all/contradiction/duplicate)，默认all

**响应**:
```json
{
  "success": true,
  "message": "检测到 1 个冲突",
  "conflicts": [
    {
      "type": "contradiction",
      "memory_ids": ["m1", "m2"],
      "description": "交货周期信息冲突"
    }
  ],
  "resolutions": [
    {
      "strategy": "keep_latest",
      "recommended_memory": "m2"
    }
  ],
  "conflict_count": 1
}
```

---

### 3. 记忆巩固

整合记忆并提取知识模式。

**请求**:
```http
POST /api/v1/memory/consolidate
Content-Type: application/json

{
  "memories": [...],
  "consolidation_type": "auto",
  "min_cluster_size": 3
}
```

**参数说明**:
- `consolidation_type` (string, 可选): 巩固类型 (auto/cluster/pattern)，默认auto
- `min_cluster_size` (integer, 可选): 最小簇大小，默认3

**响应**:
```json
{
  "success": true,
  "message": "巩固完成，压缩率: 30.00%",
  "clusters": [...],
  "patterns": [
    "华南地区供应商平均交货周期为7天"
  ],
  "consolidated_count": 20,
  "reduction_ratio": 0.3
}
```

---

### 4. 获取记忆统计

**请求**:
```http
GET /api/v1/memory/stats
```

**响应**:
```json
{
  "success": true,
  "message": "统计获取成功",
  "total_memories": 100,
  "weighted_memories": 80,
  "conflict_count": 5,
  "consolidated_memories": 20,
  "patterns_extracted": 15
}
```

---

## 提供者管理

### 1. 获取提供者状态

获取当前所有提供者的配置状态。

**请求**:
```http
GET /api/v1/providers/status
```

**响应**:
```json
{
  "success": true,
  "message": "获取成功",
  "approval_provider": "langchain",
  "memory_provider": "opspilot",
  "evaluation_provider": "agentscope"
}
```

---

### 2. 设置提供者

动态切换提供者。

**请求**:
```http
POST /api/v1/providers/set
Content-Type: application/json

{
  "provider_type": "approval",
  "provider": "opspilot"
}
```

**参数说明**:
- `provider_type` (string, 必填): 提供者类型 (approval/memory/evaluation)
- `provider` (string, 必填): 提供者名称

**审批提供者**:
- `opspilot`: OpsPilot自研审批系统
- `langchain`: LangChain人工审批回调

**记忆提供者**:
- `opspilot`: OpsPilot记忆管理
- `reme`: AgentScope ReMe记忆管理

**评估提供者**:
- `opspilot`: OpsPilot评估器
- `agentscope`: AgentScope评估框架

---

### 3. 获取提供者列表

获取所有可用的提供者及其信息。

**请求**:
```http
GET /api/v1/providers/list
```

**响应**:
```json
{
  "success": true,
  "message": "获取成功",
  "approval_providers": [
    {
      "name": "opspilot",
      "type": "approval",
      "available": true,
      "description": "OpsPilot自研审批系统",
      "features": ["审批规则配置", "超时自动批准", "多级审批"]
    },
    {
      "name": "langchain",
      "type": "approval",
      "available": true,
      "description": "LangChain人工审批回调",
      "features": ["工具调用拦截", "人工确认", "审批日志"]
    }
  ],
  "memory_providers": [...],
  "evaluation_providers": [...]
}
```

---

## 错误处理

所有错误响应遵循统一格式。

**错误响应格式**:
```json
{
  "success": false,
  "error_code": "TASK_NOT_FOUND",
  "error_message": "任务不存在",
  "details": {
    "task_id": "nonexistent"
  }
}
```

**常见错误码**:
- `TASK_NOT_FOUND`: 任务不存在
- `TOOL_NOT_FOUND`: 工具不存在
- `INVALID_PARAMETER`: 参数验证失败
- `CONNECTION_ERROR`: 连接错误
- `PERMISSION_DENIED`: 权限不足
- `PROVIDER_ERROR`: 提供者错误

---

## 附录

### HTTP状态码

- `200 OK`: 请求成功
- `201 Created`: 资源创建成功
- `400 Bad Request`: 请求参数错误
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误

### 速率限制

目前无速率限制（生产环境建议添加）。

### 版本控制

API版本通过URL前缀控制: `/api/v1/`

---

## 更新日志

### v1.0.0 (2026-02-18)
- 初始版本
- 完整API接口文档
