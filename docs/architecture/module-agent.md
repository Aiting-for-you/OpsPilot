# Agent 模块架构

## 模块概述

Agent 模块是 OpsPilot 的智能执行核心，通过多 Agent 协作实现复杂任务的智能处理。模块包含 **IntentAgent（意图识别）**、**PlanAgent（任务规划）**、**ExecAgent（任务执行）** 和 **VerifyAgent（结果验证）** 四个核心 Agent，以及 **Collaboration（协作管理）** 和 **Negotiation（博弈协商）** 支持组件。

## 1. 组件架构

```mermaid
graph TB
    subgraph AGENT_BASE["Base（基类层）"]
        direction LR
        BASE_AGENT[BaseAgent<br/>抽象基类<br/>定义 Agent 接口]
        STATE[AgentState<br/>状态管理<br/>IDLE/BUSY]
        CTX[AgentContext<br/>执行上下文<br/>任务信息]
        MSG[MessageHub<br/>消息中心<br/>订阅发布]
    end

    subgraph CORE_AGENTS["核心 Agent"]
        direction LR
        INTENT[IntentAgent<br/>意图识别<br/>解析用户输入]
        PLAN[PlanAgent<br/>任务规划<br/>生成执行计划]
        EXEC[ExecAgent<br/>任务执行<br/>调用工具]
        VERIFY[VerifyAgent<br/>结果验证<br/>质量审核]
    end

    subgraph INTENT_COMP["IntentAgent 组件"]
        direction LR
        PARSER[InputParser<br/>输入解析器]
        CLS[IntentClassifier<br/>意图分类器]
        SLOT[SlotFiller<br/>槽位填充]
    end

    subgraph PLAN_COMP["PlanAgent 组件"]
        direction LR
        DECOMP[TaskDecomposer<br/>任务分解]
        SCHED[PlanScheduler<br/>计划调度]
        EST[ResourceEstimator<br/>资源评估]
    end

    subgraph EXEC_COMP["ExecAgent 组件"]
        direction LR
        SELECTOR[ToolSelector<br/>工具选择]
        INVOKER[ToolInvoker<br/>工具调用]
        RETRY[RetryHandler<br/>重试处理]
    end

    subgraph VERIFY_COMP["VerifyAgent 组件"]
        direction LR
        RULE[RuleChecker<br/>规则检查]
        QUAL[QualityScorer<br/>质量评分]
        FEEDBACK[FeedbackGenerator<br/>反馈生成]
    end

    subgraph COLLAB["Collaboration（协作）"]
        direction LR
        COLLAB_MGR[Collaboration<br/>协作管理]
        MSG_HUB[MsgHub<br/>消息枢纽]
        LEADER[LeaderElection<br/>领导者选举]
    end

    subgraph NEGOT["Negotiation（博弈）"]
        direction LR
        NEGOT_MGR[Negotiation<br/>谈判管理]
        STRAT[StrategyEngine<br/>策略引擎]
        BID[BidEngine<br/>出价引擎]
    end

    subgraph ADAPTER["Adapter（适配器）"]
        direction LR
        AGENTSCOPE[AgentScopeAdapter<br/>框架适配]
        LLM_ADAPT[LLMAdapter<br/>LLM 适配]
    end

    %% 连接
    BASE_AGENT --> STATE
    BASE_AGENT --> CTX
    BASE_AGENT --> MSG
    
    INTENT --> PARSER
    INTENT --> CLS
    INTENT --> SLOT
    
    PLAN --> DECOMP
    PLAN --> SCHED
    PLAN --> EST
    
    EXEC --> SELECTOR
    EXEC --> INVOKER
    EXEC --> RETRY
    
    VERIFY --> RULE
    VERIFY --> QUAL
    VERIFY --> FEEDBACK
    
    COLLAB_MGR --> MSG_HUB
    COLLAB_MGR --> LEADER
    
    NEGOT_MGR --> STRAT
    NEGOT_MGR --> BID
    
    AGENTSCOPE --> LLM_ADAPT
    
    BASE_AGENT -.->|继承| INTENT
    BASE_AGENT -.->|继承| PLAN
    BASE_AGENT -.->|继承| EXEC
    BASE_AGENT -.->|继承| VERIFY
    
    MSG_HUB --> MSG
    INTENT --> PLAN
    PLAN --> EXEC
    EXEC --> VERIFY
    EXEC --> COLLAB_MGR
    NEGOT_MGR --> COLLAB_MGR
    
    %% 样式
    classDef base fill:#e3f2fd,stroke:#1976d2,color:#0d47a1
    classDef intent fill:#fff3e0,stroke:#f57c00,color:#e65100
    classDef plan fill:#e8f5e9,stroke:#388e3c,color:#1b5e20
    classDef exec fill:#e0f7fa,stroke:#0097a7,color:#006064
    classDef verify fill:#fce4ec,stroke:#c2185b,color:#880e4f
    classDef collab fill:#f3e5f5,stroke:#7b1fa2,color:#4a148c
    classDef adapter fill:#efebe9,stroke:#5d4037,color:#3e2723

    class BASE_AGENT,STATE,CTX,MSG base
    class INTENT,PARSER,CLS,SLOT intent
    class PLAN,DECOMP,SCHED,EST plan
    class EXEC,SELECTOR,INVOKER,RETRY exec
    class VERIFY,RULE,QUAL,FEEDBACK verify
    class COLLAB_MGR,MSG_HUB,LEADER,NEGOT_MGR,STRAT,BID collab
    class AGENTSCOPE,LLM_ADAPT adapter
```

