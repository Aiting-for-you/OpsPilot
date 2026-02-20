<p align="center">
  <img src="docs/images/logo.png" alt="OpsPilot Logo" width="200">
</p>

<h1 align="center">OpsPilot</h1>

<p align="center">
  <strong>企业级运维智能领航系统</strong>
</p>

<p align="center">
  基于 <strong>LangChain + AgentScope</strong> 的多智能体运维平台<br>
  通过 MCP 协议连接大模型与企业系统，实现智能化运维自动化
</p>

<p align="center">
  <a href="#快速开始">快速开始</a> •
  <a href="#核心特性">核心特性</a> •
  <a href="#架构设计">架构设计</a> •
  <a href="#文档">文档</a> •
  <a href="#贡献指南">贡献指南</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=flat&logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/PostgreSQL-15+-4169E1?style=flat&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/License-Apache%202.0-blue?style=flat" alt="License">
</p>

---

## 为什么选择 OpsPilot？

在企业级运维场景中，传统单智能体方案面临严峻挑战：

| 问题 | 传统方案 | OpsPilot 方案 |
|------|----------|---------------|
| **工具过载** | 单 Agent 管理 20+ 工具，选择准确率下降 | 多 Agent 分工协作，每个 Agent 只专注 3-5 个工具 |
| **上下文拥挤** | 工具描述 + 知识库 + 记忆，关键信息被稀释 | 分层架构，决策层与执行层解耦 |
| **决策复杂** | 业务规则 + 合规要求，容易决策失误 | 多 Agent 博弈校验，交叉验证 |
| **单点故障** | 一处出错全局失败 | 状态机驱动，故障自愈 |

## 核心特性

### 🎯 双框架分层架构

- **决策层 (AgentScope)**：多智能体 SOP 编排、消息协调、博弈仲裁
- **执行层 (LangChain)**：工具封装、RAG 检索、记忆管理、确定性逻辑

### 🤖 多智能体协作流水线

```
用户请求 → IntentAgent(意图识别) → PlanAgent(计划制定) → ExecAgent(执行调用) → VerifyAgent(结果验证)
```

### 🔧 MCP 协议标准化

- 统一的工具 Schema 定义
- 跨平台兼容
- 支持动态扩展外部工具

### 🛡️ 生产级运行时

- **工具沙箱**：Docker/本地隔离执行
- **SSE 流式输出**：实时推送任务进度
- **OpenTelemetry 追踪**：全链路可观测

### 🔄 故障自愈机制

- 6 种自动降级策略
- 多 Agent 对等校验 (Peer Review)
- 幂等性保证

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────────────┐
│                          用户接入层                                   │
│                    Web UI / CLI / API Client                         │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────┐
│                          API 网关层                                   │
│              FastAPI Router │ Auth │ Rate Limit │ SSE               │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────┐
│                        编排调度层 (AgentScope)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │ Orchestrator│  │     FSM     │  │   MsgHub    │                  │
│  │  任务编排器  │  │   状态机    │  │  消息中心   │                  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                  │
└─────────┼────────────────┼────────────────┼─────────────────────────┘
          │                │                │
┌─────────▼────────────────▼────────────────▼─────────────────────────┐
│                        Agent 协作层                                   │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐         │
│  │ Intent   │──▶│  Plan    │──▶│  Exec    │──▶│ Verify   │         │
│  │  Agent   │   │  Agent   │   │  Agent   │   │  Agent   │         │
│  │ 意图识别  │   │ 计划制定  │   │ 执行调用  │   │ 结果验证  │         │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘         │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────┐
│                       执行层 (LangChain)                              │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐         │
│  │   MCP    │   │   RAG    │   │  Memory  │   │ Healing  │         │
│  │  工具库   │   │ 检索增强  │   │  记忆库   │   │ 自愈策略  │         │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘         │
└───────┼──────────────┼──────────────┼──────────────┼────────────────┘
        │              │              │              │
