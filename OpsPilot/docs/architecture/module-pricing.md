# Pricing 模块架构（博弈定价系统）

## 组件架构图

```mermaid
graph TB
    %% ==================== 第一行：编排器 ====================
    subgraph L1[PricingOrchestrator编排器]
        direction LR
        PO[PricingOrchestrator<br/>定价编排器<br/>协调多Agent]
        PO_TASK[TaskDistributor<br/>任务分发器<br/>并行调度]
        PO_AGG[ResultAggregator<br/>结果聚合器<br/>决策融合]
        PO_MONITOR[PricingMonitor<br/>定价监控器<br/>价格追踪]
    end

    %% ==================== 第二行：博弈Agent ====================
    subgraph L2A[分析Agent]
        direction LR
        PA_COST[CostAnalystAgent<br/>成本分析Agent<br/>成本核算]
        PA_COMP[CompetitorAgent<br/>竞品分析Agent<br/>竞品监控]
        PA_DEMAND[DemandAgent<br/>需求分析Agent<br/>需求预测]
    end

    subgraph L2B[决策Agent]
        direction LR
        PA_INV[InventoryAgent<br/>库存分析Agent<br/>库存压力]
        PA_STRAT[StrategyAgent<br/>策略Agent<br/>定价策略]
    end

    %% ==================== 第三行：博弈引擎 ====================
    subgraph L3[NegotiationEngine博弈引擎]
        direction LR
        NE[NegotiationEngine<br/>博弈引擎<br/>多Agent博弈]
        NE_GAME[GameTheorist<br/>博弈理论家<br/>均衡计算]
        NE_VOTE[VoteCoordinator<br/>投票协调器<br/>共识达成]
        NE_BALANCE[BalanceEngine<br/>平衡引擎<br/>帕累托最优]
    end

    %% ==================== 第四行：定价工具 ====================
    subgraph L4[PricingTools定价工具]
        direction LR
        PT[PricingTools<br/>定价工具集]
        PT_CALC[PriceCalculator<br/>价格计算器]
        PT_HIST[HistoryAnalyzer<br/>历史分析器]
        PT_OPT[OptimizerEngine<br/>优化引擎]
    end

    %% ==================== 第五行：数据源 ====================
    subgraph L5[DataSource数据源]
        direction LR
        DS[DataSourceManager<br/>数据源管理器]
        DS_ERP[ERPConnector<br/>ERP连接器]
        DS_COMP[CompetitorAPI<br/>竞品API]
        DS_MARKET[MarketAPI<br/>市场API]
    end

    %% ==================== 第六行：决策与反馈 ====================
    subgraph L6A[Decision决策层]
        direction LR
        DEC[DecisionMaker<br/>决策器]
        DEC_CONF[ConfidenceScorer<br/>置信度评分]
        DEC_APPROVE[ApprovalManager<br/>审批管理器]
    end

    subgraph L6B[Feedback反馈闭环]
        direction LR
        FB[FeedbackLoop<br/>反馈闭环]
        FB_TRACK[SalesTracker<br/>销量追踪]
        FB_ADAPT[AdaptiveEngine<br/>自适应引擎]
    end

    %% ==================== 层间连接 ====================
    PO --> PO_TASK
    PO --> PO_AGG
    PO --> PO_MONITOR

    PA_COST --> PA_STRAT
    PA_COMP --> PA_STRAT
    PA_DEMAND --> PA_STRAT
    PA_INV --> PA_STRAT

    NE --> NE_GAME
    NE --> NE_VOTE
    NE --> NE_BALANCE

    PT --> PT_CALC
    PT --> PT_HIST
    PT --> PT_OPT

    DS --> DS_ERP
    DS --> DS_COMP
    DS --> DS_MARKET

    DEC --> DEC_CONF
    DEC --> DEC_APPROVE

    FB --> FB_TRACK
    FB --> FB_ADAPT

    PO_TASK --> PA_COST
    PO_TASK --> PA_COMP
    PO_TASK --> PA_DEMAND
    PO_TASK --> PA_INV
    PA_STRAT --> NE
    NE_VOTE --> PO_AGG
    PO_AGG --> PT_CALC
    PT_CALC --> DS
    DS_ERP --> PA_COST
    DS_COMP --> PA_COMP
    PO_AGG --> DEC
    DEC_CONF --> DEC_APPROVE
    FB_TRACK --> FB_ADAPT
    FB_ADAPT --> PA_STRAT

    %% ==================== 样式 ====================
    classDef orch fill:#083B75,color:#fff
    classDef agent fill:#1a5f7a,color:#fff
    classDef engine fill:#2e7d32,color:#fff
    classDef tool fill:#1565c0,color:#fff
    classDef data fill:#6a1b9a,color:#fff
    classDef decision fill:#c62828,color:#fff
    classDef feedback fill:#f57c00,color:#fff

    class PO,PO_TASK,PO_AGG,PO_MONITOR orch
    class PA_COST,PA_COMP,PA_DEMAND,PA_INV,PA_STRAT agent
    class NE,NE_GAME,NE_VOTE,NE_BALANCE engine
    class PT,PT_CALC,PT_HIST,PT_OPT tool
    class DS,DS_ERP,DS_COMP,DS_MARKET data
    class DEC,DEC_CONF,DEC_APPROVE decision
    class FB,FB_TRACK,FB_ADAPT feedback
```

