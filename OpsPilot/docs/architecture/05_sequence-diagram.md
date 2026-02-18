# 核心流程时序图

## 1. 任务执行完整时序

```mermaid
sequenceDiagram
    participant User as 用户
    participant API as API Gateway
    participant Auth as 认证模块
    participant Orch as Orchestrator
    participant FSM as 状态机
    participant Agent as Agent
    participant Tool as Tool
    participant Memory as Memory
    participant DB as 数据库

    User->>API: 提交任务请求
    API->>Auth: 验证Token
    Auth-->>API: 验证通过
    
    API->>Orch: 转发任务
    Orch->>FSM: 初始化状态(INIT)
    FSM->>Memory: 加载上下文
    Memory-->>FSM: 返回上下文
    
    FSM->>Agent: 分发任务
    Agent->>Agent: 意图识别
    
    opt 需要工具调用
        Agent->>Tool: 调用工具
        Tool->>DB: 数据操作
        DB-->>Tool: 返回数据
        Tool-->>Agent: 工具结果
    end
    
    Agent->>Memory: 保存执行结果
    Agent-->>FSM: 返回结果
    FSM->>FSM: 状态转换(VERIFYING)
    FSM->>Agent: 结果验证
    Agent-->>FSM: 验证通过
    FSM->>FSM: 状态转换(SUCCESS)
    FSM-->>Orch: 任务完成
    Orch-->>API: 返回结果
    API-->>User: 响应请求
```

## 2. 多Agent协作时序

### 2.1 博弈定价流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant API as API
    participant Orch as PricingOrchestrator
    participant Cost as CostAgent
    participant Market as MarketAgent
    participant Profit as ProfitAgent
    participant Tool as 竞品/弹性工具

    User->>API: POST /pricing/negotiate
    API->>Orch: 启动定价协商
    
    par 并行执行
        Orch->>Cost: 请求成本分析
        Cost-->>Orch: 成本建议价格
        
        Orch->>Market: 请求市场分析
        Market->>Tool: 获取竞品数据
        Tool-->>Market: 竞品价格
        Market-->>Orch: 市场建议价格
        
        Orch->>Profit: 请求利润分析
        Profit->>Tool: 获取弹性数据
        Tool-->>Profit: 弹性系数
        Profit-->>Orch: 利润建议价格
    end
    
    Orch->>Orch: 加权投票仲裁
    Orch-->>API: 最终定价结果
    API-->>User: 返回定价决策
```

### 2.2 客服工单处理流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant API as API
    participant Classify as ClassifierAgent
    participant Router as RouterAgent
    participant Solver as SolverAgent
    participant Review as ReviewerAgent
    participant Tool as TicketManager

    User->>API: POST /tickets/process
    API->>Classify: 工单分类
    
    Classify->>Tool: 获取工单内容
    Tool-->>Classify: 工单数据
    Classify->>Classify: 分析类型/优先级
    Classify-->>API: 分类结果
    
    API->>Router: 路由决策
    Router->>Router: 匹配部门/专家
    Router-->>API: 路由结果
    
    API->>Solver: 生成解决方案
    Solver->>Tool: 查询历史工单
    Tool-->>Solver: 历史案例
    Solver->>Solver: 生成方案
    Solver-->>API: 解决方案
    
    API->>Review: 质量审核
    Review->>Review: 检查方案质量
    Review-->>API: 审核结果
    
    API->>Tool: 更新工单状态
    Tool-->>API: 更新成功
    API-->>User: 返回处理结果
```

## 3. SOP 执行时序

```mermaid
sequenceDiagram
    participant User as 用户
    participant Exec as SOP Executor
    participant FSM as 状态机
    participant Agent as Agent
    participant Tool as Tool
    participant Human as 人工审核

    User->>Exec: 启动SOP
    Exec->>FSM: 创建状态机实例
    
    loop SOP步骤
        Exec->>FSM: 获取当前状态
        FSM-->>Exec: 当前状态
        
        alt 需要Agent执行
            Exec->>Agent: 执行步骤
            Agent->>Tool: 调用工具
            Tool-->>Agent: 返回结果
            Agent-->>Exec: 步骤完成
        end
        
        alt 需要人工确认
            Exec->>Human: 请求确认
            Human-->>Exec: 确认结果
        end
        
        Exec->>FSM: 状态转换
    end
    
    Exec-->>User: SOP执行完成
```

## 4. RAG 检索时序

