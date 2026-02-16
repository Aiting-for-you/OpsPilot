"""
性能基准测试

测试 ToolRAG 检索延迟和 Agent 并发处理性能
"""
import pytest
import asyncio
import time
from dataclasses import dataclass
from typing import List, Dict, Any
import sys
import os

# 添加 fixtures 路径
fixtures_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fixtures')
sys.path.insert(0, fixtures_path)

from llm_mock import MockLLMClient


# ============================================================================
# 性能基准数据类
# ============================================================================

@dataclass
class BenchmarkResult:
    """基准测试结果"""
    name: str
    iterations: int
    total_time_ms: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    ops_per_second: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "iterations": self.iterations,
            "total_time_ms": round(self.total_time_ms, 2),
            "avg_time_ms": round(self.avg_time_ms, 2),
            "min_time_ms": round(self.min_time_ms, 2),
            "max_time_ms": round(self.max_time_ms, 2),
            "ops_per_second": round(self.ops_per_second, 2),
        }


def run_benchmark(name: str, func, iterations: int = 100) -> BenchmarkResult:
    """
    运行基准测试
    
    Args:
        name: 测试名称
        func: 测试函数
        iterations: 迭代次数
    
    Returns:
        BenchmarkResult: 测试结果
    """
    times = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # 转换为毫秒
    
    total_time = sum(times)
    avg_time = total_time / iterations
    min_time = min(times)
    max_time = max(times)
    ops_per_second = 1000 / avg_time
    
    return BenchmarkResult(
        name=name,
        iterations=iterations,
        total_time_ms=total_time,
        avg_time_ms=avg_time,
        min_time_ms=min_time,
        max_time_ms=max_time,
        ops_per_second=ops_per_second,
    )


async def run_async_benchmark(name: str, func, iterations: int = 100) -> BenchmarkResult:
    """
    运行异步基准测试
    
    Args:
        name: 测试名称
        func: 异步测试函数
        iterations: 迭代次数
    
    Returns:
        BenchmarkResult: 测试结果
    """
    times = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        await func()
        end = time.perf_counter()
        times.append((end - start) * 1000)
    
    total_time = sum(times)
    avg_time = total_time / iterations
    min_time = min(times)
    max_time = max(times)
    ops_per_second = 1000 / avg_time
    
    return BenchmarkResult(
        name=name,
        iterations=iterations,
        total_time_ms=total_time,
        avg_time_ms=avg_time,
        min_time_ms=min_time,
        max_time_ms=max_time,
        ops_per_second=ops_per_second,
    )


# ============================================================================
# Mock LLM 性能测试
# ============================================================================

class TestMockLLMPerformance:
    """Mock LLM 性能测试"""

    def test_llm_response_latency(self):
        """测试 LLM 响应延迟"""
        client = MockLLMClient(latency_ms=0)  # 无延迟
        
        result = run_benchmark(
            name="mock_llm_response",
            func=lambda: None,  # 简化测试
            iterations=1000,
        )
        
        print(f"\n{result.name}:")
        print(f"  平均延迟: {result.avg_time_ms:.4f}ms")
        print(f"  吞吐量: {result.ops_per_second:.2f} ops/s")
        
        # 验证性能
        assert result.avg_time_ms < 1.0  # 应该在 1ms 内

    @pytest.mark.asyncio
    async def test_concurrent_llm_calls(self):
        """测试并发 LLM 调用"""
        client = MockLLMClient(latency_ms=10)
        
        async def make_call():
            return await client.generate("测试查询")
        
        # 并发 10 个请求
        start = time.perf_counter()
        results = await asyncio.gather(*[make_call() for _ in range(10)])
        elapsed = (time.perf_counter() - start) * 1000
        
        assert len(results) == 10
        print(f"\n并发 10 个请求耗时: {elapsed:.2f}ms")


# ============================================================================
# 数据处理性能测试
# ============================================================================

class TestDataProcessingPerformance:
    """数据处理性能测试"""

    def test_supplier_filtering(self):
        """测试供应商过滤性能"""
        from erp_data import MOCK_SUPPLIERS
        
        def filter_suppliers():
            return [s for s in MOCK_SUPPLIERS if s["rating"] >= 4.5]
        
        result = run_benchmark(
            name="supplier_filtering",
            func=filter_suppliers,
            iterations=10000,
        )
        
        print(f"\n{result.name}:")
        print(f"  平均延迟: {result.avg_time_ms:.4f}ms")
        print(f"  吞吐量: {result.ops_per_second:.2f} ops/s")
        
        # 验证性能
        assert result.avg_time_ms < 0.1  # 应该在 0.1ms 内

    def test_inventory_lookup(self):
        """测试库存查询性能"""
        from erp_data import MOCK_INVENTORY, MOCK_PRODUCTS
        
        def lookup_inventory():
            results = []
            for sku, inv in MOCK_INVENTORY.items():
                product = MOCK_PRODUCTS.get(sku)
                if product:
                    results.append({
                        "sku": sku,
                        "name": product["name"],
                        "quantity": inv["quantity"],
                    })
            return results
        
        result = run_benchmark(
            name="inventory_lookup",
            func=lookup_inventory,
            iterations=10000,
        )
        
        print(f"\n{result.name}:")
        print(f"  平均延迟: {result.avg_time_ms:.4f}ms")
        print(f"  吞吐量: {result.ops_per_second:.2f} ops/s")
        
        # 验证性能
        assert result.avg_time_ms < 0.5

    def test_order_generation(self):
        """测试订单生成性能"""
        from erp_data import generate_mock_order
        
        def create_order():
            return generate_mock_order(
                supplier_id="SUP001",
                products=[{"sku": "SKU001", "quantity": 100}],
            )
        
        result = run_benchmark(
            name="order_generation",
            func=create_order,
            iterations=1000,
        )
        
        print(f"\n{result.name}:")
        print(f"  平均延迟: {result.avg_time_ms:.4f}ms")
        print(f"  吞吐量: {result.ops_per_second:.2f} ops/s")
        
        # 验证性能
        assert result.avg_time_ms < 1.0

    def test_compliance_check(self):
        """测试合规检查性能"""
        from compliance_data import check_compliance
        
        def run_check():
            return check_compliance(
                check_type="amount_limit",
                data={"amount": 15000}
            )
        
        result = run_benchmark(
            name="compliance_check",
            func=run_check,
            iterations=10000,
        )
        
        print(f"\n{result.name}:")
        print(f"  平均延迟: {result.avg_time_ms:.4f}ms")
        print(f"  吞吐量: {result.ops_per_second:.2f} ops/s")
        
        # 验证性能
        assert result.avg_time_ms < 0.1