## 博弈定价时序图

```mermaid
sequenceDiagram
    participant TRIGGER as 定价触发
    participant PO as PricingOrchestrator
    participant COST as CostAnalystAgent
    participant COMP as CompetitorAgent
    participant DEMAND as DemandAgent
    participant INV as InventoryAgent
    participant NE as NegotiationEngine
    participant DEC as DecisionMaker
    participant EXEC as ExecutionEngine
    participant FB as FeedbackLoop

    TRIGGER->>PO: 1. pricing_request(product_id)
    PO->>PO: 2. init_pricing_context()

    par 并行分析
        PO->>COST: 3a. analyze_cost(product_id)
        COST->>COST: 3b. calc_base_cost()
        COST->>COST: 3c. calc_profit_margin()
        COST-->>PO: 3d. cost_analysis

        PO->>COMP: 4a. analyze_competitor(product_id)
        COMP->>COMP: 4b. fetch_competitor_prices()
        COMP->>COMP: 4c. calc_price_position()
        COMP-->>PO: 4d. competitor_analysis

        PO->>DEMAND: 5a. analyze_demand(product_id)
        DEMAND->>DEMAND: 5b. predict_demand()
        DEMAND->>DEMAND: 5c. calc_elasticity()
        DEMAND-->>PO: 5d. demand_analysis

        PO->>INV: 6a. analyze_inventory(product_id)
        INV->>INV: 6b. check_stock_level()
        INV->>INV: 6c. calc_turnover_rate()
        INV-->>PO: 6d. inventory_analysis
    end

    PO->>NE: 7. negotiate(analyses)
    
    loop 博弈轮次
        NE->>COST: 8a. propose_price()
        NE->>COMP: 8b. propose_price()
        NE->>DEMAND: 8c. propose_price()
        NE->>INV: 8d. propose_price()
        
        COST-->>NE: 9a. cost_proposal
        COMP-->>NE: 9b. comp_proposal
        DEMAND-->>NE: 9c. demand_proposal
        INV-->>NE: 9d. inv_proposal
        
        NE->>NE: 10. calculate_nash_equilibrium()
    end
    
    NE-->>PO: 11. final_proposals

    PO->>DEC: 12. make_decision(proposals)
    DEC->>DEC: 13. score_confidence()
    
    alt 高置信度
        DEC->>EXEC: 14a. execute_pricing()
    else 低置信度
        DEC->>DEC: 14b. request_approval()
        DEC->>EXEC: 14c. approved_execute()
    end
    
    EXEC-->>PO: 15. execution_result
    PO->>FB: 16. init_feedback_loop()
    FB->>FB: 17. track_sales()
    FB-->>PO: 18. feedback_data
    PO-->>TRIGGER: 19. pricing_result
```

## 文件清单

| 文件 | 类/函数 | 职责 |
|------|--------|------|
| pricing_orchestrator.py | PricingOrchestrator | 定价编排主控制器 |
| pricing_orchestrator.py | TaskDistributor | 任务分发器 |
| pricing_orchestrator.py | ResultAggregator | 结果聚合器 |
| pricing_agents.py | CostAnalystAgent | 成本分析Agent |
| pricing_agents.py | CompetitorAgent | 竞品分析Agent |
| pricing_agents.py | DemandAgent | 需求分析Agent |
| pricing_agents.py | InventoryAgent | 库存分析Agent |
| pricing_agents.py | StrategyAgent | 策略Agent |
| negotiation.py | NegotiationEngine | 博弈引擎 |
| negotiation.py | GameTheorist | 博弈理论计算 |
| negotiation.py | VoteCoordinator | 投票协调 |
| pricing_tools.py | PriceCalculator | 价格计算器 |
| pricing_tools.py | HistoryAnalyzer | 历史分析器 |
| pricing_tools.py | OptimizerEngine | 优化引擎 |
| pricing_tools.py | RuleEngine | 规则引擎 |

## Agent博弈策略

| Agent | 目标函数 | 权重 | 约束条件 |
|-------|---------|------|---------|
| CostAnalyst | 利润最大化 | 0.3 | 成本覆盖 |
| Competitor | 市场份额 | 0.25 | 竞品价格区间 |
| Demand | 销量最大化 | 0.25 | 需求弹性 |
| Inventory | 库存周转 | 0.2 | 库存水位 |

## 博弈均衡算法

```
1. 各Agent独立计算最优价格提案
2. NegotiationEngine收集所有提案
3. 计算加权平均作为初始均衡点
4. 迭代调整直至收敛（纳什均衡）
5. 验证帕累托最优性
6. 输出最终定价建议
```

## 定价触发条件

| 触发类型 | 条件 | 频率 |
|---------|------|------|
| 定时定价 | 周期性执行 | 每日/每周 |
| 事件定价 | 库存/竞品变化 | 实时 |
| 请求定价 | API调用 | 按需 |
| 异常定价 | 价格异常检测 | 实时 |
