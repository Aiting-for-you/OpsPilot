"""
记忆权重计算模块 - Memory Weight

实现多维度的记忆重要性评估，支持时间衰减、访问频率、相关性等因子。

核心功能：
1. 时间衰减（艾宾浩斯遗忘曲线）
2. 访问频率统计
3. 相关性评分
4. 综合权重计算
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class MemorySource(Enum):
    """记忆来源"""
    USER_INPUT = "user_input"          # 用户输入
    SYSTEM_OUTPUT = "system_output"    # 系统输出
    TOOL_RESULT = "tool_result"        # 工具结果
    KNOWLEDGE_BASE = "knowledge_base"  # 知识库
    EXTERNAL_API = "external_api"      # 外部API
    LLM_RESPONSE = "llm_response"      # LLM响应
    AGENT_DECISION = "agent_decision"  # Agent决策


@dataclass
class SourceCredibility:
    """来源可信度"""
    credibility: float  # 0.0 - 1.0
    description: str
    
    @classmethod
    def get_default(cls, source: MemorySource) -> SourceCredibility:
        """获取默认可信度"""
        defaults = {
            MemorySource.USER_INPUT: cls(0.7, "用户输入可能存在主观偏差"),
            MemorySource.SYSTEM_OUTPUT: cls(0.9, "系统输出通常准确"),
            MemorySource.TOOL_RESULT: cls(0.85, "工具结果来自可信数据源"),
            MemorySource.KNOWLEDGE_BASE: cls(0.95, "知识库经过审核"),
            MemorySource.EXTERNAL_API: cls(0.8, "外部API依赖第三方"),
            MemorySource.LLM_RESPONSE: cls(0.75, "LLM响应可能存在幻觉"),
            MemorySource.AGENT_DECISION: cls(0.8, "Agent决策基于规则和推理"),
        }
        return defaults.get(source, cls(0.5, "未知来源"))


@dataclass
class WeightFactors:
    """权重因子"""
    time_decay: float = 0.0           # 时间衰减因子
    frequency: float = 0.0            # 访问频率因子
    relevance: float = 0.0            # 相关性因子
    timeliness: float = 0.0           # 时效性因子
    credibility: float = 0.0          # 可信度因子
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "time_decay": self.time_decay,
            "frequency": self.frequency,
            "relevance": self.relevance,
            "timeliness": self.timeliness,
            "credibility": self.credibility,
        }


@dataclass
class WeightedMemory:
    """带权重的记忆"""
    memory_id: str
    content: Any
    timestamp: float
    source: MemorySource
    base_importance: float = 0.5
    
    # 权重因子
    factors: WeightFactors = field(default_factory=WeightFactors)
    
    # 元数据
    access_count: int = 0
    last_access_time: float = field(default_factory=time.time)
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 缓存的权重值
    _cached_weight: Optional[float] = field(default=None, repr=False)
    
    @property
    def weight(self) -> float:
        """获取综合权重"""
        if self._cached_weight is not None:
            return self._cached_weight
        
        # 综合权重计算
        weight = (
            self.base_importance *
            (1 + self.factors.time_decay) *
            (1 + self.factors.frequency) *
            (1 + self.factors.relevance) *
            (1 + self.factors.timeliness) *
            self.factors.credibility
        )
        
        # 归一化到 0-1
        weight = min(max(weight, 0.0), 1.0)
        self._cached_weight = weight
        
        return weight
    
    def invalidate_cache(self) -> None:
        """失效缓存"""
        self._cached_weight = None
    
    def record_access(self) -> None:
        """记录访问"""
        self.access_count += 1
        self.last_access_time = time.time()
        self.invalidate_cache()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "content": self.content,
            "timestamp": self.timestamp,
            "source": self.source.value,
            "base_importance": self.base_importance,
            "factors": self.factors.to_dict(),
            "weight": self.weight,
            "access_count": self.access_count,
            "last_access_time": self.last_access_time,
            "tags": list(self.tags),
            "metadata": self.metadata,
        }


class TimeDecayCalculator:
    """
    时间衰减计算器
    
    基于艾宾浩斯遗忘曲线实现时间衰减：
    R = e^(-t/S)
    其中 R 为记忆保持率，t 为时间间隔，S 为记忆强度
    
    修正模型：
    decay = e^(-λt)
    λ 为衰减速率，取决于记忆类型
    """
    
    # 不同记忆类型的衰减速率（单位：小时^-1）
    DECAY_RATES = {
        "episodic": 0.01,      # 情节记忆（具体事件）：衰减快
        "semantic": 0.001,     # 语义记忆（知识）：衰减慢
        "procedural": 0.0005,  # 程序记忆（技能）：衰减最慢
        "working": 0.1,        # 工作记忆：衰减最快
    }
    
    # 艾宾浩斯遗忘曲线的关键时间点（小时）
    EBINGHAUS_MILESTONES = [
        (1, 0.44),      # 1小时后记住44%
        (8, 0.36),      # 8小时后记住36%
        (24, 0.33),     # 1天后记住33%
        (48, 0.28),     # 2天后记住28%
        (168, 0.25),    # 1周后记住25%
        (720, 0.21),    # 30天后记住21%
    ]
    
    @classmethod
    def calculate(
        cls,
        elapsed_hours: float,
        memory_type: str = "episodic",
        reinforcement_count: int = 0,
    ) -> float:
        """
        计算时间衰减因子
        
        Args:
            elapsed_hours: 经过的小时数
            memory_type: 记忆类型
            reinforcement_count: 强化次数（复习会减缓衰减）
        
        Returns:
            衰减因子（0-1），越大表示衰减越多
        """
        base_rate = cls.DECAY_RATES.get(memory_type, 0.01)
        
        # 强化会降低衰减速率
        adjusted_rate = base_rate / (1 + 0.5 * reinforcement_count)
        
        # 计算衰减
        decay = 1 - math.exp(-adjusted_rate * elapsed_hours)
        
        return decay
    
    @classmethod
    def get_retention(cls, elapsed_hours: float) -> float:
        """
        获取记忆保持率（基于艾宾浩斯曲线）
        
        Args:
            elapsed_hours: 经过的小时数
        
        Returns:
            保持率（0-1）
        """
        # 找到最近的时间点
        for hours, retention in cls.EBINGHAUS_MILESTONES:
            if elapsed_hours <= hours:
                return retention
        
        # 超过最长时间点，使用指数衰减
        return 0.21 * math.exp(-0.001 * (elapsed_hours - 720))


class FrequencyScorer:
    """
    访问频率评分器
    
    基于访问频率计算重要性：
    score = log(1 + count) / log(1 + max_count)
    """
    
    @classmethod
    def calculate(
        cls,
        access_count: int,
        max_access_count: int = 100,
    ) -> float:
        """
        计算频率因子
        
        Args:
            access_count: 访问次数
            max_access_count: 最大访问次数（用于归一化）
        
        Returns:
            频率因子（0-1）
        """
        if max_access_count <= 0:
            return 0.0
        
        # 使用对数函数平滑处理
        score = math.log(1 + access_count) / math.log(1 + max_access_count)
        
        return min(max(score, 0.0), 1.0)
    
    @classmethod
    def calculate_recent(
        cls,
        recent_accesses: int,
        time_window: float = 3600,  # 1小时内的访问
    ) -> float:
        """
        计算近期访问频率
        
        Args:
            recent_accesses: 近期访问次数
            time_window: 时间窗口（秒）
        
        Returns:
            近期频率因子（0-1）
        """
        # 近期访问更重要
        expected_max = 10  # 假设窗口内最多访问10次
        score = recent_accesses / expected_max
        return min(max(score, 0.0), 1.0)


class RelevanceScorer:
    """
    相关性评分器
    
    基于记忆内容与当前上下文的相关性评分。
    """
    
    @classmethod
    def calculate(
        cls,
        memory_content: Any,
        query_context: str,
        keywords: Optional[Set[str]] = None,
    ) -> float:
        """
        计算相关性因子
        
        Args:
            memory_content: 记忆内容
            query_context: 查询上下文
            keywords: 关键词集合
        
        Returns:
            相关性因子（0-1）
        """
        if keywords is None:
            # 简单的关键词提取
            keywords = set(query_context.lower().split())
        
        # 将记忆内容转换为字符串
        if isinstance(memory_content, dict):
            content_str = str(memory_content)
        elif isinstance(memory_content, str):
            content_str = memory_content
        else:
            content_str = str(memory_content)
        
        # 计算关键词匹配
        content_words = set(content_str.lower().split())
        matched = keywords & content_words
        
        if not keywords:
            return 0.0
        
        # Jaccard 相似度
        similarity = len(matched) / len(keywords) if keywords else 0.0
        
        return similarity
    
    @classmethod
    def calculate_semantic(
        cls,
        memory_embedding: List[float],
        query_embedding: List[float],
    ) -> float:
        """
        计算语义相关性（基于向量相似度）
        
        Args:
            memory_embedding: 记忆向量
            query_embedding: 查询向量
        
        Returns:
            语义相关性因子（0-1）
        """
        if not memory_embedding or not query_embedding:
            return 0.0
        
        # 余弦相似度
        dot_product = sum(a * b for a, b in zip(memory_embedding, query_embedding))
        norm_a = math.sqrt(sum(a * a for a in memory_embedding))
        norm_b = math.sqrt(sum(b * b for b in query_embedding))
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        similarity = dot_product / (norm_a * norm_b)
        
        # 归一化到 0-1
        return (similarity + 1) / 2


class TimelinessScorer:
    """
    时效性评分器
    
    评估记忆的时效性价值。
    """
    
    # 不同类型信息的时效性半衰期（小时）
    HALF_LIVES = {
        "price": 24,           # 价格信息：1天
        "inventory": 4,        # 库存信息：4小时
        "order_status": 1,     # 订单状态：1小时
        "policy": 720,         # 政策信息：30天
        "supplier": 168,       # 供应商信息：1周
        "default": 48,         # 默认：2天
    }
    
    @classmethod
    def calculate(
        cls,
        elapsed_hours: float,
        info_type: str = "default",
    ) -> float:
        """
        计算时效性因子
        
        Args:
            elapsed_hours: 经过的小时数
            info_type: 信息类型
        
        Returns:
            时效性因子（0-1）
        """
        half_life = cls.HALF_LIVES.get(info_type, cls.HALF_LIVES["default"])
        
        # 使用半衰期公式
        freshness = math.exp(-elapsed_hours * math.log(2) / half_life)
        
        return freshness
    
    @classmethod
    def calculate_window(
        cls,
        timestamp: float,
        valid_window: float,
    ) -> float:
        """
        计算时间窗口内的时效性
        
        Args:
            timestamp: 记忆时间戳
            valid_window: 有效时间窗口（秒）
        
        Returns:
            时效性因子（0-1）
        """
        elapsed = time.time() - timestamp
        
        if elapsed <= 0:
            return 1.0
        
        if elapsed >= valid_window:
            return 0.0
        
        # 线性衰减
        return 1.0 - (elapsed / valid_window)


class MemoryWeightCalculator:
    """
    记忆权重计算器
    
    整合所有权重因子，计算综合权重。
    
    权重公式：
    Weight = Base × TimeDecay × Frequency × Relevance × Timeliness × Credibility
    
    示例:
        >>> calculator = MemoryWeightCalculator()
        >>> factors = calculator.calculate_all(memory, query_context)
        >>> weight = calculator.calculate_weight(factors)
    """
    
    # 各因子的权重系数
    FACTOR_WEIGHTS = {
        "time_decay": 0.25,
        "frequency": 0.15,
        "relevance": 0.25,
        "timeliness": 0.20,
        "credibility": 0.15,
    }
    
    def __init__(
        self,
        custom_weights: Optional[Dict[str, float]] = None,
    ):
        """
        初始化计算器
        
        Args:
            custom_weights: 自定义权重系数
        """
        self.weights = {**self.FACTOR_WEIGHTS}
        if custom_weights:
            self.weights.update(custom_weights)
    
    def calculate_all(
        self,
        memory: WeightedMemory,
        query_context: Optional[str] = None,
        max_access_count: int = 100,
    ) -> WeightFactors:
        """
        计算所有权重因子
        
        Args:
            memory: 记忆对象
            query_context: 查询上下文
            max_access_count: 最大访问次数
        
        Returns:
            权重因子对象
        """
        now = time.time()
        elapsed_hours = (now - memory.timestamp) / 3600
        
        # 1. 时间衰减
        time_decay = 1 - TimeDecayCalculator.calculate(
            elapsed_hours,
            memory_type="episodic",
            reinforcement_count=memory.access_count // 5,  # 每5次访问算一次强化
        )
        
        # 2. 访问频率
        frequency = FrequencyScorer.calculate(
            memory.access_count,
            max_access_count,
        )
        
        # 3. 相关性
        relevance = 0.5  # 默认中等相关性
        if query_context:
            relevance = RelevanceScorer.calculate(
                memory.content,
                query_context,
                memory.tags,
            )
        
        # 4. 时效性
        timeliness = TimelinessScorer.calculate(elapsed_hours)
        
        # 5. 可信度
        credibility = SourceCredibility.get_default(memory.source).credibility
        
        return WeightFactors(
            time_decay=time_decay,
            frequency=frequency,
            relevance=relevance,
            timeliness=timeliness,
            credibility=credibility,
        )
    
    def calculate_weight(self, factors: WeightFactors) -> float:
        """
        计算综合权重
        
        Args:
            factors: 权重因子
        
        Returns:
            综合权重（0-1）
        """
        weighted_sum = (
            self.weights["time_decay"] * factors.time_decay +
            self.weights["frequency"] * factors.frequency +
            self.weights["relevance"] * factors.relevance +
            self.weights["timeliness"] * factors.timeliness +
            self.weights["credibility"] * factors.credibility
        )
        
        return weighted_sum
    
    def update_memory_weight(
        self,
        memory: WeightedMemory,
        query_context: Optional[str] = None,
    ) -> float:
        """
        更新记忆的权重
        
        Args:
            memory: 记忆对象
            query_context: 查询上下文
        
        Returns:
            更新后的权重
        """
        factors = self.calculate_all(memory, query_context)
        memory.factors = factors
        memory.invalidate_cache()
        
        return memory.weight


# 便捷函数
def calculate_memory_weight(
    memory: WeightedMemory,
    query_context: Optional[str] = None,
) -> float:
    """
    计算记忆权重的便捷函数
    
    Args:
        memory: 记忆对象
        query_context: 查询上下文
    
    Returns:
        综合权重
    """
    calculator = MemoryWeightCalculator()
    return calculator.update_memory_weight(memory, query_context)

