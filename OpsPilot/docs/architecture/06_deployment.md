# 部署架构图

## 1. 整体部署架构

```mermaid
graph TB
    subgraph 用户访问["🌐 用户访问"]
        BROWSER["浏览器"]
        MOBILE["移动端"]
    end

    subgraph 负载均衡["⚖️ 负载均衡层"]
        LB["Nginx / ALB"]
    end

    subgraph 应用层["🖥️ 应用层"]
        API1["API Server #1<br/>FastAPI + Uvicorn"]
        API2["API Server #2<br/>FastAPI + Uvicorn"]
        API3["API Server #N<br/>FastAPI + Uvicorn"]
    end

    subgraph 服务层["⚙️ 服务层"]
        AGENT["Agent服务<br/>AgentScope"]
        TOOL["Tool服务<br/>MCP Server"]
        RAG["RAG服务<br/>LangChain"]
    end

    subgraph 存储层["💾 存储层"]
        PG[("PostgreSQL<br/>主从复制")]
        REDIS[("Redis<br/>Cluster")]
        CHROMA[("ChromaDB<br/>向量存储")]
    end

    subgraph 基础设施["🏗️ 基础设施"]
        PROM["Prometheus<br/>监控"]
        GRAF["Grafana<br/>可视化"]
        LOG["ELK Stack<br/>日志"]
    end

    BROWSER --> LB
    MOBILE --> LB
    
    LB --> API1
    LB --> API2
    LB --> API3
    
    API1 --> AGENT
    API2 --> AGENT
    API3 --> AGENT
    
    AGENT --> TOOL
    AGENT --> RAG
    
    TOOL --> PG
    AGENT --> REDIS
    RAG --> CHROMA
    
    API1 --> PROM
    API2 --> PROM
    API3 --> PROM
    
    PROM --> GRAF
    API1 --> LOG
    API2 --> LOG
    API3 --> LOG

    style 用户访问 fill:#e3f2fd
    style 负载均衡 fill:#fff3e0
    style 应用层 fill:#e8f5e9
    style 服务层 fill:#f3e5f5
    style 存储层 fill:#efebe9
    style 基础设施 fill:#fce4ec
```

## 2. 容器化部署

### 2.1 Docker Compose 部署

```mermaid
graph TB
    subgraph Docker Host
        subgraph Network: opspilot-net
            NGINX["nginx<br/>:80/:443"]
            
            subgraph API Services
                API1["opspilot-api<br/>:8000"]
                API2["opspilot-api<br/>:8001"]
            end
            
            subgraph Data Services
                PG["postgres<br/>:5432"]
                REDIS["redis<br/>:6379"]
                CHROMA["chromadb<br/>:8000"]
            end
            
            subgraph Monitoring
                PROM["prometheus<br/>:9090"]
                GRAF["grafana<br/>:3000"]
            end
        end
    end
    
    NGINX --> API1
    NGINX --> API2
    
    API1 --> PG
    API1 --> REDIS
    API1 --> CHROMA
    
    API2 --> PG
    API2 --> REDIS
    API2 --> CHROMA
    
    API1 --> PROM
    API2 --> PROM
    PROM --> GRAF
```

### 2.2 Kubernetes 部署

```mermaid
graph TB
    subgraph Kubernetes Cluster
        subgraph Ingress
            ING["Ingress Controller<br/>Nginx"]
        end
        
        subgraph Namespace: opspilot
            SVC["Service<br/>opspilot-api"]
            
            subgraph Deployment: api
                POD1["Pod #1"]
                POD2["Pod #2"]
                POD3["Pod #3"]
            end
            
            SVC --> POD1
            SVC --> POD2
            SVC --> POD3
        end
        
        subgraph Namespace: storage
            PG_SVC["PostgreSQL Service"]
            REDIS_SVC["Redis Service"]
            CHROMA_SVC["ChromaDB Service"]
            
            PG_STS["StatefulSet<br/>PostgreSQL"]
            REDIS_STS["StatefulSet<br/>Redis"]
            CHROMA_STS["StatefulSet<br/>ChromaDB"]
            
            PG_SVC --> PG_STS
            REDIS_SVC --> REDIS_STS
            CHROMA_SVC --> CHROMA_STS
        end
        
        subgraph Namespace: monitoring
            PROM_DEP["Prometheus"]
            GRAF_DEP["Grafana"]
        end
    end
    
    ING --> SVC
    POD1 --> PG_SVC
    POD1 --> REDIS_SVC
    POD1 --> CHROMA_SVC
    
    POD1 --> PROM_DEP
    PROM_DEP --> GRAF_DEP
```

## 3. 高可用部署

