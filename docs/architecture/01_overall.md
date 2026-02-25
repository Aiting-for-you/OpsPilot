# OpsPilot 整体架构

## 1. 架构概述

### 1.1 系统定位

OpsPilot 是一个 **AI 驱动的智能运维与业务自动化平台**，通过多 Agent 协作实现复杂任务的智能编排、执行与验证。系统融合了大语言模型（LLM）、Agent 协作框架、记忆系统和外部工具集成，为企业提供从任务规划到执行完成的全流程自动化能力。

### 1.2 核心特性

| 特性 | 说明 |
|------|------|
| **多 Agent 协作** | Intent → Plan → Exec → Verify 闭环执行流程 |
| **状态机驱动** | 8 种任务状态自动流转，支持重试与回退 |
| **SOP 标准化** | 支持标准操作流程模板化执行 |
| **记忆系统** | 短期/长期/工作记忆三级架构 |
| **工具生态** | 电商、数据库、HTTP、文件、通知等 50+ 工具 |
| **MCP 集成** | Model Context Protocol 标准化外部工具接入 |
| **博弈定价** | 多 Agent 博弈协商的智能定价系统 |
| **客服工单** | 智能分类、路由、解决全流程自动化 |

### 1.3 架构原则

```mermaid
flowchart TD
    %% 根节点
    ROOT(("架构原则"))
    
    %% 四大原则
    DECOUPLE[模块解耦] -.-> ROOT
    EVENT[事件驱动] -.-> ROOT
    CONFIG[配置外置] -.-> ROOT
    INTERFACE[接口隔离] -.-> ROOT
    
    %% 模块解耦详情
    API[API Layer<br/>只做请求转发] --> DECOUPLE
    CORE[Core Layer<br/>不依赖具体实现] --> DECOUPLE
    EXT[Agent/Tools/Memory<br/>可替换可扩展] --> DECOUPLE
    
    %% 事件驱动详情
    EVENTBUS[EventBus 通知] --> EVENT
    COUPLE[降低耦合] --> EVENT
    
    %% 配置外置详情
    ENV[环境变量] --> CONFIG
    YML[YAML 配置] --> CONFIG
    DEFAULT[默认值] --> CONFIG
    
    %% 接口隔离详情
    PROTOCOL[Protocol/ABC] --> INTERFACE
    DI[依赖注入] --> INTERFACE
    
    %% 样式
    classDef root fill:#1976d2,stroke:#0d47a1,color:#fff,font-size:14px
    classDef principle fill:#fff3e0,stroke:#f57c00,color:#e65100,rx:5,ry:5
    classDef detail fill:#e8f5e9,stroke:#388e3c,color:#1b5e20,rx:5,ry:5
    
    class ROOT root
    class DECOUPLE,EVENT,CONFIG,INTERFACE principle
    class API,CORE,EXT,EVENTBUS,COUPLE,ENV,YML,DEFAULT,PROTOCOL,DI detail
```

---

## 2. 系统架构图

### 2.1 整体架构（分层视图）

