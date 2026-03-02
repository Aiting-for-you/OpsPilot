<!-- Language Toggle Button -->
<div align="right">
  <a href="README.md">🇨🇳 中文</a> | <a href="README_en.md">🇺🇸 English</a>
</div>

<h1 align="center">OpsPilot</h1>

<p align="center">
  <strong>Enterprise AI Operations Automation Platform</strong>
</p>

<p align="center">
  Connect Large Language Models with enterprise systems to achieve operations automation
</p>

<p align="center">
  <a href="#core-features">Core Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#contributing">Contributing</a>
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

### Home Page Preview

![Home Page Interface](docs/images/Homepage.png)

New Task | Tool Center | SOP Management | Scheduled Tasks | Agent Management | Monitoring & Analytics | System Settings

For more features (such as Game-theoretic Pricing, Customer Service Tickets, etc.), see [Feature Modules](docs/architecture)

---

## Core Features

| Feature | Description |
|---------|-------------|
| **Multi-Agent Collaboration** | Intent → Plan → Exec → Verify closed-loop execution, multi-agent message hub, game-theoretic validation |
| **State Machine Driven** | 8 task states with automatic transitions, retry and rollback mechanisms |
| **SOP Standardization** | Standard Operating Procedure templated execution, scheduled task scheduling |
| **Memory System** | Short-term / Long-term / Working memory three-tier architecture, RAG semantic retrieval |
| **MCP Integration** | Model Context Protocol standardized tool interface, dynamic external tool extension |
| **Fault Self-Healing** | 6 automatic degradation strategies, tool sandbox isolated execution |

---

## Architecture

### Overall Architecture

