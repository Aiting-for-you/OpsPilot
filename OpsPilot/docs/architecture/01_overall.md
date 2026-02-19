# 整体架构

## 系统架构图

```mermaid
graph TB
    %% ==================== 第一行：用户接入 ====================
    subgraph L1[用户接入]
        direction LR
        WEB[Web前端<br/>React + TypeScript]
        CLI[CLI命令行]
        API_CLIENT[API调用方]
    end

    %% ==================== 第二行：网关与调度 ====================
    subgraph L2A[API网关]
        direction LR
        API[FastAPI路由<br/>REST/GraphQL]
        AUTH[认证授权<br/>JWT/OAuth2]
        RATE[限流熔断<br/>请求控制]
    end

    subgraph L2B[编排调度]
        direction LR
        ORCH[Orchestrator<br/>任务编排器]
        SCHED[Scheduler<br/>定时调度器]
        PIPELINE[Pipeline<br/>流程编排]
        SOP[SOPExecutor<br/>SOP执行器]
        STATE[StateMachine<br/>状态机]
    end

    %% ==================== 第三行：Agent与业务 ====================
    subgraph L3A[Agent协作]
        direction LR
        INTENT[IntentAgent<br/>意图识别]
        PLAN[PlanAgent<br/>任务规划]
        EXEC[ExecAgent<br/>任务执行]
        VERIFY[VerifyAgent<br/>结果验证]
        COLLAB[Collaboration<br/>Agent协作]
        NEGOT[Negotiation<br/>博弈谈判]
    end

    subgraph L3B[业务模块]
        direction LR
        PRICING[PricingModule<br/>博弈定价]
        CS[CustomerService<br/>客服工单]
        BUYER[BuyerModule<br/>智能采购]
        FINANCE[FinanceModule<br/>财务审核]
        COMPLIANCE[Compliance<br/>合规审查]
    end

    %% ==================== 第四行：工具与支撑 ====================
    subgraph L4A[工具集成]
        direction LR
        ECOM[电商工具<br/>商品/订单]
        DBTOOL[数据库工具<br/>CRUD操作]
        HTTPTOOL[HTTP工具<br/>API调用]
        FILETOOL[文件工具<br/>读写操作]
        NOTIFY[通知工具<br/>消息推送]
        HEALING[自愈工具<br/>故障恢复]
    end

    subgraph L4B[记忆检索]
        direction LR
        MEMORY[MemoryManager<br/>记忆管理]
        EMBED[EmbeddingService<br/>向量化]
        RETRIEVE[Retriever<br/>语义检索]
        INDEX[Indexer<br/>索引构建]
        COMPRESS[Compressor<br/>上下文压缩]
    end

    subgraph L4C[推理链路]
        direction LR
        CHAINS[Chains<br/>推理链]
        PROMPTS[Prompts<br/>提示词库]
        RUNTIME[Runtime<br/>LLM运行时]
    end

    subgraph L4D[MCP工具]
        direction LR
        MCP[MCP客户端<br/>外部工具接入]
        MCP_DB[MCP数据库<br/>外部数据源]
        MCP_SEARCH[MCP搜索<br/>外部检索]
    end

    %% ==================== 第五行：存储与观测 ====================
    subgraph L5A[数据存储]
        direction LR
        PG[(PostgreSQL<br/>关系数据)]
        REDIS[(Redis<br/>缓存队列)]
        CHROMA[(ChromaDB<br/>向量存储)]
        FILES[(文件存储<br/>日志/备份)]
    end

    subgraph L5B[可观测性]
        direction LR
        OBS[Observability<br/>可观测性]
        LOGS[日志收集]
        METRICS[指标监控]
        TRACES[链路追踪]
    end

    subgraph L5C[外部系统]
        direction LR
        ERP[ERP系统]
        WMS[仓储系统]
        LOGISTICS[物流系统]
        PAYMENT[支付系统]
        LLM[LLM服务<br/>GPT/Claude]
    end

    %% ==================== 层间连接 ====================
    WEB --> API
    CLI --> API
    API_CLIENT --> API
    API --> AUTH
    AUTH --> RATE
    RATE --> ORCH
    RATE --> SCHED
    ORCH --> PIPELINE
    ORCH --> SOP
    ORCH --> STATE

    PIPELINE --> INTENT
    SOP --> PLAN
    STATE --> EXEC
    EXEC --> VERIFY
    INTENT --> COLLAB
    COLLAB --> NEGOT

    PLAN --> PRICING
    EXEC --> CS
    EXEC --> BUYER
    VERIFY --> FINANCE
    VERIFY --> COMPLIANCE

    PRICING --> ECOM
    CS --> DBTOOL
    BUYER --> HTTPTOOL
    FINANCE --> FILETOOL
    COMPLIANCE --> NOTIFY
    EXEC --> HEALING

    ECOM --> MCP
    HTTPTOOL --> MCP_SEARCH
    DBTOOL --> MCP_DB

    INTENT --> MEMORY
    PLAN --> RETRIEVE
    EXEC --> EMBED
    VERIFY --> INDEX
    MEMORY --> COMPRESS

    RETRIEVE --> CHAINS
    CHAINS --> PROMPTS
    PROMPTS --> RUNTIME

    ORCH --> PG
    ORCH --> REDIS
    MEMORY --> CHROMA
    FILETOOL --> FILES

    API --> OBS
    ORCH --> LOGS
    EXEC --> METRICS
    PIPELINE --> TRACES

    MCP --> ERP
    ECOM --> WMS
    ECOM --> LOGISTICS
    ECOM --> PAYMENT
    RUNTIME --> LLM

    %% ==================== 样式 ====================
    classDef core fill:#083B75,color:#fff
    classDef agent fill:#1a5f7a,color:#fff
    classDef business fill:#2e7d32,color:#fff
    classDef tool fill:#6C8EBF,color:#fff
    classDef storage fill:#82B366,color:#fff
    classDef external fill:#B85450,color:#fff
    classDef observe fill:#D79B00,color:#fff

    class API,AUTH,RATE,ORCH,SCHED,PIPELINE,SOP,STATE core
    class INTENT,PLAN,EXEC,VERIFY,COLLAB,NEGOT agent
    class PRICING,CS,BUYER,FINANCE,COMPLIANCE business
    class ECOM,DBTOOL,HTTPTOOL,FILETOOL,NOTIFY,HEALING,MCP,MCP_DB,MCP_SEARCH tool
    class MEMORY,EMBED,RETRIEVE,INDEX,COMPRESS,CHAINS,PROMPTS,RUNTIME storage
    class PG,REDIS,CHROMA,FILES storage
    class OBS,LOGS,METRICS,TRACES observe
    class ERP,WMS,LOGISTICS,PAYMENT,LLM external
    class WEB,CLI,API_CLIENT external
```

