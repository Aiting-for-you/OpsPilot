# 详细设计：数据飞轮与 Agent 持续进化机制

## 1. 核心理念
Agent 在上线第一天不可能是完美的。本模块设计了一套闭环系统，让 Omni-Agent 能够从失败中学习。

## 2. 数据采集流水线 (Data Pipeline)
- **轨迹记录**：利用 AgentScope 的日志系统，记录每一次 `Thought -> Action -> Observation`。
- **负样本挖掘**：自动筛选出执行失败（如 API 报错、被财务 Agent 驳回后无法修正）的案例。

## 3. 自动化微调闭环 (Fine-tuning Loop)
1. **标注**：人工或更高级模型（如 GPT-4o）对失败轨迹进行修正，生成“正确轨迹”。
2. **训练**：将修正后的数据喂给 **LLaMA-Factory**，进行增量 QLoRA 微调。
3. **验证**：在 `evaluation_framework` 中进行回归测试。
4. **部署**：通过 **SGLang** 动态加载新的 Adapter，实现无缝升级。

## 4. 落地价值
- **降低维护成本**：系统具备自我修复能力，减少了人工修改 Prompt 的频率。
- **业务资产沉淀**：微调后的模型包含了公司特有的业务逻辑，形成了极高的技术壁垒。

## 5. 数据脱敏与隐私保护 (Data Masking & Privacy)

### 5.1 敏感信息自动识别
```python
class SensitiveDataDetector:
    """敏感数据检测器"""
    
    PATTERNS = {
        "email": (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL]"),
        "phone_cn": (r"1[3-9]\d{9}", "[PHONE]"),
        "phone_intl": (r"\+\d{1,3}[\s-]?\d{7,15}", "[PHONE]"),
        "id_card_cn": (r"\d{17}[\dXx]", "[ID_CARD]"),
        "passport": (r"[A-Z]\d{8}", "[PASSPORT]"),
        "bank_card": (r"\d{16,19}", "[BANK_CARD]"),
        "ip_address": (r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", "[IP]"),
        "credit_card": (r"\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}", "[CREDIT_CARD]"),
    }
    
    def detect_and_mask(self, text: str) -> Tuple[str, List[SensitiveInfo]]:
        """检测并脱敏敏感信息"""
        masked_text = text
        detected = []
        
        for info_type, (pattern, mask) in self.PATTERNS.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                detected.append(SensitiveInfo(
                    type=info_type,
                    original=match.group(),
                    position=match.span()
                ))
                masked_text = masked_text.replace(match.group(), mask)
        
        return masked_text, detected
```

### 5.2 数据回流脱敏流程
```
[原始日志采集] --> [敏感信息检测] --> [敏感信息?]
                                        │
                                ┌───────┴───────┐
                                ▼               ▼
                            [是]            [否]
                                │               │
                                ▼               ▼
                        [脱敏处理]         [直接存储]
                                │
                        ┌───────┴───────┐
                        ▼               ▼
                   [保留映射表]    [删除原文]
                   (加密存储)      (完全脱敏)
                        │
                        ▼
                [审计日志记录]
```

### 5.3 脱敏策略配置
| 数据类型 | 脱敏方式 | 可逆性 | 适用场景 |
| :--- | :--- | :--- | :--- |
| 用户姓名 | 映射替换 (张三 → USER_001) | 可逆 | 需要关联分析 |
| 手机号 | 中间四位遮蔽 (138****5678) | 不可逆 | 日志记录 |
| 身份证 | 仅保留前 3 后 1 位 | 不可逆 | 合规存档 |
| IP 地址 | 最后一段置 0 (192.168.1.0) | 不可逆 | 问题定位 |
| 银行卡 | 仅保留后 4 位 (****5678) | 不可逆 | 交易记录 |

### 5.4 合规审计要求
- **审计日志**：所有数据访问、脱敏操作记录完整日志
- **访问控制**：敏感数据访问需审批，记录访问人、时间、目的
- **数据保留**：脱敏数据保留 7 年，原始敏感数据 24 小时内删除
- **定期审查**：每季度审查脱敏规则有效性，更新敏感模式库

## 6. 数据质量监控 (Data Quality Monitoring)

### 6.1 质量指标体系
| 维度 | 指标 | 计算方式 | 目标值 |
| :--- | :--- | :--- | :--- |
| **完整性** | 字段填充率 | 非空字段数 / 总字段数 | > 95% |
| **准确性** | 数据正确率 | 正确记录数 / 总记录数 | > 98% |
| **时效性** | 数据新鲜度 | 当前时间 - 数据产生时间 | < 24h |
| **一致性** | 格式合规率 | 符合格式的记录数 / 总记录数 | > 99% |
| **唯一性** | 重复率 | 1 - (唯一记录数 / 总记录数) | < 1% |