```mermaid
sequenceDiagram
    participant Agent as Agent
    participant RAG as RAG Pipeline
    participant Rewrite as 查询改写
    participant Vec as 向量检索
    participant Key as 关键词检索
    participant Rerank as 重排序
    participant KB as ChromaDB

    Agent->>RAG: 发起检索请求
    RAG->>Rewrite: 改写查询
    Rewrite-->>RAG: 改写后查询
    
    par 并行检索
        RAG->>Vec: 向量检索
        Vec->>KB: 相似度查询
        KB-->>Vec: 向量结果
        
        RAG->>Key: 关键词检索
        Key->>KB: 全文搜索
        KB-->>Key: 关键词结果
    end
    
    Vec-->>RAG: 向量结果
    Key-->>RAG: 关键词结果
    
    RAG->>Rerank: 合并重排序
    Rerank->>Rerank: BGE-Reranker
    Rerank-->>RAG: 排序结果
    
    RAG->>RAG: 组装上下文
    RAG-->>Agent: 返回文档片段
```

## 5. 记忆管理时序

### 5.1 记忆写入

```mermaid
sequenceDiagram
    participant Agent as Agent
    participant Memory as Memory Manager
    participant Redis as Redis
    participant PG as PostgreSQL
    participant Chroma as ChromaDB

    Agent->>Memory: 保存记忆
    Memory->>Memory: 分类记忆类型
    
    par 并行写入
        Memory->>Redis: 写入短期记忆
        Redis-->>Memory: 写入成功
        
        Memory->>PG: 写入长期记忆
        PG-->>Memory: 写入成功
        
        Memory->>Chroma: 写入向量索引
        Chroma-->>Memory: 索引成功
    end
    
    Memory-->>Agent: 保存完成
```

### 5.2 记忆检索

```mermaid
sequenceDiagram
    participant Agent as Agent
    participant Memory as Memory Manager
    participant Redis as Redis
    participant PG as PostgreSQL
    participant Chroma as ChromaDB

    Agent->>Memory: 检索记忆
    Memory->>Memory: 分析检索范围
    
    par 并行检索
        Memory->>Redis: 检索短期记忆
        Redis-->>Memory: 短期记忆
        
        Memory->>PG: 检索长期记忆
        PG-->>Memory: 长期记忆
        
        Memory->>Chroma: 向量检索
        Chroma-->>Memory: 相关知识
    end
    
    Memory->>Memory: 合并去重
    Memory->>Memory: 相关性排序
    Memory-->>Agent: 返回记忆
```

## 6. 错误处理时序

```mermaid
sequenceDiagram
    participant Agent as Agent
    participant Tool as Tool
    participant Retry as 重试器
    participant Fallback as 降级器
    participant Log as 日志

    Agent->>Tool: 调用工具
    Tool-->>Agent: 调用失败
    
    Agent->>Retry: 请求重试
    Retry->>Tool: 第1次重试
    Tool-->>Retry: 失败
    
    Retry->>Tool: 第2次重试
    Tool-->>Retry: 失败
    
    Retry->>Tool: 第3次重试
    Tool-->>Retry: 失败
    
    Retry->>Log: 记录失败
    Retry->>Fallback: 触发降级
    Fallback->>Fallback: 选择降级策略
    Fallback-->>Agent: 返回降级结果
```

## 7. 认证授权时序

```mermaid
sequenceDiagram
    participant User as 用户
    participant API as API
    participant Auth as Auth模块
    participant JWT as JWT服务
    participant RBAC as RBAC服务

    User->>API: 登录请求
    API->>Auth: 验证凭证
    Auth->>Auth: 校验用户名密码
    Auth->>RBAC: 获取用户角色
    RBAC-->>Auth: 角色列表
    Auth->>JWT: 生成Token
    JWT-->>Auth: Token
    Auth-->>API: Token
    API-->>User: 返回Token
    
    Note over User,RBAC: 后续请求
    
    User->>API: 业务请求 + Token
    API->>JWT: 验证Token
    JWT-->>API: 用户信息
    API->>RBAC: 检查权限
    RBAC-->>API: 权限验证
    API->>API: 执行业务逻辑
    API-->>User: 返回结果
```

## 8. 关键时序指标

| 流程 | 正常耗时 | P99耗时 | 超时阈值 |
|------|---------|---------|---------|
| 任务执行 | 500ms | 3s | 30s |
| 博弈定价 | 2s | 5s | 60s |
| 工单处理 | 1.5s | 4s | 45s |
| RAG检索 | 200ms | 1s | 10s |
| 记忆写入 | 100ms | 500ms | 5s |
| 认证授权 | 50ms | 200ms | 3s |
