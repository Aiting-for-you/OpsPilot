# Agent 模块架构

## 模块架构图

```mermaid
graph TB
    subgraph Agent基类
        BASE["BaseAgent<br/>抽象基类"]
    end
    
    subgraph 核心Agent
        INTENT["IntentAgent<br/>意图识别"]
        PLAN["PlanAgent<br/>任务规划"]
        EXEC["ExecAgent<br/>任务执行"]
        VERIFY["VerifyAgent<br/>结果验证"]
    end
    
    subgraph 业务Agent
        BUYER["BuyerAgent<br/>采购"]
        FINANCE["FinanceAgent<br/>财务"]
        COMPLIANCE["ComplianceAgent<br/>合规"]
    end
    
    BASE --> INTENT
    BASE --> PLAN
    BASE --> EXEC
    BASE --> VERIFY
    
    BASE --> BUYER
    BASE --> FINANCE
    BASE --> COMPLIANCE

    style Agent基类 fill:#e8eaf6
    style 核心Agent fill:#e8f5e9
    style 业务Agent fill:#e3f2fd
```

## Agent协作时序图

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant I as IntentAgent
    participant P as PlanAgent
    participant E as ExecAgent
    participant V as VerifyAgent

    O->>I: 意图识别
    I->>I: 分析用户输入
    I-->>O: 返回意图
    
    O->>P: 任务规划
    P->>P: 生成执行计划
    P-->>O: 返回计划
    
    loop 执行步骤
        O->>E: 执行步骤
        E->>E: 调用工具
        E-->>O: 返回结果
    end
    
    O->>V: 结果验证
    V->>V: 检查结果
    V-->>O: 验证通过
```

## Agent列表

| Agent | 文件 | 职责 |
|------|------|------|
| IntentAgent | intent_agent.py | 识别用户意图 |
| PlanAgent | plan_agent.py | 生成执行计划 |
| ExecAgent | exec_agent.py | 执行具体任务 |
| VerifyAgent | verify_agent.py | 验证执行结果 |
| BuyerAgent | buyer_agent.py | 采购决策 |
| FinanceAgent | finance_agent.py | 财务审核 |
| ComplianceAgent | compliance_agent.py | 合规检查 |
