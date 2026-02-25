# 详细设计：Omni-Agent 评估体系与基准测试

## 1. 评估的必要性
在工业级落地中，无法量化的 Agent 是不可信的。本项目建立了一套多维度的评估框架，确保系统在复杂业务中的稳定性。

## 2. RAG 质量评估 (基于 RAGAS)
针对跨境电商政策库，我们采用 RAGAS 框架进行自动化评分：
- **Faithfulness (忠实度)**：回答是否完全来源于检索到的政策原文，防止幻觉。
- **Answer Relevance (相关性)**：回答是否直接解决了采购员的合规疑问。
- **Context Precision (检索精度)**：检索到的海关条文是否确实是解决问题所需的关键信息。

## 3. 任务执行评估 (Trajectory-based)
针对工具调用和多步推理，我们引入"轨迹评分"：
- **Success Rate (SR)**：端到端完成业务 SOP 的成功率。
- **Tool Call Accuracy (TCA)**：API 参数提取的准确率（通过 SGLang 结构化输出保障）。
- **Sub-goal Completion**：复杂任务拆解后，每个子目标的达成情况。

## 4. 落地约束
- **回归测试**：每次模型微调后，必须跑通全量评估集，确保核心业务逻辑无退化。
- **人工金标 (Golden Set)**：建立 100 个核心业务场景的"标准答案库"，作为评估的基准。

## 5. 工程成本评估 (Cost-per-Solution)

### 5.1 成本构成模型
```python
class SolutionCost:
    """单次任务成本计算"""
    
    def calculate(self, task: Task) -> CostBreakdown:
        # 1. 推理成本 (Token 消耗)
        inference_cost = (
            task.prompt_tokens * MODEL_INPUT_PRICE +
            task.completion_tokens * MODEL_OUTPUT_PRICE
        ) / 1000  # 每 1K tokens
        
        # 2. API 调用成本
        api_cost = sum(
            TOOL_PRICING.get(tool.name, 0) 
            for tool in task.tool_calls
        )
        
        # 3. 存储成本
        storage_cost = (
            task.log_size_kb * STORAGE_PRICE_PER_GB / 1024 / 1024
        )
        
        # 4. 计算资源成本
        compute_cost = task.duration_seconds * COMPUTE_PRICE_PER_SECOND
        
        return CostBreakdown(
            inference=inference_cost,
            api=api_cost,
            storage=storage_cost,
            compute=compute_cost,
            total=inference_cost + api_cost + storage_cost + compute_cost
        )
```

### 5.2 成本指标看板
| 指标 | 计算方式 | 基准值 | 警戒值 |
| :--- | :--- | :--- | :--- |
| **单任务成本** | 总成本 / 任务数 | $0.05 | $0.15 |
| **Token 效率** | 成功任务平均 Token 数 | 2000 | 5000 |
| **API 调用率** | API 调用次数 / 任务数 | 3 | 10 |
| **成本成功率比** | 成功率 / 单任务成本 | 20 | 5 |

### 5.3 成本优化策略
| 优化方向 | 具体措施 | 预期收益 |
| :--- | :--- | :--- |
| **Prompt 压缩** | 移除冗余描述，精简 System Prompt | Token -30% |
| **模型选择** | 简单任务用小模型，复杂任务用大模型 | 成本 -40% |
| **缓存复用** | 缓存常见查询的 RAG 结果 | API 调用 -50% |
| **批量处理** | 合并相似任务批量执行 | 吞吐 +100% |

### 5.4 成本上限控制
```yaml
# 成本控制配置
cost_control:
  per_task:
    max_tokens: 10000
    max_api_calls: 20
    max_cost_usd: 0.50
  
  daily_budget:
    inference_usd: 100
    api_usd: 50
    total_usd: 200
  
  alert:
    warning_threshold: 0.7   # 预算 70% 时预警
    critical_threshold: 0.9  # 预算 90% 时告警
    action: throttle         # 告警后执行限流
```

## 6. 用户体验评估 (User Experience Evaluation)

### 6.1 用户体验指标体系
| 维度 | 指标 | 计算方式 | 目标值 |
| :--- | :--- | :--- | :--- |
| **响应速度** | 首次响应时间 | 首字节返回时间 | < 3s |
| **交互效率** | 平均交互轮数 | 完成任务的总对话轮数 | < 5 轮 |
| **任务完成** | 首次完成率 | 首次尝试即成功的比例 | > 80% |
| **用户满意度** | CSAT 评分 | 用户 1-5 星评分均值 | > 4.0 |
| **信任度** | 人工干预率 | 需要人工介入的任务比例 | < 10% |

