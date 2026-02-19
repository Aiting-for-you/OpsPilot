# Core 模块架构

## 组件架构图

```mermaid
graph TB
    subgraph Core模块
        ORCH[Orchestrator<br/>编排器<br/><br/>任务分发<br/>结果聚合]
        FSM[StateMachine<br/>状态机<br/><br/>状态验证<br/>转换控制]
        CTX[Context<br/>上下文<br/><br/>数据传递<br/>序列化]
        EVT[EventBus<br/>事件总线<br/><br/>发布订阅<br/>监听通知]
        SOP[SOPExecutor<br/>执行器<br/><br/>流程编排<br/>步骤执行]
    end

    ORCH --> FSM
    ORCH --> SOP
    FSM --> CTX
    FSM --> EVT

    style ORCH fill:#083B75,color:#fff
    style FSM fill:#083B75,color:#fff
    style CTX fill:#6C8EBF,color:#fff
    style EVT fill:#6C8EBF,color:#fff
    style SOP fill:#083B75,color:#fff
```

## 状态流转时序图

```mermaid
sequenceDiagram
    participant Client as 调用方
    participant ORCH as Orchestrator
    participant FSM as StateMachine
    participant CTX as Context

    Client->>ORCH: 提交任务
    ORCH->>CTX: 创建上下文
    ORCH->>FSM: 初始化状态

    FSM->>FSM: INIT → PLANNING
    FSM->>CTX: 更新状态

    FSM->>FSM: PLANNING → EXECUTING
    FSM->>CTX: 更新状态

    FSM->>FSM: EXECUTING → VERIFYING
    FSM->>CTX: 更新状态

    FSM->>FSM: VERIFYING → SUCCESS
    FSM->>CTX: 更新状态

    FSM-->>ORCH: 状态完成
    ORCH-->>Client: 返回结果
```

## 状态定义

| 状态 | 说明 | 允许的下一状态 |
|------|------|---------------|
| INIT | 初始化 | PLANNING |
| PLANNING | 规划中 | AUDITING |
| AUDITING | 审核中 | EXECUTING, REJECTED |
| EXECUTING | 执行中 | VERIFYING |
| VERIFYING | 验证中 | SUCCESS, RETRY |
| SUCCESS | 成功 | - |
| RETRY | 重试 | EXECUTING |
| REJECTED | 拒绝 | - |

## 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| Orchestrator | orchestrator.py | 任务编排、Agent调度 |
| StateMachine | state_machine.py | 状态流转控制 |
| Context | context.py | 上下文管理 |
| EventBus | events.py | 事件发布订阅 |
| SOPExecutor | sop_executor.py | SOP流程执行 |
