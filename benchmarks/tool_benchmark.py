"""
工具层基准测试

测试范围:
1. 工具索引构建性能
2. 工具检索性能 (ToolRAG)
3. 工具描述压缩性能
4. 工具调用性能
5. 工具自愈机制性能
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from opspilot.benchmarks.runner import BenchmarkResult, BenchmarkRunner

logger = logging.getLogger(__name__)


class ToolBenchmark:
    """
    工具层基准测试
    
    测试工具检索和调用性能
    """
    
    def __init__(self, tool_indexer: Any = None, tool_retriever: Any = None):
        """
        初始化
        
        Args:
            tool_indexer: 工具索引器实例
            tool_retriever: 工具检索器实例
        """
        self.tool_indexer = tool_indexer
        self.tool_retriever = tool_retriever
        self._runner = BenchmarkRunner()
    
    def create_mock_tools(self, count: int = 100) -> List[Dict]:
        """创建模拟工具"""
        tools = []
        categories = ["erp", "compliance", "inventory", "order", "supplier", "logistics", "report", "analysis"]
        
        for i in range(count):
            category = categories[i % len(categories)]
            tools.append({
                "name": f"{category}_tool_{i}",
                "description": f"Tool for {category} operations, variant {i}. "
                              f"This tool handles various {category} related tasks.",
                "category": category,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string", "description": "First parameter"},
                        "param2": {"type": "integer", "description": "Second parameter"},
                    },
                },
            })
        
        return tools
    
    async def benchmark_indexing(
        self,
        tool_count: int = 100,
        iterations: int = 10,
    ) -> BenchmarkResult:
        """
        测试工具索引构建性能
        
        Args:
            tool_count: 工具数量
            iterations: 迭代次数
        """
        tools = self.create_mock_tools(tool_count)
        
        async def build_index():
            if self.tool_indexer:
                return await asyncio.to_thread(
                    self.tool_indexer.build_index,
                    tools,
                )
            return {"indexed": len(tools)}
        
        return await self._runner.run(
            name=f"tool_indexing_{tool_count}_tools",
            func=build_index,
            iterations=iterations,
            metadata={"tool_count": tool_count},
        )
    
    async def benchmark_retrieval(
        self,
        queries: List[str] = None,
        iterations: int = 100,
    ) -> BenchmarkResult:
        """
        测试工具检索性能
        
        Args:
            queries: 测试查询列表
            iterations: 迭代次数
        """
        if queries is None:
            queries = [
                "查询供应商信息",
                "创建采购订单",
                "检查库存水平",
                "生成合规报告",
                "分析销售数据",
            ]
        
        query_idx = 0
        
        async def retrieve():
            nonlocal query_idx
            query = queries[query_idx % len(queries)]
            query_idx += 1
            
            if self.tool_retriever:
                return await asyncio.to_thread(
                    self.tool_retriever.retrieve,
                    query,
                )
            return {"tools": []}
        
        return await self._runner.run(
            name="tool_retrieval",
            func=retrieve,
            iterations=iterations,
            metadata={"query_count": len(queries)},
        )
    
    async def benchmark_two_level_retrieval(
        self,
        iterations: int = 100,
    ) -> BenchmarkResult:
        """测试两级检索性能"""
        queries = [
            "查询供应商的联系方式和地址",
            "创建一个紧急采购订单",
            "检查SKU123的库存情况",
        ]
        
        query_idx = 0
        
        async def two_level_retrieve():
            nonlocal query_idx
            query = queries[query_idx % len(queries)]
            query_idx += 1
            
            if self.tool_retriever and hasattr(self.tool_retriever, "retrieve_two_level"):
                return await asyncio.to_thread(
                    self.tool_retriever.retrieve_two_level,
                    query,
                )
            return {"categories": [], "tools": []}
        
        return await self._runner.run(
            name="two_level_retrieval",
            func=two_level_retrieve,
            iterations=iterations,
        )
    
    async def benchmark_compression(
        self,
        iterations: int = 100,
    ) -> BenchmarkResult:
        """测试工具描述压缩性能"""
        tools = self.create_mock_tools(20)
        
        async def compress():
            # 模拟压缩
            compressed = []
            for tool in tools:
                compressed.append({
                    "name": tool["name"],
                    "action": tool["description"][:50],
                    "params": list(tool["parameters"]["properties"].keys()),
                })
            return compressed
        
        return await self._runner.run(
            name="tool_compression",
            func=compress,
            iterations=iterations,
            metadata={"tool_count": len(tools)},
        )
    
    async def benchmark_tool_call(
        self,
        iterations: int = 100,
    ) -> BenchmarkResult:
        """测试工具调用性能"""
        call_idx = 0
        
        async def call_tool():
            nonlocal call_idx
            call_idx += 1
            # 模拟工具调用
            await asyncio.sleep(0.001)  # 模拟网络延迟
            return {"result": f"call_{call_idx}"}
        
        return await self._runner.run(
            name="tool_call",
            func=call_tool,
            iterations=iterations,
        )
    
    async def benchmark_healing(
        self,
        iterations: int = 50,
    ) -> BenchmarkResult:
        """测试自愈机制性能"""
        error_types = ["timeout", "rate_limit", "invalid_param", "service_unavailable"]
        error_idx = 0
        
        async def heal():
            nonlocal error_idx
            error_type = error_types[error_idx % len(error_types)]
            error_idx += 1
            
            # 模拟自愈过程
            await asyncio.sleep(0.005)  # 模拟诊断和恢复时间
            
            return {
                "error_type": error_type,
                "recovery": "retry" if error_type in ["timeout", "rate_limit"] else "fallback",
                "success": True,
            }
        
        return await self._runner.run(
            name="tool_healing",
            func=heal,
            iterations=iterations,
        )
    
    async def run_all(
        self,
        tool_counts: List[int] = None,
    ) -> Dict[str, BenchmarkResult]:
        """
        运行所有工具基准测试
        
        Args:
            tool_counts: 工具数量列表
        
        Returns:
            测试结果字典
        """
        tool_counts = tool_counts or [10, 50, 100, 200]
        results = {}
        
        # 索引构建测试
        for count in tool_counts:
            result = await self.benchmark_indexing(count)
            results[f"indexing_{count}"] = result
        
        # 检索测试
        results["retrieval"] = await self.benchmark_retrieval()
        results["two_level_retrieval"] = await self.benchmark_two_level_retrieval()
        
        # 压缩测试
        results["compression"] = await self.benchmark_compression()
        
        # 调用测试
        results["tool_call"] = await self.benchmark_tool_call()
        
        # 自愈测试
        results["healing"] = await self.benchmark_healing()
        
        return results
    
    def generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        return self._runner.generate_report("tool_benchmark.json")

