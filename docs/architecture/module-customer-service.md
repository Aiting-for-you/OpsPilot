# Customer Service 模块架构

## 模块概述

Customer Service 模块是 OpsPilot 的智能客服核心，负责 **工单管理**、**FAQ 问答**、**会话管理**、**满意度分析** 等功能。模块支持多渠道接入（Web、API），并与 Memory 模块深度集成实现个性化服务。

## 1. 组件架构

```mermaid
graph TB
    subgraph API["API 层"]
        direction LR
        ROUTES[Routes<br/>路由层<br/>REST API]
        MIDDLEWARE[Middleware<br/>中间件<br/>认证/日志]
        VALIDATOR[Validator<br/>参数校验<br/>Schema 验证]
    end

    subgraph CORE["Core（核心服务）"]
        direction LR
        SESSION[SessionManager<br/>会话管理<br/>状态追踪]
        TICKET[TicketManager<br/>工单管理<br/>全生命周期]
        ROUTER[IntentRouter<br/>意图路由<br/>智能分发]
    end

    subgraph FAQ["FAQ 问答"]
        direction LR
        FAQ_MGR[FAQManager<br/>FAQ 管理<br/>增删改查]
        FAQ_MATCH[FAQMatcher<br/>FAQ 匹配<br/>语义检索]
        FAQ_GEN[FAQGenerator<br/>FAQ 生成<br/>LLM 自动生成]
    end

    subgraph TICKET["Ticket 工单"]
        direction LR
        CREATE[TicketCreator<br/>工单创建<br/>自动分类]
        ASSIGN[TicketAssigner<br/>分配策略<br/>负载均衡]
        ESCALATE[TicketEscalator<br/>升级机制<br/>紧急处理]
        ANALYTICS[TicketAnalytics<br/>工单分析<br/>报表生成]
    end

    subgraph ANALYZER["Analyzer（分析器）"]
        direction LR
        SENTIMENT[SentimentAnalyzer<br/>情感分析<br/>正负面]
        SATISFACTION[SatisfactionAnalyzer<br/>满意度分析<br/>NPS/CSAT]
        INTENT[IntentClassifier<br/>意图分类<br/>多意图]
        ENTITY[EntityExtractor<br/>实体提取<br/>关键信息]
    end

    subgraph INTEGRATION["Integration（集成）"]
        direction LR
        MEMORY[MemoryIntegration<br/>记忆集成<br/>上下文]
        TOOL[ToolIntegration<br/>工具集成<br/>业务查询]
        CHANNEL[ChannelIntegration<br/>渠道集成<br/>多渠道]
    end

    subgraph AGENT["Agent（客服 Agent）"]
        direction LR
        CS_AGENT[CustomerServiceAgent<br/>客服 Agent<br/>对话处理]
        REPLY[ReplyGenerator<br/>回复生成<br/>模板渲染]
        KNOWLEDGE[KnowledgeSearch<br/>知识检索<br/>RAG]
    end

    %% 连接
    API --> MIDDLEWARE
    MIDDLEWARE --> VALIDATOR
    VALIDATOR --> CORE
    
    CORE --> SESSION
    CORE --> TICKET
    CORE --> ROUTER
    
    FAQ --> FAQ_MGR
    FAQ --> FAQ_MATCH
    FAQ --> FAQ_GEN
    
    TICKET --> CREATE
    TICKET --> ASSIGN
    TICKET --> ESCALATE
    TICKET --> ANALYTICS
    
    ANALYZER --> SENTIMENT
    ANALYZER --> SATISFACTION
    ANALYZER --> INTENT
    ANALYZER --> ENTITY
    
    INTEGRATION --> MEMORY
    INTEGRATION --> TOOL
    INTEGRATION --> CHANNEL
    
    AGENT --> REPLY
    AGENT --> KNOWLEDGE
    
    ROUTER --> FAQ
    ROUTER --> TICKET
    ROUTER --> AGENT
    
    %% 样式
    classDef api fill:#e3f2fd,stroke:#1976d2,color:#0d47a1
    classDef core fill:#fff3e0,stroke:#f57c00,color:#e65100
    classDef faq fill:#e8f5e9,stroke:#388e3c,color:#1b5e20
    classDef ticket fill:#e0f7fa,stroke:#0097a7,color:#006064
    classDef analyzer fill:#f3e5f5,stroke:#7b1fa2,color:#4a148c
    classDef integration fill:#fce4ec,stroke:#c2185b,color:#880e4f
    classDef agent fill:#efebe9,stroke:#5d4037,color:#3e2723

    class ROUTES,MIDDLEWARE,VALIDATOR api
    class SESSION,TICKET,ROUTER core
    class FAQ_MGR,FAQ_MATCH,FAQ_GEN faq
    class CREATE,ASSIGN,ESCALATE,ANALYTICS ticket
    class SENTIMENT,SATISFACTION,INTENT,ENTITY analyzer
    class MEMORY,TOOL,CHANNEL integration
    class CS_AGENT,REPLY,KNOWLEDGE agent
```

