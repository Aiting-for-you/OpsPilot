# Agent 模块架构

## 组件架构图

```mermaid
graph TB
    subgraph Agent基类
        BASE[BaseAgent<br/>抽象基类<br/><br/>定义接口<br/>通用逻辑]
    end

    subgraph 核心Agent
        INTENT[IntentAgent<br/>意图识别<br/><br/>解析用户输入<br/>识别任务类型]
        PLAN[PlanAgent<br/>任务规划<br/><br/>生成执行计划<br/>资源分配]
        EXEC[ExecAgent<br/>任务执行<br/><br/>调用工具<br/>执行动作]
        VERIFY[VerifyAgent<br/>结果验证<br/><br/>检查结果<br/>质量审核]
    end

    subgraph 业务Agent
        BUYER[BuyerAgent<br/>采购Agent]
        FINANCE[FinanceAgent<br/>财务Agent]
        COMPLIANCE[ComplianceAgent<br/>合规Agent]
    end

    BASE --> INTENT
    BASE --> PLAN
    BASE --> EXEC
    BASE --> VERIFY
    BASE --> BUYER
    BASE --> FINANCE
    BASE --> COMPLIANCE

    style BASE fill:#083B75,color:#fff
    style INTENT fill:#6C8EBF,color:#fff
    style PLAN fill:#6C8EBF,color:#fff
    style EXEC fill:#6C8EBF,color:#fff
    style VERIFY fill:#6C8EBF,color:#fff
    style BUYER fill:#82B366,color:#fff
    style FINANCE fill:#82B366,color:#fff
    style COMPLIANCE fill:#82B366,color:#fff
```

## Agent协作时序图

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant I as IntentAgent
    participant P as PlanAgent
    participant E as ExecAgent
    participant V as VerifyAgent

    O->>I: 意图识别请求
    I->>I: 分析用户输入
    I-->>O: 返回意图类型

    O->>P: 任务规划请求
    P->>P: 生成执行计划
    P-->>O: 返回执行步骤

    loop 执行每个步骤
        O->>E: 执行步骤
        E->>E: 调用工具
        E-->>O: 返回结果
    end

    O->>V: 结果验证请求
    V->>V: 检查结果质量
    V-->>O: 返回验证结果
```

## Agent分类

| 类型 | Agent | 职责 |
|------|-------|------|
| 核心 | IntentAgent | 识别用户意图 |
| 核心 | PlanAgent | 生成执行计划 |
| 核心 | ExecAgent | 执行具体任务 |
| 核心 | VerifyAgent | 验证执行结果 |
| 业务 | BuyerAgent | 采购决策 |
| 业务 | FinanceAgent | 财务审核 |
| 业务 | ComplianceAgent | 合规检查 |
