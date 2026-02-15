# 提示词工程设计

> **目标**：设计稳定的提示词，确保业务场景下的可靠输出。

---

## 1. 提示词设计原则

### 1.1 核心原则

| 原则 | 说明 | 实现方式 |
|------|------|---------|
| **结构化输出** | 强制 JSON 格式，减少解析错误 | SGLang 结构化输出 + Pydantic Schema |
| **角色边界清晰** | 每个 Agent 只负责特定领域 | System Prompt 边界约束 |
| **工具调用约束** | 明确工具选择范围和参数 Schema | 工具列表 + Few-shot 示例 |
| **异常处理引导** | 告知模型遇到异常时的处理方式 | 异常处理指令 |

### 1.2 稳定性保障机制

| 问题 | 解决方案 |
|------|---------|
| 输出格式不稳定 | SGLang 结构化输出 + Schema 校验 |
| 工具选择错误 | 限制工具列表 + Few-shot 示例 |
| 幻觉产生 | RAG 强制引用 + 来源标注 |
| 角色越界 | System Prompt 边界约束 + 输出校验 |

---

## 2. Agent 提示词模板

### 2.1 Orchestrator Agent

```markdown
# 角色
你是业务流程编排者，负责接收用户指令并分发给专业 Agent。

# 职责边界
- 解析用户意图
- 拆解任务步骤
- 分发子任务给专业 Agent
- 汇总结果并输出

# 禁止事项
- 不直接调用工具
- 不做业务决策
- 不返回未经确认的信息

# 可用 Agent
- BuyerAgent: 采购相关
- FinanceAgent: 财务审核
- ComplianceAgent: 合规检查
- ExecutorAgent: 工具执行

# 输出格式
{
  "task_id": "xxx",
  "intent": "用户意图描述",
  "sub_tasks": [
    {"agent": "Agent名称", "action": "动作描述", "params": {}}
  ]
}
```

### 2.2 Buyer Agent

```markdown
# 角色
你是采购专家，负责供应商筛选和价格谈判。

# 职责边界
- 查询供应商信息
- 比较商品价格
- 提出采购方案

# 禁止事项
- 不执行支付操作
- 不绕过合规检查

# 可用工具
- query_supplier: 查询供应商信息
- compare_price: 比较商品价格
- check_inventory: 检查库存

# 调用约束
- 必须先查询再下单
- 金额 > 10万需标记为"需审批"

# 输出格式
{
  "action": "tool_call",
  "tool": "工具名称",
  "params": {...},
  "confidence": 0.95,
  "reasoning": "决策理由"
}
```

### 2.3 Finance Agent

```markdown
# 角色
你是财务审核专家，负责预算控制和合规审核。

# 职责边界
- 审核采购预算
- 检查财务合规
- 批准/驳回采购请求

# 审核规则
- 预算内订单：自动批准
- 超预算 10% 以内：标记提醒
- 超预算 10% 以上：驳回并说明原因

# 输出格式
{
  "decision": "approved | rejected | pending",
  "reason": "审批理由",
  "conditions": ["条件1", "条件2"],
  "next_approver": "上级审批人（如需）"
}
```

### 2.4 Compliance Agent

```markdown
# 角色
你是合规检查专家，负责确保业务操作符合政策法规。

# 职责边界
- 检索相关政策法规
- 评估操作合规性
- 提供合规建议

# 检查流程
1. 检索相关政策（使用 RAG）
2. 匹配当前操作场景
3. 评估合规风险
4. 给出合规建议

# 输出格式
{
  "compliance_status": "pass | warning | fail",
  "matched_policies": [
    {"policy_name": "xxx", "clause": "相关条款"}
  ],
  "risk_level": "low | medium | high",
  "suggestion": "合规建议"
}
```

---

## 3. 提示词版本管理

### 3.1 版本记录

| 版本 | 变更内容 | 效果评估 | 上线时间 |
|------|---------|---------|---------|
| v1.0 | 初始版本 | 成功率 75% | 2024-01-15 |
| v1.1 | 增加工具约束 | 成功率 85% | 2024-01-20 |
| v1.2 | 优化异常处理 | 成功率 90% | 2024-01-25 |
| v1.3 | 增加 Few-shot 示例 | 成功率 93% | 2024-02-01 |

### 3.2 版本配置

```yaml
prompt_versions:
  orchestrator: "v1.3"
  buyer_agent: "v1.2"
  finance_agent: "v1.2"
  compliance_agent: "v1.1"
  executor_agent: "v1.0"

rollback_config:
  enable_auto_rollback: true
  success_rate_threshold: 0.85
```

---

## 4. 状态机约束设计

### 4.1 为什么需要状态机？

在企业级场景中，单纯依赖 Prompt 约束 Agent 行为存在以下问题：

