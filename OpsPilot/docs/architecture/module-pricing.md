# Pricing 模块架构（博弈定价系统）

## 模块架构图

```mermaid
graph TB
    subgraph API层
        API["/api/v1/pricing/*"]
    end
    
    subgraph Agent层
        ORCH["PricingOrchestrator<br/>博弈协调器"]
        COST["CostAgent<br/>成本分析<br/>权重:40%"]
        MARKET["MarketAgent<br/>市场竞争<br/>权重:30%"]
        PROFIT["ProfitAgent<br/>利润优化<br/>权重:30%"]
    end
    
    subgraph 工具层
        MONITOR["CompetitorMonitorTool"]
        ELASTIC["PriceElasticityTool"]
    end
    
    API --> ORCH
    ORCH --> COST
    ORCH --> MARKET
    ORCH --> PROFIT
    
    COST --> |"成本数据"| ORCH
    MARKET --> MONITOR
    PROFIT --> ELASTIC
    MONITOR --> |"竞品价格"| MARKET
    ELASTIC --> |"弹性系数"| PROFIT

    style API层 fill:#fff3e0
    style Agent层 fill:#e8f5e9
    style 工具层 fill:#e3f2fd
```

## 博弈定价时序图

```mermaid
sequenceDiagram
    participant User as 用户
    participant API as API
    participant Orch as Orchestrator
    participant Cost as CostAgent
    participant Market as MarketAgent
    participant Profit as ProfitAgent

    User->>API: POST /pricing/negotiate
    API->>Orch: 启动定价协商
    
    par 并行分析
        Orch->>Cost: 成本分析
        Cost-->>Orch: 成本建议价×0.4
        
        Orch->>Market: 市场分析
        Market->>Market: 获取竞品数据
        Market-->>Orch: 市场建议价×0.3
        
        Orch->>Profit: 利润分析
        Profit->>Profit: 计算弹性
        Profit-->>Orch: 利润建议价×0.3
    end
    
    Orch->>Orch: 加权投票仲裁
    Orch-->>API: 最终定价
    API-->>User: 返回结果
```

## 核心组件

| 组件 | 职责 | 权重 |
|------|------|------|
| PricingOrchestrator | 博弈协调、投票仲裁 | - |
| CostAgent | 成本分析、确保毛利 | 40% |
| MarketAgent | 竞品分析、市场定位 | 30% |
| ProfitAgent | 利润优化、弹性分析 | 30% |

## API接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /pricing/negotiate | 启动定价协商 |
| GET | /pricing/history | 查询定价历史 |
| GET | /pricing/agents/status | 获取Agent状态 |