```mermaid
graph LR
    %% ==================== User Access Layer ====================
    subgraph USER_LAYER["User Access Layer"]
        direction LR
        WEB[Web Frontend<br/>React + TS<br/>Console UI]
        CLI[CLI Command Line<br/>Python CLI<br/>Script Interaction]
        API[API Consumers<br/>Third-party Systems<br/>Webhooks]
    end

    %% ==================== API Gateway Layer ====================
    subgraph GATEWAY_LAYER["API Gateway Layer"]
        direction LR
        FAST[FastAPI<br/>REST API<br/>Request Routing]
        AUTH[Authentication & Authorization<br/>JWT/OAuth2<br/>Access Control]
        MIDDLE[Middleware<br/>Rate Limiting/Circuit Breaker<br/>Logging/Monitoring]
    end

    %% ==================== Orchestration Layer ====================
    subgraph ORCH_LAYER["Orchestration Layer"]
        direction LR
        ORCH[Orchestrator<br/>Main Orchestrator<br/>Task Lifecycle]
        STATE[StateMachine<br/>State Machine<br/>8 State Transitions]
        SOP[SOPExecutor<br/>SOP Executor<br/>Process Standardization]
        SCHED[Scheduler<br/>Scheduled Tasks<br/>Cron Jobs]
    end

    %% ==================== Agent Collaboration Layer ====================
    subgraph AGENT_LAYER["Agent Collaboration Layer"]
        direction LR
        INTENT[IntentAgent<br/>Intent Recognition<br/>Input Parsing]
        PLAN[PlanAgent<br/>Task Planning<br/>Plan Generation]
        EXEC[ExecAgent<br/>Task Execution<br/>Tool Invocation]
        VERIFY[VerifyAgent<br/>Result Verification<br/>Quality Check]
        COLLAB[Collaboration<br/>Agent Collaboration<br/>Message Hub]
    end

    %% ==================== Business Module Layer ====================
    subgraph BIZ_LAYER["Business Module Layer"]
        direction LR
        PRICING[Pricing<br/>Game-theoretic Pricing<br/>Intelligent Quoting]
        CS[CustomerService<br/>Customer Tickets<br/>Issue Handling]
        EVAL[Evaluation<br/>Evaluation System<br/>Quality Metrics]
    end

    %% ==================== Tool Integration Layer ====================
    subgraph TOOLS_LAYER["Tool Integration Layer"]
        direction LR
        ECOM[E-commerce Tools<br/>Products/Orders/Inventory]
        DB[Database Tools<br/>CRUD/Transactions]
        HTTP[HTTP Tools<br/>API Calls]
        FILE[File Tools<br/>Read/Write/Search]
        NOTIFY[Notification Tools<br/>Email/SMS/Webhook]
        MCP[MCP Client<br/>External Tool Integration]
    end

    %% ==================== Memory & Retrieval Layer ====================
    subgraph MEM_LAYER["Memory & Retrieval Layer"]
        direction LR
        SHORT[ShortTerm<br/>Short-term Memory<br/>Redis Session]
        LONG[LongTerm<br/>Long-term Memory<br/>ChromaDB]
        WORK[Working<br/>Working Memory<br/>Task State]
        RETRIEVER[Retriever<br/>Semantic Retrieval<br/>RAG]
        EMBED[Embedding<br/>Vectorization<br/>Semantic Encoding]
    end

    %% ==================== Reasoning Chain Layer ====================
    subgraph CHAIN_LAYER["Reasoning Chain Layer"]
        direction LR
        PROMPT[Prompts<br/>Prompt Library<br/>Template Management]
        CHAIN[Chains<br/>Reasoning Chain<br/>LCEL]
        RUNTIME[Runtime<br/>LLM Runtime<br/>Multi-model Support]
    end

    %% ==================== Data Storage Layer ====================
    subgraph STORAGE_LAYER["Data Storage Layer"]
        direction LR
        PG[(PostgreSQL<br/>Relational Data<br/>Tasks/Users)]
        REDIS[(Redis<br/>Cache/Queue<br/>Session/Rate Limiting)]
        CHROMA[(ChromaDB<br/>Vector Store<br/>Semantic Search)]
        S3[(Object Storage<br/>Files/Logs<br/>Backups)]
    end

    %% ==================== Observability Layer ====================
    subgraph OBS_LAYER["Observability Layer"]
        direction LR
        LOG[Logging<br/>Log Collection<br/>Structured Logging]
        METRIC[Metrics<br/>Metrics Monitoring<br/>Prometheus]
        TRACE[Tracing<br/>Distributed Tracing<br/>OpenTelemetry]
    end

    %% ==================== External Systems ====================
    subgraph EXT_LAYER["External Systems"]
        direction LR
        LLM[LLM Services<br/>GPT/Claude/DeepSeek]
        ERP[ERP Systems<br/>SAP/Yonyou]
        WMS[WMS<br/>Warehouse Management]
        LOGISTICS[Logistics Systems<br/>Express/Delivery]
    end

    %% ==================== Connections ====================
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

    %% ==================== Styles ====================
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

### Core Flow

```mermaid
sequenceDiagram
    participant USER as User
    participant API as API Gateway
    participant AUTH as Authentication
    participant ORCH as Orchestrator
    participant STATE as State Machine
    participant INTENT as IntentAgent
    participant PLAN as PlanAgent
    participant EXEC as ExecAgent
    participant TOOL as Tool Layer
    participant MEMORY as Memory Layer
    participant LLM as LLM Service
    participant DB as Database

    USER->>API: Submit Task Request
    API->>AUTH: Verify Identity
    AUTH-->>API: Return User Info
    API->>ORCH: Create Task
    ORCH->>DB: Save Task Record
    ORCH->>STATE: Initialize State Machine

    rect rgb(240, 248, 255)
        note right of STATE: Intent Recognition Phase
        STATE->>INTENT: Intent Recognition
        INTENT->>MEMORY: Load Context
        INTENT->>LLM: Call LLM Reasoning
        LLM-->>INTENT: Return Intent
        INTENT-->>STATE: Update State
    end

    rect rgb(255, 245, 238)
        note right of STATE: Task Planning Phase
        STATE->>PLAN: Task Planning
        PLAN->>MEMORY: Retrieve Relevant Memory
        PLAN->>LLM: Generate Execution Plan
        LLM-->>PLAN: Return Plan
        PLAN-->>STATE: Update State
    end

    rect rgb(245, 255, 250)
        note right of STATE: Execution Phase (Loop)
        loop Execute Plan Steps
            STATE->>EXEC: Execute Step
            EXEC->>TOOL: Invoke Tool
            TOOL-->>EXEC: Return Result
            EXEC->>MEMORY: Save Execution Memory
            EXEC-->>STATE: Update State
        end
    end

    rect rgb(255, 250, 240)
        note right of STATE: Verification Phase
        STATE->>VERIFY: Result Verification
        VERIFY->>VERIFY: Rule Check
        VERIFY->>VERIFY: Quality Score
        VERIFY-->>STATE: Verification Result
    end

    STATE-->>ORCH: Task Complete
    ORCH->>DB: Update Task Status
    ORCH-->>API: Return Result
    API-->>USER: Response to User
```

---

## Quick Start

### Environment Requirements

| Dependency | Version |
|------------|---------|
| Python | 3.10+ |
| Node.js | 20+ |
| PostgreSQL | 15+ |
| Redis | 7+ |

### Installation Steps

```bash
# 1. Clone the project
git clone https://github.com/Aiting-for-you/OpsPilot.git
cd OpsPilot

# 2. Install backend dependencies
pip install -e .

# 3. Initialize database
python scripts/init_data.py

# 4. Start backend service
uvicorn opspilot.api:app --reload --port 8000

# 5. Install frontend dependencies
cd frontend && npm install

# 6. Start frontend development server
npm run dev
```

### Service Addresses

- Frontend UI: http://localhost:5173
- API Documentation: http://localhost:8000/docs

---

## Documentation

- [Architecture Design](docs/architecture/01_overall.md) — Complete architecture documentation and design concepts
- [Core Modules](docs/architecture/module-core.md) — Detailed core module explanations
- [Agent Module](docs/architecture/module-agent.md) — Multi-agent collaboration mechanism
- [Memory System](docs/architecture/module-memory.md) — Memory system design
- [Tool Module](docs/architecture/module-tool.md) — Tool integration and MCP

---

## Contributing

Contributions via Issues and Pull Requests are welcome! For bug feedback, feature suggestions, or partnership inquiries, please contact via email: cyx0414@outlook.com

---

## License

Apache License 2.0 - See [LICENSE](LICENSE) file for details
