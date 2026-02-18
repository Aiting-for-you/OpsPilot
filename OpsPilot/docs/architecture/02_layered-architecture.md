# 分层架构设计

## 1. 四层架构概览

OpsPilot 采用四层架构设计，自上而下分别为：**协作层 → 执行层 → 推理层 → 模型层**。

```mermaid
graph TB
    subgraph 协作层["🎯 协作层 (Orchestration Layer)"]
        direction TB
        O1["AgentScope 编排"]
        O2["MsgHub 消息中心"]
        O3["FSM 状态机"]
        O4["博弈仲裁器"]
    end

    subgraph 执行层["⚙️ 执行层 (Execution Layer)"]
        direction TB
        E1["LangChain Chains"]
        E2["MCP Tool 封装"]
        E3["RAG 检索管道"]
        E4["记忆管理"]
    end

    subgraph 推理层["🧠 推理层 (Inference Layer)"]
        direction TB
        I1["SGLang 推理引擎"]
        I2["结构化输出"]
        I3["KV Cache 优化"]
    end

    subgraph 模型层["🤖 模型层 (Model Layer)"]
        direction TB
        M1["基座模型<br/>GPT-4 / Claude"]
        M2["微调模型<br/>LLaMA-Factory"]
        M3["领域适配"]
    end

    协作层 --> 执行层
    执行层 --> 推理层
    推理层 --> 模型层

    style 协作层 fill:#e8eaf6
    style 执行层 fill:#e0f2f1
    style 推理层 fill:#fff3e0
    style 模型层 fill:#fce4ec
```

## 2. 协作层详解

### 职责
- 多智能体任务编排
- 消息路由与广播
- 状态流转控制
- 冲突仲裁与共识

### 核心组件

```mermaid
graph LR
    subgraph 协作层组件
        ORCH["Orchestrator<br/>编排器"]
        FSM["StateMachine<br/>状态机"]
        MSG["MsgHub<br/>消息中心"]
        VOTE["VotingArbiter<br/>投票仲裁"]
    end
    
    ORCH --> FSM
    ORCH --> MSG
    ORCH --> VOTE
    
    FSM --> |"状态变更"| MSG
    VOTE --> |"决策结果"| FSM
```

### 状态机流转

```mermaid
stateDiagram-v2
    [*] --> INIT: 任务创建
    INIT --> PLANNING: 意图识别完成
    PLANNING --> AUDITING: 规划完成
    AUDITING --> EXECUTING: 审核通过
    AUDITING --> REJECTED: 审核拒绝
    EXECUTING --> VERIFYING: 执行完成
    VERIFYING --> SUCCESS: 验证通过
    VERIFYING --> RETRY: 验证失败
    RETRY --> EXECUTING: 重试
    REJECTED --> [*]
    SUCCESS --> [*]
```

## 3. 执行层详解

### 职责
- 工具调用执行
- RAG 知识检索
- 记忆读写管理
- 确定性逻辑链

### 核心组件

```mermaid
graph TB
    subgraph 执行层组件
        CHAIN["Chain 执行器"]
        TOOL["Tool Router"]
        RAG["RAG Pipeline"]
        MEM["Memory Manager"]
    end
    
    subgraph MCP工具
        ERP["ERP API"]
        LOG["物流 API"]
        PAY["支付 API"]
    end
    
    subgraph 记忆存储
        SHORT["短期记忆<br/>Redis"]
        LONG["长期记忆<br/>PostgreSQL"]
        KB["知识库<br/>ChromaDB"]
    end
    
    CHAIN --> TOOL
    CHAIN --> RAG
    CHAIN --> MEM
    
    TOOL --> ERP
    TOOL --> LOG
    TOOL --> PAY
    
    MEM --> SHORT
    MEM --> LONG
    RAG --> KB
```

### RAG 检索流程

```mermaid
flowchart LR
    Q["用户查询"] --> REWRITE["查询改写"]
    REWRITE --> RETRIEVE["多路召回"]
    RETRIEVE --> RERANK["重排序"]
    RERANK --> CONTEXT["上下文组装"]
    CONTEXT --> LLM["LLM 生成"]
    
    subgraph 召回策略
        VEC["向量检索"]
        KEY["关键词检索"]
        HYBRID["混合检索"]
    end
    
    RETRIEVE --> VEC
    RETRIEVE --> KEY
    RETRIEVE --> HYBRID
```

## 4. 推理层详解

### 职责
- 高性能模型推理
- 结构化输出保证
- 并发请求优化

### 架构设计

```mermaid
graph TB
    subgraph 推理层
        GATE["推理网关"]
        POOL["连接池"]
        CACHE["KV Cache"]
        ENGINE["SGLang Engine"]
    end
    
    subgraph 优化策略
        PREFIX["Prefix Caching"]
        BATCH["Continuous Batching"]
        SPEC["Speculative Decoding"]
    end
    
    GATE --> POOL
    POOL --> CACHE
    CACHE --> ENGINE
    
    ENGINE --> PREFIX
    ENGINE --> BATCH
    ENGINE --> SPEC
```

### 性能指标

| 指标 | 目标 | 说明 |
|------|------|------|
| TTFT | < 1.5s | 首字延迟 |
| Throughput | > 100 req/s | 吞吐量 |
| P99 Latency | < 5s | 99分位延迟 |

## 5. 模型层详解

### 职责
- 提供基础推理能力
- 领域适配与微调
- 工具调用对齐

### 模型选型

```mermaid
graph LR
    subgraph 基座模型
        GPT["GPT-4<br/>通用场景"]
        CLAUDE["Claude<br/>长文本"]
        DEEP["DeepSeek<br/>性价比"]
    end
    
    subgraph 微调模型
        LORA["LoRA 微调"]
        QLORA["QLoRA 微调"]
    end
    
    subgraph 领域适配
        ECOM["电商领域"]
        FIN["金融领域"]
        LOG["物流领域"]
    end
    
    GPT --> LORA
    CLAUDE --> QLORA
    LORA --> ECOM
    LORA --> FIN
    QLORA --> LOG
```

## 6. 层间通信协议

### 请求协议

```json
{
  "trace_id": "uuid-v4",
  "layer": "orchestration",
  "action": "execute_task",
  "payload": {
    "task_type": "procurement",
    "params": {...}
  },
  "context": {
    "session_id": "sess-123",
    "user_id": "user-001"
  }
}
```

### 响应协议

```json
{
  "trace_id": "uuid-v4",
  "status": "success",
  "result": {...},
  "metadata": {
    "layer": "execution",
    "latency_ms": 234,
    "tokens_used": 150
  }
}
```

## 7. 层间依赖关系

```mermaid
graph TB
    subgraph 依赖方向
        ORCH["协作层"] --> EXEC["执行层"]
        EXEC --> INF["推理层"]
        INF --> MODEL["模型层"]
    end
    
    subgraph 反向通知
        MODEL -.->|"推理结果"| INF
        INF -.->|"执行结果"| EXEC
        EXEC -.->|"任务状态"| ORCH
    end
    
    style 依赖方向 fill:#e8f5e9
    style 反向通知 fill:#fff3e0
```
