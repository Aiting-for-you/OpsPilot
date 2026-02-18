# 电商创新模块功能说明

## 概述

本文档描述两个电商创新模块的功能设计、实现方案和开发进度。

---

## 模块一：多Agent博弈定价系统

### 1.1 功能定位

通过多Agent协作博弈，实现智能动态定价决策，平衡成本、市场竞争和利润最大化。

### 1.2 后端功能

#### 核心Agent（新增）

| Agent | 职责 | 实现方式 |
|-------|------|---------|
| CostAgent | 成本分析，确保定价覆盖成本+毛利 | 继承`agents/base.py`的BaseAgent |
| MarketAgent | 市场竞争分析，参考竞品定价 | 继承`agents/base.py`的BaseAgent |
| ProfitAgent | 利润优化，最大化收益 | 继承`agents/base.py`的BaseAgent |
| PricingOrchestrator | 博弈协调，加权投票仲裁 | 复用`integration/agentscope_integration.py`的MsgHub |

#### 工具调用（复用）

| 工具 | 功能 | 来源 |
|------|------|------|
| 数据库查询 | 查询成本数据、历史定价 | `tools/database.py` |
| 订单查询 | 查询销售数据、库存 | `tools/ecommerce.py` |
| 审批流程 | 价格变动>20%触发审批 | `approval/` |
| Token追踪 | 统计定价过程的Token消耗 | `reliability/token_tracker.py` |

#### 工具调用（新增）

| 工具 | 功能 | 实现方式 |
|------|------|---------|
| 竞品监控 | 查询竞品定价、市场趋势 | 新增`tools/competitor_monitor.py`（Mock数据） |
| 价格弹性分析 | 分析价格对销量的影响 | 新增`tools/price_elasticity.py`（Mock数据） |

#### API接口

| 接口 | 方法 | 功能 |
|------|------|------|
| `/api/v1/pricing/negotiate` | POST | 启动定价博弈协商 |
| `/api/v1/pricing/history` | GET | 查询定价历史记录 |
| `/api/v1/pricing/agents/status` | GET | 查询三个Agent的状态 |
| `/api/v1/pricing/approval/{id}` | GET | 查询定价审批详情 |

#### 数据模型

```python
# 定价协商请求
class PricingNegotiateRequest:
    product_id: str          # 产品ID
    market_context: dict     # 市场上下文
    constraints: dict        # 约束条件（成本底线、价格上限等）

# 定价协商结果
class PricingNegotiateResponse:
    product_id: str
    final_price: float       # 最终定价
    confidence: float        # 置信度
    negotiation_process: dict # 博弈过程
    agent_votes: dict        # 各Agent投票详情
    tokens_used: int         # Token消耗
```

### 1.3 前端功能

#### 页面组件（复用）

| 组件 | 功能 | 来源 |
|------|------|------|
| 统计卡片 | 显示定价次数、成功率等 | `pages/Dashboard.tsx` |
| 图表组件 | 定价趋势、Agent投票分布 | `pages/Analytics.tsx` |
| 布局组件 | 页面布局、导航 | `components/layout/` |
| 状态管理 | 定价数据管理 | `store/` |

#### 页面组件（新增）

| 组件 | 功能 |
|------|------|
| PricingManagement | 定价管理主页面 |
| PricingNegotiation | 定价博弈可视化（三个Agent对比） |
| PricingHistory | 定价历史记录查询 |
| PricingApproval | 定价审批流程 |

#### 可视化元素

- 三个Agent的定价提议对比（雷达图）
- 博弈过程时间线
- 定价历史趋势（折线图）
- Token消耗统计

---

## 模块二：智能客服工单路由系统

### 2.1 功能定位

通过多Agent协作处理客服工单，实现智能分类、路由、解决和审核。

### 2.2 后端功能

#### 核心Agent（扩展/新增）

| Agent | 职责 | 实现方式 |
|-------|------|---------|
| TicketClassifier | 工单分类，识别问题类型 | 扩展`agents/intent_agent.py` |
| TicketRouter | 路由决策，分配处理部门 | 继承`agents/base.py`的BaseAgent |
| TicketSolver | 问题解决，生成解决方案 | 继承`agents/base.py`的BaseAgent |
| TicketReviewer | 质量审核，验证解决方案 | 复用`agents/verify_agent.py` |