## 2. Agent 协作时序图

```mermaid
sequenceDiagram
    participant ORCH as Orchestrator
    participant MSG as MessageHub
    participant INTENT as IntentAgent
    participant PLAN as PlanAgent
    participant EXEC as ExecAgent
    participant TOOL as ToolLayer
    participant VERIFY as VerifyAgent
    participant LLM as LLM 服务

    ORCH->>MSG: broadcast(TASK_START)
    MSG->>INTENT: notify(intent_request)
    
    rect rgb(255, 245, 230)
        note right of INTENT: 意图识别阶段
        INTENT->>INTENT: parse_input(user_input)
        INTENT->>LLM: classify_intent(context)
        LLM-->>INTENT: intent_result
        INTENT->>INTENT: fill_slots(intent)
        INTENT->>MSG: publish(INTENT_RESOLVED)
    end
    
    MSG->>PLAN: notify(plan_request)
    
    rect rgb(230, 255, 230)
        note right of PLAN: 任务规划阶段
        PLAN->>PLAN: decompose_task(intent)
        PLAN->>LLM: generate_plan(subtasks)
        LLM-->>PLAN: execution_plan
        PLAN->>PLAN: estimate_resources(plan)
        PLAN->>MSG: publish(PLAN_READY)
    end
    
    loop 执行每个步骤
        MSG->>EXEC: notify(exec_step)
        
        rect rgb(230, 245, 255)
            note right of EXEC: 执行阶段
            EXEC->>EXEC: select_tool(step)
            EXEC->>TOOL: invoke_tool(params)
            TOOL-->>EXEC: tool_result
            
            alt 执行失败
                EXEC->>EXEC: handle_retry()
                EXEC->>TOOL: invoke_tool(params)
            end
        end
        
        EXEC->>MSG: publish(STEP_DONE)
        
        MSG->>VERIFY: notify(verify_request)
        
        rect rgb(255, 230, 230)
            note right of VERIFY: 验证阶段
            VERIFY->>VERIFY: check_rules(result)
            VERIFY->>VERIFY: score_quality(result)
            VERIFY->>MSG: publish(VERIFY_RESULT)
        end
    end
    
    MSG->>ORCH: publish(TASK_COMPLETE)
```

## 3. 文件清单

| 文件 | 类/函数 | 职责 |
|------|---------|------|
| `base.py` | `BaseAgent` | Agent 抽象基类 |
| `base.py` | `AgentState` | Agent 状态枚举 |
| `base.py` | `AgentContext` | Agent 上下文 |
| `intent_agent.py` | `IntentAgent` | 意图识别 Agent |
| `intent_agent.py` | `IntentClassifier` | 意图分类器 |
| `intent_agent.py` | `SlotFiller` | 槽位填充器 |
| `plan_agent.py` | `PlanAgent` | 任务规划 Agent |
| `plan_agent.py` | `TaskDecomposer` | 任务分解器 |
| `plan_agent.py` | `PlanScheduler` | 计划调度器 |
| `exec_agent.py` | `ExecAgent` | 任务执行 Agent |
| `exec_agent.py` | `ToolSelector` | 工具选择器 |
| `exec_agent.py` | `RetryHandler` | 重试处理器 |
| `verify_agent.py` | `VerifyAgent` | 结果验证 Agent |
| `verify_agent.py` | `QualityScorer` | 质量评分器 |
| `collaboration.py` | `Collaboration` | 协作管理器 |
| `collaboration.py` | `LeaderElection` | 领导者选举 |
| `negotiation.py` | `Negotiation` | 博弈谈判管理器 |
| `negotiation.py` | `StrategyEngine` | 策略引擎 |
| `msg_hub.py` | `MessageHub` | 消息中心 |
| `actor.py` | `Actor` | Agent 角色定义 |
| `agentscope_adapter.py` | `AgentScopeAdapter` | AgentScope 框架适配 |

## 4. Agent 生命周期

### 4.1 状态定义

