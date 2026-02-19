# Memory 模块架构

## 组件架构图

```mermaid
graph TB
    subgraph MemoryManager记忆管理器
        MM[MemoryManager<br/>记忆管理器<br/><br/>统一记忆接口<br/>生命周期管理]
        MM_SHORT[ShortTermMemory<br/>短期记忆<br/><br/>工作记忆<br/>上下文窗口]
        MM_LONG[LongTermMemory<br/>长期记忆<br/><br/>持久化存储<br/>知识积累]
        MM_WORK[WorkingMemory<br/>工作记忆<br/><br/>当前任务<br/>临时状态]
    end

    subgraph Embedding向量化
        EMBED[EmbeddingService<br/>嵌入服务<br/><br/>文本向量化<br/>批量处理]
        EMBED_OPEN[OpenAIEmbedding<br/>OpenAI嵌入<br/><br/>text-embedding-3<br/>1536维向量]
        EMBED_LOCAL[LocalEmbedding<br/>本地嵌入<br/><br/>SentenceTransformer<br/>768维向量]
        EMBED_CACHE[EmbeddingCache<br/>嵌入缓存<br/><br/>向量缓存<br/>命中率优化]
    end

    subgraph Indexer索引构建
        IDX[Indexer<br/>索引构建器<br/><br/>向量索引<br/>增量更新]
        IDX_CHROMA[ChromaIndexer<br/>Chroma索引器<br/><br/>Collection管理<br/>HNSW索引]
        IDX_FAISS[FAISSIndexer<br/>FAISS索引器<br/><br/>IVF索引<br/>GPU加速]
        IDX_META[MetadataIndexer<br/>元数据索引器<br/><br/>过滤索引<br/>范围查询]
    end

    subgraph Retriever检索器
        RET[Retriever<br/>检索器基类<br/><br/>语义检索<br/>结果排序]
        RET_VEC[VectorRetriever<br/>向量检索器<br/><br/>ANN搜索<br/>相似度计算]
        RET_HYB[HybridRetriever<br/>混合检索器<br/><br/>关键词+向量<br/>RRF融合]
        RET_CTX[ContextRetriever<br/>上下文检索器<br/><br/>窗口检索<br/>关联扩展]
    end

    subgraph Compressor压缩器
        COMP[Compressor<br/>压缩器基类<br/><br/>上下文压缩<br/>信息密度优化]
        COMP_LLM[LLMCompressor<br/>LLM压缩器<br/><br/>摘要压缩<br/>关键信息提取]
        COMP_RANK[RankCompressor<br/>排序压缩器<br/><br/>相关性排序<br/>Top-K选择]
        COMP_SEM[SemanticCompressor<br/>语义压缩器<br/><br/>去重合并<br/>主题聚类]
    end

    subgraph Storage存储层
        STORE[MemoryStorage<br/>存储抽象层<br/><br/>统一存储接口]
        STORE_PG[PostgreSQLStore<br/>PG存储<br/><br/>结构化记忆<br/>关系查询]
        STORE_REDIS[RedisStore<br/>Redis存储<br/><br/>会话记忆<br/>快速访问]
        STORE_CHROMA[ChromaStore<br/>Chroma存储<br/><br/>向量记忆<br/>语义检索]
        STORE_FILE[FileStore<br/>文件存储<br/><br/>日志记忆<br/>归档备份]
    end

    subgraph Context上下文管理
        CTX[ContextManager<br/>上下文管理器<br/><br/>窗口控制<br/>Token管理]
        CTX_WIN[WindowManager<br/>窗口管理器<br/><br/>滑动窗口<br/>动态调整]
        CTX_TOK[TokenCounter<br/>Token计数器<br/><br/>Token统计<br/>预算控制]
        CTX_PRIO[PriorityQueue<br/>优先队列<br/><br/>重要性排序<br/>淘汰策略]
    end

    subgraph RAGPipeline检索增强
        RAG[RAGPipeline<br/>RAG流水线<br/><br/>检索增强生成<br/>端到端流程]
        RAG_QUERY[QueryRewriter<br/>查询重写器<br/><br/>查询扩展<br/>意图增强]
        RAG_DOC[DocProcessor<br/>文档处理器<br/><br/>切片分割<br/>元数据提取]
        RAG_PROMPT[PromptBuilder<br/>提示构建器<br/><br/>模板填充<br/>上下文组装]
    end

    %% MemoryManager内部连接
    MM --> MM_SHORT
    MM --> MM_LONG
    MM --> MM_WORK

    %% Embedding内部连接
    EMBED --> EMBED_OPEN
    EMBED --> EMBED_LOCAL
    EMBED --> EMBED_CACHE

    %% Indexer内部连接
    IDX --> IDX_CHROMA
    IDX --> IDX_FAISS
    IDX --> IDX_META

    %% Retriever内部连接
    RET --> RET_VEC
    RET --> RET_HYB
    RET --> RET_CTX

    %% Compressor内部连接
    COMP --> COMP_LLM
    COMP --> COMP_RANK
    COMP --> COMP_SEM

    %% Storage内部连接
    STORE --> STORE_PG
    STORE --> STORE_REDIS
    STORE --> STORE_CHROMA
    STORE --> STORE_FILE

    %% Context内部连接
    CTX --> CTX_WIN
    CTX --> CTX_TOK
    CTX --> CTX_PRIO

    %% RAG内部连接
    RAG --> RAG_QUERY
    RAG --> RAG_DOC
    RAG --> RAG_PROMPT

    %% 模块间连接
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

    %% 样式
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
    class STORE,STORE_PG,STORE_REDIS,STORE_CHROMA,STORE_FILE storage
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
