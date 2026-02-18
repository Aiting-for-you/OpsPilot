# 数据流图

## 1. 整体数据流向

```mermaid
flowchart TB
    subgraph 输入["📥 输入层"]
        USER["用户输入"]
        WEB["Web请求"]
        CLI["CLI命令"]
    end

    subgraph 处理["⚙️ 处理层"]
        GATEWAY["API Gateway"]
        AUTH["认证授权"]
        PARSE["请求解析"]
    end

    subgraph 编排["🎯 编排层"]
        ORCH["Orchestrator"]
        FSM["状态机"]
        AGENTS["Agent协作"]
    end

    subgraph 执行["🔧 执行层"]
        TOOLS["工具调用"]
        RAG["RAG检索"]
        MEMORY["记忆读写"]
    end

    subgraph 存储["💾 存储层"]
        DB[("PostgreSQL")]
        REDIS[("Redis")]
        VECTOR[("ChromaDB")]
    end

    subgraph 输出["📤 输出层"]
        RESULT["结果返回"]
        LOG["日志记录"]
        METRIC["指标上报"]
    end

    USER --> GATEWAY
    WEB --> GATEWAY
    CLI --> GATEWAY
    
    GATEWAY --> AUTH
    AUTH --> PARSE
    PARSE --> ORCH
    
    ORCH --> FSM
    FSM --> AGENTS
    AGENTS --> TOOLS
    AGENTS --> RAG
    AGENTS --> MEMORY
    
    TOOLS --> DB
    RAG --> VECTOR
    MEMORY --> REDIS
    MEMORY --> DB
    
    AGENTS --> RESULT
    AGENTS --> LOG
    AGENTS --> METRIC

    style 输入 fill:#e3f2fd
    style 处理 fill:#fff3e0
    style 编排 fill:#f3e5f5
    style 执行 fill:#e8f5e9
    style 存储 fill:#efebe9
    style 输出 fill:#fce4ec
```

## 2. 请求处理数据流

### 2.1 同步请求流程

```mermaid
flowchart LR
    A["HTTP请求"] --> B["认证"]
    B --> C["参数校验"]
    C --> D["意图识别"]
    D --> E{"任务类型"}
    
    E -->|"定价协商"| F1["PricingOrchestrator"]
    E -->|"工单处理"| F2["CustomerServiceFlow"]
    E -->|"常规任务"| F3["StandardFlow"]
    
    F1 --> G["Agent执行"]
    F2 --> G
    F3 --> G
    
    G --> H["结果聚合"]
    H --> I["响应返回"]
```

### 2.2 异步任务流程

```mermaid
flowchart TB
    A["任务提交"] --> B["任务入队"]
    B --> C["返回TaskID"]
    
    C --> D["后台处理"]
    D --> E["状态更新"]
    E --> F["完成通知"]
    
    subgraph 轮询
        G["客户端轮询"] --> H["查询状态"]
        H --> I{"完成?"}
        I -->|"否"| G
        I -->|"是"| J["获取结果"]
    end
    
    F --> J
```

## 3. Agent 协作数据流

### 3.1 单Agent执行流

```mermaid
flowchart TB
    START["开始"] --> INPUT["接收输入"]
    INPUT --> MEMORY["加载上下文<br/>从Memory"]
    MEMORY --> LLM["调用LLM推理"]
    LLM --> DECIDE{"需要工具?"}
    
    DECIDE -->|"是"| TOOL["执行工具"]
    TOOL --> RESULT["获取结果"]
    RESULT --> MEMORY2["更新记忆"]
    
    DECIDE -->|"否"| MEMORY2
    
    MEMORY2 --> OUTPUT["生成输出"]
    OUTPUT --> END["结束"]
```

### 3.2 多Agent协作流

```mermaid
flowchart TB
    ORCH["Orchestrator"] --> |"分发任务"| A1["Agent 1"]
    ORCH --> |"分发任务"| A2["Agent 2"]
    ORCH --> |"分发任务"| A3["Agent 3"]
    
    A1 --> |"投票"| VOTE["投票仲裁"]
    A2 --> |"投票"| VOTE
    A3 --> |"投票"| VOTE
    
    VOTE --> |"达成共识"| AGREE["共识结果"]
    VOTE --> |"分歧过大"| HUMAN["人工介入"]
    
    AGREE --> FINAL["最终决策"]
    HUMAN --> FINAL
```

## 4. 工具调用数据流

### 4.1 MCP工具调用

```mermaid
sequenceDiagram
    participant Agent
    participant ToolRouter
    participant MCPClient
    participant MCPServer
    participant ExternalAPI

    Agent->>ToolRouter: 请求工具调用
    ToolRouter->>ToolRouter: 查找工具
    ToolRouter->>MCPClient: 调用MCP客户端
    MCPClient->>MCPServer: JSON-RPC请求
    MCPServer->>ExternalAPI: API调用
    ExternalAPI-->>MCPServer: API响应
    MCPServer-->>MCPClient: JSON-RPC响应
    MCPClient-->>ToolRouter: 工具结果
    ToolRouter-->>Agent: 返回结果
```

