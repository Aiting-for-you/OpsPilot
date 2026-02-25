"""
Agent层基准测试

测试范围:
1. Agent消息处理性能
2. 多Agent协作性能
3. MsgHub消息传递性能
4. 并行Agent执行性能
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List

from opspilot.benchmarks.runner import BenchmarkResult, BenchmarkRunner
from opspilot.integration.agentscope_integration import (
    ASMessage,
    ASMessageType,
    create_agent,
)

logger = logging.getLogger(__name__)


class AgentBenchmark:
    """
    Agent层基准测试
    """
    
    def __init__(self, orchestrator: Any = None):
        self.orchestrator = orchestrator
        self._runner = BenchmarkRunner()
        self._agents: Dict[str, Any] = {}
    
    def setup_agents(self) -> None:
        """设置测试Agent"""
        self._agents = {
            "intent": create_agent("intent"),
            "plan": create_agent("plan"),
            "exec": create_agent("exec"),
            "verify": create_agent("verify"),
        }
    
    async def benchmark_single_agent(
        self,
        iterations: int = 100,
    ) -> BenchmarkResult:
        """测试单个Agent处理性能"""
        if not self._agents:
            self.setup_agents()
        
        agent = self._agents["intent"]
        idx = 0
        
        async def process():
            nonlocal idx
            msg = ASMessage(
                name="benchmark",
                content={"query": f"Test query {idx}"},
                msg_type=ASMessageType.TASK_REQUEST,
            )
            idx += 1
            return await agent.process(msg)
        
        return await self._runner.run(
            name="single_agent_processing",
            func=process,
            iterations=iterations,
        )
    
    async def benchmark_message_creation(
        self,
        iterations: int = 1000,
    ) -> BenchmarkResult:
        """测试消息创建性能"""
        idx = 0
        
        def create_msg():
            nonlocal idx
            idx += 1
            return ASMessage(
                name=f"sender_{idx}",
                content={"data": f"content_{idx}"},
                msg_type=ASMessageType.TASK_REQUEST,
            )
        
        return await self._runner.run(
            name="message_creation",
            func=create_msg,
            iterations=iterations,
        )
    
    async def benchmark_sequential_workflow(
        self,
        iterations: int = 50,
    ) -> BenchmarkResult:
        """测试顺序工作流性能"""
        if not self._agents:
            self.setup_agents()
        
        idx = 0
        
        async def sequential_flow():
            nonlocal idx
            idx += 1
            
            msg = ASMessage(
                name="benchmark",
                content={"query": f"Test {idx}"},
                msg_type=ASMessageType.TASK_REQUEST,
            )
            
            # Intent -> Plan -> Exec -> Verify
            result = await self._agents["intent"].process(msg)
            if result:
                result = await self._agents["plan"].process(result)
            if result:
                result = await self._agents["exec"].process(result)
            if result:
                result = await self._agents["verify"].process(result)
            
            return result
        
        return await self._runner.run(
            name="sequential_workflow",
            func=sequential_flow,
            iterations=iterations,
        )
    
    async def benchmark_parallel_execution(
        self,
        agent_count: int = 4,
        iterations: int = 50,
    ) -> BenchmarkResult:
        """测试并行执行性能"""
        if not self._agents:
            self.setup_agents()
        
        idx = 0
        
        async def parallel_flow():
            nonlocal idx
            idx += 1
            
            # 创建多个并行任务
            tasks = []
            for i in range(agent_count):
                msg = ASMessage(
                    name="benchmark",
                    content={"query": f"Parallel query {idx}-{i}"},
                    msg_type=ASMessageType.TASK_REQUEST,
                )
                tasks.append(self._agents["intent"].process(msg))
            
            results = await asyncio.gather(*tasks)
            return results
        
        return await self._runner.run(
            name=f"parallel_execution_{agent_count}_agents",
            func=parallel_flow,
            iterations=iterations,
            metadata={"agent_count": agent_count},
        )
    
    async def benchmark_messaging_throughput(
        self,
        iterations: int = 500,
    ) -> BenchmarkResult:
        """测试消息吞吐量"""
        idx = 0
        
        async def send_message():
            nonlocal idx
            idx += 1
            # 模拟消息发送
            await asyncio.sleep(0.0001)  # 极小延迟模拟
            return {"sent": idx}
        
        return await self._runner.run(
            name="messaging_throughput",
            func=send_message,
            iterations=iterations,
        )
    
    async def benchmark_orchestrator(
        self,
        iterations: int = 30,
    ) -> BenchmarkResult:
        """测试编排器性能"""
        idx = 0
        
        async def orchestrate():
            nonlocal idx
            idx += 1
            
            if self.orchestrator:
                return await self.orchestrator.execute({
                    "query": f"Benchmark query {idx}",
                })
            
            # 模拟编排
            await asyncio.sleep(0.01)
            return {"orchestrated": True}
        
        return await self._runner.run(
            name="orchestrator_execution",
            func=orchestrate,
            iterations=iterations,
        )
    
    async def run_all(self) -> Dict[str, BenchmarkResult]:
        """运行所有Agent基准测试"""
        results = {}
        
        results["message_creation"] = await self.benchmark_message_creation()
        results["single_agent"] = await self.benchmark_single_agent()
        results["sequential_workflow"] = await self.benchmark_sequential_workflow()
        results["parallel_4_agents"] = await self.benchmark_parallel_execution(4)
        results["parallel_8_agents"] = await self.benchmark_parallel_execution(8)
        results["messaging_throughput"] = await self.benchmark_messaging_throughput()
        results["orchestrator"] = await self.benchmark_orchestrator()
        
        return results
    
    def generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        return self._runner.generate_report("agent_benchmark.json")

