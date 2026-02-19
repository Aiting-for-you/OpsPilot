# OpsPilot 架构文档

## 📊 文档导航

| 文档 | 说明 | 图表数量 |
|------|------|---------|
| [01_overall.md](./01_overall.md) | 整体架构 | 架构图 + 时序图 |
| [module-core.md](./module-core.md) | Core模块 - 编排与状态管理 | 架构图 + 时序图 |
| [module-agent.md](./module-agent.md) | Agent模块 - 智能体协作 | 架构图 + 时序图 |
| [module-tool.md](./module-tool.md) | Tool模块 - 工具集成 | 架构图 + 时序图 |
| [module-memory.md](./module-memory.md) | Memory模块 - 记忆与检索 | 架构图 + 时序图 |
| [module-pricing.md](./module-pricing.md) | Pricing模块 - 博弈定价 | 架构图 + 时序图 |
| [module-customer-service.md](./module-customer-service.md) | CustomerService模块 - 客服工单 | 架构图 + 时序图 |

## 🏗️ 架构概览

### 系统层次

```
用户接入层 → API网关层 → 编排调度层 → Agent协作层 → 业务模块层 → 工具集成层 → 数据存储层
```

### 核心模块

| 模块 | 文件数 | 核心组件 |
|------|-------|---------|
| Core | 7 | Orchestrator, StateMachine, SOPExecutor, Context |
| Agents | 11 | IntentAgent, PlanAgent, ExecAgent, VerifyAgent |
| Tools | 18 | EcommerceTool, DatabaseTool, HTTPTool, MCPTool |
| Memory | 12 | MemoryManager, Retriever, Embedding, Compressor |
| Pricing | 10 | PricingOrchestrator, NegotiationEngine, PricingAgents |
| CustomerService | 9 | TicketRouter, TicketAgents, KnowledgeBase |

### 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | React + TypeScript |
| API | FastAPI + Pydantic |
| Agent | AgentScope + LangGraph |
| LLM | GPT-4 / Claude / DeepSeek |
| 向量库 | ChromaDB |
| 数据库 | PostgreSQL + Redis |

## 📈 统计数据

| 项目 | 数量 |
|------|------|
| 总模块数 | 20+ |
| 总文件数 | 100+ |
| Agent数量 | 20+ |
| 工具数量 | 50+ |
| API接口 | 50+ |

## 🎨 图表说明

本架构文档使用 **Mermaid** 语法编写，支持以下图表类型：

| 图表类型 | 语法 | 用途 |
|---------|------|------|
| 架构图 | `graph TB/LR` | 展示系统结构和组件关系 |
| 时序图 | `sequenceDiagram` | 展示交互流程和消息传递 |
| 状态图 | `stateDiagram-v2` | 展示状态流转 |

## 📖 查看方式

1. **GitHub** - 直接渲染Mermaid图表
2. **VS Code** - 安装 `Markdown Preview Mermaid Support` 插件
3. **在线工具** - [Mermaid Live Editor](https://mermaid.live)
