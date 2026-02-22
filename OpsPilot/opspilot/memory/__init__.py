"""
记忆模块

按文档要求，使用 LangChain 负责记忆管理：
- ChromaDB: 向量存储（长期记忆）
- Redis: 会话存储（短期记忆）

包含:
- base: 记忆存储基础接口
- short_term: 短期记忆（Redis 会话存储）
- long_term: 长期记忆（ChromaDB 向量存储）
- vectorstore: LangChain ChromaDB 适配
- redis_store: LangChain Redis 适配
- knowledge: 知识库
- weight: 记忆权重计算（创新保留）
- conflict: 冲突检测与解决（创新保留）
- consolidation: 记忆巩固机制（创新保留）
"""

from opspilot.memory.base import (
    MemoryType,
    MemoryPriority,
    MemoryEntry,
    SearchResult,
    BaseMemoryStore,
    MemoryManager,
)

from opspilot.memory.memory_factory import (
    MemoryFactory,
    MemoryProvider,
)

from opspilot.memory.short_term import (
    InMemoryShortTermStore,
    ShortTermMemory,
    create_short_term_memory,
)

from opspilot.memory.long_term import (
    InMemoryLongTermStore,
    LongTermMemory,
    create_long_term_memory,
)

# LangChain 向量存储 - 按文档要求使用 ChromaDB
from opspilot.memory.vectorstore import (
    ChromaDBStore,
    create_vectorstore,
    LANGCHAIN_AVAILABLE,
)

# LangChain Redis 存储 - 按文档要求使用 Redis
try:
    from opspilot.memory.redis_store import (
        RedisSessionStore,
        RedisMemoryManager,
        create_redis_store,
        REDIS_AVAILABLE,
    )
except ImportError:
    REDIS_AVAILABLE = False
    RedisSessionStore = None
    RedisMemoryManager = None
    create_redis_store = None

from opspilot.memory.knowledge import (
    InMemoryKnowledgeStore,
    KnowledgeBase,
)

# 记忆优化模块
from opspilot.memory.weight import (
    MemorySource,
    SourceCredibility,
    WeightFactors,
    WeightedMemory,
    TimeDecayCalculator,
    FrequencyScorer,
    RelevanceScorer,
    TimelinessScorer,
    MemoryWeightCalculator,
    calculate_memory_weight,
)

from opspilot.memory.conflict import (
    ConflictType,
    ResolutionStrategy,
    MemoryHistory,
    ConflictDetection,
    ConflictResolution,
    ConflictDetector,
    ConflictResolver,
    MemoryConflictManager,
    resolve_memory_conflict,
)

from opspilot.memory.consolidation import (
    ConsolidationAction,
    MemoryCluster,
    KnowledgePattern,
    ConsolidationResult,
    MemoryClusterer,
    MemoryReinforcer,
    MemoryForgetter,
    PatternExtractor,
    MemoryConsolidator,
    consolidate_memories,
)

__all__ = [
    # 基础
    "MemoryType",
    "MemoryPriority",
    "MemoryEntry",
    "SearchResult",
    "BaseMemoryStore",
    "MemoryManager",
    # 工厂
    "MemoryFactory",
    "MemoryProvider",
    "create_memory_handler",
    # 短期记忆（Redis）
    "InMemoryShortTermStore",
    "ShortTermMemory",
    "create_short_term_memory",
    # 长期记忆（ChromaDB）
    "InMemoryLongTermStore",
    "LongTermMemory",
    "create_long_term_memory",
    # LangChain 向量存储
    "ChromaDBStore",
    "create_vectorstore",
    "LANGCHAIN_AVAILABLE",
    # LangChain Redis 存储
    "RedisSessionStore",
    "RedisMemoryManager",
    "create_redis_store",
    "REDIS_AVAILABLE",
    # 知识库
    "InMemoryKnowledgeStore",
    "KnowledgeBase",
    # 权重计算
    "MemorySource",
    "SourceCredibility",
    "WeightFactors",
    "WeightedMemory",
    "TimeDecayCalculator",
    "FrequencyScorer",
    "RelevanceScorer",
    "TimelinessScorer",
    "MemoryWeightCalculator",
    "calculate_memory_weight",
    # 冲突处理
    "ConflictType",
    "ResolutionStrategy",
    "MemoryHistory",
    "ConflictDetection",
    "ConflictResolution",
    "ConflictDetector",
    "ConflictResolver",
    "MemoryConflictManager",
    "resolve_memory_conflict",
    # 记忆巩固
    "ConsolidationAction",
    "MemoryCluster",
    "KnowledgePattern",
    "ConsolidationResult",
    "MemoryClusterer",
    "MemoryReinforcer",
    "MemoryForgetter",
    "PatternExtractor",
    "MemoryConsolidator",
    "consolidate_memories",
]

