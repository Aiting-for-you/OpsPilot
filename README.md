<h1 align="center">OpsPilot</h1>

<p align="center">
  <strong>企业级 AI 运维自动化平台</strong>
</p>

<p align="center">
  连接大语言模型与企业系统，实现运维自动化
</p>

<p align="center">
  <a href="#核心特性">核心特性</a> •
  <a href="#架构设计">架构设计</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#文档">文档</a> •
  <a href="#贡献">贡献</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=flat&logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/PostgreSQL-15+-4169E1?style=flat&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/License-Apache%202.0-blue?style=flat" alt="License">
  <img src="https://img.shields.io/badge/AgentScope-1.0.16-orange?style=flat" alt="AgentScope">
  <img src="https://img.shields.io/badge/LangChain-0.3.25-blue?style=flat" alt="LangChain">
</p>

---

### 主页预览

![主页界面](docs/images/Homepage.png)

新任务 | 工具中心 | SOP 管理 | 定时调度 | Agent 管理 | 监控分析 | 系统设置

更多功能（如博弈定价、客服工单等）详见 [功能模块](docs/architecture)

---

## 核心特性

| 特性 | 说明 |
|------|------|
| **多 Agent 协作** | Intent → Plan → Exec → Verify 闭环执行流程，多 Agent 消息中枢，博弈校验 |
| **状态机驱动** | 8 种任务状态自动流转，支持重试与回退机制 |
| **SOP 标准化** | 标准操作流程模板化执行，定时任务调度 |
| **记忆系统** | 短期/长期/工作记忆三级架构，RAG 语义检索 |
| **MCP 集成** | Model Context Protocol 标准化工具接口，动态扩展外部工具 |
| **故障自愈** | 6 种自动降级策略，工具沙箱隔离执行 |

---

## 架构设计

### 整体架构

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

### 核心流程

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

## 快速开始

### 环境要求

| 依赖 | 版本 |
|------|------|
| Python | 3.10+ |
| Node.js | 20+ |
| PostgreSQL | 15+ |
| Redis | 7+ |

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/Aiting-for-you/OpsPilot.git
cd OpsPilot

# 2. 安装后端依赖
pip install -e .

# 3. 初始化数据库
python scripts/init_data.py

# 4. 启动后端服务
uvicorn opspilot.api:app --reload --port 8000

# 5. 安装前端依赖
cd frontend && npm install

# 6. 启动前端开发服务器
npm run dev
```

### 服务地址

- 前端界面：http://localhost:5173
- API 文档：http://localhost:8000/docs

---

## 文档

- [架构设计](docs/architecture/01_overall.md) — 完整架构文档与设计理念
- [核心模块](docs/architecture/module-core.md) — 核心模块详解
- [Agent 模块](docs/architecture/module-agent.md) — 多 Agent 协作机制
- [记忆系统](docs/architecture/module-memory.md) — 记忆系统设计
- [工具模块](docs/architecture/module-tool.md) — 工具集成与 MCP

---

## 贡献

欢迎提交 Issue 和 Pull Request！如有 Bug 反馈、功能建议或合作意向，欢迎通过邮箱联系：cyx0414@outlook.com

---

## 许可证

Apache License 2.0 - 详见 [LICENSE](LICENSE) 文件