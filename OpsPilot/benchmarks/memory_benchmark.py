"""
记忆层基准测试

测试范围:
1. 记忆存储性能
2. 记忆检索性能
3. 记忆权重计算性能
4. 冲突检测与解决性能
5. 记忆巩固性能
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from opspilot.benchmarks.runner import BenchmarkResult, BenchmarkRunner

logger = logging.getLogger(__name__)


class MemoryBenchmark:
    """
    记忆层基准测试
    """
    
    def __init__(
        self,
        memory_store: Any = None,
        weight_calculator: Any = None,
        conflict_resolver: Any = None,
    ):
        self.memory_store = memory_store
        self.weight_calculator = weight_calculator
        self.conflict_resolver = conflict_resolver
        self._runner = BenchmarkRunner()
    
    def create_mock_memories(self, count: int = 100) -> List[Dict]:
        """创建模拟记忆"""
        memories = []
        base_time = time.time()
        
        for i in range(count):
            memories.append({
                "id": f"mem_{i}",
                "content": {
                    "type": "fact" if i % 3 == 0 else "event" if i % 3 == 1 else "knowledge",
                    "text": f"Memory content {i}: This is a sample memory entry.",
                    "metadata": {"source": "user", "session_id": f"session_{i % 10}"},
                },
                "timestamp": base_time - i * 3600,  # 每小时一个
                "weight": 0.5 + (i % 5) * 0.1,
                "access_count": i % 10,
            })
        
        return memories
    
    async def benchmark_storage(
        self,
        iterations: int = 100,
    ) -> BenchmarkResult:
        """测试记忆存储性能"""
        idx = 0
        
        async def store():
            nonlocal idx
            memory = {
                "content": f"Test memory {idx}",
                "timestamp": time.time(),
                "metadata": {"idx": idx},
            }
            idx += 1
            
            if self.memory_store:
                return await asyncio.to_thread(
                    self.memory_store.store,
                    memory,
                )
            return {"stored": True}
        
        return await self._runner.run(
            name="memory_storage",
            func=store,
            iterations=iterations,
        )
    
    async def benchmark_retrieval(
        self,
        iterations: int = 100,
    ) -> BenchmarkResult:
        """测试记忆检索性能"""
        queries = [
            "供应商信息",
            "订单状态",
            "库存水平",
            "合规要求",
            "历史记录",
        ]
        query_idx = 0
        
        async def retrieve():
            nonlocal query_idx
            query = queries[query_idx % len(queries)]
            query_idx += 1
            
            if self.memory_store:
                return await asyncio.to_thread(
                    self.memory_store.search,
                    query,
                    limit=10,
                )
            return {"memories": []}
        
        return await self._runner.run(
            name="memory_retrieval",
            func=retrieve,
            iterations=iterations,
        )
    
    async def benchmark_weight_calculation(
        self,
        iterations: int = 200,
    ) -> BenchmarkResult:
        """测试权重计算性能"""
        memories = self.create_mock_memories(50)
        mem_idx = 0
        
        async def calculate_weight():
            nonlocal mem_idx
            memory = memories[mem_idx % len(memories)]
            mem_idx += 1
            
            if self.weight_calculator:
                return self.weight_calculator.calculate(memory)
            
            # 模拟权重计算
            age_hours = (time.time() - memory["timestamp"]) / 3600
            decay = 0.9 ** age_hours
            frequency_factor = 1 + 0.1 * memory["access_count"]
            return {
                "weight": memory["weight"] * decay * frequency_factor,
                "decay": decay,
            }
        
        return await self._runner.run(
            name="weight_calculation",
            func=calculate_weight,
            iterations=iterations,
        )
    
    async def benchmark_conflict_detection(
        self,
        iterations: int = 100,
    ) -> BenchmarkResult:
        """测试冲突检测性能"""
        base_time = time.time()
        idx = 0
        
        async def detect_conflict():
            nonlocal idx
            idx += 1
            
            # 创建两个可能冲突的记忆
            old_memory = {
                "content": {"price": 10},
                "timestamp": base_time - 3600,
                "source": "user_input",
                "confidence": 0.7,
            }
            new_memory = {
                "content": {"price": 15},
                "timestamp": base_time,
                "source": "official_api",
                "confidence": 0.95,
            }
            
            if self.conflict_resolver:
                return self.conflict_resolver.detect(old_memory, new_memory)
            
            # 模拟冲突检测
            return {
                "has_conflict": True,
                "conflict_type": "value_update",
                "resolution": "use_newer",
            }
        
        return await self._runner.run(
            name="conflict_detection",
            func=detect_conflict,
            iterations=iterations,
        )
    
    async def benchmark_conflict_resolution(
        self,
        iterations: int = 100,
    ) -> BenchmarkResult:
        """测试冲突解决性能"""
        idx = 0
        
        async def resolve_conflict():
            nonlocal idx
            idx += 1
            
            # 模拟冲突解决
            await asyncio.sleep(0.001)
            
            return {
                "winner": "new_memory",
                "reason": "higher_confidence",
                "confidence": 0.95,
            }
        
        return await self._runner.run(
            name="conflict_resolution",
            func=resolve_conflict,
            iterations=iterations,
        )
    
    async def benchmark_consolidation(
        self,
        memory_count: int = 100,
        iterations: int = 10,
    ) -> BenchmarkResult:
        """测试记忆巩固性能"""
        memories = self.create_mock_memories(memory_count)
        
        async def consolidate():
            # 模拟记忆巩固
            # 1. 聚类
            clusters = {}
            for m in memories:
                key = m["content"]["type"]
                if key not in clusters:
                    clusters[key] = []
                clusters[key].append(m)
            
            # 2. 强化/遗忘
            consolidated = []
            for cluster_memories in clusters.values():
                avg_weight = sum(m["weight"] for m in cluster_memories) / len(cluster_memories)
                if avg_weight > 0.5:
                    consolidated.extend(cluster_memories)
            
            return {"consolidated": len(consolidated)}
        
        return await self._runner.run(
            name=f"memory_consolidation_{memory_count}",
            func=consolidate,
            iterations=iterations,
            metadata={"memory_count": memory_count},
        )
    
    async def run_all(self) -> Dict[str, BenchmarkResult]:
        """运行所有记忆基准测试"""
        results = {}
        
        results["storage"] = await self.benchmark_storage()
        results["retrieval"] = await self.benchmark_retrieval()
        results["weight_calculation"] = await self.benchmark_weight_calculation()
        results["conflict_detection"] = await self.benchmark_conflict_detection()
        results["conflict_resolution"] = await self.benchmark_conflict_resolution()
        results["consolidation_100"] = await self.benchmark_consolidation(100)
        results["consolidation_500"] = await self.benchmark_consolidation(500)
        
        return results
    
    def generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        return self._runner.generate_report("memory_benchmark.json")

