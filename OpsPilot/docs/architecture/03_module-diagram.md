# 模块架构图

## 1. 模块总览

```mermaid
graph TB
    subgraph 核心模块["🎯 核心模块"]
        CORE["core/<br/>状态机/上下文/事件"]
        AGENTS["agents/<br/>各类Agent实现"]
        TOOLS["tools/<br/>工具封装"]
    end

    subgraph 业务模块["💼 业务模块"]
        PRICING["pricing/<br/>博弈定价"]
        CS["customer_service/<br/>客服工单"]
        APPROVAL["approval/<br/>审批流程"]
    end

    subgraph 支撑模块["🔧 支撑模块"]
        MEMORY["memory/<br/>记忆管理"]
        MCP["mcp/<br/>MCP协议"]
        DB["db/<br/>数据库"]
        UTILS["utils/<br/>工具函数"]
    end

    subgraph 接口模块["🌐 接口模块"]
        API["api/<br/>REST API"]
        AUTH["auth/<br/>认证授权"]
    end

    subgraph 可观测性["📊 可观测性"]
        OBS["observability/<br/>追踪/监控"]
        RELIABILITY["reliability/<br/>可靠性"]
    end

    API --> CORE
    API --> AGENTS
    API --> PRICING
    API --> CS
    
    CORE --> MEMORY
    CORE --> DB
    
    AGENTS --> TOOLS
    AGENTS --> MCP
    
    TOOLS --> UTILS
    
    PRICING --> AGENTS
    CS --> AGENTS
    
    CORE --> OBS
    AGENTS --> OBS
    TOOLS --> RELIABILITY

    style 核心模块 fill:#e8eaf6
    style 业务模块 fill:#e0f2f1
    style 支撑模块 fill:#fff3e0
    style 接口模块 fill:#fce4ec
    style 可观测性 fill:#f3e5f5
```

## 2. 核心模块详解

### 2.1 Core 模块

```mermaid
graph TB
    subgraph core模块
        SM["state_machine.py<br/>状态机"]
        CTX["context.py<br/>上下文管理"]
        EVT["events.py<br/>事件系统"]
        ORCH["orchestrator.py<br/>编排器"]
        SOP["sop_executor.py<br/>SOP执行器"]
    end
    
    SM --> |"状态变更"| EVT
    CTX --> |"上下文传递"| SM
    ORCH --> |"任务分发"| SM
    ORCH --> |"流程执行"| SOP
    EVT --> |"事件通知"| ORCH
```

### 2.2 Agents 模块

```mermaid
graph TB
    subgraph Agent基类
        BASE["BaseAgent<br/>抽象基类"]
    end
    
    subgraph 核心Agent
        INTENT["IntentAgent<br/>意图识别"]
        PLAN["PlanAgent<br/>任务规划"]
        EXEC["ExecAgent<br/>任务执行"]
        VERIFY["VerifyAgent<br/>结果验证"]
    end
    
    subgraph 业务Agent
        BUYER["BuyerAgent<br/>采购"]
        FINANCE["FinanceAgent<br/>财务"]
        COMPLIANCE["ComplianceAgent<br/>合规"]
    end
    
    BASE --> INTENT
    BASE --> PLAN
    BASE --> EXEC
    BASE --> VERIFY
    
    BASE --> BUYER
    BASE --> FINANCE
    BASE --> COMPLIANCE
```

### 2.3 Tools 模块

```mermaid
graph TB
    subgraph 工具基类
        TOOLBASE["BaseTool<br/>工具基类"]
    end
    
    subgraph MCP工具
        ERPTOOL["ERP工具<br/>订单/库存"]
        LOGTOOL["物流工具<br/>追踪/查询"]
        PAYTOOL["支付工具<br/>支付/退款"]
    end
    
    subgraph 内部工具
        FORMAT["格式化工具"]
        CALC["计算工具"]
        VALIDATE["验证工具"]
    end
    
    subgraph 电商工具
        COMPETITOR["竞品监控"]
        ELASTICITY["价格弹性"]
        TICKET["工单管理"]
    end
    
    TOOLBASE --> ERPTOOL
    TOOLBASE --> LOGTOOL
    TOOLBASE --> PAYTOOL
    TOOLBASE --> FORMAT
    TOOLBASE --> CALC
    TOOLBASE --> VALIDATE
    TOOLBASE --> COMPETITOR
    TOOLBASE --> ELASTICITY
    TOOLBASE --> TICKET
```

## 3. 业务模块详解

### 3.1 Pricing 模块（博弈定价）

```mermaid
graph TB
    subgraph 定价模块["pricing/"]
        subgraph Agents
            COST["CostAgent<br/>成本分析"]
            MARKET["MarketAgent<br/>市场竞争"]
            PROFIT["ProfitAgent<br/>利润优化"]
            ORCHESTRA["PricingOrchestrator<br/>博弈协调"]
        end
        
        subgraph Tools
            MONITOR["CompetitorMonitorTool"]
            ELASTIC["PriceElasticityTool"]
        end
        
        subgraph API
            API1["/pricing/negotiate"]
            API2["/pricing/history"]
            API3["/pricing/agents/status"]
        end
    end
    
    ORCHESTRA --> COST
    ORCHESTRA --> MARKET
    ORCHESTRA --> PROFIT
    
    MARKET --> MONITOR
    PROFIT --> ELASTIC
    
    API1 --> ORCHESTRA
    API2 --> ORCHESTRA
    API3 --> ORCHESTRA

    style 定价模块 fill:#e8f5e9
```