## 核心流程时序图

```mermaid
sequenceDiagram
    participant U as 用户
    participant API as API网关
    participant AUTH as 认证授权
    participant ORCH as 编排器
    participant STATE as 状态机
    participant INTENT as IntentAgent
    participant PLAN as PlanAgent
    participant EXEC as ExecAgent
    participant TOOL as 工具层
    participant MEMORY as 记忆层
    participant LLM as LLM服务
    participant DB as 数据库

    U->>API: 1. 提交任务请求
    API->>AUTH: 2. 验证身份
    AUTH-->>API: 3. 返回用户信息
    API->>ORCH: 4. 创建任务
    ORCH->>DB: 5. 保存任务记录
    ORCH->>STATE: 6. 初始化状态机

    loop 任务执行循环
        STATE->>INTENT: 7. 意图识别
        INTENT->>MEMORY: 8. 加载上下文
        INTENT->>LLM: 9. 调用LLM推理
        LLM-->>INTENT: 10. 返回意图
        INTENT-->>STATE: 11. 更新状态

        STATE->>PLAN: 12. 任务规划
        PLAN->>MEMORY: 13. 检索相关记忆
        PLAN->>LLM: 14. 生成执行计划
        LLM-->>PLAN: 15. 返回计划
        PLAN-->>STATE: 16. 更新状态

        loop 执行计划步骤
            STATE->>EXEC: 17. 执行步骤
            EXEC->>TOOL: 18. 调用工具
            TOOL-->>EXEC: 19. 返回结果
            EXEC->>MEMORY: 20. 保存执行记忆
            EXEC-->>STATE: 21. 更新状态
        end
    end

    STATE-->>ORCH: 22. 任务完成
    ORCH->>DB: 23. 更新任务状态
    ORCH-->>API: 24. 返回结果
    API-->>U: 25. 响应用户
```

## 模块清单

| 模块 | 路径 | 核心文件 | 说明 |
|------|------|---------|------|
| **Core** | opspilot/core | orchestrator, state_machine, sop_executor, context, events, llm_config | 核心编排与状态管理 |
| **Agents** | opspilot/agents | base, intent_agent, plan_agent, exec_agent, verify_agent, collaboration, negotiation | Agent协作与执行 |
| **Tools** | opspilot/tools | ecommerce, database, http_client, file_ops, notification, healing, mcp, retriever | 工具封装与集成 |
| **Memory** | opspilot/memory | memory_manager, embeddings, retriever, indexer, compressor | 记忆与检索系统 |
| **Pricing** | opspilot/pricing | pricing_orchestrator, pricing_agents, pricing_tools | 博弈定价系统 |
| **CustomerService** | opspilot/customer_service | ticket_router, ticket_agents, ticket_tools | 客服工单系统 |
| **API** | opspilot/api | routes, handlers, middleware | REST API服务 |
| **Auth** | opspilot/auth | jwt, oauth, permissions | 认证授权 |
| **Chains** | opspilot/chains | llm_chains, rag_chains | 推理链路 |
| **Runtime** | opspilot/runtime | llm_runtime, model_loader | LLM运行时 |
| **Scheduler** | opspilot/scheduler | cron, task_queue | 定时调度 |
| **Observability** | opspilot/observability | logging, metrics, tracing | 可观测性 |
| **Pipeline** | opspilot/pipeline | pipeline_executor, stages | 流程编排 |
| **Reliability** | opspilot/reliability | retry, circuit_breaker | 可靠性保障 |
| **MCP** | opspilot/mcp | mcp_client, mcp_tools | 外部工具接入 |
| **DB** | opspilot/db | models, migrations | 数据模型 |
| **Utils** | opspilot/utils | helpers, validators | 工具函数 |
| **Prompts** | opspilot/prompts | templates, few_shots | 提示词库 |

## 技术栈

| 层次 | 技术选型 | 说明 |
|------|---------|------|
| 前端 | React + TypeScript + Tailwind | Web界面 |
| API | FastAPI + Pydantic | REST服务 |
| 编排 | AgentScope + LangGraph | Agent协作 |
| LLM | GPT-4 / Claude / DeepSeek | 大语言模型 |
| 向量库 | ChromaDB + OpenAI Embeddings | 语义检索 |
| 数据库 | PostgreSQL + SQLAlchemy | 关系存储 |
| 缓存 | Redis | 会话/缓存 |
| 部署 | Docker + Kubernetes | 容器化部署 |
