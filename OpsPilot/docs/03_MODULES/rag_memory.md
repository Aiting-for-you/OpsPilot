# 详细设计：多路召回 RAG 与混合记忆系统

## 1. 增强型 RAG 架构
跨境电商政策更新频繁，传统的简单向量检索难以满足需求。

### 1.1 检索策略
- **多路召回**：结合 ChromaDB 的向量检索与 Elasticsearch 的全文检索。
- **重排序 (Re-ranking)**：使用 BGE-Reranker 对初始结果进行精排，确保前 3 条结果的准确率。
- **文档切片优化**：针对法律条文，采用“父子文档”切片法，保留上下文语义。

## 2. 混合记忆系统 (Hybrid Memory)

### 2.1 短期会话记忆 (Short-term)
- 存储在 Redis 中，记录当前 SOP 的执行轨迹。
- 采用 **Sliding Window** 机制，防止 Token 溢出。

### 2.2 长期经验记忆 (Long-term)
- **经验沉淀**：将成功的业务闭环案例（Case）转化为向量存储。
- **经验检索**：当遇到类似任务时，Agent 优先检索“过去是怎么成功的”，实现经验迁移。

### 2.3 落地约束
- **记忆清理**：定期清理过期的会话数据，保持系统轻量化。
- **一致性**：确保多 Agent 之间共享必要的全局状态记忆。

## 3. 记忆衰减与更新算法 (Memory Decay & Update)

### 3.1 新鲜度权重 (Recency Bias)
当一年前的排查方案与现在的 SOP 冲突时，系统按以下规则处理：

```python
def calculate_memory_weight(memory: Memory) -> float:
    """计算记忆权重：时间衰减 + 使用频率 + 成功率"""
    # 时间衰减因子（半衰期 30 天）
    age_days = (datetime.now() - memory.created_at).days
    recency_weight = math.exp(-age_days / 30)
    
    # 使用频率因子
    usage_weight = min(1.0, memory.usage_count / 100)
    
    # 成功率因子
    success_weight = memory.success_rate
    
    # 综合权重
    return 0.5 * recency_weight + 0.3 * usage_weight + 0.2 * success_weight
```

### 3.2 记忆冲突消解策略
| 冲突类型 | 检测条件 | 解决策略 |
| :--- | :--- | :--- |
| **版本冲突** | 新旧 SOP 规则不一致 | 采用最新版本，旧版本标记为 `deprecated` |
| **场景冲突** | 相同场景不同解决方案 | 根据 `recency_weight` 选择高权重方案 |
| **优先级冲突** | 多条记忆适用 | 合规类记忆优先级 > 效率类记忆 |

### 3.3 记忆更新流程
```
[新案例发生] --> [相似度匹配] --> [找到旧记忆?]
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
               [是：合并更新]          [否：新建记忆]
                    │                       │
                    ▼                       ▼
              [版本号+1]              [初始权重=1.0]
              [更新时间戳]
              [重新计算权重]
```

## 4. 记忆一致性保障 (Memory Consistency)

### 4.1 多 Agent 共享记忆同步
```python
class SharedMemoryManager:
    def __init__(self):
        self.local_cache = {}  # 本地缓存
        self.central_store = RedisCluster()  # 中心存储
        self.version_vector = {}  # 版本向量
    
    async def read(self, key: str, agent_id: str) -> Memory:
        """读取记忆：优先本地缓存，异步同步中心"""
        if key in self.local_cache:
            return self.local_cache[key]
        
        memory = await self.central_store.get(key)
        self.local_cache[key] = memory
        return memory
    
    async def write(self, key: str, memory: Memory, agent_id: str):
        """写入记忆：CAS 保证原子性"""
        memory.version = self.version_vector.get(key, 0) + 1
        memory.last_writer = agent_id
        
        # Compare-And-Swap 操作
        success = await self.central_store.cas(
            key, 
            expected_version=self.version_vector.get(key, 0),
            new_value=memory
        )
        
        if success:
            self.version_vector[key] = memory.version
            self.local_cache[key] = memory
        else:
            raise ConflictError("Memory conflict detected, retry needed")
```

### 4.2 分布式场景一致性保证
| 级别 | 保证内容 | 实现方式 |
| :--- | :--- | :--- |
| **强一致性** | 关键决策记忆 | 分布式锁 + 同步写入 |
| **最终一致性** | 普通会话记忆 | 异步复制 + 冲突检测 |
| **弱一致性** | 统计类记忆 | 定期同步，允许短暂不一致 |

### 4.3 冲突检测与恢复
```
[写入冲突检测] --> [版本不匹配?] 
                      │
              ┌───────┴───────┐
              ▼               ▼
          [是：合并策略]   [否：正常写入]
              │
              ▼
      [保留双方变更]
      [标记为待人工确认]
      [通知相关 Agent]
```

## 5. 隐私保护设计 (Privacy Protection)

### 5.1 敏感信息自动识别
```python
SENSITIVE_PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone": r"1[3-9]\d{9}",
    "id_card": r"\d{17}[\dXx]",
    "bank_account": r"\d{16,19}",
    "ip_address": r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
}

def auto_mask(text: str) -> str:
    """自动脱敏敏感信息"""
    for pattern_name, pattern in SENSITIVE_PATTERNS.items():
        text = re.sub(pattern, f"[{pattern_name}_MASKED]", text)
    return text
```

### 5.2 记忆访问权限控制
| 角色 | 可访问记忆类型 | 脱敏要求 |
| :--- | :--- | :--- |
| **采购 Agent** | 采购案例、供应商信息 | 客户联系方式脱敏 |
| **财务 Agent** | 预算记录、审批历史 | 金额明细完整保留 |
| **合规 Agent** | 政策解读、合规案例 | 无脱敏要求 |
| **系统管理员** | 全部 | 审计日志记录所有访问 |

### 5.3 记忆生命周期管理
```
[记忆创建] --> [敏感检测] --> [脱敏处理] --> [加密存储]
                                      │
                                      ▼
                              [访问控制] --> [使用记录]
                                      │
                                      ▼
[过期检测] <-- [定期扫描] <-- [权限校验]
     │
     ▼
[归档/删除] --> [审计日志]

