# Tool 模块架构

## 组件架构图

```mermaid
graph TB
    %% ==================== 第一行：基类 ====================
    subgraph L1[Base基类]
        direction LR
        BASE[BaseTool<br/>工具基类<br/>定义工具接口]
        BASE_SCHEMA[ToolSchema<br/>工具模式<br/>JSON Schema]
        BASE_VALID[Validator<br/>参数验证器<br/>类型检查]
        BASE_EXEC[Executor<br/>执行器<br/>超时控制]
    end

    %% ==================== 第二行：电商与数据库 ====================
    subgraph L2A[Ecommerce电商工具]
        direction LR
        ECOM[电商工具集]
        ECOM_PROD[ProductTool<br/>商品工具]
        ECOM_ORDER[OrderTool<br/>订单工具]
        ECOM_INV[InventoryTool<br/>库存工具]
    end

    subgraph L2B[Database数据库工具]
        direction LR
        DB[数据库工具集]
        DB_QUERY[QueryTool<br/>查询工具]
        DB_MUTATE[MutateTool<br/>变更工具]
        DB_TRANS[TransactionTool<br/>事务工具]
    end

    %% ==================== 第三行：HTTP与文件 ====================
    subgraph L3A[HTTP网络工具]
        direction LR
        HTTP[HTTP工具集]
        HTTP_GET[GETTool<br/>GET请求]
        HTTP_POST[POSTTool<br/>POST请求]
        HTTP_AUTH[AuthManager<br/>认证管理]
    end

    subgraph L3B[File文件工具]
        direction LR
        FILE[文件工具集]
        FILE_READ[FileReader<br/>文件读取]
        FILE_WRITE[FileWriter<br/>文件写入]
        FILE_GLOB[FileGlobber<br/>文件搜索]
    end

    %% ==================== 第四行：通知与自愈 ====================
    subgraph L4A[Notification通知工具]
        direction LR
        NOTIFY[通知工具集]
        NOTIFY_EMAIL[EmailNotifier<br/>邮件通知]
        NOTIFY_SMS[SMSNotifier<br/>短信通知]
        NOTIFY_WEB[WebhookNotifier<br/>Webhook]
    end

    subgraph L4B[Healing自愈工具]
        direction LR
        HEAL[自愈工具集]
        HEAL_DIAG[DiagnosticTool<br/>诊断工具]
        HEAL_FIX[FixTool<br/>修复工具]
        HEAL_ROLL[RollbackTool<br/>回滚工具]
    end

    %% ==================== 第五行：MCP与检索 ====================
    subgraph L5A[MCP外部工具]
        direction LR
        MCP[MCP工具集]
        MCP_CLIENT[MCPClient<br/>MCP客户端]
        MCP_DB[MCPDatabase<br/>外部数据源]
        MCP_SEARCH[MCPSearch<br/>外部检索]
    end

    subgraph L5B[Retrieval检索工具]
        direction LR
        RETR[检索工具集]
        RETR_VEC[VectorRetriever<br/>向量检索]
        RETR_HYB[HybridRetriever<br/>混合检索]
        RETR_CTX[ContextManager<br/>上下文管理]
    end

    %% ==================== 第六行：向量与集成 ====================
    subgraph L6A[Embedding向量工具]
        direction LR
        EMBED[向量化工具]
        EMBED_OPEN[OpenAIEmbedding<br/>OpenAI嵌入]
        EMBED_LOCAL[LocalEmbedding<br/>本地嵌入]
    end

    subgraph L6B[Langchain集成]
        direction LR
        LC[Langchain工具]
        LC_WRAP[ToolWrapper<br/>工具包装器]
    end

    %% ==================== 层间连接 ====================
    BASE --> BASE_SCHEMA
    BASE --> BASE_VALID
    BASE --> BASE_EXEC

    ECOM --> ECOM_PROD
    ECOM --> ECOM_ORDER
    ECOM --> ECOM_INV

    DB --> DB_QUERY
    DB --> DB_MUTATE
    DB --> DB_TRANS

    HTTP --> HTTP_GET
    HTTP --> HTTP_POST
    HTTP --> HTTP_AUTH

    FILE --> FILE_READ
    FILE --> FILE_WRITE
    FILE --> FILE_GLOB

    NOTIFY --> NOTIFY_EMAIL
    NOTIFY --> NOTIFY_SMS
    NOTIFY --> NOTIFY_WEB

    HEAL --> HEAL_DIAG
    HEAL --> HEAL_FIX
    HEAL --> HEAL_ROLL

    MCP --> MCP_CLIENT
    MCP --> MCP_DB
    MCP --> MCP_SEARCH

    RETR --> RETR_VEC
    RETR --> RETR_HYB
    RETR --> RETR_CTX

    EMBED --> EMBED_OPEN
    EMBED --> EMBED_LOCAL

    LC --> LC_WRAP

    BASE -.->|继承| ECOM
    BASE -.->|继承| DB
    BASE -.->|继承| HTTP
    BASE -.->|继承| FILE
    BASE -.->|继承| NOTIFY
    BASE -.->|继承| HEAL
    BASE -.->|继承| MCP
    BASE -.->|继承| RETR
    BASE -.->|继承| EMBED
    BASE -.->|继承| LC

    RETR_VEC --> EMBED
    HTTP_AUTH --> HTTP_GET
    HEAL_DIAG --> HEAL_FIX

    %% ==================== 样式 ====================
    classDef base fill:#083B75,color:#fff
    classDef ecommerce fill:#1a5f7a,color:#fff
    classDef database fill:#2e7d32,color:#fff
    classDef http fill:#1565c0,color:#fff
    classDef file fill:#6a1b9a,color:#fff
    classDef notify fill:#c62828,color:#fff
    classDef healing fill:#f57c00,color:#fff
    classDef mcp fill:#455a64,color:#fff
    classDef retrieval fill:#00838f,color:#fff

    class BASE,BASE_SCHEMA,BASE_VALID,BASE_EXEC base
    class ECOM,ECOM_PROD,ECOM_ORDER,ECOM_INV ecommerce
    class DB,DB_QUERY,DB_MUTATE,DB_TRANS database
    class HTTP,HTTP_GET,HTTP_POST,HTTP_AUTH http
    class FILE,FILE_READ,FILE_WRITE,FILE_GLOB file
    class NOTIFY,NOTIFY_EMAIL,NOTIFY_SMS,NOTIFY_WEB notify
    class HEAL,HEAL_DIAG,HEAL_FIX,HEAL_ROLL healing
    class MCP,MCP_CLIENT,MCP_DB,MCP_SEARCH mcp
    class RETR,RETR_VEC,RETR_HYB,RETR_CTX,EMBED,EMBED_OPEN,EMBED_LOCAL retrieval
    class LC,LC_WRAP base
```

