# 电商创新模块架构图

## 1. 电商模块总览

```mermaid
graph TB
    subgraph 电商创新模块["🛒 电商创新模块"]
        direction TB
        
        subgraph 定价模块["💰 博弈定价系统"]
            PRICING_ORCH["PricingOrchestrator<br/>博弈协调器"]
            COST["CostAgent<br/>成本分析"]
            MARKET["MarketAgent<br/>市场竞争"]
            PROFIT["ProfitAgent<br/>利润优化"]
        end
        
        subgraph 客服模块["🎫 客服工单系统"]
            CS_ORCH["工单流水线"]
            CLASSIFY["ClassifierAgent<br/>工单分类"]
            ROUTER["RouterAgent<br/>路由决策"]
            SOLVER["SolverAgent<br/>问题解决"]
            REVIEWER["ReviewerAgent<br/>质量审核"]
        end
    end
    
    PRICING_ORCH --> COST
    PRICING_ORCH --> MARKET
    PRICING_ORCH --> PROFIT
    
    CS_ORCH --> CLASSIFY
    CLASSIFY --> ROUTER
    ROUTER --> SOLVER
    SOLVER --> REVIEWER

    style 定价模块 fill:#e8f5e9
    style 客服模块 fill:#e3f2fd
```

## 2. 博弈定价系统架构

### 2.1 整体架构

```mermaid
graph TB
    subgraph 前端["🖥️ 前端"]
        PRICING_UI["PricingManagement.tsx<br/>定价管理页面"]
    end

    subgraph API层["🔌 API层"]
        PRICING_API["/api/v1/pricing/*<br/>定价API"]
    end

    subgraph Agent层["🤖 Agent层"]
        ORCH["PricingOrchestrator<br/>博弈协调器"]
        
        subgraph 参与者
            COST_A["CostAgent<br/>成本视角<br/>权重: 40%"]
            MARKET_A["MarketAgent<br/>市场视角<br/>权重: 30%"]
            PROFIT_A["ProfitAgent<br/>利润视角<br/>权重: 30%"]
        end
    end

    subgraph 工具层["🛠️ 工具层"]
        MONITOR["CompetitorMonitorTool<br/>竞品监控"]
        ELASTIC["PriceElasticityTool<br/>价格弹性"]
    end

    subgraph 数据层["💾 数据层"]
        PRODUCT["产品数据"]
        COMPETITOR["竞品数据"]
        HISTORY["定价历史"]
    end

    PRICING_UI --> PRICING_API
    PRICING_API --> ORCH
    
    ORCH --> COST_A
    ORCH --> MARKET_A
    ORCH --> PROFIT_A
    
    COST_A --> PRODUCT
    MARKET_A --> MONITOR
    PROFIT_A --> ELASTIC
    
    MONITOR --> COMPETITOR
    ELASTIC --> HISTORY

    style 前端 fill:#e3f2fd
    style API层 fill:#fff3e0
    style Agent层 fill:#f3e5f5
    style 工具层 fill:#e8f5e9
    style 数据层 fill:#efebe9
```

### 2.2 博弈流程

```mermaid
flowchart TB
    START["产品定价请求"] --> PARALLEL{"并行分析"}
    
    PARALLEL --> COST["CostAgent<br/>成本分析"]
    PARALLEL --> MARKET["MarketAgent<br/>市场分析"]
    PARALLEL --> PROFIT["ProfitAgent<br/>利润分析"]
    
    COST --> C_RESULT["成本建议价<br/>+ 成本覆盖率"]
    MARKET --> M_RESULT["市场建议价<br/>+ 竞争力评分"]
    PROFIT --> P_RESULT["利润建议价<br/>+ 利润率预测"]
    
    C_RESULT --> VOTE["加权投票仲裁"]
    M_RESULT --> VOTE
    P_RESULT --> VOTE
    
    VOTE --> CONSENSUS{"达成共识?"}
    
    CONSENSUS -->|"是"| FINAL["最终定价"]
    CONSENSUS -->|"否"| HUMAN["人工介入"]
    
    HUMAN --> FINAL
    FINAL --> END["返回结果"]
```

### 2.3 投票仲裁机制

```mermaid
graph LR
    subgraph 投票权重
        W1["CostAgent<br/>权重: 0.4"]
        W2["MarketAgent<br/>权重: 0.3"]
        W3["ProfitAgent<br/>权重: 0.3"]
    end
    
    subgraph 仲裁逻辑
        CALC["加权平均计算"]
        CHECK["置信度检查"]
        DECIDE["决策输出"]
    end
    
    W1 --> CALC
    W2 --> CALC
    W3 --> CALC
    
    CALC --> CHECK
    CHECK --> DECIDE
```

**投票计算公式**：
```
最终价格 = CostPrice × 0.4 + MarketPrice × 0.3 + ProfitPrice × 0.3
置信度 = Σ(Weight × Confidence) / ΣWeight
```

## 3. 客服工单系统架构

### 3.1 整体架构

