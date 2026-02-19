# Customer Service 模块架构（客服工单系统）

## 模块架构图

```mermaid
graph TB
    subgraph API层
        API["/api/v1/customer-service/*"]
    end
    
    subgraph Agent流水线
        CLASSIFY["ClassifierAgent<br/>工单分类"]
        ROUTER["RouterAgent<br/>路由决策"]
        SOLVER["SolverAgent<br/>问题解决"]
        REVIEWER["ReviewerAgent<br/>质量审核"]
    end
    
    subgraph 工具层
        TM["TicketManagerTool<br/>工单CRUD"]
        KB["知识库检索"]
    end
    
    API --> CLASSIFY
    CLASSIFY --> |"类型/优先级"| ROUTER
    ROUTER --> |"部门/专家"| SOLVER
    SOLVER --> |"解决方案"| REVIEWER
    REVIEWER --> API
    
    CLASSIFY --> TM
    SOLVER --> TM
    SOLVER --> KB

    style API层 fill:#fff3e0
    style Agent流水线 fill:#e3f2fd
    style 工具层 fill:#e8f5e9
```

## 工单处理时序图

```mermaid
sequenceDiagram
    participant User as 用户
    participant API as API
    participant C as Classifier
    participant R as Router
    participant S as Solver
    participant V as Reviewer

    User->>API: POST /tickets/process
    API->>C: 工单分类
    
    C->>C: 分析内容
    C->>C: 识别类型
    C-->>API: 类型/优先级
    
    API->>R: 路由决策
    R->>R: 匹配部门规则
    R-->>API: 部门/专家
    
    API->>S: 生成解决方案
    S->>S: 检索历史案例
    S->>S: 生成方案
    S-->>API: 解决方案
    
    API->>V: 质量审核
    V->>V: 检查完整性
    V-->>API: 审核结果
    
    API-->>User: 返回处理结果
```

## 核心组件

| 组件 | 职责 | 输入 | 输出 |
|------|------|------|------|
| ClassifierAgent | 工单分类 | 工单内容 | 类型、优先级 |
| RouterAgent | 路由决策 | 分类结果 | 部门、专家 |
| SolverAgent | 问题解决 | 路由结果 | 解决方案 |
| ReviewerAgent | 质量审核 | 解决方案 | 审核结果 |

## API接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /customer-service/tickets | 创建工单 |
| POST | /customer-service/tickets/process | 处理工单 |
| GET | /customer-service/tickets | 查询工单列表 |
| GET | /customer-service/tickets/{id} | 查询工单详情 |
| GET | /customer-service/agents/status | 获取Agent状态 |
