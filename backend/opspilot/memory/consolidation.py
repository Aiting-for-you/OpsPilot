"""
记忆巩固机制 - Memory Consolidation

模拟人类记忆的巩固过程，实现记忆强化、遗忘和知识提取。

核心功能：
1. 相似记忆聚类
2. 重要记忆强化
3. 不重要记忆遗忘
4. 知识模式提取
"""

from __future__ import annotations

import math
import time
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from opspilot.memory.weight import (
    WeightedMemory,
    MemorySource,
    WeightFactors,
    MemoryWeightCalculator,
)
from opspilot.memory.conflict import (
    MemoryConflictManager,
    ConflictResolution,
)


class ConsolidationAction(Enum):
    """巩固动作"""
    RETAIN = "retain"          # 保留
    REINFORCE = "reinforce"    # 强化
    MERGE = "merge"            # 合并
    FORGET = "forget"          # 遗忘
    ARCHIVE = "archive"        # 归档


@dataclass
class MemoryCluster:
    """记忆簇"""
    cluster_id: str
    memories: List[WeightedMemory]
    centroid: Optional[WeightedMemory] = None
    representative: Optional[WeightedMemory] = None
    topic: str = ""
    keywords: Set[str] = field(default_factory=set)
    
    @property
    def size(self) -> int:
        return len(self.memories)
    
    @property
    def avg_weight(self) -> float:
        if not self.memories:
            return 0.0
        return sum(m.weight for m in self.memories) / len(self.memories)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "size": self.size,
            "avg_weight": self.avg_weight,
            "topic": self.topic,
            "keywords": list(self.keywords),
            "memory_ids": [m.memory_id for m in self.memories],
        }


@dataclass
class KnowledgePattern:
    """知识模式"""
    pattern_id: str
    pattern_type: str          # rule, fact, relation, trend
    content: str
    confidence: float
    support_count: int         # 支持该模式的记忆数量
    source_memories: List[str]
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "content": self.content,
            "confidence": self.confidence,
            "support_count": self.support_count,
            "source_memories": self.source_memories,
            "created_at": self.created_at,
        }


@dataclass
class ConsolidationResult:
    """巩固结果"""
    retained: List[WeightedMemory]
    reinforced: List[WeightedMemory]
    merged: List[WeightedMemory]
    forgotten: List[WeightedMemory]
    archived: List[WeightedMemory]
    patterns: List[KnowledgePattern]
    stats: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "retained_count": len(self.retained),
            "reinforced_count": len(self.reinforced),
            "merged_count": len(self.merged),
            "forgotten_count": len(self.forgotten),
            "archived_count": len(self.archived),
            "patterns_count": len(self.patterns),
            "stats": self.stats,
        }


