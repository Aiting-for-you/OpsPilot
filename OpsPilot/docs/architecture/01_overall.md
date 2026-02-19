# 整体架构

## 系统架构图

```mermaid
graph TB
    subgraph 用户层["👤 用户层"]
        WEB["🌐 Web 前端"]
        CLI["💻 CLI 工具"]
    end

    subgraph API层["🔌 API层"]
        GATEWAY["FastAPI Gateway"]
        AUTH["认证授权"]
    end

    subgraph 编排层["🎯 编排层"]
        ORCH["Orchestrator<br/>任务编排"]
        FSM["StateMachine<br/>状态机"]
        SOP["SOP Executor"]
    end

    subgraph Agent层["🤖 Agent层"]
        INTENT["IntentAgent"]
        PLAN["PlanAgent"]
        EXEC["ExecAgent"]
        VERIFY["VerifyAgent"]
    end

    subgraph 工具层["🛠️ 工具层"]
        MCP["MCP Tools"]
        INTERNAL["Internal Tools"]
    end

    subgraph 记忆层["🧠 记忆层"]
        SHORT["短期记忆<br/>Redis"]
        LONG["长期记忆<br/>PostgreSQL"]
        KB["知识库<br/>ChromaDB"]
    end

    WEB --> GATEWAY
    CLI --> GATEWAY
    GATEWAY --> AUTH
    AUTH --> ORCH
    ORCH --> FSM
    FSM --> Agent层
    Agent层 --> 工具层
    Agent层 --> 记忆层

    style 用户层 fill:#e3f2fd
    style API层 fill:#fff3e0
    style 编排层 fill:#f3e5f5
    style Agent层 fill:#e8f5e9
    style 工具层 fill:#fce4ec
    style 记忆层 fill:#fff8e1
```

## 核心流程时序图

```mermaid
sequenceDiagram
    participant U as 用户
    participant API as API Gateway
    participant Orch as Orchestrator
    participant Agent as Agent
    participant Tool as Tool
    participant Mem as Memory

    U->>API: 提交任务
    API->>Orch: 转发请求
    Orch->>Mem: 加载上下文
    Mem-->>Orch: 返回上下文
    
    Orch->>Agent: 分发任务
    
    loop 执行循环
        Agent->>Tool: 调用工具
        Tool-->>Agent: 返回结果
        Agent->>Mem: 保存状态
    end
    
    Agent-->>Orch: 返回结果
    Orch-->>API: 任务完成
    API-->>U: 响应结果
```

## 技术栈

| 层次 | 技术 | 说明 |
|------|------|------|
| 前端 | React + TypeScript | Web界面 |
| 后端 | FastAPI + Python | API服务 |
| 编排 | AgentScope | 多Agent协作 |
| 执行 | LangChain | 工具调用 |
| 存储 | PostgreSQL + Redis + ChromaDB | 数据持久化 |

## 核心模块列表

| 模块 | 说明 | 详细文档 |
|------|------|---------|
| Core | 状态机、编排器、SOP执行 | [core模块](./module-core.md) |
| Agent | 各类Agent实现 | [agent模块](./module-agent.md) |
| Tool | 工具封装 | [tool模块](./module-tool.md) |
| Memory | 记忆管理 | [memory模块](./module-memory.md) |
| Pricing | 博弈定价系统 | [pricing模块](./module-pricing.md) |
| CustomerService | 客服工单系统 | [customer-service模块](./module-customer-service.md) |