### 4.2 降级流程

```mermaid
flowchart TB
    A["工具调用"] --> B{"MCP可用?"}
    B -->|"是"| C["MCP调用"]
    B -->|"否"| D["重试3次"]
    
    D --> E{"重试成功?"}
    E -->|"是"| C
    E -->|"否"| F["降级到GUI模式"]
    
    F --> G["UI-TARS执行"]
    G --> H["人工确认"]
    H --> I["返回结果"]
    
    C --> I
```

## 5. RAG 检索数据流

```mermaid
flowchart TB
    Q["用户查询"] --> REWRITE["查询改写"]
    REWRITE --> EMBED["查询向量化"]
    
    EMBED --> VEC["向量检索"]
    EMBED --> KEY["关键词检索"]
    
    VEC --> MERGE["结果合并"]
    KEY --> MERGE
    
    MERGE --> RERANK["重排序"]
    RERANK --> FILTER["过滤低分"]
    FILTER --> CONTEXT["上下文组装"]
    
    CONTEXT --> LLM["LLM生成"]
    LLM --> ANSWER["最终答案"]
    
    subgraph 向量库
        VEC --> CHROMA[("ChromaDB")]
    end
```

## 6. 记忆数据流

### 6.1 写入流程

```mermaid
flowchart LR
    A["Agent执行结果"] --> B["提取关键信息"]
    B --> C["向量化"]
    C --> D{"记忆类型"}
    
    D -->|"短期"| E["写入Redis<br/>TTL=1h"]
    D -->|"长期"| F["写入PostgreSQL<br/>永久存储"]
    D -->|"知识"| G["写入ChromaDB<br/>向量索引"]
```

### 6.2 读取流程

```mermaid
flowchart TB
    A["记忆查询"] --> B["并行查询"]
    
    B --> C["Redis短期记忆"]
    B --> D["PostgreSQL长期记忆"]
    B --> E["ChromaDB知识库"]
    
    C --> F["结果合并"]
    D --> F
    E --> F
    
    F --> G["相关性排序"]
    G --> H["返回Top-K"]
```

## 7. 数据流转示例

### 7.1 定价协商完整数据流

```mermaid
flowchart TB
    REQ["POST /pricing/negotiate"] --> PARSE["解析请求<br/>product_id"]
    PARSE --> ORCH["PricingOrchestrator"]
    
    ORCH --> COST["CostAgent"]
    ORCH --> MARKET["MarketAgent"]
    ORCH --> PROFIT["ProfitAgent"]
    
    COST --> COST_DATA["成本数据"]
    MARKET --> MONITOR["CompetitorMonitorTool"]
    PROFIT --> ELASTIC["PriceElasticityTool"]
    
    MONITOR --> COMP_DATA["竞品数据"]
    ELASTIC --> ELAST_DATA["弹性数据"]
    
    COST_DATA --> VOTE["投票仲裁"]
    COMP_DATA --> VOTE
    ELAST_DATA --> VOTE
    
    VOTE --> FINAL["最终定价"]
    FINAL --> RESP["返回响应"]
```

### 7.2 工单处理完整数据流

```mermaid
flowchart TB
    REQ["POST /customer-service/tickets/process"] --> GET["获取工单"]
    GET --> CLASSIFY["ClassifierAgent"]
    
    CLASSIFY --> TYPE["工单分类"]
    TYPE --> ROUTER["RouterAgent"]
    
    ROUTER --> DEPT["部门分配"]
    DEPT --> SOLVER["SolverAgent"]
    
    SOLVER --> SOLUTION["解决方案"]
    SOLUTION --> REVIEW["ReviewerAgent"]
    
    REVIEW --> QUALITY["质量审核"]
    QUALITY --> UPDATE["更新工单"]
    UPDATE --> RESP["返回响应"]
```

## 8. 数据格式规范

### 8.1 请求数据格式

```json
{
  "trace_id": "trace-uuid-v4",
  "timestamp": "2026-02-18T10:00:00Z",
  "source": "web|cli|api",
  "action": "execute_task",
  "payload": {
    "task_type": "string",
    "params": {}
  },
  "context": {
    "session_id": "string",
    "user_id": "string",
    "roles": ["string"]
  }
}
```

### 8.2 响应数据格式

```json
{
  "trace_id": "trace-uuid-v4",
  "status": "success|error|pending",
  "result": {},
  "metadata": {
    "processing_time_ms": 1234,
    "tokens_used": 500,
    "agents_involved": ["agent1", "agent2"],
    "tools_called": ["tool1", "tool2"]
  },
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message",
    "retry_suggested": true
  }
}
```
