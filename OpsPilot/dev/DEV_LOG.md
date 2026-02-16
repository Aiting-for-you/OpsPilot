# 开发记录

> 记录每次开发的情况，包括目标、进展、问题、决策

---

## 记录格式

```markdown
## [日期] - [版本/阶段]

### 开发目标
- 目标1
- 目标2

### 完成内容
- [x] 已完成项
- [ ] 未完成项

### 遇到的问题
| 问题 | 解决方案 | 状态 |
|------|---------|------|
| 问题1 | 方案1 | 已解决/待解决 |

### 技术决策
- 决策1：原因...

### 下一步计划
- 计划1
- 计划2
```

---

## 开发记录

### [2026-02-13] - 项目初始化

#### 开发目标
- 完成设计文档和开发文档编写
- 确定代码框架结构

#### 完成内容
- [x] 设计文档体系（docs/）
- [x] 开发文档体系（dev/）
- [x] 状态机与PRD对齐
- [x] 代码框架创建

#### 技术决策
- **前后端分离**：后端优先（CLI + REST API），前端后续扩展
- **Python 全栈**：FastAPI 作为 API 层，支持后续 Web 界面集成

#### 下一步计划
- 实现状态机模块（opspilot.core.state_machine）
- 实现 MCP 工具骨架（opspilot.tools）

---

### [2026-02-13] - 阶段一：基础设施

#### 开发目标
- 实现 utils.exceptions 自定义异常类
- 实现 utils.config 配置加载器
- 实现 utils.logger 日志系统
- 编写单元测试

#### 完成内容
- [x] opspilot/utils/exceptions.py - 自定义异常类（按模块分层）
- [x] opspilot/utils/config.py - 配置加载器（YAML + 环境变量 + Pydantic验证）
- [x] opspilot/utils/logger.py - 日志系统（控制台/文件、结构化日志、trace_id追踪）
- [x] opspilot/utils/__init__.py - 模块导出
- [x] tests/utils/test_exceptions.py - 异常类测试
- [x] tests/utils/test_config.py - 配置加载器测试
- [x] tests/utils/test_logger.py - 日志系统测试
- [x] pyproject.toml - 添加依赖（pydantic、pydantic-settings、pyyaml）

#### 技术决策
- **异常分层设计**：按模块划分异常类（Config/StateMachine/Agent/Tool/Memory），便于精确捕获
- **配置来源优先级**：环境变量 > .env > YAML > 默认值，环境变量前缀 `opspilot_`
- **日志格式**：控制台彩色输出，文件结构化JSON，支持 trace_id 请求追踪
- **依赖注入准备**：配置通过 `get_config()` 获取，而非直接导入，便于测试时替换

#### 遇到的问题
| 问题 | 解决方案 | 状态 |
|------|---------|------|
| 无 | - | - |

#### 下一步计划
- 阶段二：核心模块
- 实现状态机（opspilot/core/state_machine.py）
- 实现上下文管理（opspilot/core/context.py）
- 实现事件系统（opspilot/core/events.py）

---

### [2026-02-13] - 阶段二：核心模块

#### 开发目标
- 实现状态机模块（状态定义、转换控制、行为约束）
- 实现上下文管理（任务上下文、状态机上下文）
- 实现事件系统（事件定义、事件总线）
- 编写单元测试

#### 完成内容
- [x] opspilot/core/state_machine.py - 状态机核心控制器
  - State 枚举（8个状态：INIT/PLANNING/AUDITING/EXECUTING/VERIFYING/SUCCESS/RETRY/REJECTED）
  - StateTransition 转换记录
  - StateConfig 状态配置（允许/禁止动作、提示词约束）
  - StateMachine 核心控制器（转换验证、监听器通知）
- [x] opspilot/core/context.py - 上下文管理
  - StateMachineContext 状态机上下文（序列化/反序列化）
  - TaskContext 任务执行上下文
  - ContextManager 上下文管理器
- [x] opspilot/core/events.py - 事件系统
  - EventType 事件类型枚举
  - 各类事件定义（StateChanged/TaskCreated/AgentStarted/ToolCalled等）
  - EventBus 事件总线（发布/订阅模式、单例模式）
- [x] opspilot/core/__init__.py - 模块导出
- [x] tests/core/test_state_machine.py - 状态机测试（15个测试用例）
- [x] tests/core/test_context.py - 上下文测试（13个测试用例）
- [x] tests/core/test_events.py - 事件系统测试（16个测试用例）

#### 技术决策
- **状态机解耦**：StateMachine 不直接依赖持久化，通过 Context 传递状态，便于测试和替换存储
- **事件驱动**：状态变化通过 EventBus 通知，而非直接回调，降低模块耦合
- **单例 EventBus**：全局共享一个事件总线，简化订阅管理
- **dataclass 简化**：使用 @dataclass 定义数据结构，自动生成 __init__ 等方法

#### 遇到的问题
| 问题 | 解决方案 | 状态 |
|------|---------|------|
| 循环导入 | state_machine.py 末尾延迟导入 Context | 已解决 |

#### 下一步计划
- 阶段三：工具层
- 实现工具基类（opspilot/tools/base.py）
- 实现 MCP 工具（opspilot/tools/mcp.py）
- 实现内部工具（opspilot/tools/internal.py）

---

### [2026-02-13] - 阶段三：工具层

#### 开发目标
- 实现工具基类和注册机制
- 实现 ERP Server（供应商查询、订单管理、库存管理）
- 实现合规 Server（政策查询、合规检查）
- 实现内部工具（格式化、计算、验证）
- 编写单元测试

#### 完成内容
- [x] opspilot/tools/base.py - 工具基础设施
  - ToolSchema 工具定义（名称、描述、参数Schema、超时）
  - ToolResult 执行结果（状态、数据、错误、降级建议）
  - ToolContext 执行上下文
  - BaseToolServer 抽象基类（装饰器注册、参数校验、超时控制）
  - ToolRouter 路由器（多Server管理、重试机制）
- [x] opspilot/tools/mcp.py - MCP Server 实现
  - ERPServer：query_supplier、create_order、query_inventory、query_order、update_order_status
  - ComplianceServer：query_policy、check_compliance
  - Mock 数据支持（供应商、库存、订单）
- [x] opspilot/tools/internal.py - 内部工具
  - format_currency 金额格式化（含中文大写）
  - calculate_total 计算总价（支持折扣）
  - calculate_date 日期计算
  - format_json JSON 格式化
  - validate_data 数据验证（邮箱、手机、身份证等）
  - merge_data 数据合并
- [x] opspilot/tools/__init__.py - 模块导出
- [x] tests/tools/test_base.py - 基础模块测试（17个测试用例）
- [x] tests/tools/test_mcp.py - MCP Server 测试（15个测试用例）
- [x] tests/tools/test_internal.py - 内部工具测试（16个测试用例）
- [x] pyproject.toml - 添加 jsonschema 依赖

#### 技术决策
- **装饰器注册**：使用 @register_tool 装饰器注册工具，代码更清晰
- **JSON Schema 校验**：使用 jsonschema 库验证参数，保证类型安全
- **超时控制**：asyncio.wait_for 实现超时，防止工具阻塞
- **重试机制**：ToolRouter 提供带重试的调用接口，支持指数退避
- **Mock 数据**：内置 Mock 数据便于开发和测试，后续可替换为真实 API

#### 遇到的问题
| 问题 | 解决方案 | 状态 |
|------|---------|------|
| 无 | - | - |

#### 下一步计划
- 阶段四：记忆层
- 实现记忆存储接口（opspilot/memory/base.py）
- 实现短期记忆（opspilot/memory/short_term.py）
- 实现长期记忆（opspilot/memory/long_term.py）
- 实现知识库检索（opspilot/memory/knowledge.py）

---

### [2026-02-14] - 阶段四：记忆层

#### 开发目标
- 实现记忆存储抽象接口
- 实现短期记忆（会话级别，自动过期）
- 实现长期记忆（持久化，向量检索）
- 实现知识库（RAG支持）
- 编写单元测试

#### 完成内容
- [x] opspilot/memory/base.py - 记忆基础模块
  - MemoryType 枚举（SHORT_TERM/LONG_TERM/KNOWLEDGE）
  - MemoryPriority 优先级
  - MemoryEntry 记忆条目（支持过期、序列化）
  - BaseMemoryStore 抽象基类（store/retrieve/delete/search/clear/count）
  - MemoryManager 多路召回管理器
- [x] opspilot/memory/short_term.py - 短期记忆
  - InMemoryShortTermStore 内存存储（Mock实现）
  - ShortTermMemory 管理器（remember/recall/forget/get_context）
  - 自动过期清理机制
- [x] opspilot/memory/long_term.py - 长期记忆
  - InMemoryLongTermStore 内存存储（含简单向量化）
  - LongTermMemory 管理器（memorize/recall/reinforce/consolidate）
  - 记忆强化和巩固机制
- [x] opspilot/memory/knowledge.py - 知识库
  - InMemoryKnowledgeStore 内存存储（倒排索引+向量检索）
  - KnowledgeBase 管理器（query/add/get_context_for_task）
  - Mock 知识数据（政策法规、流程说明等）
- [x] opspilot/memory/__init__.py - 模块导出
- [x] tests/memory/test_short_term.py - 短期记忆测试（14个测试用例）
- [x] tests/memory/test_long_term.py - 长期记忆测试（11个测试用例）
- [x] tests/memory/test_knowledge.py - 知识库测试（13个测试用例）

