"""
基准测试运行器

提供统一的基准测试框架
"""

from __future__ import annotations

import asyncio
import json
import logging
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    name: str
    iterations: int
    total_time: float
    min_time: float
    max_time: float
    mean_time: float
    median_time: float
    p95_time: float
    p99_time: float
    ops_per_second: float
    errors: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_samples(
        cls,
        name: str,
        samples: List[float],
        errors: int = 0,
        metadata: Dict = None,
    ) -> "BenchmarkResult":
        """从样本创建结果"""
        if not samples:
            return cls(
                name=name,
                iterations=0,
                total_time=0,
                min_time=0,
                max_time=0,
                mean_time=0,
                median_time=0,
                p95_time=0,
                p99_time=0,
                ops_per_second=0,
                errors=errors,
                metadata=metadata or {},
            )
        
        sorted_samples = sorted(samples)
        n = len(sorted_samples)
        
        return cls(
            name=name,
            iterations=n,
            total_time=sum(samples),
            min_time=sorted_samples[0],
            max_time=sorted_samples[-1],
            mean_time=statistics.mean(samples),
            median_time=statistics.median(samples),
            p95_time=sorted_samples[int(n * 0.95)] if n > 0 else 0,
            p99_time=sorted_samples[int(n * 0.99)] if n > 0 else 0,
            ops_per_second=n / sum(samples) if sum(samples) > 0 else 0,
            errors=errors,
            metadata=metadata or {},
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "total_time": round(self.total_time, 4),
            "min_time": round(self.min_time, 4),
            "max_time": round(self.max_time, 4),
            "mean_time": round(self.mean_time, 4),
            "median_time": round(self.median_time, 4),
            "p95_time": round(self.p95_time, 4),
            "p99_time": round(self.p99_time, 4),
            "ops_per_second": round(self.ops_per_second, 2),
            "errors": self.errors,
            "metadata": self.metadata,
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        return (
            f"{self.name}:\n"
            f"  Iterations: {self.iterations}\n"
            f"  Mean: {self.mean_time:.4f}s\n"
            f"  Median: {self.median_time:.4f}s\n"
            f"  P95: {self.p95_time:.4f}s\n"
            f"  P99: {self.p99_time:.4f}s\n"
            f"  Ops/s: {self.ops_per_second:.2f}\n"
            f"  Errors: {self.errors}"
        )


class BenchmarkRunner:
    """
    基准测试运行器
    
    使用示例:
    ```python
    runner = BenchmarkRunner()
    
    # 运行单个基准测试
    result = await runner.run(
        name="tool_retrieval",
        func=retrieve_tools,
        iterations=100,
        args={"query": "查询供应商"},
    )
    
    # 运行多个基准测试
    results = await runner.run_all([
        ("tool_retrieval", retrieve_tools, {"query": "test"}),
        ("memory_search", search_memory, {"query": "test"}),
    ])
    
    # 生成报告
    runner.generate_report("benchmark_report.json")
    ```
    """
    
    def __init__(self, output_dir: str = "./benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._results: List[BenchmarkResult] = []
    
    async def run(
        self,
        name: str,
        func: Callable,
        iterations: int = 100,
        warmup: int = 5,
        args: Dict[str, Any] = None,
        kwargs: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
    ) -> BenchmarkResult:
        """
        运行基准测试
        
        Args:
            name: 测试名称
            func: 测试函数（同步或异步）
            iterations: 迭代次数
            warmup: 预热次数
            args: 位置参数
            kwargs: 关键字参数
            metadata: 元数据
        
        Returns:
            BenchmarkResult
        """
        args = args or {}
        kwargs = kwargs or {}
        
        logger.info(f"Running benchmark: {name}")
        
        # 预热
        for _ in range(warmup):
            try:
                if asyncio.iscoroutinefunction(func):
                    await func(**args, **kwargs)
                else:
                    func(**args, **kwargs)
            except Exception:
                pass
        
        # 正式测试
        samples: List[float] = []
        errors = 0
        
        for _ in range(iterations):
            start = time.perf_counter()
            try:
                if asyncio.iscoroutinefunction(func):
                    await func(**args, **kwargs)
                else:
                    func(**args, **kwargs)
            except Exception as e:
                errors += 1
                logger.warning(f"Benchmark error: {e}")
            
            elapsed = time.perf_counter() - start
            samples.append(elapsed)
        
        result = BenchmarkResult.from_samples(
            name=name,
            samples=samples,
            errors=errors,
            metadata=metadata,
        )
        
        self._results.append(result)
        logger.info(f"Benchmark completed: {name}")
        
        return result
    
    async def run_all(
        self,
        tests: List[tuple],
        iterations: int = 100,
    ) -> List[BenchmarkResult]:
        """
        运行多个基准测试
        
        Args:
            tests: [(name, func, args), ...]
            iterations: 迭代次数
        
        Returns:
            结果列表
        """
        results = []
        for name, func, args in tests:
            result = await self.run(
                name=name,
                func=func,
                iterations=iterations,
                args=args,
            )
            results.append(result)
        return results
    
    def generate_report(
        self,
        filename: str = None,
        format: str = "json",
    ) -> Dict[str, Any]:
        """
        生成报告
        
        Args:
            filename: 输出文件名
            format: 输出格式 (json, markdown)
        
        Returns:
            报告数据
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self._results),
            "results": [r.to_dict() for r in self._results],
        }
        
        if filename:
            filepath = self.output_dir / filename
            
            if format == "json":
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
            elif format == "markdown":
                markdown = self._generate_markdown_report(report)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(markdown)
        
        return report
    
    def _generate_markdown_report(self, report: Dict) -> str:
        """生成Markdown报告"""
        lines = [
            "# 性能基准测试报告",
            "",
            f"**测试时间**: {report['timestamp']}",
            f"**测试数量**: {report['total_tests']}",
            "",
            "## 测试结果",
            "",
            "| 测试名称 | 迭代次数 | 平均延迟(s) | P95延迟(s) | P99延迟(s) | Ops/s | 错误数 |",
            "|----------|----------|-------------|------------|------------|-------|--------|",
        ]
        
        for r in report["results"]:
            lines.append(
                f"| {r['name']} | {r['iterations']} | "
                f"{r['mean_time']:.4f} | {r['p95_time']:.4f} | "
                f"{r['p99_time']:.4f} | {r['ops_per_second']:.2f} | {r['errors']} |"
            )
        
        return "\n".join(lines)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取摘要"""
        if not self._results:
            return {}
        
        return {
            "total_tests": len(self._results),
            "total_iterations": sum(r.iterations for r in self._results),
            "total_errors": sum(r.errors for r in self._results),
            "avg_latency": statistics.mean([r.mean_time for r in self._results]),
            "avg_ops_per_second": statistics.mean([r.ops_per_second for r in self._results]),
        }


async def run_benchmark(
    name: str,
    func: Callable,
    iterations: int = 100,
    **kwargs,
) -> BenchmarkResult:
    """
    快速运行基准测试
    
    便捷函数，不需要创建BenchmarkRunner实例
    """
    runner = BenchmarkRunner()
    return await runner.run(name, func, iterations, **kwargs)