### 6.2 用户反馈采集
```python
class UserFeedbackCollector:
    """用户反馈采集器"""
    
    FEEDBACK_POINTS = {
        "task_complete": "任务完成后",
        "error_occurred": "发生错误后",
        "human_intervention": "人工介入后",
        "session_end": "会话结束时"
    }
    
    async def collect(self, context: FeedbackContext) -> UserFeedback:
        """采集用户反馈"""
        return UserFeedback(
            session_id=context.session_id,
            task_type=context.task_type,
            
            # 量化指标
            task_success=context.success,
            duration=context.duration,
            interaction_rounds=context.rounds,
            
            # 主观评价
            rating=await self.ask_rating(context.user_id),
            comment=await self.ask_comment(context.user_id),
            
            # 行为数据
            retry_count=context.retries,
            cancel_rate=context.cancellations / context.total_actions
        )
```

### 6.3 用户满意度调研
| 调研维度 | 问题示例 | 评分方式 |
| :--- | :--- | :--- |
| **准确性** | "Agent 的回答是否准确解决了您的问题？" | 1-5 星 |
| **效率** | "完成任务的速度是否满足您的期望？" | 1-5 星 |
| **易用性** | "与 Agent 交互是否顺畅？" | 1-5 星 |
| **信任度** | "您是否信任 Agent 的决策？" | 1-5 星 |
| **推荐意愿** | "您是否愿意推荐同事使用此系统？" | NPS 0-10 |

### 6.4 反馈闭环机制
```
[用户反馈采集] --> [问题分类] --> [根因分析] --> [改进方案] --> [验证发布]
       ▲                                                          │
       └──────────────────── 效果监控 ←───────────────────────────┘
```

## 7. 竞品对比分析 (Competitive Analysis)

### 7.1 与主流 Agent 框架对比
| 维度 | Omni-Agent | AutoGPT | MetaGPT | CrewAI | LangGraph |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **架构模式** | 混合架构 | 单体循环 | 多角色协作 | 团队协作 | 图状态机 |
| **企业级特性** | ✅ 完整 | ⚠️ 基础 | ⚠️ 部分 | ⚠️ 部分 | ✅ 完整 |
| **工具标准化** | MCP 协议 | 插件系统 | 自定义 | 自定义 | LangChain |
| **合规审计** | ✅ 内置 | ❌ 无 | ⚠️ 基础 | ❌ 无 | ⚠️ 可扩展 |
| **GUI 自动化** | ✅ UI-TARS | ⚠️ 浏览器 | ❌ 无 | ❌ 无 | ❌ 无 |
| **推理优化** | ✅ SGLang | ❌ 无 | ❌ 无 | ❌ 无 | ⚠️ 可选 |
| **成本控制** | ✅ 内置 | ❌ 无 | ❌ 无 | ❌ 无 | ⚠️ 手动 |
| **学习曲线** | 中等 | 简单 | 中等 | 简单 | 较难 |

### 7.2 Omni-Agent 核心优势
```
┌─────────────────────────────────────────────────────────────────┐
│                    Omni-Agent 差异化优势                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 混合架构哲学                                                 │
│     • LangChain 执行层 + AgentScope 决策层                       │
│     • 确定性与灵活性兼顾                                          │
│                                                                 │
│  2. 工业级合规                                                   │
│     • 内置审计日志、权限控制、数据脱敏                             │
│     • 满足 GDPR、SOX 等合规要求                                   │
│                                                                 │
│  3. 全场景覆盖                                                   │
│     • API 路径 + GUI 路径双轨并行                                 │
│     • UI-TARS 解决"最后一公里"问题                                │
│                                                                 │
│  4. 成本可控                                                     │
│     • Token 级别成本监控                                          │
│     • 预算预警与自动限流                                          │
│                                                                 │
│  5. 方法论可迁移                                                 │
│     • 四步落地法                                                 │
│     • 跨行业复用经验                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.3 适用场景对比
| 场景 | 推荐框架 | 原因 |
| :--- | :--- | :--- |
| **个人项目/Demo** | AutoGPT | 快速上手，无需企业级特性 |
| **软件开发团队** | MetaGPT | 软件开发角色分工明确 |
| **企业业务自动化** | **Omni-Agent** | 合规、审计、GUI 全覆盖 |
| **复杂工作流** | LangGraph | 图状态机适合复杂分支 |
| **内容创作团队** | CrewAI | 角色协作模式契合创意工作 |

