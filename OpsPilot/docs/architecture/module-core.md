# Core 模块架构

## 组件架构图

```mermaid
graph TB
    subgraph Orchestrator编排器
        ORCH[Orchestrator<br/>主编排器<br/><br/>任务生命周期管理<br/>资源调度协调]
        ORCH_TASK[TaskManager<br/>任务管理器<br/><br/>任务创建/销毁<br/>状态跟踪]
        ORCH_RES[ResourceManager<br/>资源管理器<br/><br/>Agent分配<br/>工具调度]
        ORCH_EVENT[EventEmitter<br/>事件发射器<br/><br/>事件广播<br/>状态通知]
    end

    subgraph StateMachine状态机
        SM[StateMachine<br/>状态机核心<br/><br/>状态定义<br/>转换规则]
        SM_DEF[StateDefinition<br/>状态定义<br/><br/>PENDING/RUNNING<br/>SUCCESS/FAILED]
        SM_TRANS[Transition<br/>状态转换<br/><br/>条件检查<br/>动作触发]
        SM_HIST[StateHistory<br/>状态历史<br/><br/>变更记录<br/>回溯支持]
    end

    subgraph SOPExecutor执行器
        SOP[SOPExecutor<br/>SOP执行器<br/><br/>标准流程执行<br/>步骤编排]
        SOP_STEP[StepExecutor<br/>步骤执行器<br/><br/>单步执行<br/>结果收集]
        SOP_CTX[ExecutionContext<br/>执行上下文<br/><br/>变量管理<br/>状态传递]
        SOP_HOOK[HookManager<br/>钩子管理器<br/><br/>前置/后置处理<br/>异常处理]
    end

    subgraph Context上下文
        CTX[Context<br/>上下文管理器<br/><br/>全局状态<br/>数据共享]
        CTX_VAR[VariableStore<br/>变量存储<br/><br/>运行时变量<br/>参数传递]
        CTX_META[Metadata<br/>元数据<br/><br/>任务信息<br/>环境配置]
        CTX_CACHE[ContextCache<br/>上下文缓存<br/><br/>快照存储<br/>状态恢复]
    end

    subgraph Events事件系统
        EVT[EventManager<br/>事件管理器<br/><br/>事件订阅<br/>消息分发]
        EVT_BUS[EventBus<br/>事件总线<br/><br/>异步通信<br/>解耦组件]
        EVT_HANDLER[EventHandler<br/>事件处理器<br/><br/>回调执行<br/>错误处理]
    end

    subgraph LLMConfig配置
        LLM_CFG[LLMConfig<br/>LLM配置<br/><br/>模型选择<br/>参数设置]
        LLM_MODEL[ModelRegistry<br/>模型注册表<br/><br/>GPT/Claude<br/>DeepSeek]
        LLM_PARAMS[ParameterStore<br/>参数存储<br/><br/>temperature<br/>max_tokens]
    end

    %% Orchestrator内部连接
    ORCH --> ORCH_TASK
    ORCH --> ORCH_RES
    ORCH --> ORCH_EVENT
    ORCH_TASK --> ORCH_RES

    %% StateMachine内部连接
    SM --> SM_DEF
    SM --> SM_TRANS
    SM --> SM_HIST
    SM_TRANS --> SM_DEF

    %% SOPExecutor内部连接
    SOP --> SOP_STEP
    SOP --> SOP_CTX
    SOP --> SOP_HOOK
    SOP_CTX --> SOP_HOOK

    %% Context内部连接
    CTX --> CTX_VAR
    CTX --> CTX_META
    CTX --> CTX_CACHE

    %% Events内部连接
    EVT --> EVT_BUS
    EVT --> EVT_HANDLER
    EVT_BUS --> EVT_HANDLER

    %% LLMConfig内部连接
    LLM_CFG --> LLM_MODEL
    LLM_CFG --> LLM_PARAMS

    %% 模块间连接
    ORCH --> SM
    ORCH --> SOP
    ORCH --> CTX
    ORCH_EVENT --> EVT_BUS
    SM_TRANS --> CTX_VAR
    SOP_CTX --> CTX
    SOP_HOOK --> EVT_HANDLER

    %% 样式
    classDef primary fill:#083B75,color:#fff
    classDef secondary fill:#1a5f7a,color:#fff
    classDef tertiary fill:#2e7d32,color:#fff
    classDef support fill:#6C8EBF,color:#fff

    class ORCH,SM,SOP,CTX,EVT,LLM_CFG primary
    class ORCH_TASK,SM_DEF,SOP_STEP,CTX_VAR,EVT_BUS,LLM_MODEL secondary
    class ORCH_RES,SM_TRANS,SOP_CTX,CTX_META,EVT_HANDLER,LLM_PARAMS tertiary
    class ORCH_EVENT,SM_HIST,SOP_HOOK,CTX_CACHE support
```

