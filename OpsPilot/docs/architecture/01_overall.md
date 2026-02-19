# 整体架构

## 系统上下文图 (System Context)

```mermaid
graph TB
    subgraph 外部用户
        USER[用户]
    end

    subgraph 外部系统
        ERP[ERP系统]
        LOGISTICS[物流系统]
        PAYMENT[支付系统]
    end

    subgraph OpsPilot系统
        SYSTEM[OpsPilot<br/>跨境电商智能自动化平台<br/><br/>提供多Agent协作的<br/>定价、客服、采购自动化服务]
    end

    USER -->|使用| SYSTEM
    SYSTEM -->|调用| ERP
    SYSTEM -->|调用| LOGISTICS
    SYSTEM -->|调用| PAYMENT

    style SYSTEM fill:#083B75,color:#fff
    style USER fill:#6C8EBF,color:#fff
    style ERP fill:#B85450,color:#fff
    style LOGISTICS fill:#B85450,color:#fff
    style PAYMENT fill:#B85450,color:#fff
```

## 容器架构图 (Container Diagram)

```mermaid
graph TB
    subgraph 用户
        WEB[Web前端<br/>React应用]
        CLI[CLI工具]
    end

    subgraph OpsPilot
        API[API服务<br/>FastAPI<br/><br/>REST接口<br/>认证授权]
        ORCH[编排服务<br/>Orchestrator<br/><br/>任务调度<br/>状态管理]
        AGENT[Agent服务<br/>AgentScope<br/><br/>意图识别<br/>任务执行]
    end

    subgraph 数据存储
        DB[(PostgreSQL<br/>持久化存储)]
        CACHE[(Redis<br/>缓存/会话)]
        VECTOR[(ChromaDB<br/>向量检索)]
    end

    WEB -->|HTTP| API
    CLI -->|HTTP| API
    API --> ORCH
    ORCH --> AGENT
    AGENT --> DB
    AGENT --> CACHE
    AGENT --> VECTOR

    style API fill:#083B75,color:#fff
    style ORCH fill:#083B75,color:#fff
    style AGENT fill:#083B75,color:#fff
    style WEB fill:#6C8EBF,color:#fff
    style CLI fill:#6C8EBF,color:#fff
    style DB fill:#82B366,color:#fff
    style CACHE fill:#82B366,color:#fff
    style VECTOR fill:#82B366,color:#fff
```

## 核心流程时序图

```mermaid
sequenceDiagram
    participant U as 用户
    participant API as API服务
    participant ORCH as 编排服务
    participant AGENT as Agent服务
    participant DB as 数据库

    U->>API: 提交任务请求
    API->>ORCH: 创建任务
    ORCH->>DB: 保存任务状态
    
    loop 任务执行
        ORCH->>AGENT: 调度Agent
        AGENT->>AGENT: 执行任务
        AGENT->>DB: 更新状态
        AGENT-->>ORCH: 返回结果
    end
    
    ORCH-->>API: 任务完成
    API-->>U: 返回结果
```

## 技术栈

| 层次 | 技术 | 说明 |
|------|------|------|
| 前端 | React + TypeScript | Web界面 |
| API | FastAPI + Python | REST服务 |
| 编排 | AgentScope | 多Agent协作 |
| 存储 | PostgreSQL + Redis + ChromaDB | 数据持久化 |

## 模块列表

| 模块 | 说明 | 文档 |
|------|------|------|
| Core | 状态机、编排器 | [module-core.md](./module-core.md) |
| Agent | 各类Agent实现 | [module-agent.md](./module-agent.md) |
| Tool | 工具封装 | [module-tool.md](./module-tool.md) |
| Memory | 记忆管理 | [module-memory.md](./module-memory.md) |
| Pricing | 博弈定价系统 | [module-pricing.md](./module-pricing.md) |
| CustomerService | 客服工单系统 | [module-customer-service.md](./module-customer-service.md) |
