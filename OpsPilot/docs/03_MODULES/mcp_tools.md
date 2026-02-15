# MCP 工具体系设计

> **核心定位**：本项目以工具调用为核心，通过 MCP 协议实现大模型与企业系统的连接。

---

## 1. MCP 协议概述

MCP (Model Context Protocol) 是标准化的工具接口协议，使大模型能够：
- 发现可用工具
- 理解工具参数
- 执行工具调用
- 获取结构化结果

### 1.1 为什么选择 MCP？

| 优势 | 说明 |
|------|------|
| **标准化** | 统一的工具 Schema，跨平台兼容 |
| **可扩展** | 新工具只需遵循协议，无需修改核心代码 |
| **安全隔离** | 工具执行在独立沙箱中 |
| **可观测** | 所有调用有完整日志 |

---

## 2. 工具分类与体系

### 2.1 工具分类

| 类别 | 工具示例 | 用途 | 优先级 |
|------|---------|------|--------|
| **数据查询** | query_supplier, query_inventory | 供应商/库存查询 | P0 |
| **业务操作** | create_order, update_status | 订单创建/状态更新 | P0 |
| **外部集成** | query_logistics, query_exchange_rate | 物流/汇率查询 | P1 |
| **系统管理** | notify_user, generate_report | 通知/报表生成 | P2 |

### 2.2 工具体系架构

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentScope 决策层                         │
│                  (工具选择与调用决策)                         │
└─────────────────────────┬───────────────────────────────────┘
                          │ 标准化调用请求
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    LangChain 执行层                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Tool Router (工具路由)                   │    │
│  │  • 根据意图选择工具                                   │    │
│  │  • 校验参数完整性                                     │    │
│  │  • 路由到对应 MCP Server                              │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ MCP      │    │ MCP      │    │ MCP      │
    │ Server 1 │    │ Server 2 │    │ Server N │
    │ (ERP)    │    │ (物流)    │    │ (支付)   │
    └────┬─────┘    └────┬─────┘    └────┬─────┘
         │               │               │
         ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  ERP     │    │ 物流 API  │    │ 支付网关  │
    │  系统    │    │          │    │         │
    └──────────┘    └──────────┘    └──────────┘
```

---

## 3. MCP Server 设计

### 3.1 Server 配置示例

```json
{
  "name": "erp-tools",
  "description": "ERP 系统工具集",
  "tools": [
    {
      "name": "query_supplier",
      "description": "查询供应商信息",
      "inputSchema": {
        "type": "object",
        "properties": {
          "supplier_name": {
            "type": "string",
            "description": "供应商名称（模糊匹配）"
          },
          "region": {
            "type": "string",
            "enum": ["华东", "华南", "华北", "西部"],
            "description": "供应商所在区域"
          }
        },
        "required": []
      },
      "outputSchema": {
        "type": "object",
        "properties": {
          "suppliers": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "name": {"type": "string"},
                "rating": {"type": "number"},
                "products": {"type": "array"}
              }
            }
          }
        }
      }
    },
    {
      "name": "create_order",
      "description": "创建采购订单",
      "inputSchema": {
        "type": "object",
        "properties": {
          "supplier_id": {"type": "string"},
          "products": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "product_id": {"type": "string"},
                "quantity": {"type": "integer"}
              }
            }
          },
          "delivery_date": {"type": "string", "format": "date"}
        },
        "required": ["supplier_id", "products"]
      }
    }
  ]
}
```

### 3.2 内置 MCP Server

| Server | 功能 | 工具列表 |
|--------|------|---------|
| **ERP Server** | 企业资源管理 | query_supplier, query_inventory, create_order, update_status |
| **Compliance Server** | 合规检查 | check_policy, query_hs_code, validate_contract |
| **Logistics Server** | 物流追踪 | query_tracking, estimate_delivery |
| **Payment Server** | 支付处理 | create_payment, query_balance |

---

## 4. 工具调用流程

### 4.1 标准调用流程

```
用户意图
    │
    ▼
┌─────────────────┐
│ 意图解析        │ → 识别操作类型
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 工具选择        │ → 匹配可用工具
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 参数提取        │ → 填充工具参数
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Schema 校验     │ → 参数完整性检查
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 工具执行        │ → 调用 MCP Server
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 结果处理        │ → 解析返回结果
└────────┬────────┘
         │
         ▼
    [成功/失败]
         │
         ├─[成功]→ 返回结果
         │
         └─[失败]→ 错误处理
                    │
                    ├─[可重试]→ 指数退避重试 (最多3次)
                    │
                    └─[不可重试]→ 降级 GUI
```

### 4.2 调用示例

```python
# 工具调用请求
tool_call_request = {
    "tool": "query_supplier",
    "params": {
        "supplier_name": "华为",
        "region": "华南"
    },
    "context": {
        "session_id": "sess-001",
        "task_id": "task-123"
    }
}

# 工具调用响应（成功）
tool_call_response = {
    "status": "success",
    "result": {
        "suppliers": [
            {
                "name": "华为技术有限公司",
                "rating": 4.8,
                "region": "华南",
                "products": ["电子元件A", "电子元件B"]
            }
        ]
    },
    "metadata": {
        "latency_ms": 234,
        "source": "erp_api"
    }
}