#### 技术决策
- **Mock 优先**：所有存储使用内存实现，后续可无缝替换为 Redis/ChromaDB
- **简单向量化**：使用字符频率向量，生产环境替换为真实 embedding 模型
- **多路召回**：MemoryManager 支持从多来源同时检索记忆
- **记忆衰减**：短期记忆设置 expires_at，长期记忆支持 reinforce 强化

#### 遇到的问题
| 问题 | 解决方案 | 状态 |
|------|---------|------|
| 无 | - | - |

#### 下一步计划
- 阶段五：Agent层
- 实现 Agent 基类（opspilot/agents/base.py）
- 实现意图识别 Agent（opspilot/agents/intent_agent.py）
- 实现规划 Agent（opspilot/agents/plan_agent.py）
- 实现执行 Agent（opspilot/agents/exec_agent.py）
- 实现验证 Agent（opspilot/agents/verify_agent.py）
- 实现提示词模块（opspilot/prompts/）

---

### [2026-02-14] - 阶段五：Agent层

#### 开发目标
- 实现 Agent 抽象基类和 LLM 客户端接口
- 实现四个核心 Agent（意图/规划/执行/验证）
- 实现提示词模板管理
- 编写单元测试

#### 完成内容
- [x] opspilot/agents/base.py - Agent 基础模块
  - AgentRole 角色枚举（INTENT/PLANNING/EXECUTION/VERIFICATION）
  - AgentConfig 配置类
  - AgentContext 执行上下文
  - AgentOutput 输出结果
  - BaseLLMClient 抽象接口 / MockLLMClient Mock实现
  - BaseAgent 抽象基类（生命周期管理、事件发布）
  - AgentRegistry 单例注册表
- [x] opspilot/agents/intent_agent.py - 意图识别 Agent
  - IntentType 意图类型枚举（7种业务意图）
  - IntentAgent LLM 实现 / MockIntentAgent 规则匹配实现
- [x] opspilot/agents/plan_agent.py - 规划 Agent
  - PlanAgent LLM 实现 / MockPlanAgent 模板匹配实现
  - 预设计划模板（按意图类型）
- [x] opspilot/agents/exec_agent.py - 执行 Agent
  - ExecAgent 工具调用实现 / MockExecAgent 模拟执行
  - 参数引用解析（${step_N.field}）
- [x] opspilot/agents/verify_agent.py - 验证 Agent
  - VerifyAgent LLM 实现 / MockVerifyAgent 规则验证
  - 执行报告生成
- [x] opspilot/prompts/templates.py - 提示词模板
  - PromptTemplate 模板类（变量替换、序列化）
  - PromptRegistry 单例注册表
  - 四个内置提示词模板
- [x] opspilot/prompts/loader.py - 提示词加载器
  - 支持 JSON/YAML 文件加载
- [x] opspilot/agents/__init__.py / opspilot/prompts/__init__.py - 模块导出
- [x] tests/agents/test_base.py - 基础模块测试（15个测试用例）
- [x] tests/agents/test_agents.py - Agent 测试（14个测试用例，含集成测试）
- [x] tests/prompts/test_templates.py - 提示词测试（12个测试用例）

#### 技术决策
- **LLM 接口抽象**：BaseLLMClient 定义接口，MockLLMClient 用于测试，后续可替换真实实现
- **Agent 生命周期**：execute() 方法统一管理开始事件、执行、完成/失败事件
- **Mock 实现优先**：每个 Agent 都有 Mock 版本，使用规则匹配而非 LLM，便于测试
- **提示词模板化**：支持变量替换，便于后续版本管理和 A/B 测试

#### 遇到的问题
| 问题 | 解决方案 | 状态 |
|------|---------|------|
| 无 | - | - |

#### 下一步计划
- 阶段六：编排层
- 实现编排器（opspilot/core/orchestrator.py）
- 实现 SOP 执行器（opspilot/core/sop_executor.py）

---

### [2026-02-14] - 阶段六：编排层

#### 开发目标
- 实现编排器，协调多 Agent 协作
- 实现 SOP 执行器，支持标准操作流程
- 集成状态机、记忆、工具
- 编写单元测试

#### 完成内容
- [x] opspilot/core/orchestrator.py - 编排器
  - Orchestrator 主编排类
  - process() 主入口方法
  - 完整流程：意图识别 -> 规划 -> 审核 -> 执行 -> 验证
  - 状态变化事件发布
  - 短期记忆记录
  - 任务状态查询
- [x] opspilot/core/sop_executor.py - SOP 执行器
  - SOPStepType 步骤类型（顺序/并行/条件/循环/工具）
  - SOPStep 步骤定义
  - SOPDefinition SOP 定义
  - SOPExecutor 执行器（变量解析、条件评估）
  - SOPExecutionResult 执行结果
  - 预定义 SOP：create_order_sop、query_supplier_sop
- [x] opspilot/core/__init__.py - 更新模块导出
- [x] tests/core/test_orchestrator.py - 编排器测试（8个测试用例）
- [x] tests/core/test_sop_executor.py - SOP执行器测试（12个测试用例）

#### 技术决策
- **编排器职责单一**：只负责流程协调，不包含业务逻辑
- **SOP 支持多种执行模式**：顺序、并行、条件分支、循环
- **变量引用**：支持 $var_name 格式的变量引用和替换
- **事件驱动**：状态变化通过 EventBus 发布，便于监控和日志

#### 遇到的问题
| 问题 | 解决方案 | 状态 |
|------|---------|------|
| 无 | - | - |

#### 下一步计划
- 阶段七：API层
- 实现 API Schema（opspilot/api/schemas.py）
- 实现路由（opspilot/api/routes.py）
- 实现中间件（opspilot/api/middleware.py）

---

### [2026-02-14] - 阶段七：API层

#### 开发目标
- 实现 REST API Schema
- 实现 API 路由
- 实现中间件
- 创建主应用入口
- 编写单元测试

#### 完成内容
- [x] opspilot/api/schemas.py - API Schema 定义
  - 任务相关：TaskCreateRequest/Response, TaskStatusResponse, TaskResultResponse
  - 工具相关：ToolCallRequest/Response, ToolSchemaResponse
  - 记忆相关：MemoryStoreRequest, MemorySearchRequest/Response
  - SOP相关：SOPExecuteRequest/Response
  - 知识库相关：KnowledgeQueryRequest/Response
  - 通用：BaseResponse, HealthCheckResponse, ErrorResponse
- [x] opspilot/api/routes.py - API 路由
  - 任务接口：POST /tasks, GET /tasks/{id}, GET /tasks/{id}/result
  - 工具接口：POST /tools/call, GET /tools
  - 记忆接口：POST /memory/store, POST /memory/search
  - SOP接口：POST /sop/execute, GET /sop/list
  - 知识库接口：POST /knowledge/query
  - 健康检查：GET /health
- [x] opspilot/api/middleware.py - 中间件
  - RequestLoggingMiddleware 请求日志
  - ErrorHandlerMiddleware 统一错误处理
  - CORS 配置
- [x] opspilot/main.py - 主应用入口
  - FastAPI 应用配置
  - 生命周期管理
  - 全局异常处理
  - uvicorn 启动
- [x] opspilot/api/__init__.py - 模块导出
- [x] tests/api/test_api.py - API 测试（18个测试用例，含集成测试）
- [x] pyproject.toml - 添加 FastAPI、uvicorn 依赖

#### 技术决策
- **FastAPI 框架**：异步支持好、自动文档、类型安全
- **依赖注入**：使用 Depends 获取服务实例，便于测试替换
- **统一响应格式**：BaseResponse 作为基础，错误使用 ErrorResponse
- **请求追踪**：每个请求分配 request_id，贯穿整个处理流程

#### 遇到的问题
| 问题 | 解决方案 | 状态 |
|------|---------|------|
| 无 | - | - |

---

## 项目完成总结

### 已完成的七个阶段

| 阶段 | 模块 | 主要内容 |
|------|------|---------|
| ✅ 阶段一 | 基础设施 | 异常类、配置加载、日志系统 |
| ✅ 阶段二 | 核心模块 | 状态机、上下文、事件系统 |
| ✅ 阶段三 | 工具层 | 工具基类、MCP Server、内部工具 |
| ✅ 阶段四 | 记忆层 | 短期记忆、长期记忆、知识库 |
| ✅ 阶段五 | Agent层 | 意图/规划/执行/验证Agent、提示词模板 |
| ✅ 阶段六 | 编排层 | 编排器、SOP执行器 |
| ✅ 阶段七 | API层 | REST API、中间件、主应用入口 |

### 项目结构

```
opspilot/
├── __init__.py
├── main.py           # 主应用入口
├── core/             # 核心模块（状态机、编排器）
├── agents/           # Agent模块
├── tools/            # 工具模块
├── memory/           # 记忆模块
├── api/              # API模块
├── utils/            # 工具函数
└── prompts/          # 提示词模块

tests/                # 测试代码
├── core/
├── agents/
├── tools/
├── memory/
├── prompts/
└── api/
```

### 后续优化方向

