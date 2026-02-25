"""
记忆冲突检测与解决模块 - Memory Conflict Resolution

检测和处理记忆冲突，保证信息一致性。

核心功能：
1. 冲突检测（值冲突、时间冲突、来源冲突）
2. 冲突分类
3. 冲突解决策略
4. 历史轨迹保留
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from opspilot.memory.weight import (
    WeightedMemory,
    MemorySource,
    SourceCredibility,
)


class ConflictType(Enum):
    """冲突类型"""
    VALUE_UPDATE = "value_update"              # 值更新（正常的数据变化）
    VALUE_CONTRADICTION = "value_contradiction"  # 值矛盾（同一时间不同值）
    SOURCE_CONFLICT = "source_conflict"        # 来源冲突（不同来源不同值）
    TEMPORAL_CONFLICT = "temporal_conflict"    # 时间冲突（时序矛盾）
    SCHEMA_CONFLICT = "schema_conflict"        # 结构冲突（字段不兼容）
    SEMANTIC_CONFLICT = "semantic_conflict"    # 语义冲突（含义矛盾）


class ResolutionStrategy(Enum):
    """解决策略"""
    TAKE_NEWEST = "take_newest"                # 取最新
    TAKE_OLDEST = "take_oldest"                # 取最早
    TAKE_MOST_CREDIBLE = "take_most_credible"  # 取最可信
    TAKE_HIGHEST_WEIGHT = "take_highest_weight"  # 取最高权重
    MERGE = "merge"                            # 合并
    KEEP_BOTH = "keep_both"                    # 保留两者
    ASK_USER = "ask_user"                      # 询问用户
    CALCULATE_AVERAGE = "calculate_average"    # 计算平均值
    TAKE_MAX = "take_max"                      # 取最大值
    TAKE_MIN = "take_min"                      # 取最小值


@dataclass
class MemoryHistory:
    """记忆历史记录"""
    old_value: Any
    new_value: Any
    change_reason: str
    timestamp: float = field(default_factory=time.time)
    source: Optional[MemorySource] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "old_value": self.old_value,
            "new_value": self.new_value,
            "change_reason": self.change_reason,
            "timestamp": self.timestamp,
            "source": self.source.value if self.source else None,
        }


@dataclass
class ConflictDetection:
    """冲突检测结果"""
    has_conflict: bool
    conflict_type: Optional[ConflictType]
    conflict_field: Optional[str]
    old_value: Any
    new_value: Any
    similarity_score: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_conflict": self.has_conflict,
            "conflict_type": self.conflict_type.value if self.conflict_type else None,
            "conflict_field": self.conflict_field,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "similarity_score": self.similarity_score,
            "details": self.details,
        }


@dataclass
class ConflictResolution:
    """冲突解决结果"""
    strategy: ResolutionStrategy
    winner: Optional[WeightedMemory]
    loser: Optional[WeightedMemory]
    merged_value: Optional[Any] = None
    confidence: float = 1.0
    history: Optional[MemoryHistory] = None
    message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy.value,
            "winner_id": self.winner.memory_id if self.winner else None,
            "loser_id": self.loser.memory_id if self.loser else None,
            "merged_value": self.merged_value,
            "confidence": self.confidence,
            "message": self.message,
        }


class ConflictDetector:
    """
    冲突检测器
    
    检测记忆之间的冲突。
    """
    
    # 值变化阈值（用于判断是否为值更新）
    VALUE_CHANGE_THRESHOLD = 0.1
    
    @classmethod
    def detect(
        cls,
        old_memory: WeightedMemory,
        new_memory: WeightedMemory,
        field_name: Optional[str] = None,
    ) -> ConflictDetection:
        """
        检测冲突
        
        Args:
            old_memory: 旧记忆
            new_memory: 新记忆
            field_name: 检测的字段名
        
        Returns:
            冲突检测结果
        """
        # 获取要比较的值
        old_value = cls._get_field_value(old_memory.content, field_name)
        new_value = cls._get_field_value(new_memory.content, field_name)
        
        # 如果值相同，无冲突
        if old_value == new_value:
            return ConflictDetection(
                has_conflict=False,
                conflict_type=None,
                conflict_field=field_name,
                old_value=old_value,
                new_value=new_value,
            )
        
        # 检测冲突类型
        conflict_type = cls._classify_conflict(
            old_memory, new_memory, old_value, new_value
        )
        
        # 计算相似度
        similarity = cls._calculate_similarity(old_value, new_value)
        
        return ConflictDetection(
            has_conflict=True,
            conflict_type=conflict_type,
            conflict_field=field_name,
            old_value=old_value,
            new_value=new_value,
            similarity_score=similarity,
            details={
                "old_timestamp": old_memory.timestamp,
                "new_timestamp": new_memory.timestamp,
                "old_source": old_memory.source.value,
                "new_source": new_memory.source.value,
                "old_weight": old_memory.weight,
                "new_weight": new_memory.weight,
            },
        )
    
    @classmethod
    def _get_field_value(cls, content: Any, field_name: Optional[str]) -> Any:
        """获取字段值"""
        if field_name is None:
            return content
        
        if isinstance(content, dict):
            return content.get(field_name)
        
        return content
    
    @classmethod
    def _classify_conflict(
        cls,
        old_memory: WeightedMemory,
        new_memory: WeightedMemory,
        old_value: Any,
        new_value: Any,
    ) -> ConflictType:
        """分类冲突类型"""
        # 检查是否为值更新（时间顺序正常）
        if new_memory.timestamp > old_memory.timestamp:
            # 检查是否为正常更新
            if cls._is_value_update(old_value, new_value):
                return ConflictType.VALUE_UPDATE
            else:
                return ConflictType.VALUE_CONTRADICTION
        
        # 时间顺序异常
        if new_memory.timestamp < old_memory.timestamp:
            return ConflictType.TEMPORAL_CONFLICT
        
        # 同一时间，不同来源
        if old_memory.source != new_memory.source:
            return ConflictType.SOURCE_CONFLICT
        
        # 默认为值矛盾
        return ConflictType.VALUE_CONTRADICTION
    
    @classmethod
    def _is_value_update(cls, old_value: Any, new_value: Any) -> bool:
        """判断是否为正常的值更新"""
        # 数值类型：检查变化幅度
        if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
            if old_value == 0:
                return True
            change = abs(new_value - old_value) / abs(old_value)
            return change < 0.5  # 变化小于50%视为正常更新
        
        # 字符串类型：检查相似度
        if isinstance(old_value, str) and isinstance(new_value, str):
            similarity = cls._calculate_similarity(old_value, new_value)
            return similarity > 0.3  # 相似度大于30%视为正常更新
        
        # 其他类型：假设为正常更新
        return True
    
    @classmethod
    def _calculate_similarity(cls, value1: Any, value2: Any) -> float:
        """计算相似度"""
        # 相同
        if value1 == value2:
            return 1.0
        
        # 数值
        if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
            if value1 == 0 and value2 == 0:
                return 1.0
            max_val = max(abs(value1), abs(value2))
            if max_val == 0:
                return 1.0
            diff = abs(value1 - value2)
            return max(0, 1 - diff / max_val)
        
        # 字符串
        if isinstance(value1, str) and isinstance(value2, str):
            # 简单的字符级相似度
            set1 = set(value1)
            set2 = set(value2)
            if not set1 and not set2:
                return 1.0
            intersection = len(set1 & set2)
            union = len(set1 | set2)
            return intersection / union if union > 0 else 0.0
        
        # 类型不同
        return 0.0


class ConflictResolver:
    """
    冲突解决器
    
    根据策略解决记忆冲突。
    
    示例:
        >>> resolver = ConflictResolver()
        >>> resolution = resolver.resolve(old_memory, new_memory, detection)
    """
    
    # 默认策略映射
    DEFAULT_STRATEGIES = {
        ConflictType.VALUE_UPDATE: ResolutionStrategy.TAKE_NEWEST,
        ConflictType.VALUE_CONTRADICTION: ResolutionStrategy.TAKE_MOST_CREDIBLE,
        ConflictType.SOURCE_CONFLICT: ResolutionStrategy.TAKE_MOST_CREDIBLE,
        ConflictType.TEMPORAL_CONFLICT: ResolutionStrategy.TAKE_NEWEST,
        ConflictType.SCHEMA_CONFLICT: ResolutionStrategy.MERGE,
        ConflictType.SEMANTIC_CONFLICT: ResolutionStrategy.ASK_USER,
    }
    
    def __init__(
        self,
        custom_strategies: Optional[Dict[ConflictType, ResolutionStrategy]] = None,
    ):
        """
        初始化解决器
        
        Args:
            custom_strategies: 自定义策略
        """
        self.strategies = {**self.DEFAULT_STRATEGIES}
        if custom_strategies:
            self.strategies.update(custom_strategies)
    
    def resolve(
        self,
        old_memory: WeightedMemory,
        new_memory: WeightedMemory,
        detection: ConflictDetection,
        strategy: Optional[ResolutionStrategy] = None,
    ) -> ConflictResolution:
        """
        解决冲突
        
        Args:
            old_memory: 旧记忆
            new_memory: 新记忆
            detection: 冲突检测结果
            strategy: 指定策略（可选）
        
        Returns:
            冲突解决结果
        """
        if not detection.has_conflict:
            return ConflictResolution(
                strategy=ResolutionStrategy.TAKE_NEWEST,
                winner=new_memory,
                loser=None,
                message="无冲突，直接使用新记忆",
            )
        
        # 选择策略
        if strategy is None:
            strategy = self.strategies.get(
                detection.conflict_type,
                ResolutionStrategy.TAKE_NEWEST,
            )
        
        # 执行策略
        return self._execute_strategy(
            strategy, old_memory, new_memory, detection
        )
    
    def _execute_strategy(
        self,
        strategy: ResolutionStrategy,
        old_memory: WeightedMemory,
        new_memory: WeightedMemory,
        detection: ConflictDetection,
    ) -> ConflictResolution:
        """执行解决策略"""
        if strategy == ResolutionStrategy.TAKE_NEWEST:
            return self._take_newest(old_memory, new_memory, detection)
        
        elif strategy == ResolutionStrategy.TAKE_OLDEST:
            return self._take_oldest(old_memory, new_memory, detection)
        
        elif strategy == ResolutionStrategy.TAKE_MOST_CREDIBLE:
            return self._take_most_credible(old_memory, new_memory, detection)
        
        elif strategy == ResolutionStrategy.TAKE_HIGHEST_WEIGHT:
            return self._take_highest_weight(old_memory, new_memory, detection)
        
        elif strategy == ResolutionStrategy.MERGE:
            return self._merge(old_memory, new_memory, detection)
        
        elif strategy == ResolutionStrategy.KEEP_BOTH:
            return self._keep_both(old_memory, new_memory, detection)
        
        elif strategy == ResolutionStrategy.CALCULATE_AVERAGE:
            return self._calculate_average(old_memory, new_memory, detection)
        
        else:
            # 默认取最新
            return self._take_newest(old_memory, new_memory, detection)
    
    def _take_newest(
        self,
        old_memory: WeightedMemory,
        new_memory: WeightedMemory,
        detection: ConflictDetection,
    ) -> ConflictResolution:
        """取最新"""
        if new_memory.timestamp >= old_memory.timestamp:
            winner, loser = new_memory, old_memory
        else:
            winner, loser = old_memory, new_memory
        
        return ConflictResolution(
            strategy=ResolutionStrategy.TAKE_NEWEST,
            winner=winner,
            loser=loser,
            confidence=0.8,
            history=MemoryHistory(
                old_value=detection.old_value,
                new_value=detection.new_value,
                change_reason="take_newest",
                source=new_memory.source,
            ),
            message=f"选择时间戳较新的记忆: {winner.memory_id}",
        )
    
    def _take_oldest(
        self,
        old_memory: WeightedMemory,
        new_memory: WeightedMemory,
        detection: ConflictDetection,
    ) -> ConflictResolution:
        """取最早"""
        if old_memory.timestamp <= new_memory.timestamp:
            winner, loser = old_memory, new_memory
        else:
            winner, loser = new_memory, old_memory
        
        return ConflictResolution(
            strategy=ResolutionStrategy.TAKE_OLDEST,
            winner=winner,
            loser=loser,
            confidence=0.7,
            message=f"选择时间戳较早的记忆: {winner.memory_id}",
        )
    
    def _take_most_credible(
        self,
        old_memory: WeightedMemory,
        new_memory: WeightedMemory,
        detection: ConflictDetection,
    ) -> ConflictResolution:
        """取最可信"""
        old_cred = SourceCredibility.get_default(old_memory.source).credibility
        new_cred = SourceCredibility.get_default(new_memory.source).credibility
        
        if new_cred >= old_cred:
            winner, loser = new_memory, old_memory
        else:
            winner, loser = old_memory, new_memory
        
        confidence = abs(new_cred - old_cred) / max(new_cred, old_cred)
        
        return ConflictResolution(
            strategy=ResolutionStrategy.TAKE_MOST_CREDIBLE,
            winner=winner,
            loser=loser,
            confidence=confidence,
            history=MemoryHistory(
                old_value=detection.old_value,
                new_value=detection.new_value,
                change_reason="take_most_credible",
                source=winner.source,
            ),
            message=f"选择来源可信度更高的记忆: {winner.source.value}",
        )
    
    def _take_highest_weight(
        self,
        old_memory: WeightedMemory,
        new_memory: WeightedMemory,
        detection: ConflictDetection,
    ) -> ConflictResolution:
        """取最高权重"""
        if new_memory.weight >= old_memory.weight:
            winner, loser = new_memory, old_memory
        else:
            winner, loser = old_memory, new_memory
        
        confidence = abs(new_memory.weight - old_memory.weight)
        
        return ConflictResolution(
            strategy=ResolutionStrategy.TAKE_HIGHEST_WEIGHT,
            winner=winner,
            loser=loser,
            confidence=confidence,
            message=f"选择权重更高的记忆: {winner.weight:.2f}",
        )
    
    def _merge(
        self,
        old_memory: WeightedMemory,
        new_memory: WeightedMemory,
        detection: ConflictDetection,
    ) -> ConflictResolution:
        """合并"""
        merged_value = self._merge_values(
            detection.old_value,
            detection.new_value,
            old_memory,
            new_memory,
        )
        
        return ConflictResolution(
            strategy=ResolutionStrategy.MERGE,
            winner=None,
            loser=None,
            merged_value=merged_value,
            confidence=0.6,
            message="合并两个记忆的值",
        )
    
    def _merge_values(
        self,
        old_value: Any,
        new_value: Any,
        old_memory: WeightedMemory,
        new_memory: WeightedMemory,
    ) -> Any:
        """合并值"""
        # 字典合并
        if isinstance(old_value, dict) and isinstance(new_value, dict):
            merged = {**old_value}
            merged.update(new_value)
            return merged
        
        # 列表合并
        if isinstance(old_value, list) and isinstance(new_value, list):
            return old_value + new_value
        
        # 数值加权平均
        if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
            total_weight = old_memory.weight + new_memory.weight
            if total_weight > 0:
                return (
                    old_value * old_memory.weight +
                    new_value * new_memory.weight
                ) / total_weight
            return (old_value + new_value) / 2
        
        # 字符串拼接
        if isinstance(old_value, str) and isinstance(new_value, str):
            if old_value == new_value:
                return old_value
            return f"{old_value}; {new_value}"
        
        # 默认取新值
        return new_value
    
    def _keep_both(
        self,
        old_memory: WeightedMemory,
        new_memory: WeightedMemory,
        detection: ConflictDetection,
    ) -> ConflictResolution:
        """保留两者"""
        return ConflictResolution(
            strategy=ResolutionStrategy.KEEP_BOTH,
            winner=None,
            loser=None,
            merged_value={
                "old": {"value": detection.old_value, "source": old_memory.source.value},
                "new": {"value": detection.new_value, "source": new_memory.source.value},
            },
            confidence=0.5,
            message="保留两个记忆的值",
        )
    
    def _calculate_average(
        self,
        old_memory: WeightedMemory,
        new_memory: WeightedMemory,
        detection: ConflictDetection,
    ) -> ConflictResolution:
        """计算平均值"""
        old_val = detection.old_value
        new_val = detection.new_value
        
        if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
            avg = (old_val + new_val) / 2
            return ConflictResolution(
                strategy=ResolutionStrategy.CALCULATE_AVERAGE,
                winner=None,
                loser=None,
                merged_value=avg,
                confidence=0.7,
                message=f"计算平均值: {avg}",
            )
        
        # 非数值类型，退化为取新值
        return self._take_newest(old_memory, new_memory, detection)


class MemoryConflictManager:
    """
    记忆冲突管理器
    
    整合检测和解决，提供完整的冲突处理流程。
    """
    
    def __init__(
        self,
        custom_strategies: Optional[Dict[ConflictType, ResolutionStrategy]] = None,
    ):
        """
        初始化管理器
        
        Args:
            custom_strategies: 自定义解决策略
        """
        self.detector = ConflictDetector()
        self.resolver = ConflictResolver(custom_strategies)
        
        # 冲突历史
        self.conflict_history: List[Dict[str, Any]] = []
    
    def process(
        self,
        old_memory: WeightedMemory,
        new_memory: WeightedMemory,
        field_name: Optional[str] = None,
        strategy: Optional[ResolutionStrategy] = None,
    ) -> ConflictResolution:
        """
        处理记忆冲突
        
        Args:
            old_memory: 旧记忆
            new_memory: 新记忆
            field_name: 检测的字段名
            strategy: 指定解决策略
        
        Returns:
            冲突解决结果
        """
        # 检测冲突
        detection = self.detector.detect(old_memory, new_memory, field_name)
        
        # 解决冲突
        resolution = self.resolver.resolve(
            old_memory, new_memory, detection, strategy
        )
        
        # 记录历史
        self._record_conflict(old_memory, new_memory, detection, resolution)
        
        return resolution
    
    def _record_conflict(
        self,
        old_memory: WeightedMemory,
        new_memory: WeightedMemory,
        detection: ConflictDetection,
        resolution: ConflictResolution,
    ) -> None:
        """记录冲突历史"""
        self.conflict_history.append({
            "timestamp": time.time(),
            "old_memory_id": old_memory.memory_id,
            "new_memory_id": new_memory.memory_id,
            "detection": detection.to_dict(),
            "resolution": resolution.to_dict(),
        })
    
    def get_conflict_stats(self) -> Dict[str, Any]:
        """获取冲突统计"""
        if not self.conflict_history:
            return {"total": 0}
        
        # 按类型统计
        type_counts: Dict[str, int] = {}
        strategy_counts: Dict[str, int] = {}
        
        for record in self.conflict_history:
            conflict_type = record["detection"].get("conflict_type")
            if conflict_type:
                type_counts[conflict_type] = type_counts.get(conflict_type, 0) + 1
            
            strategy = record["resolution"].get("strategy")
            if strategy:
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        return {
            "total": len(self.conflict_history),
            "by_type": type_counts,
            "by_strategy": strategy_counts,
        }
    
    def clear_history(self) -> None:
        """清空历史"""
        self.conflict_history.clear()


# 便捷函数
def resolve_memory_conflict(
    old_memory: WeightedMemory,
    new_memory: WeightedMemory,
    field_name: Optional[str] = None,
) -> ConflictResolution:
    """
    解决记忆冲突的便捷函数
    
    Args:
        old_memory: 旧记忆
        new_memory: 新记忆
        field_name: 检测的字段名
    
    Returns:
        冲突解决结果
    """
    manager = MemoryConflictManager()
    return manager.process(old_memory, new_memory, field_name)