class MemoryClusterer:
    """
    记忆聚类器
    
    将相似记忆聚类，便于后续处理。
    """
    
    def __init__(
        self,
        similarity_threshold: float = 0.5,
        min_cluster_size: int = 2,
    ):
        """
        初始化聚类器
        
        Args:
            similarity_threshold: 相似度阈值
            min_cluster_size: 最小簇大小
        """
        self.similarity_threshold = similarity_threshold
        self.min_cluster_size = min_cluster_size
    
    def cluster(
        self,
        memories: List[WeightedMemory],
    ) -> List[MemoryCluster]:
        """
        聚类记忆
        
        使用简单的层次聚类算法。
        
        Args:
            memories: 记忆列表
        
        Returns:
            记忆簇列表
        """
        if not memories:
            return []
        
        # 初始化：每个记忆一个簇
        clusters: List[List[WeightedMemory]] = [[m] for m in memories]
        
        # 层次合并
        while True:
            # 找到最相似的两个簇
            max_similarity = -1
            merge_indices = (-1, -1)
            
            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    similarity = self._cluster_similarity(clusters[i], clusters[j])
                    if similarity > max_similarity:
                        max_similarity = similarity
                        merge_indices = (i, j)
            
            # 如果最大相似度低于阈值，停止
            if max_similarity < self.similarity_threshold:
                break
            
            # 合并簇
            i, j = merge_indices
            if i >= 0 and j >= 0 and i < len(clusters) and j < len(clusters):
                clusters[i].extend(clusters[j])
                clusters.pop(j)
        
        # 过滤小簇
        clusters = [c for c in clusters if len(c) >= self.min_cluster_size]
        
        # 创建簇对象
        result = []
        for idx, cluster_memories in enumerate(clusters):
            cluster = self._create_cluster(str(idx), cluster_memories)
            result.append(cluster)
        
        return result
    
    def _cluster_similarity(
        self,
        cluster1: List[WeightedMemory],
        cluster2: List[WeightedMemory],
    ) -> float:
        """计算两个簇之间的相似度"""
        # 使用平均链接
        similarities = []
        for m1 in cluster1:
            for m2 in cluster2:
                sim = self._memory_similarity(m1, m2)
                similarities.append(sim)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _memory_similarity(
        self,
        m1: WeightedMemory,
        m2: WeightedMemory,
    ) -> float:
        """计算两个记忆之间的相似度"""
        # 基于标签的相似度
        if m1.tags and m2.tags:
            intersection = len(m1.tags & m2.tags)
            union = len(m1.tags | m2.tags)
            tag_sim = intersection / union if union > 0 else 0.0
        else:
            tag_sim = 0.0
        
        # 基于内容的相似度（简化版）
        if isinstance(m1.content, dict) and isinstance(m2.content, dict):
            keys1 = set(m1.content.keys())
            keys2 = set(m2.content.keys())
            key_intersection = len(keys1 & keys2)
            key_union = len(keys1 | keys2)
            content_sim = key_intersection / key_union if key_union > 0 else 0.0
        elif isinstance(m1.content, str) and isinstance(m2.content, str):
            # 字符串相似度
            set1 = set(m1.content)
            set2 = set(m2.content)
            intersection = len(set1 & set2)
            union = len(set1 | set2)
            content_sim = intersection / union if union > 0 else 0.0
        else:
            content_sim = 0.0
        
        # 综合相似度
        return 0.5 * tag_sim + 0.5 * content_sim
    
    def _create_cluster(
        self,
        cluster_id: str,
        memories: List[WeightedMemory],
    ) -> MemoryCluster:
        """创建记忆簇"""
        # 找到代表性记忆（权重最高的）
        representative = max(memories, key=lambda m: m.weight)
        
        # 提取关键词
        all_tags: Set[str] = set()
        for m in memories:
            all_tags.update(m.tags)
        
        # 计算主题
        tag_counter = Counter(all_tags)
        top_tags = [tag for tag, _ in tag_counter.most_common(5)]
        topic = ", ".join(top_tags) if top_tags else "未分类"
        
        return MemoryCluster(
            cluster_id=cluster_id,
            memories=memories,
            representative=representative,
            topic=topic,
            keywords=set(top_tags),
        )


class MemoryReinforcer:
    """
    记忆强化器
    
    强化重要记忆，提升其权重。
    """
    
    # 强化因子
    REINFORCEMENT_FACTOR = 1.2
    
    @classmethod
    def reinforce(
        cls,
        memory: WeightedMemory,
        factor: Optional[float] = None,
    ) -> WeightedMemory:
        """
        强化记忆
        
        Args:
            memory: 记忆对象
            factor: 强化因子
        
        Returns:
            强化后的记忆
        """
        factor = factor or cls.REINFORCEMENT_FACTOR
        
        # 提升基础重要性
        memory.base_importance = min(memory.base_importance * factor, 1.0)
        
        # 更新权重因子
        memory.factors.frequency *= factor
        
        # 失效缓存
        memory.invalidate_cache()
        
        return memory
    
    @classmethod
    def should_reinforce(
        cls,
        memory: WeightedMemory,
        access_count_threshold: int = 3,
        weight_threshold: float = 0.5,
    ) -> bool:
        """
        判断是否应该强化
        
        Args:
            memory: 记忆对象
            access_count_threshold: 访问次数阈值
            weight_threshold: 权重阈值
        
        Returns:
            是否应该强化
        """
        # 高访问次数
        if memory.access_count >= access_count_threshold:
            return True
        
        # 高权重
        if memory.weight >= weight_threshold:
            return True
        
        # 近期访问
        recent_threshold = time.time() - 3600  # 1小时内
        if memory.last_access_time >= recent_threshold:
            return True
        
        return False