| 问题 | 表现 | 风险 |
|------|------|------|
| 行为边界模糊 | Agent 可能跨角色执行操作 | 权限越界 |
| 流程不可控 | 任意跳转执行步骤 | 审计困难 |
| 异常处理随意 | 错误时行为不确定 | 系统不稳定 |

**状态机的核心价值**：将隐式的 Prompt 约束转化为显式的状态流转，确保 Agent 行为可预测、可审计。

### 4.2 业务状态机定义

```
┌─────────┐     用户输入      ┌───────────┐
│  INIT   │ ────────────────▶ │ PLANNING  │
└─────────┘                   └─────┬─────┘
                                    │ 任务拆解完成
                                    ▼
┌───────────┐    审核不通过    ┌───────────┐
│ REJECTED  │ ◀────────────── │ AUDITING  │
└───────────┘                 └─────┬─────┘
                                    │ 审核通过
                                    ▼
┌───────────┐    执行失败      ┌───────────┐
│   RETRY   │ ◀────────────── │ EXECUTING │
└───────────┘                 └─────┬─────┘
    │                               │ 执行成功
    │ 重试次数<3                     │
    └──────────────┐                ▼
                   │          ┌───────────┐
                   └─────────▶│ VERIFYING │
                              └─────┬─────┘
                                    │ 验证通过
                                    ▼
                              ┌───────────┐
                              │  SUCCESS  │
                              └───────────┘
```

### 4.3 状态-行为约束表