# 工具调用响应（失败）
tool_call_response = {
    "status": "error",
    "error": {
        "code": "API_TIMEOUT",
        "message": "ERP API 响应超时",
        "retry_suggested": true,
        "fallback": "gui_mode"
    }
}
```

---

## 5. 错误处理与降级策略

### 5.1 错误分类

| 错误类型 | 错误码 | 处理策略 |
|---------|--------|---------|
| **临时错误** | API_TIMEOUT, RATE_LIMIT | 指数退避重试 |
| **参数错误** | INVALID_PARAMS, MISSING_FIELD | 返回错误，要求修正 |
| **权限错误** | PERMISSION_DENIED | 上报决策层，人工处理 |
| **系统错误** | SERVICE_UNAVAILABLE | 降级 GUI 模式 |

### 5.2 重试策略

```python
class RetryStrategy:
    def __init__(self):
        self.max_retries = 3
        self.base_delay = 1.0  # 秒
        self.max_delay = 30.0
    
    async def execute_with_retry(self, tool_call: ToolCall) -> ToolResult:
        for attempt in range(self.max_retries):
            try:
                result = await self.execute_tool(tool_call)
                return result
            except RetryableError as e:
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                await asyncio.sleep(delay)
            except NonRetryableError as e:
                return ToolResult(status="error", error=e)
        
        # 重试耗尽，触发降级
        return await self.fallback_to_gui(tool_call)
```

### 5.3 降级触发条件

| 条件 | 触发动作 |
|------|---------|
| API 连续失败 3 次 | 启用 GUI 模式 |
| API 不存在 | 直接使用 GUI |
| API 权限不足 | 通知人工处理 |

---

## 6. 工具执行沙箱

### 6.1 沙箱隔离架构

```
┌─────────────────────────────────────────────────────────────┐
│                    沙箱管理器 (Sandbox Manager)              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  资源配额管理                                          │    │
│  │  • CPU: 1 core / tool                                 │    │
│  │  • Memory: 512MB / tool                               │    │
│  │  • Network: 10Mbps / tool                            │    │
│  │  • Timeout: 30s default                              │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌────────────┬────────────┬────────────┐
│  Sandbox 1 │  Sandbox 2 │  Sandbox N │
│  (ERP)     │  (物流)     │  (支付)    │
└────────────┴────────────┴────────────┘
```

### 6.2 安全配置

```yaml
sandbox:
  cpu_limit: 1.0
  memory_limit: 512MB
  network_limit: 10Mbps
  timeout_default: 30s
  
  security:
    disable_file_write: true
    allowed_domains:
      - api.erp.internal
      - api.logistics.com
    read_only_paths:
      - /etc/config
```

### 6.3 恶意工具防护

| 防护层 | 检测内容 | 处理方式 |
|--------|---------|---------|
| 静态扫描 | 危险操作（eval, exec） | 阻止加载 |
| 行为监控 | 异常行为（高频请求） | 立即终止 |
| 权限校验 | 越权访问 | 拒绝执行 |
| 签名验证 | 完整性校验 | 不匹配则拒绝 |

---

## 7. Skill 封装

### 7.1 Skill vs Tool

| 维度 | Tool | Skill |
|------|------|-------|
| 粒度 | 单一操作 | 组合操作 |
| 示例 | query_supplier | complete_procurement_flow |
| 复杂度 | 低 | 高 |
| 可复用性 | 高 | 中 |

### 7.2 Skill 示例

```python
@skill("complete_procurement_flow")
async def complete_procurement_flow(
    product: str, 
    quantity: int, 
    budget: float
) -> ProcurementResult:
    """完成采购流程的 Skill"""
    # 1. 查询供应商
    suppliers = await query_supplier(product)
    
    # 2. 比价
    best = await compare_price(suppliers, quantity)
    
    # 3. 合规检查
    compliance = await check_compliance(best)
    
    # 4. 创建订单
    if compliance.passed:
        order = await create_order(best, quantity)
        return ProcurementResult(success=True, order=order)
    else:
        return ProcurementResult(success=False, reason=compliance.reason)
```

---

## 8. 审计与监控

### 8.1 调用日志

```json
{
  "log_id": "log-001",
  "timestamp": "2024-01-15T10:30:00Z",
  "session_id": "sess-123",
  "task_id": "task-456",
  "tool": "query_supplier",
  "params": {"supplier_name": "华为"},
  "result_status": "success",
  "latency_ms": 234,
  "tokens_used": 150,
  "agent": "BuyerAgent"
}
```

### 8.2 监控指标

| 指标 | 定义 | 目标值 |
|------|------|--------|
| 工具选择准确率 | 正确选择工具的比例 | > 95% |
| 参数提取准确率 | 参数正确填充的比例 | > 98% |
| 调用成功率 | 工具调用成功的比例 | > 90% |
| 降级触发率 | 需要降级到 GUI 的比例 | < 10% |

