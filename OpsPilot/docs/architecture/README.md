# OpsPilot 架构文档

## 📚 文档结构

```
architecture/
├── README.md                      # 本文档
├── 01_overall.md                  # 整体架构（1架构图 + 1时序图）
├── module-core.md                 # Core模块（1架构图 + 1时序图）
├── module-agent.md                # Agent模块（1架构图 + 1时序图）
├── module-tool.md                 # Tool模块（1架构图 + 1时序图）
├── module-memory.md               # Memory模块（1架构图 + 1时序图）
├── module-pricing.md              # Pricing模块（1架构图 + 1时序图）
└── module-customer-service.md     # CustomerService模块（1架构图 + 1时序图）
```

## 📖 文档索引

| 文档 | 架构图 | 时序图 | 说明 |
|------|--------|--------|------|
| [01_overall.md](./01_overall.md) | 系统架构图 | 核心流程时序图 | 整体架构概览 |
| [module-core.md](./module-core.md) | Core模块架构图 | 状态流转时序图 | 编排器、状态机、SOP执行器 |
| [module-agent.md](./module-agent.md) | Agent模块架构图 | Agent协作时序图 | 各类Agent实现 |
| [module-tool.md](./module-tool.md) | Tool模块架构图 | 工具调用时序图 | MCP工具、内部工具、电商工具 |
| [module-memory.md](./module-memory.md) | Memory模块架构图 | 记忆读写时序图 | 短期/长期记忆、知识库 |
| [module-pricing.md](./module-pricing.md) | Pricing模块架构图 | 博弈定价时序图 | 多Agent博弈定价系统 |
| [module-customer-service.md](./module-customer-service.md) | 客服模块架构图 | 工单处理时序图 | 智能客服工单路由系统 |

## 🎯 快速导航

- **想了解整体架构？** → [01_overall.md](./01_overall.md)
- **想了解核心模块？** → 按模块查看对应文档

## 📐 图表说明

所有图表使用 **Mermaid** 语法，支持：
- 架构图 (`graph TB`)
- 时序图 (`sequenceDiagram`)

在 GitHub、VS Code（安装 Mermaid 插件）中可直接渲染。
