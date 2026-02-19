# Memory 模块架构

## 组件架构图

```mermaid
graph TB
    %% ==================== 第一行：记忆管理器 ====================
    subgraph L1[MemoryManager记忆管理器]
        direction LR
        MM[MemoryManager<br/>记忆管理器<br/>统一记忆接口]
        MM_SHORT[ShortTermMemory<br/>短期记忆<br/>工作记忆]
        MM_LONG[LongTermMemory<br/>长期记忆<br/>持久化存储]
        MM_WORK[WorkingMemory<br/>工作记忆<br/>当前任务]
    end

    %% ==================== 第二行：向量化与索引 ====================
    subgraph L2A[Embedding向量化]
        direction LR
        EMBED[EmbeddingService<br/>嵌入服务]
        EMBED_OPEN[OpenAIEmbedding<br/>OpenAI嵌入]
        EMBED_LOCAL[LocalEmbedding<br/>本地嵌入]
        EMBED_CACHE[EmbeddingCache<br/>嵌入缓存]
    end

    subgraph L2B[Indexer索引构建]
        direction LR
        IDX[Indexer<br/>索引构建器]
        IDX_CHROMA[ChromaIndexer<br/>Chroma索引]
        IDX_FAISS[FAISSIndexer<br/>FAISS索引]
        IDX_META[MetadataIndexer<br/>元数据索引]
    end

    %% ==================== 第三行：检索器 ====================
    subgraph L3[Retriever检索器]
        direction LR
        RET[Retriever<br/>检索器基类]
        RET_VEC[VectorRetriever<br/>向量检索器]
        RET_HYB[HybridRetriever<br/>混合检索器]
        RET_CTX[ContextRetriever<br/>上下文检索]
    end

    %% ==================== 第四行：压缩器 ====================
    subgraph L4[Compressor压缩器]
        direction LR
        COMP[Compressor<br/>压缩器基类]
        COMP_LLM[LLMCompressor<br/>LLM压缩器]
        COMP_RANK[RankCompressor<br/>排序压缩器]
        COMP_SEM[SemanticCompressor<br/>语义压缩器]
    end

    %% ==================== 第五行：存储层 ====================
    subgraph L5[Storage存储层]
        direction LR
        STORE[MemoryStorage<br/>存储抽象层]
        STORE_PG[PostgreSQLStore<br/>PG存储]
        STORE_REDIS[RedisStore<br/>Redis存储]
        STORE_CHROMA[ChromaStore<br/>Chroma存储]
    end

    %% ==================== 第六行：上下文与RAG ====================
    subgraph L6A[Context上下文管理]
        direction LR
        CTX[ContextManager<br/>上下文管理器]
        CTX_WIN[WindowManager<br/>窗口管理器]
        CTX_TOK[TokenCounter<br/>Token计数]
        CTX_PRIO[PriorityQueue<br/>优先队列]
    end

    subgraph L6B[RAGPipeline检索增强]
        direction LR
        RAG[RAGPipeline<br/>RAG流水线]
        RAG_QUERY[QueryRewriter<br/>查询重写]
        RAG_DOC[DocProcessor<br/>文档处理]
        RAG_PROMPT[PromptBuilder<br/>提示构建]
    end

    %% ==================== 层间连接 ====================
    MM --> MM_SHORT
    MM --> MM_LONG
    MM --> MM_WORK

    EMBED --> EMBED_OPEN
    EMBED --> EMBED_LOCAL
    EMBED --> EMBED_CACHE

    IDX --> IDX_CHROMA
    IDX --> IDX_FAISS
    IDX --> IDX_META

    RET --> RET_VEC
    RET --> RET_HYB
    RET --> RET_CTX

    COMP --> COMP_LLM
    COMP --> COMP_RANK
    COMP --> COMP_SEM

    STORE --> STORE_PG
    STORE --> STORE_REDIS
    STORE --> STORE_CHROMA

    CTX --> CTX_WIN
    CTX --> CTX_TOK
    CTX --> CTX_PRIO

    RAG --> RAG_QUERY
    RAG --> RAG_DOC
    RAG --> RAG_PROMPT

    MM --> STORE
    MM_SHORT --> STORE_REDIS
    MM_LONG --> STORE_CHROMA
    MM_LONG --> STORE_PG
    RET_VEC --> EMBED
    RET_VEC --> IDX
    RET_HYB --> RET_VEC
    COMP_RANK --> RET
    CTX --> COMP
    RAG_QUERY --> RET
    RAG_DOC --> IDX
    RAG_PROMPT --> CTX

    %% ==================== 样式 ====================
    classDef primary fill:#083B75,color:#fff
    classDef embedding fill:#1a5f7a,color:#fff
    classDef index fill:#2e7d32,color:#fff
    classDef retrieval fill:#1565c0,color:#fff
    classDef compress fill:#6a1b9a,color:#fff
    classDef storage fill:#c62828,color:#fff
    classDef context fill:#f57c00,color:#fff
    classDef rag fill:#00838f,color:#fff

    class MM,MM_SHORT,MM_LONG,MM_WORK primary
    class EMBED,EMBED_OPEN,EMBED_LOCAL,EMBED_CACHE embedding
    class IDX,IDX_CHROMA,IDX_FAISS,IDX_META index
    class RET,RET_VEC,RET_HYB,RET_CTX retrieval
    class COMP,COMP_LLM,COMP_RANK,COMP_SEM compress
    class STORE,STORE_PG,STORE_REDIS,STORE_CHROMA storage
    class CTX,CTX_WIN,CTX_TOK,CTX_PRIO context
    class RAG,RAG_QUERY,RAG_DOC,RAG_PROMPT rag
```

