# Tool 模块架构

## 模块架构图

```mermaid
graph TB
    subgraph 工具基类
        BASE["BaseTool<br/>抽象基类"]
    end
    
    subgraph MCP工具
        ERP["ERP Tool<br/>订单/库存"]
        LOG["Logistics Tool<br/>物流追踪"]
        PAY["Payment Tool<br/>支付处理"]
    end
    
    subgraph 内部工具
        FORMAT["FormatTool<br/>格式化"]
        CALC["CalcTool<br/>计算"]
        VALIDATE["ValidateTool<br/>验证"]
    end
    
    subgraph 电商工具
        COMPETITOR["CompetitorMonitor<br/>竞品监控"]
        ELASTIC["PriceElasticity<br/>价格弹性"]
        TICKET["TicketManager<br/>工单管理"]
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

    style 工具基类 fill:#e8eaf6
    style MCP工具 fill:#e8f5e9
    style 内部工具 fill:#fff3e0
    style 电商工具 fill:#e3f2fd
```

## 工具调用时序图

```mermaid
sequenceDiagram
    participant Agent as Agent
    participant Router as ToolRouter
    participant MCP as MCP Client
    participant API as External API

    Agent->>Router: 请求工具调用
    Router->>Router: 查找工具
    
    alt MCP工具
        Router->>MCP: JSON-RPC调用
        MCP->>API: HTTP请求
        API-->>MCP: 响应
        MCP-->>Router: 结果
    else 内部工具
        Router->>Router: 本地执行
    end
    
    Router-->>Agent: 返回结果
```

## 工具分类

| 类别 | 工具 | 说明 |
|------|------|------|
| MCP | ERP Tool | 订单管理、库存查询 |
| MCP | Logistics Tool | 物流追踪、运费计算 |
| MCP | Payment Tool | 支付、退款 |
| 内部 | FormatTool | 数据格式化 |
| 内部 | CalcTool | 业务计算 |
| 内部 | ValidateTool | 数据验证 |
| 电商 | CompetitorMonitor | 竞品价格监控 |
| 电商 | PriceElasticity | 价格弹性分析 |
| 电商 | TicketManager | 工单CRUD |
