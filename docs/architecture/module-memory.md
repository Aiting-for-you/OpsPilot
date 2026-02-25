# Memory 模块架构

## 模块概述

Memory 模块是 OpsPilot 的记忆与知识管理核心，负责 **短期记忆**、**长期记忆**、**向量知识库**、**冲突检测**、**记忆 consolidation** 等功能。模块采用分层存储架构，支持 Redis 短期记忆、PostgreSQL 长期存储、Chroma 向量检索。

## 1. 组件架构

```mermaid
graph TB
    subgraph MEMORY_BASE["Base（基类层）"]
        direction LR
        BASE_MEM[MemoryBase<br/>记忆基类<br/>定义接口]
        STORE[MemoryStore<br/>存储抽象<br/>CRUD 接口]
        SERIAL[Serializer<br/>序列化<br/>JSON/MsgPack]
    end

    subgraph SHORT_TERM["ShortTerm（短期记忆）"]
        direction LR
        SHORT[ShortTermMemory<br/>短期记忆<br/>Redis]
        CONV[ConversationBuffer<br/>会话缓冲<br/>最近 N 条]
        ENTITY[EntityBuffer<br/>实体缓冲<br/>当前任务实体]
        CTX[ContextWindow<br/>上下文窗口<br/>token 限制]
    end

    subgraph LONG_TERM["LongTerm（长期记忆）"]
        direction LR
        LONG[LongTermMemory<br/>长期记忆<br/>PostgreSQL]
        EPISODE[EpisodeStore<br/>经验存储<br/>结构化记录]
        FACT[FactStore<br/>事实存储<br/>实体关系]
        SUMM[Summarizer<br/>摘要生成<br/>LLM 压缩]
    end

    subgraph KNOWLEDGE["Knowledge（知识库）"]
        direction LR
        KNOW[KnowledgeBase<br/>知识库<br/>向量存储]
        VECTOR[VectorStore<br/>向量存储<br/>Chroma/Milvus]
        EMBED[EmbeddingService<br/>嵌入服务<br/>OpenAI/本地]
        INDEX[Indexer<br/>索引管理<br/>增量构建]
        RETRIEVE[Retriever<br/>检索器<br/>混合检索]
    end

    subgraph CONSOL["Consolidation（记忆整合）"]
        direction LR
        CONSOL_MGR[ConsolidationManager<br/>整合管理器<br/>调度]
        EXTRACT[Extractor<br/>信息提取<br/>实体关系]
        MERGE[Merger<br/>记忆合并<br/>冲突解决]
        PRUNE[Pruner<br/>记忆修剪<br/>过期清理]
    end

    subgraph CONFLICT["Conflict（冲突检测）"]
        direction LR
        DETECT[ConflictDetector<br/>冲突检测<br/>版本比较]
        RESOLVE[Resolver<br/>冲突解决<br/>策略选择]
        VERSION[VersionManager<br/>版本管理<br/>历史追溯]
    end

    subgraph WEIGHT["Weight（权重计算）"]
        direction LR
        CALC[WeightCalculator<br/>权重计算<br/>多维度]
        DECAY[DecayEngine<br/>衰减引擎<br/>时间衰减]
        BOOST[BoostEngine<br/>增强引擎<br/>重要性提升]
    end

    %% 连接
    BASE_MEM --> STORE
    BASE_MEM --> SERIAL
    
    SHORT --> CONV
    SHORT --> ENTITY
    SHORT --> CTX
    
    LONG --> EPISODE
    LONG --> FACT
    LONG --> SUMM
    
    KNOW --> VECTOR
    KNOW --> EMBED
    KNOW --> INDEX
    KNOW --> RETRIEVE
    
    CONSOL_MGR --> EXTRACT
    CONSOL_MGR --> MERGE
    CONSOL_MGR --> PRUNE
    
    DETECT --> RESOLVE
    DETECT --> VERSION
    
    CALC --> DECAY
    CALC --> BOOST
    
    SHORT -.->|下沉| LONG
    LONG -.->|整合| KNOW
    
    classDef base fill:#e3f2fd,stroke:#1976d2,color:#0d47a1
    classDef short fill:#fff3e0,stroke:#f57c00,color:#e65100
    classDef long fill:#e8f5e9,stroke:#388e3c,color:#1b5e20
    classDef knowledge fill:#e0f7fa,stroke:#0097a7,color:#006064
    classDef consol fill:#f3e5f5,stroke:#7b1fa2,color:#4a148c
    classDef conflict fill:#fce4ec,stroke:#c2185b,color:#880e4f
    classDef weight fill:#fff8e1,stroke:#ffa000,color:#ff6f00

    class BASE_MEM,STORE,SERIAL base
    classDef conflict fill:#fce4ec,stroke:#c2185b,color:#880e4f
    classDef weight fill:#fff8e1,stroke:#ffa000,color:#ff6f00

    class BASE,STORE,SERIAL base
    class SHORT,CONV,ENTITY,CTX short
    class LONG,EPISODE,FACT,SUMM long
    class KNOW,VECTOR,EMBED,INDEX,RETRIEVE knowledge
    class CONSOL_MGR,EXTRACT,MERGE,PRUNE consol
    class DETECT,RESOLVE,VERSION conflict
    class CALC,DECAY,BOOST weight
```