### 3.2 Customer Service 模块（客服工单）

```mermaid
graph TB
    subgraph 客服模块["customer_service/"]
        subgraph Agents
            CLASSIFY["ClassifierAgent<br/>工单分类"]
            ROUTER["RouterAgent<br/>路由决策"]
            SOLVER["SolverAgent<br/>问题解决"]
            REVIEWER["ReviewerAgent<br/>质量审核"]
        end
        
        subgraph Tools
            TM["TicketManagerTool"]
        end
        
        subgraph API
            A1["/customer-service/tickets"]
            A2["/customer-service/tickets/process"]
            A3["/customer-service/agents/status"]
        end
    end
    
    CLASSIFY --> ROUTER
    ROUTER --> SOLVER
    SOLVER --> REVIEWER
    
    CLASSIFY --> TM
    SOLVER --> TM
    
    A1 --> TM
    A2 --> CLASSIFY
    A3 --> CLASSIFY

    style 客服模块 fill:#e3f2fd
```

## 4. 支撑模块详解

### 4.1 Memory 模块

```mermaid
graph TB
    subgraph 记忆模块["memory/"]
        BASE["MemoryBase<br/>抽象接口"]
        
        subgraph 实现
            SHORT["ShortTermMemory<br/>Redis"]
            LONG["LongTermMemory<br/>PostgreSQL"]
            KB["KnowledgeBase<br/>ChromaDB"]
        end
        
        subgraph 功能
            STORE["存储"]
            RETRIEVE["检索"]
            EXPIRE["过期清理"]
        end
    end
    
    BASE --> SHORT
    BASE --> LONG
    BASE --> KB
    
    SHORT --> STORE
    LONG --> STORE
    KB --> RETRIEVE
```

### 4.2 MCP 模块

```mermaid
graph TB
    subgraph MCP模块["mcp/"]
        CLIENT["MCPClient<br/>客户端"]
        SERVER["MCPServer<br/>服务端"]
        PROTOCOL["协议层<br/>JSON-RPC"]
        
        subgraph Server实现
            ERP_S["ERP Server"]
            COMPLIANCE_S["Compliance Server"]
        end
    end
    
    CLIENT --> PROTOCOL
    SERVER --> PROTOCOL
    
    PROTOCOL --> ERP_S
    PROTOCOL --> COMPLIANCE_S
```

## 5. 模块依赖矩阵

| 模块 | core | agents | tools | memory | mcp | api |
|------|------|--------|-------|--------|-----|-----|
| **core** | - | ✗ | ✗ | ✓ | ✗ | ✗ |
| **agents** | ✓ | - | ✓ | ✓ | ✓ | ✗ |
| **tools** | ✗ | ✗ | - | ✗ | ✓ | ✗ |
| **memory** | ✗ | ✗ | ✗ | - | ✗ | ✗ |
| **mcp** | ✗ | ✗ | ✗ | ✗ | - | ✗ |
| **api** | ✓ | ✓ | ✗ | ✓ | ✗ | - |
| **pricing** | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| **customer_service** | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |

> ✓ = 依赖，✗ = 不依赖

## 6. 模块目录结构

```
opspilot/
├── core/                    # 核心模块
│   ├── state_machine.py     # 状态机
│   ├── context.py           # 上下文管理
│   ├── events.py            # 事件系统
│   ├── orchestrator.py      # 编排器
│   └── sop_executor.py      # SOP执行器
│
├── agents/                  # Agent模块
│   ├── base.py              # 基类
│   ├── intent_agent.py      # 意图识别
│   ├── plan_agent.py        # 任务规划
│   ├── exec_agent.py        # 任务执行
│   └── verify_agent.py      # 结果验证
│
├── tools/                   # 工具模块
│   ├── base.py              # 基类
│   ├── internal.py          # 内部工具
│   └── ecommerce.py         # 电商工具
│
├── memory/                  # 记忆模块
│   ├── base.py              # 基类
│   ├── short_term.py        # 短期记忆
│   └── long_term.py         # 长期记忆
│
├── pricing/                 # 定价模块
│   ├── agents/              # 定价Agent
│   ├── tools/               # 定价工具
│   └── api.py               # 定价API
│
├── customer_service/        # 客服模块
│   ├── agents/              # 客服Agent
│   ├── tools/               # 工单工具
│   └── api.py               # 客服API
│
├── api/                     # API模块
│   ├── routes.py            # 路由
│   ├── schemas.py           # Schema
│   └── middleware.py        # 中间件
│
└── utils/                   # 工具函数
    ├── config.py            # 配置
    ├── logger.py            # 日志
    └── exceptions.py        # 异常
```