```mermaid
graph LR
    %% ==================== 用户接入层 ====================
    subgraph USER_LAYER["用户接入层"]
        direction LR
        WEB[Web 前端<br/>React + TS<br/>控制台界面]
        CLI[CLI 命令行<br/>Python CLI<br/>脚本交互]
        API[API 调用方<br/>第三方系统<br/>Webhooks]
    end

    %% ==================== API 网关层 ====================
    subgraph GATEWAY_LAYER["API 网关层"]
        direction LR
        FAST[FastAPI<br/>REST API<br/>请求路由]
        AUTH[认证授权<br/>JWT/OAuth2<br/>权限控制]
        MIDDLE[中间件<br/>限流/熔断<br/>日志/监控]
    end

    %% ==================== 编排调度层 ====================
    subgraph ORCH_LAYER["编排调度层"]
        direction LR
        ORCH[Orchestrator<br/>主编排器<br/>任务生命周期]
        STATE[StateMachine<br/>状态机<br/>8种状态流转]
        SOP[SOPExecutor<br/>SOP执行器<br/>流程标准化]
        SCHED[Scheduler<br/>定时调度<br/>Cron 任务]
    end

    %% ==================== Agent 协作层 ====================
    subgraph AGENT_LAYER["Agent 协作层"]
        direction LR
        INTENT[IntentAgent<br/>意图识别<br/>输入解析]
        PLAN[PlanAgent<br/>任务规划<br/>计划生成]
        EXEC[ExecAgent<br/>任务执行<br/>工具调用]
        VERIFY[VerifyAgent<br/>结果验证<br/>质量检查]
        COLLAB[Collaboration<br/>Agent 协作<br/>消息中枢]
    end

    %% ==================== 业务模块层 ====================
    subgraph BIZ_LAYER["业务模块层"]
        direction LR
        PRICING[Pricing<br/>博弈定价<br/>智能报价]
        CS[CustomerService<br/>客服工单<br/>问题处理]
        EVAL[Evaluation<br/>评估系统<br/>质量度量]
    end

    %% ==================== 工具集成层 ====================
    subgraph TOOLS_LAYER["工具集成层"]
        direction LR
        ECOM[电商工具<br/>商品/订单/库存]
        DB[数据库工具<br/>CRUD/事务]
        HTTP[HTTP 工具<br/>API 调用]
        FILE[文件工具<br/>读写/搜索]
        NOTIFY[通知工具<br/>邮件/短信/Webhook]
        MCP[MCP 客户端<br/>外部工具接入]
    end

    %% ==================== 记忆检索层 ====================
    subgraph MEM_LAYER["记忆检索层"]
        direction LR
        SHORT[ShortTerm<br/>短期记忆<br/>Redis 会话]
        LONG[LongTerm<br/>长期记忆<br/>ChromaDB]
        WORK[Working<br/>工作记忆<br/>任务状态]
        RETRIEVER[Retriever<br/>语义检索<br/>RAG]
        EMBED[Embedding<br/>向量化<br/>语义编码]
    end

    %% ==================== 推理链路层 ====================
    subgraph CHAIN_LAYER["推理链路层"]
        direction LR
        PROMPT[Prompts<br/>提示词库<br/>模板管理]
        CHAIN[Chains<br/>推理链<br/>LCEL]
        RUNTIME[Runtime<br/>LLM 运行时<br/>多模型支持]
    end

    %% ==================== 数据存储层 ====================
    subgraph STORAGE_LAYER["数据存储层"]
        direction LR
        PG[(PostgreSQL<br/>关系数据<br/>任务/用户)]
        REDIS[(Redis<br/>缓存/队列<br/>会话/限流)]
        CHROMA[(ChromaDB<br/>向量存储<br/>语义搜索)]
        S3[(对象存储<br/>文件/日志<br/>备份)]
    end

    %% ==================== 可观测性层 ====================
    subgraph OBS_LAYER["可观测性层"]
        direction LR
        LOG[Logging<br/>日志收集<br/>结构化日志]
        METRIC[Metrics<br/>指标监控<br/>Prometheus]
        TRACE[Tracing<br/>链路追踪<br/>OpenTelemetry]
    end

    %% ==================== 外部系统 ====================
    subgraph EXT_LAYER["外部系统"]
        direction LR
        LLM[LLM 服务<br/>GPT/Claude/DeepSeek]
        ERP[ERP 系统<br/>SAP/用友]
        WMS[仓储系统<br/>WMS]
        LOGISTICS[物流系统<br/>快递/配送]
    end

    %% ==================== 连接关系 ====================
    USER_LAYER --> GATEWAY_LAYER
    GATEWAY_LAYER --> ORCH_LAYER
    ORCH_LAYER --> AGENT_LAYER
    
    AGENT_LAYER --> BIZ_LAYER
    AGENT_LAYER --> TOOLS_LAYER
    AGENT_LAYER --> MEM_LAYER
    
    MEM_LAYER --> RETRIEVER
    MEM_LAYER --> EMBED
    RETRIEVER --> CHAIN
    CHAIN --> PROMPT
    PROMPT --> RUNTIME
    
    ORCH_LAYER --> STORAGE_LAYER
    MEM_LAYER --> STORAGE_LAYER
    
    GATEWAY_LAYER --> OBS_LAYER
    AGENT_LAYER --> OBS_LAYER
    
    MCP --> EXT_LAYER
    RUNTIME --> LLM
    TOOLS_LAYER --> EXT_LAYER

    %% ==================== 样式 ====================
    classDef user fill:#e3f2fd,stroke:#1976d2,color:#0d47a1
    classDef gateway fill:#e8f5e9,stroke:#388e3c,color:#1b5e20
    classDef orchestrate fill:#fff3e0,stroke:#f57c00,color:#e65100
    classDef agent fill:#f3e5f5,stroke:#7b1fa2,color:#4a148c
    classDef business fill:#fce4ec,stroke:#c2185b,color:#880e4f
    classDef tools fill:#e0f7fa,stroke:#0097a7,color:#006064
    classDef memory fill:#f1f8e9,stroke:#558b2f,color:#33691e
    classDef chain fill:#fff8e1,stroke:#ffa000,color:#ff6f00
    classDef storage fill:#efebe9,stroke:#5d4037,color:#3e2723
    classDef observe fill:#fafafa,stroke:#616161,color:#212121
    classDef external fill:#ffebee,stroke:#d32f2f,color:#b71c1c
    classDef layer fill:#f5f5f5,stroke:#999,stroke-dasharray:5 5,color:#666

    class WEB,CLI,API user
    class FAST,AUTH,MIDDLE gateway
    class ORCH,STATE,SOP,SCHED orchestrate
    class INTENT,PLAN,EXEC,VERIFY,COLLAB agent
    class PRICING,CS,EVAL business
    class ECOM,DB,HTTP,FILE,NOTIFY,MCP tools
    class SHORT,LONG,WORK,RETRIEVER,EMBED memory
    class PROMPT,CHAIN,RUNTIME chain
    class PG,REDIS,CHROMA,S3 storage
    class LOG,METRIC,TRACE observe
    class LLM,ERP,WMS,LOGISTICS external
    class USER_LAYER,GATEWAY_LAYER,ORCH_LAYER,AGENT_LAYER,BIZ_LAYER,TOOLS_LAYER,MEM_LAYER,CHAIN_LAYER,STORAGE_LAYER,OBS_LAYER,EXT_LAYER layer
```