```mermaid
graph TB
    subgraph Region A["🏢 区域 A (主)"]
        LB_A["Load Balancer"]
        
        subgraph App Cluster A
            API_A1["API #1"]
            API_A2["API #2"]
        end
        
        PG_A[("PostgreSQL<br/>Primary")]
        REDIS_A[("Redis<br/>Primary")]
    end
    
    subgraph Region B["🏢 区域 B (备)"]
        LB_B["Load Balancer"]
        
        subgraph App Cluster B
            API_B1["API #1"]
            API_B2["API #2"]
        end
        
        PG_B[("PostgreSQL<br/>Replica")]
        REDIS_B[("Redis<br/>Replica")]
    end
    
    subgraph DNS["🌐 DNS / CDN"]
        DNS_SRV["DNS服务器"]
    end
    
    DNS_SRV --> LB_A
    DNS_SRV -.->|"故障切换"| LB_B
    
    LB_A --> API_A1
    LB_A --> API_A2
    
    LB_B --> API_B1
    LB_B --> API_B2
    
    API_A1 --> PG_A
    API_A2 --> REDIS_A
    
    API_B1 --> PG_B
    API_B2 --> REDIS_B
    
    PG_A -.->|"同步复制"| PG_B
    REDIS_A -.->|"同步复制"| REDIS_B

    style Region A fill:#e8f5e9
    style Region B fill:#fff3e0
```

## 4. 网络架构

```mermaid
graph TB
    subgraph 外网
        USER["用户"]
        CDN["CDN"]
    end
    
    subgraph DMZ区
        WAF["WAF<br/>防火墙"]
        LB["Load Balancer<br/>:443"]
    end
    
    subgraph 应用区
        API["API Gateway<br/>:8000"]
        AGENT["Agent Service<br/>:8001"]
        TOOL["Tool Service<br/>:8002"]
    end
    
    subgraph 数据区
        PG[("PostgreSQL<br/>:5432")]
        REDIS[("Redis<br/>:6379")]
        CHROMA[("ChromaDB<br/>:8000")]
    end
    
    subgraph 管理区
        PROM["Prometheus<br/>:9090"]
        GRAF["Grafana<br/>:3000"]
        LOG["ELK<br/>:9200"]
    end
    
    USER --> CDN
    CDN --> WAF
    WAF --> LB
    LB --> API
    
    API --> AGENT
    API --> TOOL
    
    AGENT --> PG
    AGENT --> REDIS
    TOOL --> PG
    TOOL --> REDIS
    AGENT --> CHROMA
    
    API --> PROM
    AGENT --> PROM
    PROM --> GRAF
    API --> LOG

    style 外网 fill:#e3f2fd
    style DMZ区 fill:#fff3e0
    style 应用区 fill:#e8f5e9
    style 数据区 fill:#efebe9
    style 管理区 fill:#f3e5f5
```

## 5. 服务依赖关系

```mermaid
graph LR
    subgraph 核心服务
        API["opspilot-api"]
        AGENT["agent-service"]
        TOOL["tool-service"]
        RAG["rag-service"]
    end
    
    subgraph 基础服务
        PG[("postgresql")]
        REDIS[("redis")]
        CHROMA[("chromadb")]
    end
    
    subgraph 监控服务
        PROM[("prometheus")]
        GRAF[("grafana")]
    end
    
    API --> AGENT
    API --> TOOL
    API --> RAG
    
    AGENT --> REDIS
    AGENT --> PG
    AGENT --> CHROMA
    
    TOOL --> PG
    RAG --> CHROMA
    
    API --> PROM
    AGENT --> PROM
    TOOL --> PROM
    RAG --> PROM
```

## 6. 资源配置建议

### 6.1 最小部署配置

| 服务 | CPU | 内存 | 存储 | 副本数 |
|------|-----|------|------|--------|
| API Server | 2核 | 4GB | - | 2 |
| PostgreSQL | 2核 | 4GB | 50GB | 1 |
| Redis | 1核 | 2GB | - | 1 |
| ChromaDB | 2核 | 4GB | 20GB | 1 |

### 6.2 生产环境配置

| 服务 | CPU | 内存 | 存储 | 副本数 |
|------|-----|------|------|--------|
| API Server | 4核 | 8GB | - | 3+ |
| PostgreSQL | 4核 | 16GB | 200GB | 2 (主从) |
| Redis | 2核 | 8GB | - | 3 (Cluster) |
| ChromaDB | 4核 | 16GB | 100GB | 3 |
| Prometheus | 2核 | 4GB | 50GB | 1 |
| Grafana | 1核 | 2GB | 10GB | 1 |

## 7. 部署检查清单

### 7.1 部署前检查

- [ ] 环境变量配置完成
- [ ] 数据库连接配置正确
- [ ] SSL证书已配置
- [ ] 防火墙规则已设置
- [ ] 监控告警已配置

### 7.2 部署后验证

- [ ] 健康检查接口正常
- [ ] API文档可访问
- [ ] 数据库连接正常
- [ ] 缓存服务正常
- [ ] 监控面板正常

## 8. 运维命令速查

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f opspilot-api

# 扩容API服务
docker-compose up -d --scale opspilot-api=3

# 数据库备份
pg_dump -h localhost -U postgres opspilot > backup.sql

# Redis缓存清理
redis-cli FLUSHDB

# 查看服务状态
kubectl get pods -n opspilot

# 滚动更新
kubectl rollout restart deployment/opspilot-api -n opspilot
```
