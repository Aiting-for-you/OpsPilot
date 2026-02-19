# Customer Service 模块架构（客服工单系统）

## 组件架构图

```mermaid
graph TB
    subgraph API层
        API[API接口<br/><br/>/customer-service/tickets<br/>/customer-service/tickets/process]
    end

    subgraph Agent流水线
        CLASSIFY[ClassifierAgent<br/>工单分类<br/><br/>识别类型<br/>评估优先级]
        ROUTER[RouterAgent<br/>路由决策<br/><br/>分配部门<br/>指定专家]
        SOLVER[SolverAgent<br/>问题解决<br/><br/>生成方案<br/>检索案例]
        REVIEWER[ReviewerAgent<br/>质量审核<br/><br/>检查完整性<br/>评估满意度]
    end

    subgraph 工具层
        TM[TicketManager<br/>工单管理]
        KB[知识库检索]
    end

    API --> CLASSIFY
    CLASSIFY --> ROUTER
    ROUTER --> SOLVER
    SOLVER --> REVIEWER
    REVIEWER --> API

    CLASSIFY --> TM
    SOLVER --> TM
    SOLVER --> KB

    style API fill:#083B75,color:#fff
    style CLASSIFY fill:#6C8EBF,color:#fff
    style ROUTER fill:#6C8EBF,color:#fff
    style SOLVER fill:#6C8EBF,color:#fff
    style REVIEWER fill:#6C8EBF,color:#fff
    style TM fill:#82B366,color:#fff
    style KB fill:#D79B00,color:#fff
```

## 工单处理时序图

```mermaid
sequenceDiagram
    participant U as 用户
    participant API as API
    participant C as Classifier
    participant R as Router
    participant S as Solver
    participant V as Reviewer

    U->>API: POST /tickets/process
    API->>C: 工单分类请求

    C->>C: 分析工单内容
    C->>C: 识别类型和优先级
    C-->>API: 分类结果

    API->>R: 路由决策请求
    R->>R: 匹配部门规则
    R-->>API: 部门和专家分配

    API->>S: 问题解决请求
    S->>S: 检索历史案例
    S->>S: 生成解决方案
    S-->>API: 解决方案

    API->>V: 质量审核请求
    V->>V: 检查方案完整性
    V-->>API: 审核结果

    API-->>U: 返回处理结果
```

## 处理流程

| 阶段 | Agent | 输入 | 输出 |
|------|-------|------|------|
| 分类 | Classifier | 工单内容 | 类型、优先级 |
| 路由 | Router | 分类结果 | 部门、专家 |
| 解决 | Solver | 路由结果 | 解决方案 |
| 审核 | Reviewer | 解决方案 | 审核结果 |