### 2.2 核心流程时序图

```mermaid
sequenceDiagram
    participant USER as 用户
    participant API as API 网关
    participant AUTH as 认证授权
    participant ORCH as Orchestrator
    participant STATE as 状态机
    participant INTENT as IntentAgent
    participant PLAN as PlanAgent
    participant EXEC as ExecAgent
    participant TOOL as 工具层
    participant MEMORY as 记忆层
    participant LLM as LLM 服务
    participant DB as 数据库

    USER->>API: 提交任务请求
    API->>AUTH: 验证身份
    AUTH-->>API: 返回用户信息
    API->>ORCH: 创建任务
    ORCH->>DB: 保存任务记录
    ORCH->>STATE: 初始化状态机

    rect rgb(240, 248, 255)
        note right of STATE: 意图识别阶段
        STATE->>INTENT: 意图识别
        INTENT->>MEMORY: 加载上下文
        INTENT->>LLM: 调用 LLM 推理
        LLM-->>INTENT: 返回意图
        INTENT-->>STATE: 更新状态
    end

    rect rgb(255, 245, 238)
        note right of STATE: 任务规划阶段
        STATE->>PLAN: 任务规划
        PLAN->>MEMORY: 检索相关记忆
        PLAN->>LLM: 生成执行计划
        LLM-->>PLAN: 返回计划
        PLAN-->>STATE: 更新状态
    end

    rect rgb(245, 255, 250)
        note right of STATE: 执行阶段（循环）
        loop 执行计划步骤
            STATE->>EXEC: 执行步骤
            EXEC->>TOOL: 调用工具
            TOOL-->>EXEC: 返回结果
            EXEC->>MEMORY: 保存执行记忆
            EXEC-->>STATE: 更新状态
        end
    end

    rect rgb(255, 250, 240)
        note right of STATE: 验证阶段
        STATE->>VERIFY: 结果验证
        VERIFY->>VERIFY: 规则检查
        VERIFY->>VERIFY: 质量评分
        VERIFY-->>STATE: 验证结果
    end

    STATE-->>ORCH: 任务完成
    ORCH->>DB: 更新任务状态
    ORCH-->>API: 返回结果
    API-->>USER: 响应用户
```