┌───────▼──────────────▼──────────────▼──────────────▼────────────────┐
│                          存储层                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  PostgreSQL  │  │   ChromaDB   │  │    Redis     │              │
│  │   业务数据    │  │   向量存储    │  │  会话/缓存   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
        │
┌───────▼─────────────────────────────────────────────────────────────┐
│                         外部系统                                      │
│        ERP │ WMS │ 物流系统 │ 支付网关 │ LLM API                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 技术栈

| 层次 | 技术 | 说明 |
|------|------|------|
| **决策层** | AgentScope | 多智能体编排、MsgHub 消息中心、FSM 状态机 |
| **执行层** | LangChain | LCEL 链式调用、工具封装、RAG 管道 |
| **运行时** | AgentScope Runtime | 工具沙箱、SSE 流式、OpenTelemetry 追踪、A2A 协议 |
| **工具协议** | MCP | Model Context Protocol 标准化工具接口 |
| **API 框架** | FastAPI | RESTful API、异步支持、自动文档 |
| **主数据库** | PostgreSQL | 业务数据持久化 |
| **向量存储** | ChromaDB | 知识库向量检索 |
| **缓存/会话** | Redis | 分布式缓存、会话存储 |
| **前端** | React 19 + TypeScript | Vite 构建、Tailwind CSS、Zustand 状态管理 |

---

## 项目结构

```
OpsPilot/
├── opspilot/                    # 后端核心
│   ├── agents/                  # Agent 定义
│   │   ├── base.py              # Agent 基类
│   │   ├── intent_agent.py      # 意图识别 Agent
│   │   ├── plan_agent.py        # 计划制定 Agent
│   │   ├── exec_agent.py        # 执行 Agent
│   │   ├── verify_agent.py      # 验证 Agent
│   │   └── collaboration.py     # 协作模式
│   ├── runtime/                 # 运行时模块
│   │   ├── sandbox.py           # 工具沙箱
│   │   ├── streaming.py         # SSE 流式输出
│   │   ├── tracing.py           # OpenTelemetry 追踪
│   │   └── a2a.py               # A2A 协议
│   ├── tools/                   # MCP 工具
│   │   ├── mcp.py               # MCP 协议封装
│   │   ├── database.py          # 数据库工具
│   │   ├── healing.py           # 自愈策略
│   │   └── langchain_tools.py   # LangChain 适配
│   ├── mcp/                     # MCP Server
│   │   ├── base.py              # MCP Server 基类
│   │   ├── client.py            # MCP Client 管理器
│   │   └── servers/             # 内置 Server
│   ├── memory/                  # 记忆系统
│   │   ├── vectorstore.py       # ChromaDB 适配
│   │   ├── redis_store.py       # Redis 适配
│   │   └── consolidation.py     # 记忆巩固
│   ├── chains/                  # LangChain LCEL
│   ├── core/                    # 核心引擎
│   ├── api/                     # FastAPI 路由
│   └── prompts/                 # 提示词工程
├── frontend/                    # React 前端
│   ├── src/
│   │   ├── pages/               # 页面组件
│   │   ├── components/          # UI 组件
│   │   ├── hooks/               # 自定义 Hooks
│   │   └── services/            # API 服务
│   └── package.json
├── config/                      # 配置文件
│   └── database.yaml            # 数据库配置
├── docs/                        # 设计文档
├── scripts/                     # 脚本工具
├── tests/                       # 测试用例
├── pyproject.toml               # Python 依赖
└── README.md
```

---

## 快速开始

### 环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | 3.10+ | 后端运行环境 |
| Node.js | 20+ | 前端构建工具 |
| PostgreSQL | 15+ | 主数据库 |
| Redis | 7+ | 缓存与会话存储 |

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/Aiting-for-you/OpsPilot.git
cd OpsPilot
```

#### 2. 配置数据库

编辑 `config/database.yaml`：

```yaml
postgresql:
  host: "localhost"
  port: 5432
  user: "postgres"
  password: "your_password"
  database: "opspilot"

redis:
  host: "localhost"
  port: 6379
  db: 0
```

#### 3. 启动后端

```bash
# 安装依赖
pip install -e .