class MemoryForgetter:
    """
    记忆遗忘器
    
    遗忘不重要的记忆，释放空间。
    """
    
    # 遗忘阈值
    FORGET_WEIGHT_THRESHOLD = 0.1
    FORGET_AGE_THRESHOLD = 30 * 24 * 3600  # 30天
    
    @classmethod
    def should_forget(
        cls,
        memory: WeightedMemory,
        weight_threshold: Optional[float] = None,
        age_threshold: Optional[float] = None,
    ) -> bool:
        """
        判断是否应该遗忘
        
        Args:
            memory: 记忆对象
            weight_threshold: 权重阈值
            age_threshold: 年龄阈值（秒）
        
        Returns:
            是否应该遗忘
        """
        weight_threshold = weight_threshold or cls.FORGET_WEIGHT_THRESHOLD
        age_threshold = age_threshold or cls.FORGET_AGE_THRESHOLD
        
        # 低权重
        if memory.weight < weight_threshold:
            return True
        
        # 太老且访问少
        age = time.time() - memory.timestamp
        if age > age_threshold and memory.access_count < 2:
            return True
        
        return False
    
    @classmethod
    def forget(
        cls,
        memories: List[WeightedMemory],
        max_keep: Optional[int] = None,
    ) -> Tuple[List[WeightedMemory], List[WeightedMemory]]:
        """
        执行遗忘
        
        Args:
            memories: 记忆列表
            max_keep: 最大保留数量
        
        Returns:
            (保留的记忆, 遗忘的记忆)
        """
        retained = []
        forgotten = []
        
        for memory in memories:
            if cls.should_forget(memory):
                forgotten.append(memory)
            else:
                retained.append(memory)
        
        # 如果超过最大保留数，按权重截断
        if max_keep is not None and len(retained) > max_keep:
            retained.sort(key=lambda m: m.weight, reverse=True)
            extra = retained[max_keep:]
            forgotten.extend(extra)
            retained = retained[:max_keep]
        
        return retained, forgotten


