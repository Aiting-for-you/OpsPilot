# Agent 模块架构

## 组件架构图

```mermaid
graph TB
    subgraph Base基类
        BASE[BaseAgent<br/>抽象基类<br/><br/>定义Agent接口<br/>生命周期方法]
        BASE_STATE[AgentState<br/>Agent状态<br/><br/>IDLE/BUSY<br/>ERROR]
        BASE_CTX[AgentContext<br/>Agent上下文<br/><br/>任务信息<br/>工具列表]
        BASE_MSG[MessageHub<br/>消息中心<br/><br/>消息路由<br/>订阅发布]
    end

    subgraph IntentAgent意图识别
        INTENT[IntentAgent<br/>意图识别Agent<br/><br/>解析用户输入<br/>识别任务类型]
        INTENT_PARSER[InputParser<br/>输入解析器<br/><br/>文本分词<br/>实体提取]
        INTENT_CLS[IntentClassifier<br/>意图分类器<br/><br/>ML分类<br/>规则匹配]
        INTENT_SLOT[SlotFiller<br/>槽位填充器<br/><br/>参数提取<br/>类型转换]
    end

    subgraph PlanAgent任务规划
        PLAN[PlanAgent<br/>规划Agent<br/><br/>生成执行计划<br/>资源评估]
        PLAN_DECOMP[TaskDecomposer<br/>任务分解器<br/><br/>复杂任务拆解<br/>依赖分析]
        PLAN_SCHED[PlanScheduler<br/>计划调度器<br/><br/>步骤排序<br/>并行优化]
        PLAN_RES[ResourceEstimator<br/>资源评估器<br/><br/>时间预估<br/>资源需求]
    end

    subgraph ExecAgent任务执行
        EXEC[ExecAgent<br/>执行Agent<br/><br/>调用工具执行<br/>结果收集]
        EXEC_TOOL[ToolSelector<br/>工具选择器<br/><br/>工具匹配<br/>参数组装]
        EXEC_INV[ToolInvoker<br/>工具调用器<br/><br/>执行调用<br/>超时控制]
        EXEC_RETRY[RetryHandler<br/>重试处理器<br/><br/>失败重试<br/>退避策略]
    end

    subgraph VerifyAgent结果验证
        VERIFY[VerifyAgent<br/>验证Agent<br/><br/>结果检查<br/>质量审核]
        VERIFY_RULE[RuleChecker<br/>规则检查器<br/><br/>业务规则<br/>数据校验]
        VERIFY_QUAL[QualityScorer<br/>质量评分器<br/><br/>结果评分<br/>置信度]
        VERIFY_FB[FeedbackGenerator<br/>反馈生成器<br/><br/>错误说明<br/>改进建议]
    end

    subgraph Collaboration协作模块
        COLLAB[Collaboration<br/>协作管理器<br/><br/>多Agent协调<br/>任务分发]
        COLLAB_MSG[MsgHub<br/>消息枢纽<br/><br/>Agent通信<br/>状态同步]
        COLLAB_LEAD[LeaderElection<br/>领导者选举<br/><br/>主从切换<br/>故障转移]
    end

    subgraph Negotiation博弈谈判
        NEGOT[Negotiation<br/>谈判管理器<br/><br/>多Agent博弈<br/>策略协调]
        NEGOT_STRAT[StrategyEngine<br/>策略引擎<br/><br/>定价策略<br/>谈判策略]
        NEGOT_BID[BidEngine<br/>出价引擎<br/><br/>价格计算<br/>策略选择]
    end

    subgraph Adapter适配层
        ADAPT[AgentScopeAdapter<br/>AgentScope适配器<br/><br/>框架适配<br/>API转换]
        ADAPT_LLM[LLMAdapter<br/>LLM适配器<br/><br/>模型调用<br/>响应解析]
    end

    %% Base内部连接
    BASE --> BASE_STATE
    BASE --> BASE_CTX
    BASE --> BASE_MSG

    %% IntentAgent内部连接
    INTENT --> INTENT_PARSER
    INTENT --> INTENT_CLS
    INTENT --> INTENT_SLOT
    INTENT_CLS --> INTENT_PARSER

    %% PlanAgent内部连接
    PLAN --> PLAN_DECOMP
    PLAN --> PLAN_SCHED
    PLAN --> PLAN_RES
    PLAN_DECOMP --> PLAN_SCHED

    %% ExecAgent内部连接
    EXEC --> EXEC_TOOL
    EXEC --> EXEC_INV
    EXEC --> EXEC_RETRY
    EXEC_INV --> EXEC_RETRY

    %% VerifyAgent内部连接
    VERIFY --> VERIFY_RULE
    VERIFY --> VERIFY_QUAL
    VERIFY --> VERIFY_FB
    VERIFY_RULE --> VERIFY_QUAL

    %% Collaboration内部连接
    COLLAB --> COLLAB_MSG
    COLLAB --> COLLAB_LEAD

    %% Negotiation内部连接
    NEGOT --> NEGOT_STRAT
    NEGOT --> NEGOT_BID
    NEGOT_STRAT --> NEGOT_BID

    %% Adapter内部连接
    ADAPT --> ADAPT_LLM

    %% 继承关系
    BASE -.->|继承| INTENT
    BASE -.->|继承| PLAN
    BASE -.->|继承| EXEC
    BASE -.->|继承| VERIFY

    %% 协作连接
    COLLAB_MSG --> BASE_MSG
    INTENT --> PLAN
    PLAN --> EXEC
    EXEC --> VERIFY
    EXEC --> COLLAB
    NEGOT --> COLLAB

    %% 适配器连接
    INTENT --> ADAPT_LLM
    PLAN --> ADAPT_LLM
    EXEC --> ADAPT

    %% 样式
    classDef base fill:#083B75,color:#fff
    classDef intent fill:#1a5f7a,color:#fff
    classDef plan fill:#2e7d32,color:#fff
    classDef exec fill:#1565c0,color:#fff
    classDef verify fill:#c62828,color:#fff
    classDef collab fill:#6a1b9a,color:#fff
    classDef adapt fill:#455a64,color:#fff

    class BASE,BASE_STATE,BASE_CTX,BASE_MSG base
    class INTENT,INTENT_PARSER,INTENT_CLS,INTENT_SLOT intent
    class PLAN,PLAN_DECOMP,PLAN_SCHED,PLAN_RES plan
    class EXEC,EXEC_TOOL,EXEC_INV,EXEC_RETRY exec
    class VERIFY,VERIFY_RULE,VERIFY_QUAL,VERIFY_FB verify
    class COLLAB,COLLAB_MSG,COLLAB_LEAD,NEGOT,NEGOT_STRAT,NEGOT_BID collab
    class ADAPT,ADAPT_LLM adapt
```