### 6.2 自动质量检测
```python
class DataQualityMonitor:
    """数据质量监控器"""
    
    def check_trajectory(self, trajectory: Trajectory) -> QualityReport:
        """检查执行轨迹质量"""
        issues = []
        
        # 1. 完整性检查
        if not trajectory.user_input:
            issues.append(QualityIssue("缺少用户输入", severity="critical"))
        if not trajectory.final_result:
            issues.append(QualityIssue("缺少执行结果", severity="high"))
        
        # 2. 准确性检查
        if trajectory.tool_calls:
            for call in trajectory.tool_calls:
                if call.status == "success" and not call.response:
                    issues.append(QualityIssue(f"工具 {call.name} 无响应数据", severity="medium"))
        
        # 3. 一致性检查
        if trajectory.token_count > 100000:
            issues.append(QualityIssue("Token 数量异常，可能存在循环", severity="high"))
        
        # 4. 时效性检查
        if trajectory.duration > 300:  # 5 分钟
            issues.append(QualityIssue("执行时间过长", severity="low"))
        
        return QualityReport(
            trajectory_id=trajectory.id,
            quality_score=self._calculate_score(issues),
            issues=issues,
            recommendation=self._get_recommendation(issues)
        )
```

### 6.3 低质量数据清洗策略
| 问题类型 | 检测条件 | 处理方式 |
| :--- | :--- | :--- |
| 空值过多 | > 30% 字段为空 | 标记为低质量，不参与训练 |
| 格式错误 | 不符合 JSON Schema | 尝试修复，失败则丢弃 |
| 异常长度 | Token 数 < 50 或 > 100k | 人工审核或自动过滤 |
| 重复数据 | 相似度 > 95% | 保留最新版本 |
| 循环执行 | 相同动作重复 > 5 次 | 标记为异常案例 |

### 6.4 质量对微调效果的影响
```
数据质量 → 微调效果映射表

┌─────────────┬───────────────────────────────────────────────┐
│ 数据质量     │ 微调后模型表现                                  │
├─────────────┼───────────────────────────────────────────────┤
│ 高 (>90分)  │ 工具调用准确率 +15%, 任务成功率 +8%             │
│ 中 (70-90)  │ 工具调用准确率 +8%, 任务成功率 +4%              │
│ 低 (<70)    │ 可能引入噪声, 效果不确定或下降                   │
└─────────────┴───────────────────────────────────────────────┘
```

## 7. 数据价值评估 (Data Value Assessment)

### 7.1 数据价值量化模型
```python
def calculate_data_value(sample: TrainingSample) -> float:
    """计算单条数据的价值分数"""
    # 1. 信息增益：与现有知识库的差异度
    info_gain = calculate_novelty(sample, existing_knowledge_base)
    
    # 2. 任务相关性：与核心业务场景的关联度
    task_relevance = match_business_scenario(sample.task_type)
    
    # 3. 执行质量：成功/失败案例的区分度
    quality = 1.0 if sample.success else 0.5
    
    # 4. 频率价值：常见场景 vs 边缘场景
    frequency_value = get_scenario_frequency(sample.scenario)
    
    # 综合价值
    return (
        0.3 * info_gain +
        0.3 * task_relevance +
        0.2 * quality +
        0.2 * frequency_value
    )
```

### 7.2 高价值数据特征
| 特征 | 描述 | 价值权重 |
| :--- | :--- | :--- |
| **边界案例** | 接近决策边界，难以判断的案例 | 0.9 |
| **失败转成功** | 原本失败后经修正成功的案例 | 0.85 |
| **高频场景** | 业务中出现频率高的场景 | 0.8 |
| **新场景** | 知识库中尚未覆盖的场景 | 0.75 |
| **人工标注** | 经过人工验证和标注的数据 | 0.9 |

### 7.3 数据价值看板
```
┌─────────────────────────────────────────────────────────────────┐
│                     数据价值评估看板                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  本周新增数据: 1,234 条                                          │
│  高价值数据: 456 条 (37%)                                        │
│  低价值数据: 123 条 (10%)                                        │
│                                                                 │
│  价值分布:                                                       │
│  ████████████████████░░░░░░░░░░ 高价值 (0.8-1.0)               │
│  ████████████████████████████░░ 中价值 (0.5-0.8)               │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 低价值 (0-0.5)                 │
│                                                                 │
│  对模型改进预估:                                                 │
│  • 工具调用准确率: +2.3%                                        │
│  • 任务成功率: +1.5%                                            │
│  • 新场景覆盖: +5 个                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