```mermaid
graph TB
    subgraph 前端["🖥️ 前端"]
        TICKET_UI["TicketManagement.tsx<br/>工单管理页面"]
    end

    subgraph API层["🔌 API层"]
        TICKET_API["/api/v1/customer-service/*<br/>客服API"]
    end

    subgraph Agent流水线["🤖 Agent流水线"]
        CLASSIFY["ClassifierAgent<br/>分类阶段"]
        ROUTER["RouterAgent<br/>路由阶段"]
        SOLVER["SolverAgent<br/>解决阶段"]
        REVIEWER["ReviewerAgent<br/>审核阶段"]
    end

    subgraph 工具层["🛠️ 工具层"]
        TM["TicketManagerTool<br/>工单管理"]
        KB["知识库检索"]
    end

    subgraph 数据层["💾 数据层"]
        TICKETS["工单数据"]
        CUSTOMERS["客户信息"]
        SOLUTIONS["解决方案库"]
    end

    TICKET_UI --> TICKET_API
    TICKET_API --> CLASSIFY
    
    CLASSIFY --> ROUTER
    ROUTER --> SOLVER
    SOLVER --> REVIEWER
    
    CLASSIFY --> TM
    SOLVER --> TM
    SOLVER --> KB
    
    TM --> TICKETS
    TM --> CUSTOMERS
    KB --> SOLUTIONS

    style 前端 fill:#e3f2fd
    style API层 fill:#fff3e0
    style Agent流水线 fill:#f3e5f5
    style 工具层 fill:#e8f5e9
    style 数据层 fill:#efebe9
```

### 3.2 工单处理流程

```mermaid
flowchart TB
    CREATE["创建工单"] --> CLASSIFY["分类阶段"]
    
    subgraph 分类阶段
        C1["分析工单内容"]
        C2["识别工单类型<br/>咨询/投诉/售后"]
        C3["评估优先级<br/>高/中/低"]
    end
    
    CLASSIFY --> C1 --> C2 --> C3 --> ROUTE["路由阶段"]
    
    subgraph 路由阶段
        R1["匹配部门规则"]
        R2["分配处理专家"]
        R3["预估处理时长"]
    end
    
    ROUTE --> R1 --> R2 --> R3 --> SOLVE["解决阶段"]
    
    subgraph 解决阶段
        S1["检索相似案例"]
        S2["生成解决方案"]
        S3["评估方案可行性"]
    end
    
    SOLVE --> S1 --> S2 --> S3 --> REVIEW["审核阶段"]
    
    subgraph 审核阶段
        V1["检查方案完整性"]
        V2["评估客户满意度"]
        V3["审核通过"]
    end
    
    REVIEW --> V1 --> V2 --> V3 --> UPDATE["更新工单状态"]
```

### 3.3 工单状态流转

```mermaid
stateDiagram-v2
    [*] --> CREATED: 创建工单
    CREATED --> CLASSIFYING: 开始分类
    CLASSIFYING --> ROUTING: 分类完成
    ROUTING --> SOLVING: 路由完成
    SOLVING --> REVIEWING: 方案生成
    REVIEWING --> RESOLVED: 审核通过
    REVIEWING --> SOLVING: 审核不通过
    RESOLVED --> CLOSED: 关闭工单
    CLOSED --> [*]
    
    CREATED --> ESCALATED: 超时升级
    ESCALATED --> RESOLVED: 优先处理
```

## 4. 模块复用关系

```mermaid
graph TB
    subgraph 基础模块["📦 基础模块"]
        BASE_AGENT["BaseAgent<br/>Agent基类"]
        VERIFY["VerifyAgent<br/>验证逻辑"]
        STAT_CARD["统计卡片组件"]
        QUERY["React Query"]
    end

    subgraph 定价模块["💰 定价模块"]
        PRICING_AGENTS["定价Agents"]
        PRICING_TOOLS["定价Tools"]
        PRICING_UI["定价UI"]
    end

    subgraph 客服模块["🎫 客服模块"]
        CS_AGENTS["客服Agents"]
        CS_TOOLS["客服Tools"]
        CS_UI["客服UI"]
    end

    BASE_AGENT --> PRICING_AGENTS
    BASE_AGENT --> CS_AGENTS
    
    VERIFY --> CS_AGENTS
    
    STAT_CARD --> PRICING_UI
    STAT_CARD --> CS_UI
    
    QUERY --> PRICING_UI
    QUERY --> CS_UI

    style 基础模块 fill:#e8eaf6
    style 定价模块 fill:#e8f5e9
    style 客服模块 fill:#e3f2fd
```

## 5. 数据统计

### 5.1 博弈定价系统

| 指标 | 数值 |
|------|------|
| Agent数量 | 4个 |
| 工具数量 | 2个 |
| API接口 | 3个 |
| 新增代码 | ~1050行 |
| 复用代码 | ~3500行 |
| 复用率 | 77% |

### 5.2 客服工单系统

| 指标 | 数值 |
|------|------|
| Agent数量 | 4个 |
| 工具数量 | 1个 |
| API接口 | 5个 |
| 新增代码 | ~700行 |
| 复用代码 | ~1500行 |
| 复用率 | 68% |

## 6. API 接口清单

### 6.1 定价API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/pricing/negotiate | 启动定价协商 |
| GET | /api/v1/pricing/history | 查询定价历史 |
| GET | /api/v1/pricing/agents/status | 获取Agent状态 |

### 6.2 客服API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/customer-service/tickets | 创建工单 |
| POST | /api/v1/customer-service/tickets/process | 处理工单 |
| GET | /api/v1/customer-service/tickets | 查询工单列表 |
| GET | /api/v1/customer-service/tickets/{id} | 查询工单详情 |
| GET | /api/v1/customer-service/agents/status | 获取Agent状态 |

## 7. 技术亮点

### 7.1 博弈定价

- **多Agent博弈**：成本、市场、利润三方视角
- **加权投票**：避免单一视角偏见
- **实时竞品监控**：动态调整定价策略
- **价格弹性分析**：预测价格变化影响

### 7.2 客服工单

- **流水线处理**：分类→路由→解决→审核
- **智能路由**：自动分配最优处理专家
- **案例检索**：复用历史解决方案
- **质量审核**：确保方案质量