---

## 3. 模块清单

| 模块 | 路径 | 核心组件 | 职责 |
|------|------|---------|------|
| **Core** | `opspilot/core` | Orchestrator, StateMachine, SOPExecutor, Context, Events | 任务编排、状态管理、事件驱动 |
| **Agents** | `opspilot/agents` | IntentAgent, PlanAgent, ExecAgent, VerifyAgent, Collaboration | Agent 协作、消息中枢、博弈协商 |
| **Tools** | `opspilot/tools` | BaseTool, Ecommerce, Database, HttpClient, FileOps, Notification, MCP | 工具封装、工具选择、工具调用 |
| **Memory** | `opspilot/memory` | ShortTerm, LongTerm, Working, Retriever, Embedding, Compressor | 记忆管理、语义检索、上下文压缩 |
| **Pricing** | `opspilot/pricing` | PricingOrchestrator, NegotiationEngine, CostAgent, MarketAgent | 博弈定价、多 Agent 协商、智能报价 |
| **CustomerService** | `opspilot/customer_service` | TicketRouter, ClassifierAgent, SolverAgent, KnowledgeBase | 工单路由、智能分类、问题解决 |
| **API** | `opspilot/api` | Routes, Handlers, Middleware, Schemas | REST API 服务、数据校验 |
| **Auth** | `opspilot/auth` | JWT, OAuth2, RBAC | 认证授权、权限管理 |
| **Chains** | `opspilot/chains` | LLMChains, RAGChains, Prompts | 推理链路、提示词管理 |
| **Runtime** | `opspilot/runtime` | LLMRuntime, Streaming, A2A, Tracing | LLM 运行时、流式输出、链路追踪 |
| **Scheduler** | `opspilot/scheduler` | TaskScheduler, CronParser | 定时任务、调度管理 |
| **Observability** | `opspilot/observability` | Logging, Metrics, Tracing | 日志、指标、链路追踪 |
| **Pipeline** | `opspilot/pipeline` | Sequential, Parallel, Conditional, Loop | 流程编排、条件分支、循环执行 |
| **Reliability** | `opspilot/reliability` | Retry, CircuitBreaker, LLMReliability | 重试机制、熔断器、LLM 可靠性 |
| **MCP** | `opspilot/mcp` | MCPClient, MCPServer, ExternalManager | MCP 协议实现、外部工具接入 |
| **DB** | `opspilot/db` | Models, CRUD, Connection, Cache | 数据模型、数据库操作、连接池 |
| **Evaluation** | `opspilot/evaluation` | Metrics, Evaluator, Benchmark | 评估指标、质量度量、性能基准 |

---

## 4. 技术栈

| 层次 | 技术选型 | 说明 |
|------|---------|------|
| **前端** | React 19 + TypeScript + Tailwind CSS | 现代 Web 界面 |
| **API** | FastAPI + Pydantic v2 | 高性能 REST 服务 |
| **Agent 框架** | AgentScope + LangGraph | 多 Agent 协作编排 |
| **LLM** | OpenAI GPT-4 / Anthropic Claude / DeepSeek | 大语言模型支持 |
| **向量库** | ChromaDB + OpenAI Embeddings | 语义检索 |
| **数据库** | PostgreSQL + SQLAlchemy 2.0 | 关系型数据存储 |
| **缓存** | Redis | 会话、缓存、限流、队列 |
| **部署** | Docker + Kubernetes | 容器化编排 |
| **可观测** | OpenTelemetry + Prometheus + Grafana | 监控告警 |

---

## 5. 状态机

### 5.1 任务状态定义

