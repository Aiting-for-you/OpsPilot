# Pricing 模块架构（博弈定价系统）

## 组件架构图

```mermaid
graph TB
    subgraph API层
        API[API接口<br/><br/>/pricing/negotiate<br/>/pricing/history]
    end

    subgraph 编排层
        ORCH[PricingOrchestrator<br/>博弈协调器<br/><br/>并行调度<br/>投票仲裁]
    end

    subgraph Agent层
        COST[CostAgent<br/>成本分析<br/><br/>确保毛利<br/>权重: 40%]
        MARKET[MarketAgent<br/>市场竞争<br/><br/>竞品分析<br/>权重: 30%]
        PROFIT[ProfitAgent<br/>利润优化<br/><br/>弹性分析<br/>权重: 30%]
    end

    subgraph 工具层
        MONITOR[CompetitorMonitor<br/>竞品监控]
        ELASTIC[PriceElasticity<br/>价格弹性]
    end

    API --> ORCH
    ORCH --> COST
    ORCH --> MARKET
    ORCH --> PROFIT
    MARKET --> MONITOR
    PROFIT --> ELASTIC

    style API fill:#083B75,color:#fff
    style ORCH fill:#083B75,color:#fff
    style COST fill:#6C8EBF,color:#fff
    style MARKET fill:#6C8EBF,color:#fff
    style PROFIT fill:#6C8EBF,color:#fff
    style MONITOR fill:#82B366,color:#fff
    style ELASTIC fill:#82B366,color:#fff
```

## 博弈定价时序图

```mermaid
sequenceDiagram
    participant U as 用户
    participant API as API
    participant ORCH as Orchestrator
    participant COST as CostAgent
    participant MARKET as MarketAgent
    participant PROFIT as ProfitAgent

    U->>API: POST /pricing/negotiate
    API->>ORCH: 启动定价协商

    par 并行分析
        ORCH->>COST: 成本分析请求
        COST-->>ORCH: 成本建议价 (权重0.4)

        ORCH->>MARKET: 市场分析请求
        MARKET-->>ORCH: 市场建议价 (权重0.3)

        ORCH->>PROFIT: 利润分析请求
        PROFIT-->>ORCH: 利润建议价 (权重0.3)
    end

    ORCH->>ORCH: 加权投票仲裁
    ORCH-->>API: 最终定价结果
    API-->>U: 返回定价决策
```

## 博弈机制

| Agent | 视角 | 权重 | 关注点 |
|-------|------|------|--------|
| CostAgent | 成本 | 40% | 确保覆盖成本+毛利 |
| MarketAgent | 市场 | 30% | 竞品定价、市场定位 |
| ProfitAgent | 利润 | 30% | 价格弹性、利润最大化 |

## 最终定价公式

```
最终价格 = CostPrice × 0.4 + MarketPrice × 0.3 + ProfitPrice × 0.3
```
