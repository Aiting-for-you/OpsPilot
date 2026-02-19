# Memory 模块架构

## 组件架构图

```mermaid
graph TB
    subgraph Memory基类
        BASE[MemoryBase<br/>抽象接口<br/><br/>定义读写接口]
    end

    subgraph 记忆实现
        SHORT[ShortTermMemory<br/>短期记忆<br/><br/>会话上下文<br/>临时数据]
        LONG[LongTermMemory<br/>长期记忆<br/><br/>历史记录<br/>持久化数据]
        KB[KnowledgeBase<br/>知识库<br/><br/>文档索引<br/>RAG检索]
    end

    subgraph 存储后端
        REDIS[(Redis<br/><br/>TTL: 1小时)]
        PG[(PostgreSQL<br/><br/>永久存储)]
        CHROMA[(ChromaDB<br/><br/>向量索引)]
    end

    BASE --> SHORT
    BASE --> LONG
    BASE --> KB

    SHORT --> REDIS
    LONG --> PG
    KB --> CHROMA

    style BASE fill:#083B75,color:#fff
    style SHORT fill:#6C8EBF,color:#fff
    style LONG fill:#6C8EBF,color:#fff
    style KB fill:#6C8EBF,color:#fff
    style REDIS fill:#B85450,color:#fff
    style PG fill:#82B366,color:#fff
    style CHROMA fill:#D79B00,color:#fff
```

## 记忆读写时序图

```mermaid
sequenceDiagram
    participant A as Agent
    participant M as MemoryManager
    participant S as Redis
    participant L as PostgreSQL
    participant K as ChromaDB

    Note over A,K: 写入流程
    A->>M: 保存记忆
    par 并行写入
        M->>S: 写入短期记忆
        M->>L: 写入长期记忆
        M->>K: 写入向量索引
    end
    M-->>A: 保存完成

    Note over A,K: 读取流程
    A->>M: 查询记忆
    par 并行查询
        M->>S: 查询短期记忆
        M->>L: 查询长期记忆
        M->>K: 向量检索
    end
    M->>M: 合并排序
    M-->>A: 返回结果
```

## 记忆类型

| 类型 | 存储 | TTL | 用途 |
|------|------|-----|------|
| 短期记忆 | Redis | 1小时 | 会话上下文 |
| 长期记忆 | PostgreSQL | 永久 | 历史记录 |
| 知识库 | ChromaDB | 永久 | RAG检索 |