#### 工具调用（复用）

| 工具 | 功能 | 来源 |
|------|------|---------|
| 订单查询 | 查询订单详情、状态 | `tools/ecommerce.py` |
| 物流查询 | 查询物流轨迹 | `tools/ecommerce.py` |
| 通知推送 | 发送工单处理通知 | `tools/notification.py` |
| 知识检索 | 检索客服FAQ | `memory/knowledge.py` |
| 审批流程 | 复杂工单升级审批 | `approval/` |

#### 工具调用（新增）

| 工具 | 功能 | 实现方式 |
|------|------|---------|
| 工单管理 | 创建、查询、更新工单 | 新增`tools/ticket_manager.py`（Mock数据） |

#### API接口

| 接口 | 方法 | 功能 |
|------|------|------|
| `/api/v1/customer-service/tickets` | GET | 查询工单列表 |
| `/api/v1/customer-service/tickets` | POST | 创建新工单 |
| `/api/v1/customer-service/tickets/{id}` | GET | 查询工单详情 |
| `/api/v1/customer-service/tickets/{id}/resolve` | POST | 处理工单 |
| `/api/v1/customer-service/agents/status` | GET | 查询Agent状态 |

#### 数据模型

```python
# 工单创建请求
class TicketCreateRequest:
    customer_id: str         # 客户ID
    issue_type: str          # 问题类型（订单/物流/退款/其他）
    priority: str            # 优先级（high/normal/low）
    description: str         # 问题描述
    attachments: list        # 附件列表

# 工单详情
class TicketDetail:
    ticket_id: str
    status: str              # 待处理/处理中/已解决/已关闭
    assigned_agent: str      # 分配的Agent
    resolution: str          # 解决方案
    processing_time: float   # 处理时长
    satisfaction_score: int  # 满意度评分
```

### 2.3 前端功能

#### 页面组件（复用）

| 组件 | 功能 | 来源 |
|------|------|---------|
| 任务列表 | 工单列表、状态筛选 | `pages/Tasks.tsx` |
| 流程追踪 | 工单处理流程展示 | `pages/Tracing.tsx` |
| 统计卡片 | 工单统计、处理率 | `pages/Dashboard.tsx` |
| 状态管理 | 工单数据管理 | `store/` |

#### 页面组件（新增）

| 组件 | 功能 |
|------|------|
| TicketManagement | 工单管理主页面 |
| TicketDetail | 工单详情与处理 |
| TicketFlow | 工单处理流程可视化 |
| TicketAnalytics | 工单数据分析 |

#### 可视化元素

- 工单分类分布（饼图）
- 处理流程时间线
- Agent协作过程展示
- 满意度统计

---

## 开发进度跟踪

### Phase 1：博弈定价系统

- [x] 后端Agent开发（CostAgent, MarketAgent, ProfitAgent, PricingOrchestrator）
- [x] 工具开发（竞品监控、价格弹性分析）
- [x] API接口开发
- [x] 前端页面开发
- [ ] 单元测试

### Phase 2：客服工单路由系统

- [ ] 后端Agent开发（TicketRouter, TicketSolver）
- [ ] 工具开发（工单管理）
- [ ] API接口开发
- [ ] 前端页面开发
- [ ] 单元测试

### Phase 3：集成测试

- [ ] 端到端测试
- [ ] 文档更新
- [ ] 代码提交

---

## 代码复用统计

| 模块 | 复用代码量 | 新增代码量 | 复用率 |
|------|-----------|-----------|--------|
| 博弈定价系统 | ~3000行 | ~800行 | **79%** |
| 客服工单路由 | ~3500行 | ~700行 | **83%** |

---

## 技术栈

### 后端
- **框架**：FastAPI + AgentScope + LangChain
- **数据库**：PostgreSQL（已配置）
- **缓存**：Redis（已配置）
- **工具协议**：MCP

### 前端
- **框架**：React 19 + TypeScript + Vite
- **状态管理**：Zustand
- **UI库**：Tailwind CSS + Lucide Icons
- **数据可视化**：Recharts

---

## 更新记录

| 日期 | 更新内容 | 开发者 |
|------|---------|--------|
| 2026-02-18 | 创建文档，定义功能说明 | AI Agent |
| 2026-02-18 | Phase 1后端开发完成（Agent、工具、API） | AI Agent |

