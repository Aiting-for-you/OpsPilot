# Core 模块架构

## 模块架构图

```mermaid
graph TB
    subgraph Core模块
        ORCH["Orchestrator<br/>任务编排器"]
        FSM["StateMachine<br/>状态机"]
        CTX["Context<br/>上下文管理"]
        EVT["EventBus<br/>事件总线"]
        SOP["SOPExecutor<br/>SOP执行器"]
    end
    
    subgraph 状态定义
        STATES["8个状态<br/>INIT→PLANNING→AUDITING<br/>→EXECUTING→VERIFYING<br/>→SUCCESS/RETRY/REJECTED"]
    end
    
    ORCH --> FSM
    ORCH --> SOP
    FSM --> CTX
    FSM --> EVT
    EVT --> ORCH
    
    FSM --> STATES

    style Core模块 fill:#e8eaf6
    style 状态定义 fill:#f3e5f5
```

## 核心流程时序图

```mermaid
sequenceDiagram
    participant Client as 调用方
    participant Orch as Orchestrator
    participant FSM as StateMachine
    participant CTX as Context
    participant EVT as EventBus

    Client->>Orch: 提交任务
    Orch->>CTX: 创建上下文
    CTX-->>Orch: 返回Context
    
    Orch->>FSM: 初始化状态(INIT)
    FSM->>EVT: 发布StateChangeEvent
    
    loop 状态流转
        FSM->>FSM: 验证转换
        FSM->>CTX: 更新状态
        FSM->>EVT: 发布事件
    end
    
    FSM-->>Orch: 状态完成
    Orch-->>Client: 返回结果
```

## 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| Orchestrator | orchestrator.py | 任务编排、Agent调度 |
| StateMachine | state_machine.py | 状态流转控制 |
| Context | context.py | 上下文管理 |
| EventBus | events.py | 事件发布订阅 |
| SOPExecutor | sop_executor.py | SOP流程执行 |