1. **集成真实LLM**：替换 MockLLMClient 为 OpenAI/Claude 等
2. **持久化存储**：替换内存存储为 Redis/ChromaDB
3. **前端界面**：开发 Web 管理界面
4. **性能优化**：添加缓存、连接池
5. **安全加固**：认证、授权、限流

---

## [2026-02-14] - 项目优化需求分析

### 问题诊断

基于用户反馈和代码审查，识别出以下核心技术问题：

| 问题领域 | 当前实现 | 存在问题 |
|---------|---------|---------|
| **工具调用** | 所有工具定义传递给LLM | 工具过多时突破上下文限制 |
| **失败处理** | 简单重试机制 | 缺乏智能恢复策略 |
| **记忆机制** | 简单存储和检索 | 无权重、无冲突解决 |
| **多智能体调度** | 顺序执行 | 未利用AgentScope特性 |

### 调研成果

#### 1. 工具调用优化方案 - ToolRAG
- **核心思路**：基于查询检索相关工具，而非传递所有工具
- **关键技术**：Sentence Transformers + FAISS 向量检索
- **创新点**：两级检索（类别+工具）、上下文预算管理、工具描述压缩

#### 2. 工具调用失败处理
- **多层容错**：LLM层 → 网络层 → 服务层 → 业务层
- **恢复策略**：自动修正、降级响应、备用服务、人工介入
- **自愈机制**：错误诊断 → 策略选择 → 自动恢复

#### 3. 记忆权重机制
- **权重公式**：`Weight = Base × e^(-λt) × Frequency × Relevance × Timeliness × Confidence`
- **冲突解决**：时效性优先 / 可信度优先 / 融合策略
- **记忆巩固**：聚类合并 → 强化重要记忆 → 遗忘不重要记忆 → 提取知识模式

#### 4. AgentScope 集成方案
- **MsgHub**：消息驱动架构，Agent解耦通信
- **Actor模型**：每个Agent作为独立Actor，高并发低耦合
- **协作模式**：顺序/并行/条件分支
- **分布式支持**：RpcAgent跨机器通信

### 优化计划

创建了详细优化计划文档：`dev/OPTIMIZATION_PLAN.md`

| 阶段 | 内容 | 预计时间 |
|------|------|---------|
| 阶段八 | 工具调用优化（ToolRAG、自愈机制） | 8天 |
| 阶段九 | 记忆机制优化（权重、冲突、巩固） | 6天 |
| 阶段十 | AgentScope集成（MsgHub、分布式） | 10天 |
| 阶段十一 | 集成与验证 | 6天 |

**总计：30个工作日（6周）**

### 创新点总结

| 领域 | 创新点 | 技术价值 |
|------|--------|---------|
| 工具调用 | ToolRAG + 自愈机制 | 解决上下文溢出，提升稳定性 |
| 记忆机制 | 多维权重 + 冲突解决 | 保证信息一致性 |
| 多智能体 | MsgHub + Actor模型 | 解耦、高并发、分布式 |

### 下一步行动

- [x] 确认优化计划
- [x] 开始阶段八：工具调用优化

---

### [2026-02-14] - 阶段八：工具调用优化完成

#### 开发目标
- 实现ToolRAG工具检索机制
- 实现工具描述压缩
- 实现上下文预算管理
- 实现工具自愈机制

#### 完成内容
- [x] opspilot/tools/indexer.py - 工具索引器
  - ToolCategory 工具分类（8类）
  - ToolEmbedding 向量化表示（TF-IDF + 哈希技巧）
  - ToolIndexer 索引构建器
  - SimpleTokenizer 分词器（支持中英文）
- [x] opspilot/tools/retriever.py - 工具检索器
  - RetrievalStrategy 检索策略（语义/关键词/混合/两级）
  - ToolRetriever 检索器实现
  - ToolContextBudget 上下文预算管理
- [x] opspilot/tools/compressor.py - 工具压缩器
  - CompressionLevel 压缩级别（无/轻/中/激进）
  - ToolCompressor 压缩器实现
  - TokenEstimator Token估算器
- [x] opspilot/tools/context_manager.py - 上下文管理器
  - ToolSelectionResult 选择结果
  - ToolContextManager 统一管理接口
  - DynamicToolLoader 动态加载器
- [x] opspilot/tools/healing.py - 自愈机制
  - ErrorType 错误类型（15种）
  - RecoveryStrategy 恢复策略（10种）
  - ErrorDiagnoser 错误诊断器
  - ToolHealer 自愈执行器
- [x] tests/tools/test_tool_optimization.py - 优化测试（40+测试用例）

#### 技术决策
- **两级检索**：先检索类别，再检索工具，减少噪声
- **TF-IDF向量化**：简单高效，无需外部模型依赖
- **多层容错**：LLM层 → 网络层 → 服务层 → 业务层
- **自动修复**：参数缺失/类型错误自动修正

---

### [2026-02-14] - 阶段九：记忆机制优化完成

#### 开发目标
- 实现多维记忆权重评估
- 实现冲突检测与解决
- 实现记忆巩固机制

#### 完成内容
- [x] opspilot/memory/weight.py - 权重计算模块
  - 5因子权重模型（时间衰减/频率/相关性/时效性/可信度）
  - TimeDecayCalculator 艾宾浩斯遗忘曲线
  - FrequencyScorer 访问频率评分
  - RelevanceScorer 相关性评分
  - TimelinessScorer 时效性评分
  - MemoryWeightCalculator 综合计算器
- [x] opspilot/memory/conflict.py - 冲突处理模块
  - ConflictType 冲突类型（6种）
  - ResolutionStrategy 解决策略（10种）
  - ConflictDetector 冲突检测器
  - ConflictResolver 冲突解决器
  - MemoryConflictManager 冲突管理器
- [x] opspilot/memory/consolidation.py - 记忆巩固模块
  - MemoryClusterer 记忆聚类器
  - MemoryReinforcer 记忆强化器
  - MemoryForgetter 记忆遗忘器
  - PatternExtractor 知识模式提取器
  - MemoryConsolidator 综合巩固器
- [x] tests/memory/test_memory_optimization.py - 优化测试（50+测试用例）

#### 技术决策
- **时间衰减**：基于艾宾浩斯遗忘曲线，不同记忆类型不同衰减速率
- **冲突策略**：值更新取最新，矛盾取最可信，补充则合并
- **记忆巩固**：聚类相似记忆 → 强化重要 → 遗忘不重要 → 提取知识模式

---

### [2026-02-14] - 阶段十：AgentScope集成完成

#### 开发目标
- 实现消息驱动架构（MsgHub）
- 实现Actor模式Agent
- 实现多智能体协作模式

#### 完成内容
- [x] opspilot/agents/msg_hub.py - 消息中心
  - MessageType 消息类型（8种）
  - AgentMessage 消息定义（兼容AgentScope）
  - MessageHub 消息中心（单例模式）
  - 发布/订阅机制、单播/广播、历史记录、追踪链
- [x] opspilot/agents/actor.py - Actor模式
  - ActorState 状态（5种）
  - BaseActor 抽象基类
  - IntentActor/PlanActor/ExecActor/VerifyActor 具体实现
  - ActorRegistry 全局注册表
- [x] opspilot/agents/collaboration.py - 协作模式
  - CollaborationMode 协作模式（6种）
  - SequentialCollaboration 顺序协作
  - ParallelCollaboration 并行协作
  - ConditionalCollaboration 条件分支
  - PipelineCollaboration 流水线
  - CollaborationOrchestrator 编排器
- [x] tests/agents/test_multi_agent.py - 集成测试（40+测试用例）

#### 技术决策
- **消息驱动**：Agent间通过消息通信，解耦依赖
- **Actor模型**：每个Agent独立状态空间，异步消息处理
- **协作抽象**：支持顺序/并行/条件/流水线多种模式
- **兼容设计**：可独立运行，也可集成AgentScope分布式部署

---

## 优化开发完成总结

### 已完成的优化阶段

| 阶段 | 模块 | 创新点 | 测试用例 |
|------|------|--------|----------|
| ✅ 阶段八 | 工具层 | ToolRAG + 自愈机制 | 40+ |
| ✅ 阶段九 | 记忆层 | 多维权重 + 冲突解决 | 50+ |
| ✅ 阶段十 | Agent层 | MsgHub + Actor + 协作 | 40+ |

### 创新成果

#### 1. 工具调用优化
- **ToolRAG**：基于查询的工具检索，解决上下文溢出
- **两级检索**：类别 → 工具，提高检索精度
- **上下文预算**：动态控制工具描述token数
- **自愈机制**：多层容错 + 自动修复

#### 2. 记忆机制优化
- **多维权重**：5因子综合评估（时间衰减、频率、相关性、时效性、可信度）
- **艾宾浩斯曲线**：模拟人类记忆衰减
- **冲突解决**：智能处理信息矛盾
- **记忆巩固**：聚类、强化、遗忘、模式提取

#### 3. 多智能体调度
- **消息驱动**：MsgHub统一消息路由
- **Actor模型**：独立状态、异步处理
- **多种协作**：顺序/并行/条件/流水线
- **可扩展**：支持分布式部署

### 项目价值提升

| 维度 | 优化前 | 优化后 |
|------|--------|--------|
| 工具数量上限 | ~20个（受上下文限制） | 100+（动态检索） |
| 工具调用成功率 | 基础重试 | 多层自愈 |
| 记忆一致性 | 无保证 | 冲突自动解决 |
| Agent并发 | 顺序执行 | 并行支持 |
| 扩展性 | 单机 | 分布式就绪 |

