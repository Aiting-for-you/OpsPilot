"""
端到端基准测试

测试范围:
1. 完整流程性能
2. 并发处理能力
3. 压力测试
4. 资源使用分析
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List

from opspilot.benchmarks.runner import BenchmarkResult, BenchmarkRunner

logger = logging.getLogger(__name__)


class E2EBenchmark:
    """
    端到端基准测试
    
    测试完整流程性能
    """
    
    def __init__(self, orchestrator: Any = None):
        self.orchestrator = orchestrator
        self._runner = BenchmarkRunner()
    
    async def benchmark_simple_query(
        self,
        iterations: int = 50,
    ) -> BenchmarkResult:
        """测试简单查询流程"""
        queries = [
            "查询供应商信息",
            "检查库存状态",
            "获取订单详情",
        ]
        idx = 0
        
        async def execute_query():
            nonlocal idx
            query = queries[idx % len(queries)]
            idx += 1
            
            if self.orchestrator:
                return await self.orchestrator.execute({"query": query})
            
            # 模拟完整流程
            # Intent
            await asyncio.sleep(0.005)
            # Plan
            await asyncio.sleep(0.003)
            # Exec
            await asyncio.sleep(0.010)
            # Verify
            await asyncio.sleep(0.002)
            
            return {"result": f"Processed: {query}"}
        
        return await self._runner.run(
            name="simple_query_e2e",
            func=execute_query,
            iterations=iterations,
        )
    
    async def benchmark_complex_workflow(
        self,
        iterations: int = 20,
    ) -> BenchmarkResult:
        """测试复杂工作流"""
        idx = 0
        
        async def execute_complex():
            nonlocal idx
            idx += 1
            
            if self.orchestrator:
                return await self.orchestrator.execute({
                    "query": f"复杂查询 {idx}",
                    "workflow": "parallel",
                })
            
            # 模拟复杂流程
            # 阶段1: 意图识别
            await asyncio.sleep(0.008)
            
            # 阶段2: 并行查询多个数据源
            tasks = [
                asyncio.sleep(0.015),  # ERP
                asyncio.sleep(0.012),  # 库存
                asyncio.sleep(0.010),  # 订单
            ]
            await asyncio.gather(*tasks)
            
            # 阶段3: 结果聚合
            await asyncio.sleep(0.005)
            
            # 阶段4: 验证
            await asyncio.sleep(0.003)
            
            return {"result": f"Complex workflow {idx}"}
        
        return await self._runner.run(
            name="complex_workflow_e2e",
            func=execute_complex,
            iterations=iterations,
        )
    
    async def benchmark_concurrent_requests(
        self,
        concurrency: int = 10,
        iterations: int = 10,
    ) -> BenchmarkResult:
        """测试并发请求处理"""
        
        async def execute_concurrent():
            if self.orchestrator:
                tasks = [
                    self.orchestrator.execute({"query": f"Concurrent query {i}"})
                    for i in range(concurrency)
                ]
                return await asyncio.gather(*tasks)
            
            # 模拟并发
            tasks = [
                asyncio.sleep(0.010)
                for _ in range(concurrency)
            ]
            await asyncio.gather(*tasks)
            return {"concurrent": concurrency}
        
        return await self._runner.run(
            name=f"concurrent_{concurrency}_requests",
            func=execute_concurrent,
            iterations=iterations,
            metadata={"concurrency": concurrency},
        )
    
    async def benchmark_with_caching(
        self,
        iterations: int = 100,
    ) -> BenchmarkResult:
        """测试缓存效果"""
        cache_hits = 0
        total = 0
        
        async def execute_with_cache():
            nonlocal cache_hits, total
            total += 1
            
            # 模拟80%的缓存命中
            if total % 5 != 0:
                cache_hits += 1
                await asyncio.sleep(0.001)  # 缓存命中，极快
            else:
                await asyncio.sleep(0.010)  # 缓存未命中，正常处理
            
            return {"cached": total % 5 != 0}
        
        result = await self._runner.run(
            name="e2e_with_caching",
            func=execute_with_cache,
            iterations=iterations,
        )
        
        result.metadata["cache_hit_rate"] = cache_hits / total if total > 0 else 0
        return result
    
    async def benchmark_idempotency(
        self,
        iterations: int = 100,
    ) -> BenchmarkResult:
        """测试幂等性开销"""
        idx = 0
        
        async def execute_idempotent():
            nonlocal idx
            idx += 1
            
            # 生成幂等性key
            key = f"idempotent_{idx % 10}"  # 模拟10%重复
            
            # 检查缓存
            await asyncio.sleep(0.0005)
            
            if idx % 10 == 0:
                # 缓存命中
                return {"cached": True}
            
            # 正常处理
            await asyncio.sleep(0.010)
            
            # 存储结果
            await asyncio.sleep(0.0005)
            
            return {"cached": False}
        
        return await self._runner.run(
            name="e2e_idempotency",
            func=execute_idempotent,
            iterations=iterations,
        )
    
    async def stress_test(
        self,
        duration_seconds: int = 10,
        rps: int = 10,
    ) -> Dict[str, Any]:
        """
        压力测试
        
        Args:
            duration_seconds: 测试持续时间
            rps: 目标每秒请求数
        
        Returns:
            压力测试结果
        """
        logger.info(f"Starting stress test: {rps} RPS for {duration_seconds}s")
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        completed = 0
        errors = 0
        latencies: List[float] = []
        
        async def make_request():
            nonlocal completed, errors
            request_start = time.perf_counter()
            
            try:
                if self.orchestrator:
                    await self.orchestrator.execute({"query": "stress test"})
                else:
                    await asyncio.sleep(0.01)
                
                completed += 1
            except Exception as e:
                errors += 1
                logger.warning(f"Stress test error: {e}")
            
            latencies.append(time.perf_counter() - request_start)
        
        # 持续发送请求
        interval = 1.0 / rps
        
        while time.time() < end_time:
            asyncio.create_task(make_request())
            await asyncio.sleep(interval)
        
        # 等待所有请求完成
        await asyncio.sleep(1)
        
        actual_duration = time.time() - start_time
        
        return {
            "duration_seconds": actual_duration,
            "target_rps": rps,
            "actual_rps": completed / actual_duration,
            "completed": completed,
            "errors": errors,
            "error_rate": errors / (completed + errors) if (completed + errors) > 0 else 0,
            "avg_latency": sum(latencies) / len(latencies) if latencies else 0,
            "max_latency": max(latencies) if latencies else 0,
        }
    
    async def run_all(self) -> Dict[str, BenchmarkResult]:
        """运行所有端到端基准测试"""
        results = {}
        
        results["simple_query"] = await self.benchmark_simple_query()
        results["complex_workflow"] = await self.benchmark_complex_workflow()
        results["concurrent_10"] = await self.benchmark_concurrent_requests(10)
        results["concurrent_50"] = await self.benchmark_concurrent_requests(50)
        results["with_caching"] = await self.benchmark_with_caching()
        results["idempotency"] = await self.benchmark_idempotency()
        
        return results
    
    def generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        return self._runner.generate_report("e2e_benchmark.json")


async def run_full_benchmark_suite(
    orchestrator: Any = None,
    tool_indexer: Any = None,
    tool_retriever: Any = None,
    memory_store: Any = None,
) -> Dict[str, Any]:
    """
    运行完整基准测试套件
    
    Args:
        orchestrator: 编排器实例
        tool_indexer: 工具索引器
        tool_retriever: 工具检索器
        memory_store: 记忆存储
    
    Returns:
        完整测试报告
    """
    from opspilot.benchmarks.tool_benchmark import ToolBenchmark
    from opspilot.benchmarks.memory_benchmark import MemoryBenchmark
    from opspilot.benchmarks.agent_benchmark import AgentBenchmark
    
    results = {}
    
    # 工具层测试
    tool_bench = ToolBenchmark(tool_indexer, tool_retriever)
    results["tools"] = {k: v.to_dict() for k, v in (await tool_bench.run_all()).items()}
    
    # 记忆层测试
    memory_bench = MemoryBenchmark(memory_store)
    results["memory"] = {k: v.to_dict() for k, v in (await memory_bench.run_all()).items()}
    
    # Agent层测试
    agent_bench = AgentBenchmark(orchestrator)
    results["agents"] = {k: v.to_dict() for k, v in (await agent_bench.run_all()).items()}
    
    # 端到端测试
    e2e_bench = E2EBenchmark(orchestrator)
    results["e2e"] = {k: v.to_dict() for k, v in (await e2e_bench.run_all()).items()}
    
    # 压力测试
    results["stress_test"] = await e2e_bench.stress_test(duration_seconds=5, rps=20)
    
    return {
        "timestamp": time.time(),
        "results": results,
    }