## Agent协作时序图

```mermaid
sequenceDiagram
    participant ORCH as Orchestrator
    participant MSG as MessageHub
    participant INTENT as IntentAgent
    participant PLAN as PlanAgent
    participant EXEC as ExecAgent
    participant TOOL as ToolLayer
    participant VERIFY as VerifyAgent
    participant LLM as LLM服务

    ORCH->>MSG: 1. broadcast(TASK_START)
    MSG->>INTENT: 2. notify(intent_request)
    
    INTENT->>INTENT: 3. parse_input(user_input)
    INTENT->>LLM: 4. classify_intent(context)
    LLM-->>INTENT: 5. intent_result
    INTENT->>INTENT: 6. fill_slots(intent)
    INTENT->>MSG: 7. publish(INTENT_RESOLVED)
    
    MSG->>PLAN: 8. notify(plan_request)
    PLAN->>PLAN: 9. decompose_task(intent)
    PLAN->>LLM: 10. generate_plan(subtasks)
    LLM-->>PLAN: 11. execution_plan
    PLAN->>PLAN: 12. estimate_resources(plan)
    PLAN->>MSG: 13. publish(PLAN_READY)

    loop 执行每个步骤
        MSG->>EXEC: 14. notify(exec_step)
        EXEC->>EXEC: 15. select_tool(step)
        EXEC->>TOOL: 16. invoke_tool(params)
        TOOL-->>EXEC: 17. tool_result
        
        alt 执行失败
            EXEC->>EXEC: 18. handle_retry()
            EXEC->>TOOL: 19. invoke_tool(params)
        end
        
        EXEC->>MSG: 20. publish(STEP_DONE)
        
        MSG->>VERIFY: 21. notify(verify_request)
        VERIFY->>VERIFY: 22. check_rules(result)
        VERIFY->>VERIFY: 23. score_quality(result)
        VERIFY->>MSG: 24. publish(VERIFY_RESULT)
    end
    
    MSG->>ORCH: 25. publish(TASK_COMPLETE)
```

## 文件清单

| 文件 | 类/函数 | 职责 |
|------|--------|------|
| base.py | BaseAgent | Agent抽象基类 |
| base.py | AgentState | Agent状态枚举 |
| base.py | AgentContext | Agent上下文 |
| intent_agent.py | IntentAgent | 意图识别Agent |
| intent_agent.py | IntentClassifier | 意图分类器 |
| intent_agent.py | SlotFiller | 槽位填充器 |
| plan_agent.py | PlanAgent | 任务规划Agent |
| plan_agent.py | TaskDecomposer | 任务分解器 |
| plan_agent.py | PlanScheduler | 计划调度器 |
| exec_agent.py | ExecAgent | 任务执行Agent |
| exec_agent.py | ToolSelector | 工具选择器 |
| exec_agent.py | RetryHandler | 重试处理器 |
| verify_agent.py | VerifyAgent | 结果验证Agent |
| verify_agent.py | QualityScorer | 质量评分器 |
| collaboration.py | Collaboration | 协作管理器 |
| collaboration.py | LeaderElection | 领导者选举 |
| negotiation.py | Negotiation | 博弈谈判管理器 |
| negotiation.py | StrategyEngine | 策略引擎 |
| msg_hub.py | MessageHub | 消息中心 |
| actor.py | Actor | Agent角色定义 |
| agentscope_adapter.py | AgentScopeAdapter | AgentScope框架适配 |

## Agent生命周期

```
INIT → IDLE → BUSY → SUCCESS/FAILED → IDLE
                  ↓
                ERROR → RETRY → BUSY
```

## 消息类型

| 消息类型 | 发送者 | 接收者 | 说明 |
|---------|-------|-------|------|
| TASK_START | Orchestrator | All Agents | 任务开始通知 |
| INTENT_RESOLVED | IntentAgent | PlanAgent | 意图识别完成 |
| PLAN_READY | PlanAgent | ExecAgent | 执行计划就绪 |
| STEP_DONE | ExecAgent | VerifyAgent | 步骤执行完成 |
| VERIFY_RESULT | VerifyAgent | Orchestrator | 验证结果返回 |
| TASK_COMPLETE | VerifyAgent | All Agents | 任务完成通知 |
| ERROR | Any Agent | Error Handler | 错误通知 |