---

## [2026-02-14] - 阶段十二~十四：AgentScope+LangChain混合架构优化

### 开发目标

充分利用两者的优势，构建真正有价值的企业级系统：
- **AgentScope负责**：多智能体调度、分布式通信、消息驱动
- **LangChain负责**：工具调用生态、RAG检索增强、链式执行

### 完成内容

#### 阶段十二：AgentScope核心集成

- [x] opspilot/integration/agentscope_integration.py - AgentScope集成模块
  - ASMessage 消息定义（兼容AgentScope Msg）
  - MessageAdapter 消息适配器（LangChain ↔ AgentScope）
  - ASAgentBase Agent基类（消息驱动、Actor模型）
  - ASIntentAgent/ASPlanAgent/ASExecAgent/ASVerifyAgent 具体实现
  - AgentServer/AgentClient 分布式支持
  - ServiceRegistry/ServiceDiscovery 服务发现

#### 阶段十三：LangChain集成

- [x] opspilot/integration/langchain_integration.py - LangChain集成模块
  - LCToolAdapter 工具适配器（opspilot ↔ LangChain）
  - LCToolRegistry 工具注册表
  - MCPToolWrapper MCP工具包装器
  - LCRetrieverAdapter 检索器适配器
  - LCMemoryAdapter 记忆适配器
  - LCChainExecutor 链式执行器

#### 阶段十四：混合编排器

- [x] opspilot/integration/hybrid_orchestrator.py - 混合编排器
  - HybridOrchestrator 核心编排器
  - SequentialWorkflow/ParallelWorkflow/ConditionalWorkflow 工作流
  - IdempotencyManager 幂等性管理器
  - ResultCache 结果缓存
  - 工具注册、Agent管理、统计监控

#### 阶段十四：性能基准测试

- [x] benchmarks/ 基准测试套件
  - runner.py - 测试运行器（延迟、吞吐量、P95/P99）
  - tool_benchmark.py - 工具层测试（索引、检索、压缩、调用、自愈）
  - memory_benchmark.py - 记忆层测试（存储、检索、权重、冲突、巩固）
  - agent_benchmark.py - Agent层测试（消息、协作、并行、吞吐量）
  - e2e_benchmark.py - 端到端测试（完整流程、并发、压力测试）

#### 阶段十四：集成测试

- [x] tests/integration/test_hybrid_integration.py - 混合架构集成测试
  - AgentScope集成测试（消息、Agent、服务发现）
  - LangChain集成测试（工具、注册表、调用）
  - 混合编排器测试（顺序/并行执行、幂等性、缓存）
  - 端到端测试（完整工作流、错误处理）
  - 性能测试（吞吐量、并发）

### 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                    Hybrid Orchestration                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   AgentScope Layer (调度层)                                     │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  MsgHub ──► IntentAgent ──► PlanAgent ──► Coordination   │  │
│   │   (消息驱动)    (意图识别)     (规划)      (协调)        │  │
│   └─────────────────────────────────────────────────────────┘  │
│                           │                                     │
│                           ▼                                     │
│   LangChain Layer (执行层)                                      │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  Tool Router ──► MCP Tools ──► RAG ──► Chain Executor   │  │
│   │   (工具路由)     (工具调用)    (检索)    (链式执行)      │  │
│   └─────────────────────────────────────────────────────────┘  │
│                           │                                     │
│                           ▼                                     │
│   Verification Layer (验证层)                                   │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  VerifyAgent ──► 结果校验 ──► 输出格式化                  │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 技术决策

#### 1. AgentScope优势利用
| 特性 | 利用方式 | 价值 |
|------|---------|------|
| MsgHub | 统一消息路由，Agent解耦通信 | 降低耦合度 |
| Actor模型 | 每个Agent独立状态空间 | 高并发支持 |
| RpcAgent | 分布式Agent调用 | 水平扩展 |
| 服务发现 | 自动注册与发现 | 动态扩缩容 |

#### 2. LangChain优势利用
| 特性 | 利用方式 | 价值 |
|------|---------|------|
| StructuredTool | 标准化工具接口 | 工具生态丰富 |
| Retriever | RAG检索增强 | 知识注入 |
| LCEL | 链式表达式 | 灵活组合 |
| Memory | 对话记忆管理 | 上下文保持 |

#### 3. 混合设计原则
- **调度与执行分离**：AgentScope调度，LangChain执行
- **消息驱动**：所有交互通过消息传递
- **工具可扩展**：MCP工具自动包装为LangChain工具
- **分布式就绪**：支持单机运行，可平滑升级到分布式

### 项目结构更新

```
opspilot/
├── opspilot/
│   ├── integration/          # ✨新增：集成模块
│   │   ├── agentscope_integration.py  # AgentScope集成
│   │   ├── langchain_integration.py   # LangChain集成
│   │   └── hybrid_orchestrator.py     # 混合编排器
│   ├── agents/               # Agent模块
│   ├── tools/                # 工具模块
│   ├── memory/               # 记忆模块
│   └── ...
├── benchmarks/               # ✨新增：性能基准测试
│   ├── runner.py             # 测试运行器
│   ├── tool_benchmark.py     # 工具层测试
│   ├── memory_benchmark.py   # 记忆层测试
│   ├── agent_benchmark.py    # Agent层测试
│   └── e2e_benchmark.py      # 端到端测试
├── tests/
│   ├── integration/          # ✨新增：集成测试
│   │   └── test_hybrid_integration.py
│   └── ...
└── ...
```

### 创新成果总结

| 领域 | 创新点 | 技术价值 |
|------|--------|---------|
| 混合架构 | AgentScope调度 + LangChain执行 | 发挥两者优势 |
| 消息驱动 | 统一消息格式，解耦通信 | 易于扩展 |
| 工具适配 | MCP → LangChain自动转换 | 工具生态融合 |
| 幂等性 | 请求去重 + 结果缓存 | 企业级可靠 |
| 性能基准 | 多层次基准测试套件 | 可量化优化 |

---

<!-- 混合架构优化完成 -->

---

## [2026-02-14] - 框架集成修复：真正使用 LangChain + AgentScope

### 问题发现

之前的实现存在严重的框架集成偏差：

| 设计要求 | 之前实现 | 问题 |
|---------|---------|------|
| LangChain 负责 ChromaDB | 自研 mock embedding | ❌ 无法使用向量数据库生态 |
| LangChain 负责 Redis | 自研内存存储 | ❌ 无分布式能力 |
| LangChain 负责 Tool | 自研 ToolRouter | ❌ 无法使用工具生态 |
| LangChain 负责 LCEL | 未实现 | ❌ 无链式调用能力 |
| AgentScope 负责 Agent | 自研 Actor 模拟 | ❌ 无分布式能力 |

### 修复内容

#### 1. memory/ 模块 - 使用 LangChain ChromaDB + Redis

**新增文件**：
- `memory/vectorstore.py` - ChromaDB 向量存储适配器
- `memory/redis_store.py` - Redis 会话存储适配器

**修改文件**：
- `memory/long_term.py` - 默认使用 ChromaDB
- `memory/short_term.py` - 默认使用 Redis

**保留创新**：
- `memory/weight.py` - 5因子权重模型 ✅
- `memory/conflict.py` - 冲突检测与解决 ✅
- `memory/consolidation.py` - 记忆巩固机制 ✅

#### 2. tools/ 模块 - 使用 LangChain Tool + Embeddings

**新增文件**：
- `tools/langchain_tools.py` - MCP → LangChain Tool 适配器
- `tools/embeddings.py` - LangChain Embeddings 适配器

**保留创新**：
- `tools/healing.py` - 6种自愈策略 ✅
- `tools/compressor.py` - Token 压缩 ✅
- `tools/retriever.py` - 两级检索 ✅

#### 3. chains/ 模块 - 新增 LangChain LCEL

**新增文件**：
- `chains/__init__.py` - 模块入口
- `chains/prompts.py` - 提示模板
- `chains/executor.py` - LCEL 链式执行器
  - RAGChain - RAG 检索链
  - ToolChain - 工具调用链
  - DecisionChain - 决策验证链
  - OpsChainExecutor - 统一执行器

#### 4. agents/ 模块 - 使用 AgentScope

**新增文件**：
- `agents/agentscope_adapter.py` - AgentScope 适配器
  - AgentScopeAdapter - 框架适配
  - OpsAgentBase - 自动适配 AgentScope 的 Agent 基类
  - IntentAgent/PlanAgent/ExecAgent/VerifyAgent - 具体实现

**保留创新**：
- `agents/msg_hub.py` - 消息中心设计 ✅
- `agents/collaboration.py` - 协作模式 ✅
- `agents/actor.py` - Actor 模式 ✅

### 架构修正

```
修正前（偏差）：
┌─────────────────────────────────────┐
│  自研 Actor + 自研 ToolRouter       │
│  + 自研 mock embedding + mock 存储  │
│                                     │
│  问题：无法使用框架生态              │
└─────────────────────────────────────┘

修正后（按文档要求）：
┌─────────────────────────────────────┐
│         AgentScope（决策层）         │
│  MsgHub + FSM + Agent编排 + 博弈    │
└─────────────────┬───────────────────┘
                  │ 调用
                  ▼
┌─────────────────────────────────────┐
│         LangChain（执行层）          │
│  Tool(Retriver(RAG) + ChromaDB      │
│  + Redis + LCEL Chain)              │
└─────────────────────────────────────┘
```