# 初始化数据库
python scripts/init_data.py

# 启动服务
uvicorn opspilot.api:app --reload --port 8000
```

#### 4. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build
```

### 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 UI | http://localhost:5173 | Web 管理界面 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| API 文档 | http://localhost:8000/redoc | ReDoc |
| 健康检查 | http://localhost:8000/api/v1/health | 服务状态 |

---

## 使用示例

### 工具沙箱

安全隔离执行运维脚本：

```python
from opspilot.runtime import create_sandbox

# 自动选择 Docker/本地模式
sandbox = create_sandbox("auto")

# 执行 Shell 命令
result = await sandbox.execute_shell("kubectl get pods -n production")
print(result.stdout)
```

### SSE 流式输出

实时推送任务执行进度：

```python
from opspilot.runtime import StreamingTaskExecutor

executor = StreamingTaskExecutor()

async for event in executor.execute_with_stream(task_id, execute_fn):
    # event: {"type": "progress", "data": {...}}
    yield event
```

### 外部 MCP Server 管理

动态添加和管理外部工具：

```python
from opspilot.mcp import get_external_mcp_manager

manager = get_external_mcp_manager()

# 添加文件系统工具
manager.add_server({
    "name": "filesystem",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/data"],
    "enabled": True,
})

# 连接并调用
await manager.connect("filesystem")
result = await manager.call_tool("read_file", {"path": "/data/config.json"})
```

### 多 Agent 协作

```python
from opspilot.agents import Orchestrator

orchestrator = Orchestrator()

# 提交任务
task_id = await orchestrator.submit_task(
    intent="procurement",
    params={
        "product": "电子元件A",
        "quantity": 1000,
        "urgent": True
    }
)

# 获取结果
result = await orchestrator.get_result(task_id)
```

---

## 文档

| 文档 | 内容 | 阅读时间 |
|------|------|---------|
| [架构设计](docs/02_ARCHITECTURE.md) | 双框架分层设计、幻觉抑制机制 | 15 分钟 |
| [MCP 工具体系](docs/03_MODULES/mcp_tools.md) | 工具调用为核心、降级策略 | 10 分钟 |
| [数据库设计](docs/10_DATABASE_DATA.md) | 数据模型与初始化 | 8 分钟 |
| [开发日志](dev/DEV_LOG.md) | 完整开发记录与技术决策 | 20 分钟 |

---

## 路线图

| 阶段 | 状态 | 目标 |
|------|------|------|
| MVP | ✅ 完成 | 单 Agent + 基础 RAG |
| 协作版 | ✅ 完成 | 多 Agent + MCP 集成 |
| 工业版 | 🚧 进行中 | 完整状态机 + 工具调用 |
| 规模化 | 📅 计划中 | 分布式部署 + 持续微调 |

---

## 项目状态

| 模块 | 状态 | 说明 |
|------|------|------|
| 核心架构 | ✅ 已完成 | AgentScope + LangChain 混合架构 |
| Runtime | ✅ 已完成 | 沙箱、流式、追踪、A2A |
| 前端 UI | ✅ 已完成 | React 19 + TypeScript |
| MCP 工具 | ✅ 已完成 | 内置工具 + 外部 Server 管理 |
| 文档 | 🚧 进行中 | 架构文档完善中 |
| 测试覆盖 | 📅 计划中 | 单元测试、集成测试 |

---

## 贡献指南

欢迎参与 OpsPilot 开发！

### 贡献流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: 添加某某功能'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

### 代码规范

- Python: 遵循 PEP 8，使用 Black 格式化
- TypeScript: 遵循 ESLint 规则
- 提交信息: 遵循 [Conventional Commits](https://www.conventionalcommits.org/)

---

## 许可证

本项目基于 [Apache 2.0 License](LICENSE) 开源。

---

## 致谢

- [AgentScope](https://github.com/modelscope/agentscope) - 多智能体框架
- [LangChain](https://github.com/langchain-ai/langchain) - LLM 应用框架
- [MCP](https://modelcontextprotocol.io/) - 工具协议标准