## RAG检索时序图

```mermaid
sequenceDiagram
    participant AGENT as Agent
    participant RAG as RAGPipeline
    participant QUERY as QueryRewriter
    participant RET as Retriever
    participant EMBED as EmbeddingService
    participant IDX as Indexer
    participant COMP as Compressor
    participant CTX as ContextManager
    participant STORE as Storage

    AGENT->>RAG: 1. retrieve(query, k=5)
    RAG->>QUERY: 2. rewrite(query)
    QUERY->>QUERY: 3. expand_synonyms()
    QUERY->>QUERY: 4. add_filters()
    QUERY-->>RAG: 5. enhanced_query

    RAG->>EMBED: 6. embed(enhanced_query)
    EMBED->>EMBED: 7. check_cache()
    alt 缓存命中
        EMBED-->>RAG: 8. cached_vector
    else 缓存未命中
        EMBED->>EMBED: 9. compute_embedding()
        EMBED->>EMBED: 10. update_cache()
        EMBED-->>RAG: 11. query_vector
    end

    RAG->>RET: 12. search(query_vector, k=10)
    RET->>IDX: 13. ann_search(vector)
    IDX-->>RET: 14. candidates
    
    RET->>IDX: 15. filter_by_metadata()
    IDX-->>RET: 16. filtered_results
    
    RET->>RET: 17. rerank(results)
    RET-->>RAG: 18. top_k_documents

    RAG->>COMP: 19. compress(documents)
    COMP->>COMP: 20. rank_by_relevance()
    COMP->>COMP: 21. deduplicate()
    COMP->>COMP: 22. extract_key_info()
    COMP-->>RAG: 23. compressed_context

    RAG->>CTX: 24. build_context(compressed)
    CTX->>CTX: 25. count_tokens()
    CTX->>CTX: 26. adjust_window()
    CTX-->>RAG: 27. final_context

    RAG-->>AGENT: 28. retrieval_result
```

## 文件清单

| 文件 | 类/函数 | 职责 |
|------|--------|------|
| memory_manager.py | MemoryManager | 记忆管理器主类 |
| memory_manager.py | ShortTermMemory | 短期记忆管理 |
| memory_manager.py | LongTermMemory | 长期记忆管理 |
| memory_manager.py | WorkingMemory | 工作记忆管理 |
| embeddings.py | EmbeddingService | 嵌入服务基类 |
| embeddings.py | OpenAIEmbedding | OpenAI嵌入实现 |
| embeddings.py | LocalEmbedding | 本地嵌入实现 |
| embeddings.py | EmbeddingCache | 嵌入结果缓存 |
| indexer.py | Indexer | 索引构建器基类 |
| indexer.py | ChromaIndexer | ChromaDB索引器 |
| indexer.py | FAISSIndexer | FAISS索引器 |
| retriever.py | Retriever | 检索器基类 |
| retriever.py | VectorRetriever | 向量检索器 |
| retriever.py | HybridRetriever | 混合检索器 |
| retriever.py | ContextRetriever | 上下文检索器 |
| compressor.py | Compressor | 压缩器基类 |
| compressor.py | LLMCompressor | LLM摘要压缩 |
| compressor.py | RankCompressor | 排序压缩 |
| compressor.py | SemanticCompressor | 语义去重压缩 |
| context_manager.py | ContextManager | 上下文管理器 |
| context_manager.py | WindowManager | 窗口管理器 |
| context_manager.py | TokenCounter | Token计数器 |

## 记忆类型

| 类型 | 存储 | 生命周期 | 用途 |
|------|------|---------|------|
| 短期记忆 | Redis | 会话级别 | 当前对话上下文 |
| 长期记忆 | ChromaDB | 持久化 | 知识库、历史经验 |
| 工作记忆 | Redis | 任务级别 | 任务执行状态 |
| 情景记忆 | PostgreSQL | 持久化 | 事件历史记录 |

## RAG检索流程

```
Query → QueryRewrite → Embedding → ANN Search → Filter → Rerank → Compress → Context
```

## Token管理策略

| 策略 | 说明 |
|------|------|
| 滑动窗口 | 保持最近N轮对话 |
| 优先级队列 | 保留高重要性记忆 |
| 语义去重 | 合并相似内容 |
| 摘要压缩 | 历史对话摘要 |
