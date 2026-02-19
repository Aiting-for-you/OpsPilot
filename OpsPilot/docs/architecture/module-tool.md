# Tool 模块架构

## 组件架构图

```mermaid
graph TB
    subgraph 工具基类
        BASE[BaseTool<br/>抽象基类<br/><br/>定义接口<br/>参数验证]
    end

    subgraph MCP工具
        ERP[ERP Tool<br/><br/>订单管理<br/>库存查询]
        LOG[Logistics Tool<br/><br/>物流追踪<br/>运费计算]
        PAY[Payment Tool<br/><br/>支付处理<br/>退款操作]
    end

    subgraph 内部工具
        FORMAT[Format Tool<br/><br/>数据格式化]
        CALC[Calc Tool<br/><br/>业务计算]
        VALIDATE[Validate Tool<br/><br/>数据验证]
    end

    subgraph 电商工具
        COMPETITOR[Competitor Monitor<br/><br/>竞品监控]
        ELASTIC[Price Elasticity<br/><br/>价格弹性分析]
        TICKET[Ticket Manager<br/><br/>工单管理]
    end

    BASE --> ERP
    BASE --> LOG
    BASE --> PAY
    BASE --> FORMAT
    BASE --> CALC
    BASE --> VALIDATE
    BASE --> COMPETITOR
    BASE --> ELASTIC
    BASE --> TICKET

    style BASE fill:#083B75,color:#fff
    style ERP fill:#B85450,color:#fff
    style LOG fill:#B85450,color:#fff
    style PAY fill:#B85450,color:#fff
    style FORMAT fill:#6C8EBF,color:#fff
    style CALC fill:#6C8EBF,color:#fff
    style VALIDATE fill:#6C8EBF,color:#fff
    style COMPETITOR fill:#82B366,color:#fff
    style ELASTIC fill:#82B366,color:#fff
    style TICKET fill:#82B366,color:#fff
```

## 工具调用时序图

```mermaid
sequenceDiagram
    participant A as Agent
    participant R as ToolRouter
    participant M as MCP Client
    participant E as External API

    A->>R: 请求工具调用
    R->>R: 查找工具定义

    alt MCP工具
        R->>M: JSON-RPC调用
        M->>E: HTTP请求
        E-->>M: 响应数据
        M-->>R: 返回结果
    else 内部工具
        R->>R: 本地执行
    end

    R-->>A: 返回结果
```

## 工具分类

| 类别 | 工具 | 功能 |
|------|------|------|
| MCP | ERP Tool | 订单管理、库存查询 |
| MCP | Logistics Tool | 物流追踪、运费计算 |
| MCP | Payment Tool | 支付、退款 |
| 内部 | Format Tool | 数据格式化 |
| 内部 | Calc Tool | 业务计算 |
| 内部 | Validate Tool | 数据验证 |
| 电商 | Competitor Monitor | 竞品价格监控 |
| 电商 | Price Elasticity | 价格弹性分析 |
| 电商 | Ticket Manager | 工单CRUD操作 |