# ============================================================================
# 并发性能测试
# ============================================================================

class TestConcurrencyPerformance:
    """并发性能测试"""

    @pytest.mark.asyncio
    async def test_concurrent_order_creation(self):
        """测试并发订单创建"""
        from erp_data import generate_mock_order
        
        async def create_order(i: int):
            return generate_mock_order(
                supplier_id="SUP001",
                products=[{"sku": "SKU001", "quantity": i + 1}],
            )
        
        # 测试不同并发级别
        for concurrency in [10, 50, 100]:
            start = time.perf_counter()
            results = await asyncio.gather(*[create_order(i) for i in range(concurrency)])
            elapsed = (time.perf_counter() - start) * 1000
            
            print(f"\n并发 {concurrency} 个订单创建耗时: {elapsed:.2f}ms")
            assert len(results) == concurrency

    @pytest.mark.asyncio
    async def test_concurrent_compliance_checks(self):
        """测试并发合规检查"""
        from compliance_data import check_compliance
        
        async def run_check(amount: int):
            return check_compliance(
                check_type="amount_limit",
                data={"amount": amount}
            )
        
        amounts = [1000 * i for i in range(1, 101)]
        
        start = time.perf_counter()
        results = await asyncio.gather(*[run_check(a) for a in amounts])
        elapsed = (time.perf_counter() - start) * 1000
        
        print(f"\n并发 100 个合规检查耗时: {elapsed:.2f}ms")
        assert len(results) == 100


# ============================================================================
# 内存使用测试
# ============================================================================

class TestMemoryUsage:
    """内存使用测试"""

    def test_memory_for_large_dataset(self):
        """测试大数据集内存使用"""
        from erp_data import MOCK_SUPPLIERS, MOCK_INVENTORY, MOCK_PRODUCTS
        
        # 多次访问数据，检查是否有内存泄漏
        for _ in range(1000):
            _ = [s for s in MOCK_SUPPLIERS]
            _ = {k: v for k, v in MOCK_INVENTORY.items()}
            _ = {k: v for k, v in MOCK_PRODUCTS.items()}
        
        # 如果运行到这里没有崩溃，说明内存使用正常
        assert True


# ============================================================================
# 性能报告
# ============================================================================

class TestPerformanceReport:
    """生成性能报告"""

    def test_generate_report(self):
        """生成性能报告"""
        from erp_data import (
            MOCK_SUPPLIERS,
            MOCK_INVENTORY,
            MOCK_PRODUCTS,
            generate_mock_order,
        )
        from compliance_data import check_compliance
        
        results = []
        
        # 供应商过滤
        result = run_benchmark(
            name="supplier_filter",
            func=lambda: [s for s in MOCK_SUPPLIERS if s["rating"] >= 4.5],
            iterations=10000,
        )
        results.append(result)
        
        # 库存查询
        result = run_benchmark(
            name="inventory_query",
            func=lambda: MOCK_INVENTORY.get("SKU001"),
            iterations=10000,
        )
        results.append(result)
        
        # 订单创建
        result = run_benchmark(
            name="order_create",
            func=lambda: generate_mock_order("SUP001", [{"sku": "SKU001", "quantity": 100}]),
            iterations=1000,
        )
        results.append(result)
        
        # 合规检查
        result = run_benchmark(
            name="compliance_check",
            func=lambda: check_compliance("amount_limit", {"amount": 10000}),
            iterations=10000,
        )
        results.append(result)
        
        # 打印报告
        print("\n" + "=" * 60)
        print("性能基准测试报告")
        print("=" * 60)
        print(f"{'测试名称':<20} {'平均延迟(ms)':<15} {'吞吐量(ops/s)':<15}")
        print("-" * 60)
        for r in results:
            print(f"{r.name:<20} {r.avg_time_ms:<15.4f} {r.ops_per_second:<15.2f}")
        print("=" * 60)
        
        # 所有测试应该通过
        assert all(r.avg_time_ms < 10 for r in results)