### 依赖更新

```toml
dependencies = [
    # AgentScope - 决策层
    "agentscope>=0.1.0",
    # LangChain - 执行层
    "langchain>=0.3.0",
    "langchain-core>=0.3.0",
    "langchain-community>=0.3.0",
    "langchain-chroma>=0.1.0",  # ChromaDB 向量存储
    "langchain-redis>=0.0.1",   # Redis 会话存储
    "redis>=5.0.0",
]
```

### 测试验证

**新增测试**：
- `tests/test_framework_integration.py` - 框架集成测试
  - TestLangChainIntegration - LangChain 集成测试
  - TestAgentScopeIntegration - AgentScope 集成测试
  - TestFrameworkStatus - 框架状态检查
  - TestIntegration - 端到端测试

### 修复统计

| 类型 | 数量 |
|------|------|
| 新增文件 | 6 |
| 修改文件 | 5 |
| 删除文件 | 0（保留创新代码）|
| 测试文件 | 1 |

### 完成度对比

| 模块 | 修复前 | 修复后 |
|------|--------|--------|
| memory 存储 | ❌ Mock | ✅ ChromaDB + Redis |
| tools 封装 | ❌ 自研 | ✅ LangChain Tool |
| embeddings | ❌ Mock | ✅ LangChain Embeddings |
| chains | ❌ 无 | ✅ LCEL |
| agents | ❌ 模拟 | ✅ AgentScope 适配 |
| 创新保留 | - | ✅ 100% |

---

<!-- 框架集成修复完成 -->

---

## [2026-02-15] - 前端开发：OpsPilot Web UI

### 项目重命名

| 项目 | 原名 | 新名 |
|------|------|------|
| 目录 | OpsGPT | OpsPilot |
| Python 包 | opsgpt | opspilot |
| 含义 | 运维 GPT | 运维领航员 |

### 技术选型

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 19.x | 前端框架 |
| TypeScript | 5.9 | 类型安全 |
| Vite | 7.x | 构建工具 |
| Tailwind CSS | 4.x | 样式框架 |
| Zustand | 5.x | 状态管理 |
| React Router | 7.x | 路由管理 |
| React Query | 5.x | 数据请求 |
| Lucide React | 0.564 | 图标库 |
| Axios | 1.13 | HTTP 客户端 |

### 前端架构

```
frontend/
├── src/
│   ├── components/
│   │   └── layout/
│   │       └── Layout.tsx      # 主布局（侧边栏+头部）
│   ├── pages/
│   │   ├── Dashboard.tsx       # 仪表盘
│   │   ├── Tasks.tsx           # 任务管理
│   │   ├── Tools.tsx           # 工具调用
│   │   ├── SOP.tsx             # SOP 执行
│   │   ├── Agents.tsx          # Agent 监控
│   │   └── Settings.tsx        # 系统设置
│   ├── services/
│   │   └── api.ts              # API 服务封装
│   ├── store/
│   │   └── index.ts            # Zustand 状态管理
│   ├── types/
│   │   └── index.ts            # TypeScript 类型定义
│   ├── App.tsx                 # 应用入口
│   ├── main.tsx                # React 入口
│   └── index.css               # Tailwind 样式
├── index.html
├── tailwind.config.js
├── postcss.config.js
├── vite.config.ts
└── package.json
```

### 页面功能

#### 1. 仪表盘 (Dashboard)
- 系统统计卡片（活跃任务、完成任务、平均耗时、失败率）
- Agent 状态实时监控
- 系统健康状态显示
- 最近任务列表

#### 2. 任务管理 (Tasks)
- 创建新任务（自然语言输入）
- 任务列表展示
- 任务详情查看
- 执行轨迹可视化
- 结果 JSON 展示

#### 3. 工具调用 (Tools)
- 工具列表展示
- 工具 Schema 查看
- 参数 JSON 编辑
- 工具执行与结果展示
- 降级模式提示

#### 4. SOP 执行 (SOP)
- SOP 列表选择
- 步骤可视化（进度条）
- 变量配置
- 执行结果展示

#### 5. Agent 监控 (Agents)
- Agent 状态概览
- 协作流程可视化
- 消息中心 (MsgHub)
- Agent 详细信息表格

#### 6. 系统设置 (Settings)
- API 配置
- LLM 配置
- Agent 配置
- 本地存储持久化

### UI 设计