## 2. 记忆流转时序图

```mermaid
sequenceDiagram
    participant AGENT as Agent
    participant SHORT as ShortTermMemory
    participant LONG as LongTermMemory
    participant KNOW as KnowledgeBase
    participant CONSOL as ConsolidationManager
    participant CONFLICT as ConflictDetector
    participant LLM as LLM 服务

    AGENT->>SHORT: add_interaction(message)
    SHORT->>SHORT: buffer_message()
    SHORT->>SHORT: update_entity_buffer()
    
    rect rgb(255, 245, 230)
        note right of CONSOL: 定期整合触发
        CONSOL->>SHORT: extract_episodes()
        CONSOL->>LLM: summarize_old_messages()
        LLM-->>CONSOL: summary
        
        CONSOL->>CONFLICT: check_conflicts(episodes)
        
        alt 发现冲突
            CONFLICT->>CONFLICT: resolve_conflict()
        end
        
        CONSOL->>LONG: store_episodes(episodes)
        CONSOL->>KNOW: index_new_knowledge(episodes)
    end
    
    AGENT->>SHORT: retrieve_recent(k)
    SHORT-->>AGENT: recent_context
    
    AGENT->>KNOW: query(query_text, k)
    KNOW->>KNOW: hybrid_retrieve()
    KNOW-->>AGENT: relevant_knowledge
```

## 3. 文件清单

| 文件 | 类/函数 | 职责 |
|------|---------|------|
| `base.py` | `MemoryBase` | 记忆抽象基类 |
| `base.py` | `MemoryStore` | 存储接口定义 |
| `short_term.py` | `ShortTermMemory` | 短期记忆实现 |
| `short_term.py` | `ConversationBuffer` | 会话缓冲 |
| `long_term.py` | `LongTermMemory` | 长期记忆实现 |
| `long_term.py` | `EpisodeStore` | 经验存储 |
| `long_term.py` | `FactStore` | 事实存储 |
| `knowledge.py` | `KnowledgeBase` | 知识库管理 |
| `knowledge.py` | `VectorStore` | 向量存储接口 |
| `knowledge.py` | `Retriever` | 检索器 |
| `vectorstore.py` | `ChromaStore` | Chroma 向量存储 |
| `vectorstore.py` | `MilvusStore` | Milvus 向量存储 |
| `redis_store.py` | `RedisStore` | Redis 存储适配 |
| `consolidation.py` | `ConsolidationManager` | 整合管理器 |
| `consolidation.py` | `MemoryExtractor` | 信息提取器 |
| `conflict.py` | `ConflictDetector` | 冲突检测器 |
| `conflict.py` | `VersionManager` | 版本管理器 |
| `weight.py` | `WeightCalculator` | 权重计算器 |
| `weight.py` | `DecayEngine` | 衰减引擎 |

## 4. 记忆层次结构

### 4.1 分层架构

```mermaid
graph TB
    A[用户输入] --> B[短期记忆<br/>Redis]
    B --> C{是否需要<br/>整合?}
    C -->|是| D[长期记忆<br/>PostgreSQL]
    C -->|否| E[直接返回]
    D --> F{是否需要<br/>检索?}
    F -->|是| G[知识库<br/>Chroma]
    F -->|否| H[直接返回]
    G --> I[混合检索结果]
    
    subgraph STORAGE[存储层]
        B
        D
        G
    end
```

### 4.2 存储对比

| 类型 | 存储 | 容量 | 持久性 | 延迟 |
|------|------|------|--------|------|
| 短期 | Redis | ~10000 条 | ❌ | <1ms |
| 长期 | PostgreSQL | 无限制 | ✅ | <10ms |
| 向量 | Chroma | 百万级 | ✅ | <50ms |

## 5. 短期记忆设计

### 5.1 缓冲结构