```mermaid
stateDiagram-v2
    [*] --> INIT: 任务创建
    
    %% 状态样式
    classDef init fill:#e3f2fd,stroke:#1976d2,color:#0d47a1
    classDef planning fill:#fff3e0,stroke:#f57c00,color:#e65100
    classDef auditing fill:#fce4ec,stroke:#c2185b,color:#880e4f
    classDef executing fill:#e8f5e9,stroke:#388e3c,color:#1b5e20
    classDef verifying fill:#e1f5fe,stroke:#0277bd,color:#01579b
    classDef success fill:#c8e6c9,stroke:#2e7d32,color:#1b5e20
    classDef failed fill:#ffcdd2,stroke:#c62828,color:#b71c1c
    classDef retry fill:#fff9c4,stroke:#f9a825,color:#f57f17
    classDef rejected fill:#d7ccc8,stroke:#5d4037,color:#3e2723
    
    [*] --> INIT
    INIT --> PLANNING: 开始规划
    PLANNING --> AUDITING: 计划待审
    AUDITING --> EXECUTING: 审核通过
    AUDITING --> REJECTED: 审核拒绝
    EXECUTING --> VERIFYING: 执行完成
    EXECUTING --> RETRY: 需要重试
    RETRY --> EXECUTING: 重试执行
    VERIFYING --> SUCCESS: 验证通过
    VERIFYING --> FAILED: 验证失败
    FAILED --> RETRY: 允许重试
    SUCCESS --> [*]: 任务完成
    REJECTED --> [*]: 任务终止
    
    class INIT init
    class PLANNING planning
    class AUDITING auditing
    class EXECUTING executing
    class VERIFYING verifying
    class SUCCESS success
    class FAILED failed
    class RETRY retry
    class REJECTED rejected
```

### 5.2 状态说明

| 状态 | 说明 | 可转换状态 |
|------|------|-----------|
| INIT | 初始状态 | PLANNING |
| PLANNING | 规划中 | AUDITING, REJECTED |
| AUDITING | 待审核 | EXECUTING, REJECTED |
| EXECUTING | 执行中 | VERIFYING, RETRY |
| VERIFYING | 验证中 | SUCCESS, FAILED |
| SUCCESS | 成功 | - |
| FAILED | 失败 | RETRY |
| RETRY | 重试中 | EXECUTING |
| REJECTED | 已拒绝 | - |

---

## 6. 数据流

### 6.1 请求处理流程

```mermaid
flowchart LR
    A[用户请求] --> B[API 网关<br/>认证/限流]
    B --> C[Orchestrator<br/>任务创建]
    C --> D[状态机<br/>状态初始化]
    D --> E[Agent 协作循环]
    E --> F1[IntentAgent<br/>意图识别]
    E --> F2[PlanAgent<br/>任务规划]
    E --> F3[ExecAgent<br/>工具执行]
    E --> F4[VerifyAgent<br/>结果验证]
    F1 --> G[记忆系统<br/>上下文管理]
    F2 --> G
    F3 --> G
    F4 --> G
    G --> H[数据存储<br/>持久化]
    H --> I[响应返回]
    
    classDef step fill:#e3f2fd,stroke:#1976d2,color:#0d47a1
    classDef agent fill:#f3e5f5,stroke:#7b1fa2,color:#4a148c
    classDef system fill:#e8f5e9,stroke:#388e3c,color:#1b5e20
    
    class A,B,C,D,H,I step
    class E,F1,F2,F3,F4 agent
    class G system
```

### 6.2 工具调用流程

```mermaid
flowchart LR
    A[ExecAgent] --> B[ToolSelector<br/>工具选择]
    B --> C[BaseTool.execute]
    C --> D1[Validator<br/>参数验证]
    C --> D2[Executor<br/>超时控制]
    C --> D3[RetryHandler<br/>重试处理]
    D1 --> E[ToolImpl<br/>具体实现]
    D2 --> E
    D3 --> E
    E --> F[返回结果]
    
    classDef actor fill:#f3e5f5,stroke:#7b1fa2,color:#4a148c
    classDef tool fill:#e0f7fa,stroke:#0097a7,color:#006064
    classDef impl fill:#fff3e0,stroke:#f57c00,color:#e65100
    
    class A,B actor
    class C,D1,D2,D3 tool
    class E,F impl
```