#### 配色方案
- 主色：Primary Blue (#3b82f6)
- 背景：Dark (#0f172a)
- 边框：Dark-700 (#334155)
- 文字：Dark-100 (#f1f5f9)

#### 组件设计
- 卡片：圆角、边框、阴影
- 按钮：Primary/Secondary/Ghost 三种风格
- 输入框：暗色背景、边框高亮
- 表格：深色主题、悬浮效果

### API 集成

```typescript
// API 端点映射
const API_BASE_URL = 'http://localhost:8000/api/v1';

// 主要接口
POST /tasks              // 创建任务
GET  /tasks/:id          // 查询任务状态
GET  /tasks/:id/result   // 获取任务结果
GET  /tools              // 获取工具列表
POST /tools/call         // 调用工具
GET  /sop/list           // 获取 SOP 列表
POST /sop/execute        // 执行 SOP
GET  /health             // 健康检查
```

### 状态管理

```typescript
// Zustand Store
interface AppState {
  currentTask: Task | null;
  tasks: Task[];
  tools: Tool[];
  agents: AgentStatus[];
  sidebarOpen: boolean;
  activeTab: string;
  isLoading: boolean;
  error: string | null;
}
```

### 开发命令

```bash
# 安装依赖
cd frontend && npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

### 完成统计

| 项目 | 数量 |
|------|------|
| React 组件 | 7 |
| TypeScript 文件 | 9 |
| 样式文件 | 1 |
| 配置文件 | 4 |
| 总代码行数 | ~800 |

---

<!-- 前端开发完成 -->

---

## [2026-02-15] - AgentScope Runtime & Studio 特性集成

### 集成背景

AgentScope 提供了 Runtime 和 Studio 两大配套组件，为 OpsPilot 提供生产级能力：

| 组件 | 核心能力 | 适用场景 |
|------|---------|----------|
| **Runtime** | 工具沙箱、AaaS、A2A | 生产部署、安全隔离 |
| **Studio** | 可视化追踪、项目管理 | 开发调试、性能分析 |

### 新增模块：opspilot/runtime/

```
opspilot/runtime/
├── __init__.py          # 模块入口
├── sandbox.py           # 工具沙箱
├── streaming.py         # SSE 流式输出
├── tracing.py           # OpenTelemetry 追踪
└── a2a.py               # Agent-to-Agent 协议
```

### 1. 工具沙箱 (sandbox.py)

**特性**：
- 加固沙箱环境，安全隔离执行运维脚本
- 支持 Python/Shell 双模式
- 本地沙箱 + Docker 沙箱自动切换
- 资源限制（内存、超时、命令白名单）

**核心类**：
```python
class LocalSandbox(BaseSandbox):
    """本地沙箱 - 开发环境"""
    async def execute_python(code: str) -> SandboxResult
    async def execute_shell(command: str) -> SandboxResult

class DockerSandbox(BaseSandbox):
    """Docker 沙箱 - 生产环境"""
    async def execute_python(code: str) -> SandboxResult
    async def execute_shell(command: str) -> SandboxResult

class ToolSandboxManager:
    """沙箱管理器 - 自动选择最佳沙箱"""
    async def execute_tool(tool_name, tool_code, tool_command)
```

**使用示例**：
```python
from opspilot.runtime import create_sandbox

sandbox = create_sandbox("auto")  # 自动选择 Docker/本地
result = await sandbox.execute_shell("kubectl get pods")
```

### 2. SSE 流式输出 (streaming.py)

**特性**：
- Server-Sent Events 实时推送
- OpenAI SDK 兼容格式
- 任务/Agent/LLM 多级事件
- 支持中断与恢复

**事件类型**：
```python
class StreamEventType(Enum):
    # 任务事件
    TASK_START = "task_start"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETE = "task_complete"
    TASK_ERROR = "task_error"
    
    # Agent 事件
    AGENT_START = "agent_start"
    AGENT_MESSAGE = "agent_message"
    AGENT_TOOL_CALL = "agent_tool_call"
    AGENT_COMPLETE = "agent_complete"
    
    # LLM 事件
    LLM_TOKEN = "llm_token"
    LLM_COMPLETE = "llm_complete"
```

**使用示例**：
```python
from opspilot.runtime import StreamingTaskExecutor

executor = StreamingTaskExecutor()
async for event in executor.execute_with_stream(task_id, execute_fn):
    # SSE 格式: event: task_start\ndata: {...}\n\n
    yield event
```

### 3. OpenTelemetry 追踪 (tracing.py)

**特性**：
- LLM 调用追踪（Token、耗时）
- Agent 调用链追踪
- 工具执行追踪
- 自定义 Span 装饰器

**核心类**：
```python
class Tracer:
    """通用追踪器"""
    def start_span(name, attributes) -> str
    def end_span(span_id, status) -> TraceSpan
    @contextmanager
    def span(name)  # 上下文管理器
    @traced(name)   # 装饰器

class LLMTracer(Tracer):
    """LLM 专用追踪器"""
    def trace_llm_call(model, prompt, completion, tokens, latency)

class AgentTracer(Tracer):
    """Agent 专用追踪器"""
    def trace_agent_call(agent_name, input, output, duration, tools)

class ToolTracer(Tracer):
    """工具专用追踪器"""
    def trace_tool_call(tool_name, params, result, duration, success)
```

**使用示例**：
```python
from opspilot.runtime import get_llm_tracer, traced

@traced("my_function")
async def my_function():
    # 自动追踪
    pass

tracer = get_llm_tracer()
tracer.trace_llm_call(
    model="gpt-4",
    prompt="...",
    completion="...",
    prompt_tokens=100,
    completion_tokens=50,
    latency_ms=150,
)
```

### 4. A2A 协议 (a2a.py)

**特性**：
- Agent 发现与注册
- 标准化消息格式
- 技能发布与发现
- 本地/分布式注册中心

**核心类**：
```python
class AgentCard:
    """Agent 名片"""
    agent_id: str
    name: str
    description: str
    skills: List[AgentSkill]
    endpoints: Dict[str, str]
    status: AgentStatus

class A2AMessage:
    """A2A 消息"""
    message_id: str
    sender_id: str
    receiver_id: str
    skill_id: str
    content: Any

class LocalAgentRegistry(AgentRegistry):
    """本地注册中心"""
    async def register(agent_card) -> bool
    async def discover(skill_id, tags) -> List[AgentCard]
    async def get_agent(agent_id) -> AgentCard

class A2AClient:
    """A2A 客户端"""
    async def discover_agents(skill_id) -> List[AgentCard]
    async def invoke_skill(agent_id, skill_id, input) -> Any

class A2AServer:
    """A2A 服务端"""
    def register_skill_handler(skill_id, handler)
    async def handle_message(message) -> A2AMessage
```

**使用示例**：
```python
from opspilot.runtime import create_agent_card, A2AServer, LocalAgentRegistry

# 创建 Agent 名片
card = create_agent_card(
    agent_id="intent-agent-001",
    name="IntentAgent",
    description="意图识别 Agent",
    skills=[{
        "id": "intent_recognition",
        "name": "意图识别",
        "description": "识别用户意图",
    }],
)

# 启动 A2A 服务
registry = LocalAgentRegistry()
server = A2AServer(card, registry)
server.register_skill_handler("intent_recognition", handle_intent)
await server.start()
```

### 前端升级

#### 新增页面：Tracing.tsx

**功能**：
- OpenTelemetry 追踪可视化
- Span 树形展示
- 时间轴瀑布图
- LLM/Agent/Tool 过滤
- 详情面板

**特性**：
- 调用链树形展示
- 时间轴瀑布视图
- 事件详情查看
- 按类型过滤

#### 新增 Hook：useSSE.ts

**功能**：
- SSE 连接管理
- 自动重连（指数退避）
- 事件解析与分发

```typescript
export function useSSE(options: UseSSEOptions): UseSSEReturn {
  // 自动连接、事件收集、状态管理
}

export function useTaskStream(taskId: string | null) {
  // 任务专用流订阅
}
```

#### API 服务扩展

新增接口：
```typescript
// 追踪接口
getTrace(traceId: string): Promise<{ spans: TraceSpan[] }>
getTaskTrace(taskId: string): Promise<{ spans: TraceSpan[] }>

// A2A 接口
discoverAgents(skillId?: string): Promise<{ agents: AgentCard[] }>
getAgent(agentId: string): Promise<AgentCard>
invokeAgentSkill(agentId, skillId, input): Promise<{ result: any }>
```

### 依赖更新

```toml
# pyproject.toml 新增
"agentscope-runtime>=0.1.0",
"opentelemetry-api>=1.20.0",
"opentelemetry-sdk>=1.20.0",
"opentelemetry-exporter-otlp>=1.20.0",
"sse-starlette>=2.0.0",
```

### 架构升级

```
┌─────────────────────────────────────────────────────────────┐
│                      OpsPilot Frontend                       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │Dashboard│ │  Tasks  │ │ Agents  │ │ Tracing │           │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
│       │          │          │          │                    │
│       └──────────┴──────────┴──────────┘                    │
│                      │                                      │
│              useSSE / api.ts                                │
└──────────────────────┼──────────────────────────────────────┘
                       │ SSE / REST
┌──────────────────────┼──────────────────────────────────────┐
│                  OpsPilot Backend                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   opspilot/runtime/                   │  │
│  │  ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌─────────┐   │  │
│  │  │ Sandbox │ │Streaming │ │ Tracing │ │   A2A   │   │  │
│  │  └────┬────┘ └────┬─────┘ └────┬────┘ └────┬────┘   │  │
│  │       │           │            │           │        │  │
│  │       └───────────┴────────────┴───────────┘        │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │ AgentScope │  │  LangChain │  │ ChromaDB   │           │
│  │  Runtime   │  │    LCEL    │  │   Redis    │           │
│  └────────────┘  └────────────┘  └────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### 完成统计

| 类型 | 数量 |
|------|------|
| Python 新增模块 | 4 |
| Python 代码行数 | ~1200 |
| React 新增组件 | 1 (Tracing) |
| React 新增 Hook | 1 (useSSE) |
| TypeScript 类型 | +50 行 |
| 依赖包 | +5 |

### 集成优势

| 特性 | 价值 |
|------|------|
| **工具沙箱** | 运维脚本安全隔离执行 |
| **SSE 流式** | 前端实时展示执行进度 |
| **OpenTelemetry** | 生产级链路追踪 |
| **A2A 协议** | Agent 间标准化通信 |

---

<!-- AgentScope Runtime/Studio 集成完成 -->

---

## [2026-02-15] - MCP 核心工具开发 + 测试覆盖

### 新增工具模块

| 模块 | 文件 | 功能 |
|------|------|------|
| **数据库工具** | `tools/database.py` | MySQL/PostgreSQL/Mock 数据库操作 |
| **HTTP API 工具** | `tools/http_client.py` | REST/GraphQL API 调用 |
| **运维工具** | `tools/devops.py` | Kubernetes/系统监控/命令执行 |
| **文件工具** | `tools/file_ops.py` | 文件读写/日志解析/搜索 |
| **通知工具** | `tools/notification.py` | 邮件/钉钉/企业微信通知 |

### 1. 数据库工具 (database.py)

**特性**：
- MySQL、PostgreSQL 连接支持
- Mock 数据库（开发测试）
- SQL 注入检测
- 连接池管理
- 批量操作

**核心类**：
```python
class DatabaseServer(BaseToolServer):
    # 工具列表
    - db_query: 执行 SELECT 查询
    - db_execute: 执行 INSERT/UPDATE/DELETE
    - db_batch_insert: 批量插入
    - db_describe_table: 查询表结构
    - db_health_check: 健康检查
```

**安全特性**：
```python
# SQL 注入检测模式
SQL_INJECTION_PATTERNS = [
    r";\s*DROP", r";\s*DELETE", r";\s*TRUNCATE",
    r"UNION\s+SELECT", r"OR\s+1\s*=\s*1",
]

# 命令白名单验证
def validate_sql(sql, allowed_commands):
    # 检查注入模式 + 命令类型
```

### 2. HTTP API 工具 (http_client.py)

**特性**：
- REST API (GET/POST/PUT/DELETE)
- GraphQL 查询
- 认证支持 (Basic/Bearer/API Key)
- 响应缓存
- 批量请求

**核心类**：
```python
class ApiServer(BaseToolServer):
    # 工具列表
    - http_get: GET 请求
    - http_post: POST 请求
    - http_put: PUT 请求
    - http_delete: DELETE 请求
    - graphql_query: GraphQL 查询
    - http_batch: 批量请求
```

**认证配置**：
```python
class AuthConfig:
    auth_type: str  # none/basic/bearer/api_key/oauth2
    username: str
    password: str
    token: str
    api_key: str
```

### 3. 运维工具 (devops.py)

**特性**：
- Kubernetes 工具 (kubectl 封装)
- 系统监控 (CPU/内存/磁盘)
- 安全命令执行
- 命令白名单

**核心类**：
```python
class DevOpsServer(BaseToolServer):
    # Kubernetes 工具
    - k8s_get_pods: 获取 Pod 列表
    - k8s_get_services: 获取 Service 列表
    - k8s_describe_pod: 获取 Pod 详情
    - k8s_logs: 获取 Pod 日志
    
    # 系统监控工具
    - system_info: 系统信息
    - system_cpu: CPU 使用率
    - system_memory: 内存使用
    - system_disk: 磁盘使用
    - system_processes: 进程列表
    
    # 命令执行
    - execute_command: 安全执行命令
```

**安全特性**：
```python
# 命令白名单
ALLOWED_COMMANDS = [
    "kubectl", "docker", "ansible",
    "systemctl", "curl", "ping",
    "top", "ps", "free", "df", ...
]

# 危险命令模式阻止
BLOCKED_PATTERNS = [
    r"rm\s+-rf\s+/", r"mkfs", r"dd\s+if=", ...
]
```

### 4. 文件工具 (file_ops.py)

**特性**：
- 安全文件读写
- 日志解析 (JSON/Nginx/Apache/Syslog)
- 文件搜索
- 格式自动检测

**核心类**：
```python
class FileServer(BaseToolServer):
    # 文件操作
    - file_read: 读取文件
    - file_write: 写入文件
    - file_list: 列出目录
    - file_search: 搜索文件内容
    
    # 日志工具
    - log_parse: 解析日志
    - log_analyze: 分析日志（错误/警告统计）
```

**安全特性**：
```python
# 允许的文件扩展名
ALLOWED_EXTENSIONS = {
    ".txt", ".log", ".json", ".yaml", ".csv",
    ".py", ".js", ".sh", ".conf", ...
}

# 禁止访问的路径
BLOCKED_PATHS = [
    "/etc/shadow", "/etc/passwd",
    "~/.ssh", ".env", ...
]

# 最大文件大小
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
```

### 5. 通知工具 (notification.py)

**特性**：
- 多渠道通知 (邮件/钉钉/企业微信/Slack)
- 模板支持
- 批量发送
- 发送记录

**核心类**：
```python
class NotificationServer(BaseToolServer):
    # 通知工具
    - send_notification: 发送通知
    - send_template_notification: 模板通知
    - batch_send_notification: 批量发送
    - get_notification_history: 发送记录
    - list_notification_templates: 模板列表
```

**预定义模板**：
```python
NOTIFICATION_TEMPLATES = {
    "alert": 告警通知模板,
    "order_created": 订单创建通知,
    "task_complete": 任务完成通知,
}
```

### 测试覆盖

**新增测试文件**：

| 文件 | 测试内容 | 测试用例数 |
|------|---------|-----------|
| `tests/test_mcp_tools.py` | MCP 工具单元测试 | 25+ |
| `tests/test_integration.py` | 集成测试 | 15+ |

**测试覆盖模块**：
- 数据库工具测试 (DatabaseTools)
- HTTP 工具测试 (HttpTools)
- 运维工具测试 (DevOpsTools)
- 文件工具测试 (FileTools)
- 通知工具测试 (NotificationTools)
- 工具路由集成测试
- 沙箱集成测试
- 流式输出集成测试
- 追踪集成测试
- A2A 协议集成测试
- 端到端工作流测试

### 运行测试

```bash
# 运行所有测试
cd OpsPilot
pytest tests/ -v

# 运行特定测试
pytest tests/test_mcp_tools.py -v
pytest tests/test_integration.py -v

# 带覆盖率
pytest tests/ --cov=opspilot --cov-report=html
```

### 工具使用示例

```python
# 1. 数据库工具
from opspilot.tools import DatabaseServer

db = DatabaseServer(db_type="mock")
result = await db.call_tool("db_query", {"sql": "SELECT * FROM users"})

# 2. HTTP 工具
from opspilot.tools import ApiServer

api = ApiServer(base_url="https://api.example.com")
result = await api.call_tool("http_get", {"url": "/users"})

# 3. 运维工具
from opspilot.tools import DevOpsServer

devops = DevOpsServer()
result = await devops.call_tool("system_info", {})

# 4. 文件工具
from opspilot.tools import FileServer

files = FileServer()
result = await files.call_tool("log_analyze", {"content": log_content})

# 5. 通知工具
from opspilot.tools import NotificationServer

notify = NotificationServer()
result = await notify.call_tool("send_notification", {
    "channel": "dingtalk",
    "subject": "告警",
    "body": "CPU 使用率过高"
})
```

### 完成统计

| 项目 | 数量 |
|------|------|
| 新增工具模块 | 5 |
| 新增工具数量 | 25+ |
| Python 代码行数 | ~2500 |
| 测试用例 | 40+ |

---

<!-- MCP 核心工具开发完成 -->

---

## [2026-02-15] - LLM API 配置管理优化

### 开发目标

完善大模型 API 配置功能：
- 支持主流模型：OpenAI、Claude、通义千问、文心一言、智谱AI、DeepSeek
- 支持自定义 API 端点
- 前后端配置同步

### 完成内容

#### 后端新增模块

- [x] `opspilot/core/llm_config.py` - LLM 配置管理器
  - `LLMProvider` 枚举（8种提供商）
  - `ProviderConfig` 提供商配置类
  - `LLMConfigManager` 配置管理器（单例模式）
  - 配置持久化存储（JSON 文件）
  - 连接测试功能
  - 热更新支持

#### API 接口新增

- [x] `opspilot/api/schemas.py` - 新增 Schema
  - `LLMProviderEnum` 枚举
  - `LLMProviderConfigRequest` 配置请求
  - `LLMProviderConfigResponse` 配置响应
  - `LLMConfigListResponse` 列表响应
  - `LLMTestConnectionResponse` 测试响应

- [x] `opspilot/api/routes.py` - 新增接口
  - `GET /llm/config` - 获取所有配置
  - `GET /llm/config/{provider}` - 获取单个配置
  - `PUT /llm/config/{provider}` - 更新配置
  - `POST /llm/config/{provider}/test` - 测试连接
  - `POST /llm/config/{provider}/set-default` - 设置默认

#### 前端更新

- [x] `frontend/src/types/index.ts` - 新增类型
  - `LLMProviderType` 类型
  - `LLMProviderConfig` 接口
  - `LLMConfigList` 接口
  - `LLMConfigUpdateRequest` 接口
  - `LLMTestResult` 接口

- [x] `frontend/src/services/api.ts` - 新增 API 方法
  - `getLLMConfigs()` - 获取配置列表
  - `getLLMProviderConfig()` - 获取单个配置
  - `updateLLMConfig()` - 更新配置
  - `testLLMConnection()` - 测试连接
  - `setDefaultLLM()` - 设置默认

- [x] `frontend/src/pages/Settings.tsx` - 重写配置页面
  - 支持 8 种主流 LLM 提供商
  - API Key 输入（可显示/隐藏）
  - 自定义 API Base URL
  - 模型选择
  - 参数配置（Temperature、Max Tokens、Top P）
  - 启用/禁用开关
  - 连接测试
  - 设置默认提供商

### 支持的 LLM 提供商

| 提供商 | 默认 API Base | 默认模型 |
|--------|--------------|---------|
| OpenAI | https://api.openai.com/v1 | gpt-4o |
| Azure OpenAI | 用户自定义 | gpt-4 |
| Claude | https://api.anthropic.com/v1 | claude-3-5-sonnet |
| 通义千问 | https://dashscope.aliyuncs.com/compatible-mode/v1 | qwen-max |
| 文心一言 | https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat | ernie-4.0-8k |
| 智谱AI | https://open.bigmodel.cn/api/paas/v4 | glm-4 |
| DeepSeek | https://api.deepseek.com/v1 | deepseek-chat |
| 自定义 | 用户自定义 | 用户自定义 |

### 技术决策

- **配置持久化**：使用 JSON 文件存储，路径 `data/llm_config.json`
- **API Key 安全**：前端显示脱敏后的 Key，完整 Key 仅存储在后端
- **热更新**：配置更新后立即生效，无需重启服务
- **连接测试**：支持 OpenAI 和 DeepSeek 的实际 API 验证

### 完成统计

| 项目 | 数量 |
|------|------|
| 后端新增模块 | 1 |
| API 新增接口 | 5 |
| 前端更新文件 | 3 |
| 支持的 LLM 提供商 | 8 |

---

## [2026-02-15] - 模型列表获取与批量添加功能

### 开发目标

添加功能：
- 输入 API URL 和 API Key 后自动获取可用模型列表
- 支持批量添加模型到配置

### 完成内容

#### 后端新增

- [x] `opspilot/core/llm_config.py` - 新增函数
  - `fetch_available_models()` - 从 API 端点获取模型列表
  - `batch_add_custom_models()` - 批量添加模型配置

- [x] `opspilot/api/schemas.py` - 新增 Schema
  - `FetchModelsRequest` - 获取模型请求
  - `FetchModelsResponse` - 获取模型响应
  - `ModelInfo` - 模型信息
  - `BatchAddModelsRequest` - 批量添加请求
  - `BatchAddModelsResponse` - 批量添加响应

- [x] `opspilot/api/routes.py` - 新增接口
  - `POST /llm/models/fetch` - 获取可用模型列表
  - `POST /llm/models/batch-add` - 批量添加模型

#### 前端更新

- [x] `frontend/src/types/index.ts` - 新增类型
  - `ModelInfo` 接口
  - `FetchModelsRequest` 接口
  - `FetchModelsResponse` 接口
  - `BatchAddModelsRequest` 接口
  - `BatchAddModelsResponse` 接口

- [x] `frontend/src/services/api.ts` - 新增方法
  - `fetchModels()` - 获取模型列表
  - `batchAddModels()` - 批量添加模型

- [x] `frontend/src/pages/Settings.tsx` - 新增功能
  - "获取模型列表"按钮
  - 模型获取弹窗（输入 URL 和 Key）
  - 模型列表展示（支持多选）
  - 批量添加到自定义配置

### 支持的 API 格式

| API 类型 | 说明 |
|---------|------|
| OpenAI 兼容 | 支持自动获取模型列表 |
| DeepSeek | 支持自动获取模型列表 |
| 通义千问 | 支持自动获取模型列表（兼容模式） |

### 使用流程

```
1. 点击"获取模型列表"按钮
2. 输入 API Base URL 和 API Key
3. 点击获取，展示可用模型
4. 勾选需要添加的模型
5. 选择默认模型
6. 点击"批量添加"
```

### 完成统计

| 项目 | 数量 |
|------|------|
| 后端新增函数 | 2 |
| API 新增接口 | 2 |
| 前端新增类型 | 5 |

---

<!-- 模型列表获取与批量添加功能完成 -->

## [2026-02-16] - 前端 UI 全面重构

### 开发目标

- 使用官方 Skills 重构前端界面
- 应用专业 UI 设计规范
- 提升用户体验和视觉效果

### 完成内容

#### 安装官方 Skills

- [x] 从 Anthropic 官方 Skills 仓库下载
  - `frontend-design` - 专业前端设计 Skill
  - `web-artifacts-builder` - Web 产物构建器
  - `theme-factory` - 10 种预设专业主题

#### 设计规范输出

- [x] 输出 Design Specification
  - 工业风格 + 科技感美学方向
  - Electric Cyan (#00E5FF) 主强调色
  - Deep Navy (#0A1929) 主背景色
  - JetBrains Mono + DM Sans 字体组合
  - 斜切角装饰元素
  - 玻璃态效果

#### 全局样式重构

- [x] `frontend/src/index.css` - 全新设计系统
  - CSS 变量定义（颜色、字体、阴影、动画）
  - 玻璃态效果（glass-panel）
  - 斜切角装饰（clip-corner）
  - 脉冲动画效果
  - 滚动条美化

- [x] `frontend/tailwind.config.js` - 新配色 + 动画
  - 自定义颜色（navy, cyan, steel 等）
  - 自定义动画（pulse-slow, shimmer）
  - JetBrains Mono 字体集成

#### 组件重构

- [x] `frontend/src/components/layout/Layout.tsx`
  - 玻璃态侧边栏
  - 活跃状态指示器
  - 悬停动效

#### 页面重构

- [x] `frontend/src/pages/Dashboard.tsx` - 仪表盘
  - 统计卡片（带图标和趋势）
  - 活动时间线
  - 系统状态指示

- [x] `frontend/src/pages/Tasks.tsx` - 任务管理
  - 任务队列界面
  - 优先级标签
  - 任务卡片样式

- [x] `frontend/src/pages/Tools.tsx` - 工具调用
  - 工具卡片网格
  - 分类标签
  - 执行按钮样式

- [x] `frontend/src/pages/Agents.tsx` - Agent 监控
  - Agent 状态卡片
  - 活动指示器
  - 统计数据展示

- [x] `frontend/src/pages/Settings.tsx` - LLM 配置
  - 提供商配置面板
  - 参数调节滑块
  - 连接测试反馈

- [x] `frontend/src/pages/SOP.tsx` - SOP 执行
  - SOP 列表卡片
  - 步骤进度展示
  - 执行控制按钮

- [x] `frontend/src/pages/Tracing.tsx` - 追踪分析
  - 追踪列表
  - Span 详情展示
  - 时间线可视化

### 配色方案

| 颜色 | 色值 | 用途 |
|------|------|------|
| Electric Cyan | `#00E5FF` | 主强调色、按钮、活跃状态 |
| Deep Navy | `#0A1929` | 主背景色 |
| Dark Steel | `#1A252F` | 卡片背景 |
| Signal Green | `#00C853` | 成功状态 |
| Alert Amber | `#FFAB00` | 警告/处理中 |
| Critical Red | `#FF5252` | 错误状态 |

### 字体方案

| 类型 | 字体 | 用途 |
|------|------|------|
| Display | JetBrains Mono | 数据、代码、ID、状态 |
| Body | DM Sans | UI文本、标签、按钮 |
| Mono | IBM Plex Mono | 时间戳、日志 |

### 完成统计

| 项目 | 数量 |
|------|------|
| 重构文件 | 10 |
| 新增 Skills | 3 |
| 设计规范 | 1 |

---

## [2026-02-16] - 前端国际化 (i18n) 实现

### 开发目标

- 添加前端国际化支持
- 实现中英文一键切换
- 替换所有硬编码文本

### 完成内容

#### 核心模块

- [x] `frontend/src/i18n/index.ts` - i18n 配置
  - react-i18next 集成
  - 浏览器语言自动检测
  - localStorage 持久化
  - 中文默认 fallback

- [x] `frontend/src/i18n/locales/zh-CN.json` - 中文翻译
  - common: 通用文本（应用名、按钮、状态）
  - nav: 导航菜单
  - dashboard: 仪表盘
  - tasks: 任务管理
  - tools: 工具调用
  - sop: SOP 执行
  - agents: Agent 监控
  - tracing: 追踪分析
  - settings: 系统设置
  - errors: 错误消息

- [x] `frontend/src/i18n/locales/en-US.json` - 英文翻译
  - 与中文完整对应

#### 组件更新

- [x] `frontend/src/components/LanguageSwitcher.tsx` - 语言切换器
  - 下拉菜单样式
  - 国旗图标 + 语言名称
  - 当前语言高亮

- [x] `frontend/src/main.tsx` - 入口文件
  - 导入 i18n 配置

- [x] `frontend/src/components/layout/Layout.tsx` - 主布局
  - useTranslation hook
  - 导航文本国际化
  - 集成语言切换器

#### 页面国际化

- [x] `frontend/src/pages/Dashboard.tsx` - 仪表盘
  - 统计标签、表格头、状态文本

- [x] `frontend/src/pages/Tasks.tsx` - 任务管理
  - 任务创建、队列、详情

- [x] `frontend/src/pages/Tools.tsx` - 工具调用
  - 工具库、执行面板

- [x] `frontend/src/pages/SOP.tsx` - SOP 执行
  - SOP 库、步骤执行

- [x] `frontend/src/pages/Agents.tsx` - Agent 监控
  - Agent 列表、协作流程

- [x] `frontend/src/pages/Tracing.tsx` - 追踪分析
  - 追踪列表、Span 详情

- [x] `frontend/src/pages/Settings.tsx` - 系统设置
  - LLM 配置、提供商名称、表单标签
  - 语言设置提示

### 翻译键结构

```
{
  "common": { "appName", "loading", "save", "cancel", ... },
  "nav": { "dashboard", "tasks", "tools", ... },
  "dashboard": { "activeTasks", "completedTasks", ... },
  "tasks": { "newTask", "taskQueue", ... },
  "tools": { "toolLibrary", "executionPanel", ... },
  "sop": { "sopLibrary", "stepExecution", ... },
  "agents": { "agentList", "collaborationFlow", ... },
  "tracing": { "traceAnalysis", "spanDetails", ... },
  "settings": { "llmConfig", "providers", ... },
  "errors": { "networkError", "serverError", ... }
}
```

### 技术决策

- **react-i18next**: React 生态最成熟的 i18n 方案
- **浏览器检测**: 自动检测用户浏览器语言
- **持久化**: localStorage 保存用户语言偏好
- **嵌套键**: 使用 `nav.dashboard` 格式组织翻译

### 依赖更新

```json
{
  "i18next": "^24.2.3",
  "react-i18next": "^15.4.1",
  "i18next-browser-languagedetector": "^8.0.4"
}
```

### 完成统计

| 项目 | 数量 |
|------|------|
| 新增文件 | 4 |
| 更新文件 | 9 |
| 翻译键 | 100+ |
| 支持语言 | 2（中文、英文）|

---

## [2026-02-16] - 优化方案实施确认

### 开发目标

确认优化计划（OPTIMIZATION_PLAN.md）的实施状态。

### 实施状态

| 优化项 | 状态 | 实现位置 |
|--------|------|---------|
| **失败处理优化** | ✅ 已实现 | `opspilot/tools/healing.py` |
| **记忆权重机制** | ✅ 已实现 | `opspilot/memory/weight.py` |
| **记忆冲突解决** | ✅ 已实现 | `opspilot/memory/conflict.py` |
| **多智能体调度** | ✅ 已实现 | `opspilot/agents/collaboration.py` |
| **工具调用优化** | ✅ 已实现 | `opspilot/tools/indexer.py` 等 |

### 工具调用优化详情

已实现的 ToolRAG 模块：

| 文件 | 功能 |
|------|------|
| `indexer.py` | 工具定义向量化、索引构建、类别分组 |
| `retriever.py` | 两级检索（类别→工具）、混合检索策略 |
| `compressor.py` | 工具描述压缩、Token 估算 |
| `context_manager.py` | 上下文预算管理、动态工具加载 |

### 核心功能

1. **两级检索机制**
   - 第一级：类别检索（确定相关类别）
   - 第二级：工具检索（类别内检索具体工具）

2. **混合检索策略**
   - 语义相似度检索
   - 关键词匹配检索
   - 混合检索

3. **上下文预算管理**
   - 工具定义最大 Token 数控制
   - 动态工具选择
   - 预算约束下的最优选择

### 技术决策

- **向量表示**：使用 TF-IDF 和字符频率向量（无需额外 embedding 模型）
- **类别自动分类**：基于工具名称和描述自动分类
- **压缩策略**：支持 minimal/compact/detailed 三种级别

### 优化计划完成度

```
✅ 工具调用优化 (ToolRAG)
✅ 失败处理优化 (自愈机制)
✅ 记忆权重机制
✅ 记忆冲突解决
✅ 多智能体调度 (并行协作)
```

**优化计划已 100% 完成！**

---