```python
class ConversationBuffer:
    max_length: int = 100  # 最大消息数
    window_type: str = "sliding"  # 滑动窗口
    
    def add_message(self, message: Message):
        """添加消息到缓冲"""
        
    def get_context(self, k: int) -> List[Message]:
        """获取最近 k 条消息"""
        
    def get_entities(self) -> Set[Entity]:
        """提取当前实体"""
```

### 5.2 上下文窗口管理

```mermaid
flowchart LR
    A[输入] --> B[Token 计数]
    B --> C{超限?}
    C -->|是| D[压缩旧消息]
    C -->|否| E[直接使用]
    D --> F[摘要替换]
    F --> E
```

## 6. 长期记忆设计

### 6.1 经验 Episode

```python
class Episode:
    id: str
    task_type: str
    start_time: datetime
    end_time: datetime
    steps: List[Step]
    result: Result
    summary: str  # LLM 生成的摘要
    importance: float  # 0-1 重要性
    embedding: List[float]  # 向量表示
```

### 6.2 事实 Fact

```python
class Fact:
    id: str
    entity: str
    relation: str
    value: Any
    confidence: float
    sources: List[str]
    timestamp: datetime
```

## 7. 知识库设计

### 7.1 向量检索流程

```mermaid
sequenceDiagram
    participant USER as 用户查询
    participant RETRIEVE as Retriever
    participant VECTOR as VectorStore
    participant KEYWORD as KeywordIndex
    participant RERANK as ReRanker
    participant LLM as LLM

    USER->>RETRIEVE: search(query, k)
    RETRIEVE->>VECTOR: vector_search(embedding)
    VECTOR-->>RETRIEVE: top_k_vectors
    
    RETRIEVE->>KEYWORD: keyword_search(query)
    KEYWORD-->>RETRIEVE: keyword_results
    
    RETRIEVE->>RETRIEVE: merge_results()
    RETRIEVE->>RERANK: rerank(merged_results)
    RERANK-->>RETRIEVE: reranked_results
    
    RETRIEVE-->>USER: final_results(k)
```

### 7.2 混合检索策略

| 策略 | 说明 | 权重 |
|------|------|------|
| 向量检索 | 语义相似度 | 0.6 |
| 关键词检索 | BM25 | 0.3 |
| Rerank | LLM 重排 | 0.1 |

### 7.3 支持的向量存储

| 存储 | 类型 | 特点 |
|------|------|------|
| Chroma | 本地 | 轻量易用 |
| Milvus | 分布式 | 亿级向量 |
| Pinecone | 云服务 | 托管运维 |
| Qdrant | 本地/云 | 高性能 |

## 8. 记忆整合机制

### 8.1 整合触发条件

| 条件 | 说明 |
|------|------|
| 定时触发 | 每小时/每天 |
| 数量触发 | 缓冲超过阈值 |
| 任务结束 | Agent 完成任务 |
| 手动触发 | API 调用 |

### 8.2 整合流程

```mermaid
flowchart TB
    A[触发整合] --> B[提取新实体]
    B --> C[与已有实体匹配]
    C --> D{发现冲突?}
    D -->|是| E[冲突解决策略]
    D -->|否| F[直接合并]
    E --> F
    F --> G[更新长期记忆]
    G --> H[增量索引知识库]
    H --> I[清理过期短期记忆]
```

## 9. 冲突检测与解决

### 9.1 冲突类型

| 类型 | 示例 | 处理策略 |
|------|------|---------|
| 事实冲突 | A 是 B 的父亲 vs A 是 B 的母亲 | 时间戳优先 |
| 数值冲突 | 库存 100 vs 库存 50 | 取最新 |
| 关系冲突 | 公司 A 收购 B vs 公司 B 收购 A | 置信度优先 |

### 9.2 解决策略

```python
class ConflictResolution:
    STRATEGY_TIME = "timestamp"     # 时间戳优先
    STRATEGY_CONFIDENCE = "confidence"  # 置信度优先
    STRATEGY_VOTE = "vote"          # 多数投票
    STRATEGY_MANUAL = "manual"      # 人工确认
```

## 10. 权重与衰减

### 10.1 权重计算因素

| 因素 | 权重 | 说明 |
|------|------|------|
| 时间衰减 | -0.1/天 | 随时间递减 |
| 重要性 | +0.3 | 任务关键程度 |
| 引用次数 | +0.2 | 被引用频率 |
| 验证通过 | +0.2 | 结果验证通过 |
| 用户反馈 | +0.3 | 人工标记重要 |

### 10.2 衰减曲线

```python
# 指数衰减
weight = initial_weight * exp(-decay_rate * days_since_access)

# 自适应衰减
decay_rate = base_rate * importance_multiplier
```