class PatternExtractor:
    """
    知识模式提取器
    
    从记忆中提取知识模式。
    """
    
    @classmethod
    def extract(
        cls,
        memories: List[WeightedMemory],
    ) -> List[KnowledgePattern]:
        """
        提取知识模式
        
        Args:
            memories: 记忆列表
        
        Returns:
            知识模式列表
        """
        patterns = []
        
        # 提取事实模式
        fact_patterns = cls._extract_facts(memories)
        patterns.extend(fact_patterns)
        
        # 提取关系模式
        relation_patterns = cls._extract_relations(memories)
        patterns.extend(relation_patterns)
        
        # 提取趋势模式
        trend_patterns = cls._extract_trends(memories)
        patterns.extend(trend_patterns)
        
        return patterns
    
    @classmethod
    def _extract_facts(cls, memories: List[WeightedMemory]) -> List[KnowledgePattern]:
        """提取事实模式"""
        patterns = []
        
        # 统计常见字段值
        field_values: Dict[str, Counter] = {}
        
        for memory in memories:
            if isinstance(memory.content, dict):
                for key, value in memory.content.items():
                    if key not in field_values:
                        field_values[key] = Counter()
                    field_values[key][str(value)] += 1
        
        # 提取高频事实
        for field, counter in field_values.items():
            for value, count in counter.most_common(3):
                if count >= 2:  # 至少出现2次
                    patterns.append(KnowledgePattern(
                        pattern_id=f"fact_{field}_{len(patterns)}",
                        pattern_type="fact",
                        content=f"{field} = {value}",
                        confidence=count / len(memories),
                        support_count=count,
                        source_memories=[],  # TODO: 记录来源
                    ))
        
        return patterns
    
    @classmethod
    def _extract_relations(cls, memories: List[WeightedMemory]) -> List[KnowledgePattern]:
        """提取关系模式"""
        patterns = []
        
        # 简单的关系提取：共现字段
        field_pairs: Counter = Counter()
        
        for memory in memories:
            if isinstance(memory.content, dict):
                keys = list(memory.content.keys())
                for i in range(len(keys)):
                    for j in range(i + 1, len(keys)):
                        pair = (keys[i], keys[j])
                        field_pairs[pair] += 1
        
        # 提取高频共现
        for (field1, field2), count in field_pairs.most_common(5):
            if count >= 3:
                patterns.append(KnowledgePattern(
                    pattern_id=f"relation_{len(patterns)}",
                    pattern_type="relation",
                    content=f"{field1} ↔ {field2}",
                    confidence=count / len(memories),
                    support_count=count,
                    source_memories=[],
                ))
        
        return patterns
    
    @classmethod
    def _extract_trends(cls, memories: List[WeightedMemory]) -> List[KnowledgePattern]:
        """提取趋势模式"""
        patterns = []
        
        # 按时间排序
        sorted_memories = sorted(memories, key=lambda m: m.timestamp)
        
        # 检测数值字段的变化趋势
        numeric_fields: Dict[str, List[Tuple[float, float]]] = {}
        
        for memory in sorted_memories:
            if isinstance(memory.content, dict):
                for key, value in memory.content.items():
                    if isinstance(value, (int, float)):
                        if key not in numeric_fields:
                            numeric_fields[key] = []
                        numeric_fields[key].append((memory.timestamp, value))
        
        # 分析趋势
        for field, values in numeric_fields.items():
            if len(values) >= 3:
                # 简单趋势判断：比较首尾
                first_values = [v[1] for v in values[:len(values)//2]]
                last_values = [v[1] for v in values[len(values)//2:]]
                
                first_avg = sum(first_values) / len(first_values)
                last_avg = sum(last_values) / len(last_values)
                
                if last_avg > first_avg * 1.1:
                    trend = "上升"
                elif last_avg < first_avg * 0.9:
                    trend = "下降"
                else:
                    trend = "稳定"
                
                patterns.append(KnowledgePattern(
                    pattern_id=f"trend_{field}",
                    pattern_type="trend",
                    content=f"{field} 趋势: {trend}",
                    confidence=0.7,
                    support_count=len(values),
                    source_memories=[],
                ))
        
        return patterns


class MemoryConsolidator:
    """
    记忆巩固器
    
    整合所有巩固操作，提供完整的巩固流程。
    
    示例:
        >>> consolidator = MemoryConsolidator()
        >>> result = consolidator.consolidate(memories)
    """
    
    def __init__(
        self,
        similarity_threshold: float = 0.5,
        forget_weight_threshold: float = 0.1,
        max_memories: int = 1000,
    ):
        """
        初始化巩固器
        
        Args:
            similarity_threshold: 相似度阈值
            forget_weight_threshold: 遗忘权重阈值
            max_memories: 最大记忆数量
        """
        self.similarity_threshold = similarity_threshold
        self.forget_weight_threshold = forget_weight_threshold
        self.max_memories = max_memories
        
        self.clusterer = MemoryClusterer(similarity_threshold)
        self.conflict_manager = MemoryConflictManager()
        self.weight_calculator = MemoryWeightCalculator()
    
    def consolidate(
        self,
        memories: List[WeightedMemory],
    ) -> ConsolidationResult:
        """
        执行记忆巩固
        
        流程：
        1. 更新所有记忆的权重
        2. 聚类相似记忆
        3. 合并簇内冲突
        4. 强化重要记忆
        5. 遗忘不重要记忆
        6. 提取知识模式
        
        Args:
            memories: 记忆列表
        
        Returns:
            巩固结果
        """
        start_time = time.time()
        
        # 1. 更新权重
        for memory in memories:
            self.weight_calculator.update_memory_weight(memory)
        
        # 2. 聚类
        clusters = self.clusterer.cluster(memories)
        
        # 3. 处理每个簇
        retained = []
        reinforced = []
        merged = []
        forgotten = []
        archived = []
        
        # 处理聚类后的记忆
        clustered_ids = set()
        for cluster in clusters:
            clustered_ids.update(m.memory_id for m in cluster.memories)
            
            # 合并簇内冲突
            merged_memory = self._merge_cluster(cluster)
            if merged_memory:
                merged.append(merged_memory)
            else:
                retained.extend(cluster.memories)
        
        # 处理未聚类的记忆
        unclustered = [m for m in memories if m.memory_id not in clustered_ids]
        
        for memory in unclustered:
            if MemoryReinforcer.should_reinforce(memory):
                reinforced_memory = MemoryReinforcer.reinforce(memory)
                reinforced.append(reinforced_memory)
            elif MemoryForgetter.should_forget(memory, self.forget_weight_threshold):
                forgotten.append(memory)
            else:
                retained.append(memory)
        
        # 4. 遗忘检查
        if len(retained) + len(reinforced) + len(merged) > self.max_memories:
            retained, extra_forgotten = MemoryForgetter.forget(
                retained,
                max_keep=self.max_memories - len(reinforced) - len(merged),
            )
            forgotten.extend(extra_forgotten)
        
        # 5. 提取知识模式
        all_active = retained + reinforced + merged
        patterns = PatternExtractor.extract(all_active)
        
        # 构建结果
        result = ConsolidationResult(
            retained=retained,
            reinforced=reinforced,
            merged=merged,
            forgotten=forgotten,
            archived=archived,
            patterns=patterns,
            stats={
                "input_count": len(memories),
                "cluster_count": len(clusters),
                "elapsed_ms": (time.time() - start_time) * 1000,
            },
        )
        
        return result
    
    def _merge_cluster(self, cluster: MemoryCluster) -> Optional[WeightedMemory]:
        """合并簇内的记忆"""
        if len(cluster.memories) < 2:
            return None
        
        # 选择代表性记忆作为基础
        base = cluster.representative or cluster.memories[0]
        
        # 合并其他记忆
        merged_content = dict(base.content) if isinstance(base.content, dict) else base.content
        
        for memory in cluster.memories:
            if memory.memory_id == base.memory_id:
                continue
            
            if isinstance(memory.content, dict) and isinstance(merged_content, dict):
                # 解决冲突并合并
                for key, value in memory.content.items():
                    if key in merged_content and merged_content[key] != value:
                        # 使用冲突解决器
                        resolution = resolve_memory_conflict(
                            WeightedMemory(
                                memory_id="temp",
                                content={key: merged_content[key]},
                                timestamp=base.timestamp,
                                source=base.source,
                            ),
                            WeightedMemory(
                                memory_id="temp2",
                                content={key: value},
                                timestamp=memory.timestamp,
                                source=memory.source,
                            ),
                            key,
                        )
                        
                        if resolution.merged_value is not None:
                            merged_content[key] = resolution.merged_value
                        elif resolution.winner:
                            merged_content[key] = resolution.winner.content.get(key, value)
                    else:
                        merged_content[key] = value
        
        # 创建合并后的记忆
        return WeightedMemory(
            memory_id=f"merged_{cluster.cluster_id}",
            content=merged_content,
            timestamp=time.time(),
            source=MemorySource.SYSTEM_OUTPUT,
            base_importance=cluster.avg_weight,
            tags=cluster.keywords,
        )


# 便捷函数
def consolidate_memories(
    memories: List[WeightedMemory],
    max_memories: int = 1000,
) -> ConsolidationResult:
    """
    巩固记忆的便捷函数
    
    Args:
        memories: 记忆列表
        max_memories: 最大记忆数量
    
    Returns:
        巩固结果
    """
    consolidator = MemoryConsolidator(max_memories=max_memories)
    return consolidator.consolidate(memories)


# 导入便捷函数
from opspilot.memory.conflict import resolve_memory_conflict