## 2. 客服流程时序图

```mermaid
sequenceDiagram
    participant USER as 用户
    participant API as CS API
    participant ROUTER as IntentRouter
    participant SESSION as SessionManager
    participant ANALYZER as 意图/情感分析
    participant FAQ as FAQ Matcher
    participant AGENT as CS Agent
    participant TICKET as TicketManager
    participant TOOL as Tool Layer
    participant MEMORY as Memory

    USER->>API: 发送消息
    API->>SESSION: get_or_create(session_id)
    SESSION-->>API: session_context
    
    API->>ANALYZER: classify_intent(message)
    ANALYZER-->>API: intent_type
    
    API->>ANALYZER: analyze_sentiment(message)
    ANALYZER-->>API: sentiment_score
    
    rect rgb(240, 248, 255)
        note right of ROUTER: 智能路由
        API->>ROUTER: route(intent_type, context)
        
        alt 意图匹配 FAQ
            ROUTER->>FAQ: search_faq(query)
            FAQ-->>ROUTER: faq_answer
            ROUTER-->>API: faq_response
        else 需要人工处理
            ROUTER->>TICKET: create_ticket(issue)
            TICKET-->>ROUTER: ticket_id
            ROUTER-->>API: ticket_created
        else Agent 自动处理
            ROUTER->>AGENT: handle_message(message)
            
            rect rgb(255, 245, 230)
                note right of AGENT: Agent 处理
                AGENT->>MEMORY: retrieve_context(user_id)
                MEMORY-->>AGENT: user_history
                
                AGENT->>TOOL: query_product(order_id)
                TOOL-->>AGENT: product_info
                
                AGENT->>AGENT: generate_reply(context, info)
                AGENT-->>ROUTER: agent_response
            end
        end
    end
    
    API->>SESSION: update_session(message, response)
    API->>ANALYZER: analyze_satisfaction(response)
    API->>USER: 返回响应
```

## 3. 文件清单

| 文件 | 类/函数 | 职责 |
|------|---------|------|
| `api.py` | `CSRouter` | 客服 API 路由 |
| `api.py` | `SessionEndpoint` | 会话端点 |
| `api.py` | `TicketEndpoint` | 工单端点 |
| `session.py` | `SessionManager` | 会话管理器 |
| `session.py` | `ConversationContext` | 会话上下文 |
| `ticket.py` | `TicketManager` | 工单管理器 |
| `ticket.py` | `TicketCreator` | 工单创建器 |
| `ticket.py` | `TicketAssigner` | 工单分配器 |
| `faq.py` | `FAQManager` | FAQ 管理器 |
| `faq.py` | `FAQMatcher` | FAQ 匹配器 |
| `faq.py` | `FAQGenerator` | FAQ 生成器 |
| `analyzer.py` | `IntentClassifier` | 意图分类器 |
| `analyzer.py` | `SentimentAnalyzer` | 情感分析器 |
| `analyzer.py` | `SatisfactionAnalyzer` | 满意度分析器 |
| `agent.py` | `CSAgent` | 客服 Agent |
| `agent.py` | `ReplyGenerator` | 回复生成器 |
| `channel.py` | `WebChannel` | Web 渠道 |
| `channel.py` | `APIChannel` | API 渠道 |

## 4. 会话管理

### 4.1 会话状态

```mermaid
stateDiagram-v2
    [*] --> NEW: 新建会话
    
    %% 样式定义
    classDef new fill:#e3f2fd,stroke:#1976d2,color:#0d47a1
    classDef active fill:#fff3e0,stroke:#f57c00,color:#e65100
    classDef waiting fill:#e8f5e9,stroke:#388e3c,color:#1b5e20
    classDef handling fill:#f3e5f5,stroke:#7b1fa2,color:#4a148c
    classDef closed fill:#efebe9,stroke:#5d4037,color:#3e2723
    
    [*] --> NEW
    NEW --> ACTIVE: 用户发送消息
    ACTIVE --> WAITING: 等待用户回复
    ACTIVE --> HANDLING: Agent 处理中
    HANDLING --> ACTIVE: 处理完成
    WAITING --> ACTIVE: 用户回复
    ACTIVE --> CLOSED: 会话结束
    CLOSED --> [*]
    
    class NEW new
    class ACTIVE active
    class WAITING waiting
    class HANDLING handling
    class CLOSED closed
```

### 4.2 会话数据结构

```python
class ConversationSession:
    session_id: str
    user_id: str
    channel: str  # web, api, wechat
    status: SessionStatus
    messages: List[Message]
    context: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]
```