```mermaid
stateDiagram-v2
    [*] --> IDLE: Agent 创建
    
    %% 样式定义
    classDef idle fill:#e8f5e9,stroke:#388e3c,color:#1b5e20
    classDef busy fill:#fff3e0,stroke:#f57c00,color:#e65100
    classDef error fill:#ffcdd2,stroke:#c62828,color:#b71c1c
    
    [*] --> IDLE
    IDLE --> BUSY: 接收任务
    BUSY --> IDLE: 任务完成
    BUSY --> ERROR: 执行错误
    ERROR --> BUSY: 重试成功
    ERROR --> IDLE: 重试失败
    
    class IDLE idle
    class BUSY busy
    class ERROR error
```

### 4.2 状态说明

| 状态 | 说明 |
|------|------|
| IDLE | 空闲，等待任务 |
| BUSY | 执行中，处理任务 |
| ERROR | 错误，需要重试 |

## 5. 消息类型

### 5.1 消息格式

```python
class Message:
    id: str
    type: MessageType
    sender: str
    receiver: Optional[str]
    payload: Dict[str, Any]
    timestamp: float
```

### 5.2 消息类型定义

| 消息类型 | 发送者 | 接收者 | 说明 |
|---------|-------|-------|------|
| TASK_START | Orchestrator | All Agents | 任务开始通知 |
| INTENT_RESOLVED | IntentAgent | PlanAgent | 意图识别完成 |
| PLAN_READY | PlanAgent | ExecAgent | 执行计划就绪 |
| STEP_DONE | ExecAgent | VerifyAgent | 步骤执行完成 |
| VERIFY_RESULT | VerifyAgent | Orchestrator | 验证结果返回 |
| TASK_COMPLETE | VerifyAgent | All Agents | 任务完成通知 |
| ERROR | Any Agent | Error Handler | 错误通知 |

## 6. 核心 Agent 详解

### 6.1 IntentAgent（意图识别）

```mermaid
flowchart LR
    A[用户输入] --> B[输入解析]
    B --> C{意图分类}
    C -->|清晰| D[槽位填充]
    C -->|模糊| E[多意图识别]
    D --> F[意图确认]
    E --> F
    F --> G[输出意图]
```

**核心能力**：
- 自然语言理解
- 意图分类（支持 100+ 意图类型）
- 槽位提取与填充
- 意图置信度评估

### 6.2 PlanAgent（任务规划）

```mermaid
flowchart LR
    A[意图输入] --> B[任务分解]
    B --> C[依赖分析]
    C --> D[资源估算]
    D --> E[计划生成]
    E --> F[计划优化]
    F --> G[执行计划]
```

**核心能力**：
- 任务自动分解
- 执行顺序优化
- 资源需求评估
- 备选方案生成

### 6.3 ExecAgent（任务执行）

```mermaid
flowchart LR
    A[执行计划] --> B[工具选择]
    B --> C[参数组装]
    C --> D{执行}
    D -->|成功| E[结果处理]
    D -->|失败| F{重试?}
    F -->|是| B
    F -->|否| G[错误上报]
    E --> H[输出结果]
```

**核心能力**：
- 智能工具选择
- 参数自动组装
- 失败自动重试
- 执行结果处理

### 6.4 VerifyAgent（结果验证）

```mermaid
flowchart LR
    A[执行结果] --> B[规则检查]
    B --> C[质量评分]
    C --> D{通过?}
    D -->|是| E[输出通过]
    D -->|否| F[生成反馈]
    F --> G[反馈给 Exec]
    E --> H[最终结果]
```

**核心能力**：
- 规则引擎验证
- 质量评分模型
- 失败原因分析
- 自动修复建议

## 7. 协作机制

### 7.1 MessageHub 架构

```mermaid
graph LR
    SUB[订阅者] -->|订阅| TOPIC[Topic]
    PUB[发布者] -->|发布| TOPIC
    TOPIC -->|路由| DISPATCH[分发器]
    DISPATCH --> SUB
    
    subgraph BUS[消息总线]
        TOPIC
        DISPATCH
    end
```

### 7.2 领导者选举

采用 **Raft 简化版** 选举算法：
1. 所有 Agent 启动时为 Follower
2. 超时未收到心跳则转为 Candidate
3. 获得多数投票则成为 Leader
4. Leader 负责协调任务分配

## 8. 博弈协商（Negotiation）

### 8.1 应用场景

- 多 Agent 定价决策
- 资源竞争分配
- 冲突任务调度

### 8.2 协商流程

```mermaid
sequenceDiagram
    participant AGENT1 as Agent A
    participant AGENT2 as Agent B
    participant ENGINE as NegotiationEngine
    
    AGENT1->>ENGINE: propose(value_A)
    AGENT2->>ENGINE: propose(value_B)
    ENGINE->>ENGINE: calculate_nash_equilibrium()
    ENGINE-->>AGENT1: consensus_value
    ENGINE-->>AGENT2: consensus_value
```

## 9. Agent 配置

### 9.1 配置参数

```python
class AgentConfig:
    name: str
    role: str
    max_retries: int
    timeout: int
    temperature: float
    system_prompt: str
    tools: List[str]
```