---

## 7. 部署架构

```mermaid
graph TB
    %% 样式定义
    classDef client fill:#e3f2fd,stroke:#1976d2,color:#0d47a1
    classDef k8s fill:#f3e5f5,stroke:#7b1fa2,color:#4a148c
    classDef ingress fill:#e8f5e9,stroke:#388e3c,color:#1b5e20
    classDef api fill:#fff3e0,stroke:#f57c00,color:#e65100
    classDef agent fill:#fce4ec,stroke:#c2185b,color:#880e4f
    classDef worker fill:#e0f7fa,stroke:#0097a7,color:#006064
    classDef data fill:#efebe9,stroke:#5d4037,color:#3e2723
    classDef external fill:#ffebee,stroke:#d32f2f,color:#b71c1c
    
    subgraph CLIENT["客户端"]
        direction LR
        BROWSER[浏览器]
        MOBILE[移动端]
        API[第三方 API]
    end

    subgraph K8S["Kubernetes 集群"]
        direction LR
        subgraph INGRESS["入口层"]
            direction LR
            NGINX[Ingress Controller<br/>HTTPS/TLS]
        end

        subgraph API_POD["API 层"]
            direction LR
            API_PODS[FastAPI Pods<br/>多副本]
        end

        subgraph AGENT_POD["Agent 层"]
            direction LR
            AGENT_PODS[Agent Pods<br/>多副本]
        end

        subgraph WORKER_POD["Worker 层"]
            direction LR
            WORKER[Celery Workers<br/>异步任务]
        end

        subgraph DATA["数据层"]
            direction LR
            PG[PostgreSQL<br/>主从]
            REDIS[Redis 集群<br/>缓存/队列]
            CHROMA[ChromaDB<br/>向量服务]
        end
    end

    CLOUD["云服务"]
    LLM["LLM Provider"]

    CLIENT --> NGINX
    NGINX --> API_PODS
    API_PODS --> AGENT_PODS
    API_PODS --> WORKER
    AGENT_PODS --> PG
    AGENT_PODS --> REDIS
    AGENT_PODS --> CHROMA
    WORKER --> PG
    WORKER --> REDIS
    API_PODS --> CLOUD
    AGENT_PODS --> LLM
    
    class BROWSER,MOBILE,API client
    class K8S k8s
    class NGINX ingress
    class API_PODS api
    class AGENT_PODS agent
    class WORKER worker
    class PG,REDIS,CHROMA data
    class CLOUD,LLM external
```

---

## 8. 安全架构

```mermaid
graph LR
    %% 样式定义
    classDef request fill:#e3f2fd,stroke:#1976d2,color:#0d47a1
    classDef app fill:#fff3e0,stroke:#f57c00,color:#e65100
    classDef data fill:#fce4ec,stroke:#c2185b,color:#880e4f
    
    subgraph REQUEST["请求安全"]
        direction LR
        TLS[HTTPS/TLS 加密]
        AUTH[JWT 认证]
        RATE[限流保护]
        CORS[CORS 控制]
    end

    subgraph APP["应用安全"]
        direction LR
        RBAC[RBAC 权限]
        VALIDATE[输入验证]
        SANITIZE[SQL/XSS 防护]
    end

    subgraph DATA["数据安全"]
        direction LR
        ENCRYPT[存储加密]
        MASK[敏感脱敏]
        AUDIT[操作审计]
    end

    REQUEST --> APP --> DATA
    
    class TLS,AUTH,RATE,CORS request
    class RBAC,VALIDATE,SANITIZE app
    class ENCRYPT,MASK,AUDIT data
```

---

## 9. 可观测性

| 类型 | 工具 | 指标 |
|------|------|------|
| **日志** | 结构化 JSON 日志 | trace_id 追踪 |
| **指标** | Prometheus | 请求延迟、错误率、队列长度 |
| **链路** | OpenTelemetry | 请求流程、Agent 协作、工具调用 |
| **告警** | Alertmanager | 任务失败、延迟过高、资源不足 |