## 5. 工单管理

### 5.1 工单生命周期

```mermaid
stateDiagram-v2
    [*] --> CREATED: 用户提交
    
    %% 样式定义
    classDef created fill:#e3f2fd,stroke:#1976d2,color:#0d47a1
    classDef auto fill:#c8e6c9,stroke:#2e7d32,color:#1b5e20
    classDef pending fill:#fff9c4,stroke:#f9a825,color:#f57f17
    classDef assigned fill:#b3e5fc,stroke:#0277bd,color:#01579b
    classDef progress fill:#fff3e0,stroke:#f57c00,color:#e65100
    classDef waiting fill:#e1f5fe,stroke:#0277bd,color:#01579b
    classDef resolved fill:#c8e6c9,stroke:#2e7d32,color:#1b5e20
    classDef escalated fill:#ffcdd2,stroke:#c62828,color:#b71c1c
    classDef closed fill:#efebe9,stroke:#5d4037,color:#3e2723
    
    [*] --> CREATED
    CREATED --> AUTO_HANDLED: 自动处理
    AUTO_HANDLED --> RESOLVED: 已解决
    CREATED --> PENDING: 待分配
    PENDING --> ASSIGNED: 已分配
    ASSIGNED --> IN_PROGRESS: 处理中
    IN_PROGRESS --> WAITING_USER: 等待用户
    WAITING_USER --> IN_PROGRESS: 用户回复
    IN_PROGRESS --> RESOLVED: 已解决
    IN_PROGRESS --> ESCALATED: 已升级
    ESCALATED --> IN_PROGRESS: 升级处理
    RESOLVED --> CLOSED: 已关闭
    
    class CREATED created
    class AUTO_HANDLED auto
    class PENDING pending
    class ASSIGNED assigned
    class IN_PROGRESS progress
    class WAITING_USER waiting
    class RESOLVED resolved
    class ESCALATED escalated
    class CLOSED closed
```

### 5.2 工单优先级

| 优先级 | 说明 | SLA |
|--------|------|-----|
| P0 | 紧急（系统故障） | 15 分钟 |
| P1 | 高（影响业务） | 1 小时 |
| P2 | 中（部分影响） | 4 小时 |
| P3 | 低（轻微问题） | 24 小时 |

### 5.3 分配策略

| 策略 | 说明 | 适用场景 |
|------|------|---------|
| 负载均衡 | 分配给最空闲客服 | 客服水平相当 |
| 技能匹配 | 按技能分配 | 专业问题 |
| 轮询 | 轮流分配 | 简单问题 |
| 优先级 | 高优先级优先 | 紧急问题 |

## 6. FAQ 系统

### 6.1 FAQ 匹配流程

```mermaid
flowchart TB
    A[用户问题] --> B[向量化]
    B --> C[向量检索]
    C --> D[Top-K 候选]
    D --> E[重排序]
    E --> F{阈值匹配?}
    F -->|是| G[返回 FAQ]
    F -->|否| H[转人工]
```

### 6.2 FAQ 自动生成

```mermaid
sequenceDiagram
    participant LLM as LLM
    participant KB as Knowledge Base
    
    KB->>LLM: generate_faq(document)
    LLM-->>KB: faq_candidates
    
    KB->>KB: review_faq(candidates)
    KB->>KB: approve_faq()
    KB->>KB: index_faq()
```

## 7. 智能分析

### 7.1 意图分类

| 类别 | 示例 | 处理方式 |
|------|------|---------|
| 咨询 | "这个产品怎么样" | FAQ/Agent |
| 投诉 | "东西坏了" | 创建工单 |
| 退货 | "我要退货" | 工单+流程 |
| 售后 | "订单在哪" | 工具查询 |
| 闲聊 | "你好" | 友好回复 |

### 7.2 情感分析

```python
class SentimentResult:
    label: str  # positive, neutral, negative
    score: float  # 0-1 置信度
    emotions: List[str]  # anger, sad, happy...
```

### 7.3 满意度分析

| 指标 | 说明 | 计算方式 |
|------|------|---------|
| CSAT | 客户满意度 | 评分/5 * 100% |
| NPS | 推荐意愿 | 推荐者% - 贬低者% |
| CES | 费力度 | 1-7 分，越低越好 |

## 8. 渠道集成

### 8.1 支持渠道

| 渠道 | 协议 | 特点 |
|------|------|------|
| Web | WebSocket | 实时对话 |
| API | REST | 批量处理 |
| WeChat | 微信公众号 | 微信生态 |
| DingTalk | 钉钉 | 企业集成 |

### 8.2 消息格式统一

```python
class UnifiedMessage:
    channel: str
    message_id: str
    sender: str
    content: Content  # 文本/图片/语音
    metadata: Dict[str, Any]
```