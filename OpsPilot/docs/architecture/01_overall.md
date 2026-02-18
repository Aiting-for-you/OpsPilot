# 整体架构概览

## 1. 系统定位

**OpsPilot** 是一个跨境电商全链路智能自动化平台，通过多智能体协作实现业务流程自动化。

### 核心能力

```
┌─────────────────────────────────────────────────────────────────┐
│                      OpsPilot 核心能力                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   🤖 多Agent协作     📋 SOP编排      🛠️ 工具调用     📊 可观测性  │
│   ┌─────────┐      ┌─────────┐    ┌─────────┐    ┌─────────┐   │
│   │  20+    │      │  状态机  │    │  50+   │    │  追踪   │   │
│   │ Agents  │      │  驱动   │    │  Tools  │    │  监控   │   │
│   └─────────┘      └─────────┘    └─────────┘    └─────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 2. 整体架构图

```mermaid
graph TB
    subgraph 用户层["👤 用户层"]
        WEB["🌐 Web 前端<br/>React + TypeScript"]
        CLI["💻 CLI 工具"]
        API_CLIENT["📡 API 调用方"]
    end

    subgraph 接入层["🔌 接入层"]
        GATEWAY["API Gateway<br/>FastAPI"]
        AUTH["认证授权<br/>JWT + RBAC"]
    end

    subgraph 编排层["🎯 编排层 (Orchestration)"]
        ORCHESTRATOR["Orchestrator<br/>任务编排器"]
        STATE_MACHINE["StateMachine<br/>状态机"]
        SOP_EXECUTOR["SOP Executor<br/>SOP执行器"]
    end

    subgraph Agent层["🤖 Agent层"]
        INTENT["IntentAgent<br/>意图识别"]
        PLAN["PlanAgent<br/>任务规划"]
        EXEC["ExecAgent<br/>任务执行"]
        VERIFY["VerifyAgent<br/>结果验证"]
        
        PRICING["Pricing Agents<br/>博弈定价"]
        CS["Customer Service Agents<br/>客服工单"]
    end

    subgraph 工具层["🛠️ 工具层"]
        MCP["MCP Tools<br/>外部API集成"]
        INTERNAL["Internal Tools<br/>内部工具"]
        ECOMMERCE["E-commerce Tools<br/>电商工具"]
    end

    subgraph 记忆层["🧠 记忆层"]
        SHORT["Short-term Memory<br/>短期记忆"]
        LONG["Long-term Memory<br/>长期记忆"]
        KNOWLEDGE["Knowledge Base<br/>知识库(RAG)"]
    end

    subgraph 基础设施["🏗️ 基础设施"]
        DB[("🗄️ PostgreSQL")]
        REDIS[("⚡ Redis")]
        VECTOR[("📊 ChromaDB")]
        OBS["📈 可观测性<br/>Tracing/Metrics/Logs"]
    end

    %% 连接关系
    WEB --> GATEWAY
    CLI --> GATEWAY
    API_CLIENT --> GATEWAY
    GATEWAY --> AUTH
    AUTH --> ORCHESTRATOR
    
    ORCHESTRATOR --> STATE_MACHINE
    ORCHESTRATOR --> SOP_EXECUTOR
    STATE_MACHINE --> INTENT
    STATE_MACHINE --> PLAN
    STATE_MACHINE --> EXEC
    STATE_MACHINE --> VERIFY
    
    ORCHESTRATOR --> PRICING
    ORCHESTRATOR --> CS
    
    INTENT --> MCP
    INTENT --> INTERNAL
    EXEC --> MCP
    EXEC --> ECOMMERCE
    
    INTENT --> SHORT
    EXEC --> SHORT
    EXEC --> LONG
    INTENT --> KNOWLEDGE
    
    SHORT --> REDIS
    LONG --> DB
    KNOWLEDGE --> VECTOR
    
    ORCHESTRATOR --> OBS
    EXEC --> OBS

    style 用户层 fill:#e1f5fe
    style 接入层 fill:#fff3e0
    style 编排层 fill:#f3e5f5
    style Agent层 fill:#e8f5e9
    style 工具层 fill:#fce4ec
    style 记忆层 fill:#fff8e1
    style 基础设施 fill:#efebe9
```

## 3. 技术栈概览

```mermaid
graph LR
    subgraph 前端
        REACT["React 18"]
        TS["TypeScript"]
        TAILWIND["TailwindCSS"]
        QUERY["React Query"]
    end
    
    subgraph 后端
        FASTAPI["FastAPI"]
        PYDANTIC["Pydantic"]
        AGENTSCOPE["AgentScope"]
        LANGCHAIN["LangChain"]
    end
    
    subgraph 数据存储
        PG["PostgreSQL"]
        RD["Redis"]
        CHROMA["ChromaDB"]
    end
    
    subgraph 可观测性
        PROM["Prometheus"]
        GRAF["Grafana"]
        JAEGER["Jaeger"]
    end
    
    REACT --> FASTAPI
    FASTAPI --> AGENTSCOPE
    FASTAPI --> LANGCHAIN
    AGENTSCOPE --> PG
    LANGCHAIN --> CHROMA
    FASTAPI --> RD
    FASTAPI --> PROM
```

## 4. 核心设计原则

| 原则 | 说明 | 实现方式 |
|------|------|---------|
| **确定性优先** | 核心流程由显式SOP驱动 | 状态机 + 规则引擎 |
| **可观测性** | 每一步都可追踪审计 | TraceID + 结构化日志 |
| **故障自愈** | 完善的重试与降级机制 | 指数退避 + 熔断器 |
| **模块化** | 高内聚低耦合 | 依赖注入 + 接口抽象 |

## 5. 关键指标

| 指标 | 目标值 | 当前值 |
|------|--------|--------|
| Agent数量 | 20+ | 22 |
| 工具数量 | 50+ | 55 |
| API接口 | 40+ | 52 |
| 页面数量 | 15+ | 17 |
| 测试覆盖率 | 80%+ | 85% |

## 6. 系统边界

```mermaid
graph TB
    subgraph OpsPilot系统
        CORE["核心系统"]
        EC["电商模块"]
        WEB["Web前端"]
    end
    
    subgraph 外部系统
        ERP["ERP系统"]
        LOGISTICS["物流API"]
        PAYMENT["支付网关"]
        POLICY["政策库"]
    end
    
    subgraph 用户
        OPS["运营人员"]
        FINANCE["财务人员"]
        ADMIN["管理员"]
    end
    
    OPS --> WEB
    FINANCE --> WEB
    ADMIN --> WEB
    
    CORE --> ERP
    CORE --> LOGISTICS
    CORE --> PAYMENT
    CORE --> POLICY
    
    EC --> CORE
    WEB --> CORE
```
