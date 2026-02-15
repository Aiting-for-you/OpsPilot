# 详细设计：LangChain + AgentScope 混合编排架构

## 1. 架构定位
本项目采用“大脑-肢体”分离模型，解决多智能体协作中的逻辑混乱问题。
- **AgentScope (大脑/Orchestrator)**：负责高层业务逻辑、多角色博弈、状态流转。
- **LangChain (肢体/Executor)**：负责具体的工具执行、RAG 检索、长链条逻辑处理。

## 2. 核心组件设计

### 2.1 显式状态机 (FSM)
在 AgentScope 中，业务流程不再仅依赖 Prompt，而是定义为显式状态：
- **IDLE**：等待任务输入。
- **PLANNING**：拆解业务目标。
- **EXECUTING**：调用 LangChain 工具链。
- **REVIEWING**：财务/合规 Agent 审计。
- **FINALIZING**：输出结果或写入 ERP。

### 2.2 协作协议 (Handshake Protocol)
AgentScope 与 LangChain 通过标准化的 JSON 接口通信：
- **Input**：`{ "task_id": "...", "action": "...", "params": {...} }`
- **Output**：`{ "status": "success/fail", "data": {...}, "trace_id": "..." }`

## 3. 编排层缓存机制 (Orchestration Cache)

### 3.1 热路径与冷路径分离
| 路径类型 | 定义 | 处理策略 | 示例场景 |
| :--- | :--- | :--- | :--- |
| **热路径 (Hot Path)** | 高频、模式固定的任务 | 预设工作流模板，跳过实时推理 | 常规采购审批、库存查询 |
| **冷路径 (Cold Path)** | 低频、复杂多变的任务 | 完整 LLM 推理链路 | 新供应商审核、异常合规处理 |

### 3.2 预设路径模板 (Workflow Templates)
```python
# 常见排查工作流预设模板
WORKFLOW_TEMPLATES = {
    "routine_procurement": {
        "steps": ["parse_intent", "check_budget", "create_order", "notify"],
        "skip_inference": ["parse_intent", "check_budget"],  # 跳过 LLM，直接规则匹配
        "cache_key": "procurement_{category}_{amount_range}",
        "ttl": 3600
    },
    "compliance_check": {
        "steps": ["rag_lookup", "policy_match", "decision"],
        "skip_inference": [],  # 全流程推理
        "cache_key": None,  # 不缓存
    }
}
```

### 3.3 缓存效果预估
- **延迟降低**：热路径任务首字延迟从 1.5s 降至 0.3s
- **Token 节省**：预估减少 60% 的推理 Token 消耗
- **命中率目标**：热路径缓存命中率 > 80%

## 4. 并发控制策略 (Concurrency Control)

### 4.1 资源锁机制
```python
class ResourceLockManager:
    def __init__(self):
        self.locks = {}  # resource_id -> Lock
        self.timeout = 30  # 锁超时时间（秒）
    
    async def acquire(self, resource_id: str, agent_id: str) -> bool:
        """尝试获取资源锁"""
        if resource_id not in self.locks:
            self.locks[resource_id] = {"holder": agent_id, "timestamp": time.time()}
            return True
        
        # 检查是否超时
        if time.time() - self.locks[resource_id]["timestamp"] > self.timeout:
            self.locks[resource_id] = {"holder": agent_id, "timestamp": time.time()}
            return True
        
        return False  # 锁被占用
    
    async def release(self, resource_id: str, agent_id: str):
        """释放资源锁"""
        if resource_id in self.locks and self.locks[resource_id]["holder"] == agent_id:
            del self.locks[resource_id]
```

### 4.2 死锁检测与处理
| 检测方式 | 描述 | 处理策略 |
| :--- | :--- | :--- |
| **超时检测** | 单个锁持有超过 30 秒 | 强制释放，回滚操作 |
| **有向图检测** | 构建 wait-for 图，检测环 | 选择代价最小的 Agent 终止等待 |
| **优先级抢占** | 高优先级任务可抢占低优先级锁 | 低优先级任务进入重试队列 |

### 4.3 并发限流配置
```yaml
concurrency:
  max_concurrent_agents: 100
  max_concurrent_tools_per_agent: 5
  rate_limit:
    rag_query: 100/second
    mcp_call: 50/second
    gui_action: 10/second
  queue:
    max_size: 1000
    overflow_policy: reject  # reject | drop_oldest
```

## 5. 性能基准 (Performance Benchmark)

### 5.1 延迟指标 (Latency)
| 操作类型 | P50 | P95 | P99 | 优化手段 |
| :--- | :--- | :--- | :--- | :--- |
| 意图识别 | 0.3s | 0.5s | 0.8s | 模型量化 + 缓存 |
| RAG 检索 | 0.2s | 0.4s | 0.6s | 向量索引优化 |
| MCP 调用 | 0.5s | 1.0s | 2.0s | 连接池 + 熔断 |
| GUI 操作 | 1.0s | 2.0s | 4.0s | 元素定位缓存 |
| 端到端 SOP | 3.0s | 6.0s | 10.0s | 热路径预设 |

### 5.2 吞吐量指标 (Throughput)
- **单节点**：50 并发 SOP/分钟
- **集群 (8 节点)**：400 并发 SOP/分钟
- **峰值承载**：1000 QPS（含降级）

### 5.3 性能优化手段
| 问题 | 现象 | 解决方案 |
| :--- | :--- | :--- |
| 推理延迟高 | P99 > 5s | SGLang Prefix Caching + 批量推理 |
| RAG 慢查询 | 检索 > 1s | 预计算索引 + 热点缓存 |
| 工具调用超时 | MCP 调用失败率高 | 超时熔断 + 异步重试 |
| 内存占用高 | OOM 频繁 | 会话压缩 + 滑动窗口 |

## 6. 落地约束
- **禁止跨层调用**：Agent 角色不得直接操作底层数据库，必须通过 LangChain 封装的 Tool。
- **强制审计**：所有涉及资金、合同的操作必须经过 `ReviewerAgent` 状态节点。