## 工具调用时序图

```mermaid
sequenceDiagram
    participant AGENT as ExecAgent
    participant SELECT as ToolSelector
    participant BASE as BaseTool
    participant VALID as Validator
    participant EXEC as Executor
    participant IMPL as ToolImpl
    participant RETRY as RetryHandler

    AGENT->>SELECT: 1. select_tool(task_type)
    SELECT->>SELECT: 2. match_capabilities()
    SELECT-->>AGENT: 3. tool_instance

    AGENT->>BASE: 4. execute(params)
    BASE->>VALID: 5. validate(params)
    
    alt 参数有效
        VALID-->>BASE: 6. validated_params
    else 参数无效
        VALID-->>BASE: 7. ValidationError
        BASE-->>AGENT: 8. error_response
    end

    loop 执行重试
        BASE->>EXEC: 9. run(validated_params)
        EXEC->>IMPL: 10. _execute(params)
        
        alt 执行成功
            IMPL-->>EXEC: 11. result
            EXEC-->>BASE: 12. success_response
        else 执行失败
            IMPL-->>EXEC: 13. ExecutionError
            EXEC->>RETRY: 14. should_retry()
            
            alt 需要重试
                RETRY-->>EXEC: 15. retry_with_backoff
            else 不再重试
                RETRY-->>EXEC: 16. no_retry
                EXEC-->>BASE: 17. error_response
            end
        end
    end

    BASE-->>AGENT: 18. final_response
```

## 文件清单

| 文件 | 类/函数 | 职责 |
|------|--------|------|
| base.py | BaseTool | 工具抽象基类 |
| base.py | ToolSchema | 工具Schema定义 |
| base.py | Validator | 参数验证器 |
| ecommerce.py | ProductTool | 商品操作工具 |
| ecommerce.py | OrderTool | 订单操作工具 |
| ecommerce.py | InventoryTool | 库存操作工具 |
| database.py | QueryTool | 数据库查询工具 |
| database.py | MutateTool | 数据库变更工具 |
| database.py | TransactionTool | 事务管理工具 |
| http_client.py | HttpClientTool | HTTP请求工具 |
| http_client.py | AuthManager | 认证管理器 |
| file_ops.py | FileReader | 文件读取工具 |
| file_ops.py | FileWriter | 文件写入工具 |
| notification.py | EmailNotifier | 邮件通知工具 |
| notification.py | WebhookNotifier | Webhook通知工具 |
| healing.py | DiagnosticTool | 诊断工具 |
| healing.py | FixTool | 修复工具 |
| mcp.py | MCPClient | MCP客户端 |
| mcp.py | MCPTool | MCP工具包装 |
| mcp_db.py | MCPDatabase | MCP数据库工具 |
| retriever.py | VectorRetriever | 向量检索工具 |
| retriever.py | HybridRetriever | 混合检索工具 |
| embeddings.py | OpenAIEmbedding | OpenAI嵌入工具 |
| indexer.py | Indexer | 索引构建工具 |
| compressor.py | ContextCompressor | 上下文压缩工具 |
| context_manager.py | ToolContextManager | 工具上下文管理 |
| langchain_tools.py | LangchainToolWrapper | Langchain工具包装 |
| internal.py | InternalTool | 内部工具集 |
| devops.py | DevopsTool | 运维工具集 |

## 工具分类

| 分类 | 工具 | 输入 | 输出 |
|------|------|------|------|
| 电商 | ProductTool | product_id | product_info |
| 电商 | OrderTool | order_params | order_id |
| 数据库 | QueryTool | sql, params | rows |
| 数据库 | MutateTool | sql, params | affected_rows |
| HTTP | GETTool | url, headers | response |
| HTTP | POSTTool | url, data, headers | response |
| 文件 | FileReader | file_path | content |
| 文件 | FileWriter | file_path, content | success |
| 通知 | EmailNotifier | to, subject, body | message_id |
| 检索 | VectorRetriever | query, k | documents |
| 向量 | EmbeddingTool | text | vector |