## 核心流程时序图

```mermaid
sequenceDiagram
    participant CLIENT as 外部调用
    participant ORCH as Orchestrator
    participant TASK as TaskManager
    participant SM as StateMachine
    participant SOP as SOPExecutor
    participant CTX as Context
    participant EVT as EventBus
    participant RES as ResourceManager

    CLIENT->>ORCH: 1. submit_task(request)
    ORCH->>TASK: 2. create_task(request)
    TASK->>CTX: 3. init_context(task_id)
    CTX-->>TASK: 4. context_id
    TASK-->>ORCH: 5. task_created

    ORCH->>SM: 6. init_state(task_id, PENDING)
    SM->>EVT: 7. emit(TASK_CREATED)
    
    loop 任务执行
        ORCH->>SM: 8. transition(RUNNING)
        SM->>EVT: 9. emit(STATE_CHANGED)
        
        ORCH->>SOP: 10. execute_sop(sop_id)
        SOP->>CTX: 11. load_context()
        
        loop SOP步骤
            SOP->>RES: 12. allocate_agent()
            RES-->>SOP: 13. agent_instance
            SOP->>SOP: 14. execute_step()
            SOP->>CTX: 15. update_context()
            SOP->>EVT: 16. emit(STEP_COMPLETED)
        end
        
        SOP-->>ORCH: 17. sop_result
        
        alt 执行成功
            ORCH->>SM: 18. transition(SUCCESS)
        else 执行失败
            ORCH->>SM: 19. transition(FAILED)
        end
        
        SM->>EVT: 20. emit(TASK_COMPLETED)
    end
    
    ORCH->>TASK: 21. finalize_task()
    TASK->>CTX: 22. persist_context()
    ORCH-->>CLIENT: 23. task_result
```

## 文件清单

| 文件 | 类/函数 | 职责 |
|------|--------|------|
| orchestrator.py | Orchestrator | 主编排器，协调各组件 |
| orchestrator.py | TaskManager | 任务生命周期管理 |
| orchestrator.py | ResourceManager | Agent和工具资源管理 |
| state_machine.py | StateMachine | 状态机核心实现 |
| state_machine.py | StateDefinition | 状态定义枚举 |
| state_machine.py | Transition | 状态转换逻辑 |
| sop_executor.py | SOPExecutor | SOP流程执行器 |
| sop_executor.py | StepExecutor | 单步骤执行器 |
| sop_executor.py | ExecutionContext | 执行上下文管理 |
| context.py | Context | 全局上下文管理器 |
| context.py | VariableStore | 运行时变量存储 |
| events.py | EventEmitter | 事件发射器 |
| events.py | EventBus | 异步事件总线 |
| events.py | EventHandler | 事件处理器基类 |
| llm_config.py | LLMConfig | LLM配置管理 |
| llm_config.py | ModelRegistry | 模型注册表 |

## 状态机状态流转

```
PENDING → RUNNING → SUCCESS
    ↓         ↓
  FAILED    FAILED
    ↓         ↓
 RETRY → RUNNING → ...
```

## 事件类型

| 事件 | 触发时机 | 携带数据 |
|------|---------|---------|
| TASK_CREATED | 任务创建 | task_id, request |
| STATE_CHANGED | 状态变更 | task_id, old_state, new_state |
| STEP_STARTED | 步骤开始 | task_id, step_id |
| STEP_COMPLETED | 步骤完成 | task_id, step_id, result |
| TASK_COMPLETED | 任务完成 | task_id, final_state, result |
| ERROR_OCCURRED | 错误发生 | task_id, error, stack_trace |