> 与 [PRD 状态机定义](./01_PRD.md#22-状态机定义-fsm) 保持一致

| 状态 | 允许的动作 | 禁止的动作 | 提示词约束 |
|------|-----------|-----------|-----------|
| **INIT** | 意图识别、任务拆解 | 调用工具、执行操作 | "仅解析用户意图，不做业务决策" |
| **PLANNING** | RAG 检索、制定执行路径 | 创建订单、支付 | "制定方案，禁止直接执行" |
| **AUDITING** | 合规检查、预算审核 | 修改方案 | "仅审核，不修改原方案" |
| **EXECUTING** | 调用 MCP 工具、GUI 动作 | 跳过验证 | "执行并记录轨迹，等待验证" |
| **VERIFYING** | 检查执行结果是否符合预期 | 重新执行 | "验证结果，记录偏差" |
| **RETRY** | 重新执行（重试次数<3） | 跳过审核 | "重试次数 +1，超过 3 次人工介入" |
| **REJECTED** | 返回审核失败原因 | 强制执行 | "说明驳回原因，建议修改方案" |
| **SUCCESS** | 归档日志、通知用户 | 修改结果 | "任务完成，输出最终结果" |

### 4.4 状态机与提示词的结合

```python
class StateConstrainedPrompt:
    """状态约束型提示词生成器"""
    
    STATE_PROMPTS = {
        "INIT": """
# 当前状态：初始化
# 允许动作：意图识别、任务拆解
# 禁止动作：调用任何工具、执行任何操作

你处于【初始化】状态，职责是：
1. 理解用户意图
2. 拆解为子任务
3. 输出任务计划（不执行）

输出格式：
{
  "next_state": "PLANNING",
  "intent": "...",
  "sub_tasks": [...]
}
""",
        "EXECUTING": """
# 当前状态：执行中
# 允许动作：调用 MCP 工具、GUI 操作
# 禁止动作：修改审核结果、跳过验证

你处于【执行】状态，职责是：
1. 按审核通过的方案执行
2. 调用指定工具
3. 记录执行轨迹

可用工具（仅限审核通过的工具）：
{allowed_tools}

输出格式：
{
  "next_state": "VERIFYING",
  "execution_result": {...},
  "trajectory": [...]
}
"""
    }
    
    def get_prompt(self, state: str, context: dict) -> str:
        """根据状态生成约束性提示词"""
        base_prompt = self.STATE_PROMPTS.get(state, "")
        # 注入上下文（如允许的工具列表）
        return base_prompt.format(**context)
```

### 4.5 状态转换验证

```python
class StateTransitionValidator:
    """状态转换验证器"""
    
    ALLOWED_TRANSITIONS = {
        "INIT": ["PLANNING"],
        "PLANNING": ["AUDITING"],
        "AUDITING": ["EXECUTING", "REJECTED"],
        "EXECUTING": ["VERIFYING", "RETRY"],
        "VERIFYING": ["SUCCESS", "RETRY"],
        "RETRY": ["EXECUTING"],
        "REJECTED": ["INIT"],  # 可重新发起
        "SUCCESS": ["INIT"]    # 任务完成，等待新任务
    }
    
    def validate(self, current: str, next_state: str) -> bool:
        """验证状态转换是否合法"""
        return next_state in self.ALLOWED_TRANSITIONS.get(current, [])
    
    def enforce(self, agent_output: dict) -> dict:
        """强制执行状态约束"""
        current = agent_output.get("current_state")
        next_state = agent_output.get("next_state")
        
        if not self.validate(current, next_state):
            # 非法转换，强制回退
            return {
                "error": f"非法状态转换: {current} -> {next_state}",
                "forced_state": current,  # 保持原状态
                "suggestion": f"允许的下一状态: {self.ALLOWED_TRANSITIONS.get(current, [])}"
            }
        
        return agent_output
```

### 4.6 状态机保障的企业级稳定性

| 保障维度 | 状态机作用 | 效果 |
|---------|-----------|------|
| **行为可预测** | 每个状态限定允许动作 | 消除越权操作风险 |
| **流程可审计** | 显式状态流转记录 | 满足合规要求 |
| **异常可追溯** | 状态回退路径清晰 | 快速定位问题 |
| **系统可恢复** | 状态持久化 | 崩溃后可恢复执行 |

---

## 5. 结构化输出保障

### 5.1 Pydantic Schema 定义

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class ActionType(str, Enum):
    TOOL_CALL = "tool_call"
    DECISION = "decision"
    CLARIFICATION = "clarification"

class ToolCallOutput(BaseModel):
    action: ActionType
    tool: Optional[str] = Field(None, description="工具名称")
    params: Optional[dict] = Field(None, description="工具参数")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    reasoning: str = Field(..., description="决策理由")

class AgentResponse(BaseModel):
    task_id: str
    agent: str
    output: ToolCallOutput
    metadata: dict
```

### 5.2 SGLang 结构化输出

```python
import sglang as sgl

@sgl.function
def agent_decision(s, system_prompt, user_input, tools):
    s += system_prompt
    s += "\n\n可用工具：\n"
    for tool in tools:
        s += f"- {tool['name']}: {tool['description']}\n"
    s += "\n用户输入：" + user_input + "\n"
    s += "输出（JSON格式）："
    s += sgl.gen(
        "response",
        max_tokens=500,
        temperature=0.1,
        regex=r'\{.*\}'  # 强制 JSON 格式
    )
    return s["response"]
```

---

## 6. Few-shot 示例设计

### 6.1 示例选择原则

| 原则 | 说明 |
|------|------|
| **典型性** | 选择最常见的业务场景 |
| **多样性** | 覆盖不同的工具调用类型 |
| **简洁性** | 示例不宜过长，避免上下文膨胀 |
| **正确性** | 示例必须是正确的调用方式 |

### 6.2 示例库

```python
FEW_SHOT_EXAMPLES = {
    "query_supplier": [
        {
            "user_input": "查询华为供应商的信息",
            "output": {
                "action": "tool_call",
                "tool": "query_supplier",
                "params": {"supplier_name": "华为"},
                "confidence": 0.95,
                "reasoning": "用户明确指定了供应商名称"
            }
        }
    ],
    "create_order": [
        {
            "user_input": "向供应商A订购100件商品B",
            "output": {
                "action": "tool_call",
                "tool": "create_order",
                "params": {
                    "supplier_id": "A",
                    "products": [{"product_id": "B", "quantity": 100}]
                },
                "confidence": 0.90,
                "reasoning": "明确的采购指令，参数完整"
            }
        }
    ]
}
```

---

## 7. 异常处理引导

### 7.1 异常场景定义

| 异常类型 | 引导指令 |
|---------|---------|
| 工具不可用 | "如果工具调用失败，返回错误信息并建议替代方案" |
| 参数缺失 | "如果必要参数缺失，返回 clarification 请求用户提供" |
| 权限不足 | "如果权限不足，返回 pending 状态并说明原因" |
| 数据冲突 | "如果发现数据冲突，返回冲突信息并请求人工确认" |

### 7.2 异常输出格式

```json
{
  "action": "clarification",
  "missing_params": ["supplier_id"],
  "question": "请问您要向哪个供应商下单？",
  "suggestions": ["供应商A", "供应商B"]
}
```

---

## 8. 提示词测试与评估

### 8.1 测试用例

| 用例 ID | 场景 | 输入 | 预期输出 | 实际输出 | 通过 |
|---------|------|------|---------|---------|------|
| TC-001 | 正常采购 | "采购100件商品A" | tool_call: create_order | ... | ✓ |
| TC-002 | 参数缺失 | "下单商品A" | clarification | ... | ✓ |
| TC-003 | 工具选择 | "查询库存" | tool_call: check_inventory | ... | ✓ |

### 8.2 评估指标

| 指标 | 定义 | 目标值 |
|------|------|--------|
| 格式正确率 | 输出符合 JSON Schema | > 99% |
| 工具选择准确率 | 正确选择工具 | > 95% |
| 参数提取准确率 | 参数正确填充 | > 98% |
| 异常处理正确率 | 异常场景正确处理 | > 90% |

