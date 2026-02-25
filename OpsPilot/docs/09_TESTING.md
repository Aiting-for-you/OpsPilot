# OpsPilot 测试文档

本文档记录 OpsPilot 项目的测试策略、测试数据、测试用例覆盖情况和性能基准测试结果。

---

## 1. 测试概述

### 1.1 测试目标

- 确保核心模块功能正确性
- 验证端到端业务流程
- 建立性能基准
- 支持回归测试

### 1.2 测试框架

| 组件 | 工具 | 版本 |
|------|------|------|
| 测试框架 | pytest | >=7.0 |
| 异步测试 | pytest-asyncio | >=0.21 |
| 覆盖率 | pytest-cov | >=4.0 |
| Mock | unittest.mock | 内置 |
| 性能测试 | time.perf_counter | 内置 |

### 1.3 测试目录结构

```
tests/
├── fixtures/              # 测试数据
│   ├── __init__.py
│   ├── erp_data.py        # ERP 模拟数据
│   ├── compliance_data.py # 合规模拟数据
│   ├── llm_mock.py        # LLM Mock 客户端
│   └── README.md          # Fixtures 文档
│
├── runtime/               # Runtime 模块测试
│   ├── test_sandbox.py    # 沙箱执行测试
│   ├── test_streaming.py  # 流式输出测试
│   ├── test_tracing.py    # 链路追踪测试
│   └── test_a2a.py        # Agent 间通信测试
│
├── chains/                # Chains 模块测试
│   └── test_executor.py   # 链式执行器测试
│
├── tools/                 # Tools 模块测试
│   ├── test_base.py
│   ├── test_mcp.py
│   ├── test_tool_rag.py
│   └── ...
│
├── agents/                # Agents 模块测试
│   ├── test_base.py
│   ├── test_intent.py
│   └── ...
│
├── memory/                # Memory 模块测试
│   ├── test_short_term.py
│   ├── test_long_term.py
│   └── ...
│
├── core/                  # Core 模块测试
│   ├── test_events.py
│   ├── test_state.py
│   └── ...
│
├── utils/                 # Utils 模块测试
│   ├── test_config.py
│   ├── test_logger.py
│   └── test_exceptions.py
│
├── api/                   # API 模块测试
│   └── test_routes.py
│
├── integration/           # 集成测试
│   ├── test_hybrid_integration.py
│   └── test_e2e_business.py
│
├── benchmarks/            # 性能基准测试
│   └── test_performance.py
│
├── prompts/               # Prompts 测试
│   └── ...
│
└── conftest.py            # pytest 配置
```

---

## 2. 测试数据 Fixtures

### 2.1 数据概览

| 数据类型 | 文件 | 数量 | 说明 |
|---------|------|------|------|
| 供应商 | `erp_data.py` | 5 家 | 不同区域、评分、类别 |
| 产品 SKU | `erp_data.py` | 10 个 | 电子、机械、包装、化工 |
| 库存记录 | `erp_data.py` | 10 条 | 含预警阈值 |
| 仓库 | `erp_data.py` | 3 个 | 华南、华东、华北 |
| 政策 | `compliance_data.py` | 5 条 | 采购限额、供应商准入等 |
| 合规规则 | `compliance_data.py` | 5 条 | 金额审批、评分检查等 |
| 审批流程 | `compliance_data.py` | 3 个 | 标准、大额、紧急 |

### 2.2 数据用途

| 场景 | 使用数据 | 测试文件 |
|------|---------|---------|
| 供应商查询 | `MOCK_SUPPLIERS` | `test_e2e_business.py` |
| 库存查询 | `MOCK_INVENTORY` | `test_e2e_business.py` |
| 订单创建 | `generate_mock_order()` | `test_e2e_business.py` |
| 合规检查 | `check_compliance()` | `test_e2e_business.py` |
| Agent 调用 | `MockLLMClient` | `test_*.py` |

### 2.3 详细文档

测试数据的详细结构和使用方法请参考 [`tests/fixtures/README.md`](../tests/fixtures/README.md)。

---

## 3. 测试用例覆盖

### 3.1 模块测试覆盖

| 模块 | 源文件数 | 测试文件数 | 测试用例数 | 覆盖状态 |
|------|---------|-----------|-----------|---------|
| `runtime/` | 4 | 4 | 70 | ✅ 完整 |
| `chains/` | 2 | 1 | 15 | ✅ 完整 |
| `tools/` | 16 | 4 | 50+ | ⚠️ 部分 |
| `agents/` | 10 | 3 | 40+ | ⚠️ 部分 |
| `memory/` | 10 | 4 | 35+ | ⚠️ 部分 |
| `core/` | 7 | 5 | 45+ | ✅ 完整 |
| `utils/` | 4 | 4 | 30+ | ✅ 完整 |
| `api/` | 3 | 1 | 10+ | ⚠️ 部分 |

### 3.2 新增测试用例

#### 3.2.1 Runtime 模块测试 (`tests/runtime/`)

| 文件 | 测试类 | 测试内容 | 用例数 |
|------|--------|---------|-------|
| `test_sandbox.py` | `TestSandboxConfig` | 沙箱配置验证 | 4 |
| | `TestLocalSandbox` | 本地沙箱执行 | 6 |
| | `TestSandboxSecurity` | 安全限制检查 | 5 |
| `test_streaming.py` | `TestSSEManager` | SSE 事件管理 | 5 |
| | `TestStreamBuffer` | 流缓冲区 | 5 |
| | `TestConnectionManager` | 连接管理 | 5 |
| `test_tracing.py` | `TestTraceSpan` | Span 创建与管理 | 8 |
| | `TestTraceContext` | 追踪上下文 | 6 |
| | `TestTraceExporter` | 导出功能 | 6 |
| `test_a2a.py` | `TestA2AManager` | Agent 间通信 | 8 |
| | `TestMessageRouter` | 消息路由 | 6 |
| | `TestA2AProtocol` | 协议处理 | 6 |

#### 3.2.2 Chains 模块测试 (`tests/chains/`)

| 文件 | 测试类 | 测试内容 | 用例数 |
|------|--------|---------|-------|
| `test_executor.py` | `TestRAGChain` | RAG 链执行 | 4 |
| | `TestToolChain` | 工具链执行 | 4 |
| | `TestDecisionChain` | 决策链执行 | 4 |
| | `TestChainExecutor` | 执行器管理 | 3 |

#### 3.2.3 集成测试 (`tests/integration/test_e2e_business.py`)

| 测试类 | 测试内容 | 用例数 |
|--------|---------|-------|
| `TestSupplierQueryFlow` | 供应商查询流程 | 5 |
| `TestInventoryQueryFlow` | 库存查询流程 | 4 |
| `TestOrderCreationFlow` | 订单创建流程 | 6 |
| `TestComplianceCheckFlow` | 合规检查流程 | 4 |
| `TestFullProcurementFlow` | 完整采购流程 | 4 |
| `TestConcurrentOperations` | 并发操作测试 | 2 |

---

## 4. 性能基准测试

### 4.1 测试环境

- **操作系统**: Windows 11
- **Python**: 3.10+
- **测试工具**: pytest + time.perf_counter

### 4.2 性能指标

#### 4.2.1 数据处理性能

| 测试项 | 平均延迟 | 吞吐量 | 目标阈值 | 状态 |
|--------|---------|--------|---------|------|
| 供应商过滤 (10,000 次) | < 0.1ms | > 10,000 ops/s | < 0.1ms | ✅ |
| 库存查询 (10,000 次) | < 0.5ms | > 2,000 ops/s | < 0.5ms | ✅ |
| 订单创建 (1,000 次) | < 1.0ms | > 1,000 ops/s | < 1.0ms | ✅ |
| 合规检查 (10,000 次) | < 0.1ms | > 10,000 ops/s | < 0.1ms | ✅ |

#### 4.2.2 并发性能

| 测试项 | 并发数 | 耗时 | 目标阈值 | 状态 |
|--------|-------|------|---------|------|
| 并发订单创建 | 10 | < 10ms | < 50ms | ✅ |
| 并发订单创建 | 50 | < 30ms | < 100ms | ✅ |
| 并发订单创建 | 100 | < 50ms | < 200ms | ✅ |
| 并发合规检查 | 100 | < 10ms | < 50ms | ✅ |

#### 4.2.3 内存使用

| 测试项 | 结果 | 状态 |
|--------|------|------|
| 大数据集内存使用 (1,000 次访问) | 无泄漏 | ✅ |

### 4.3 性能测试代码

```python
# tests/benchmarks/test_performance.py

def run_benchmark(name: str, func: callable, iterations: int) -> BenchmarkResult:
    """运行基准测试"""
    # 预热
    for _ in range(100):
        func()
    
    # 正式测试
    start = time.perf_counter()
    for _ in range(iterations):
        func()
    elapsed = time.perf_counter() - start
    
    return BenchmarkResult(
        name=name,
        iterations=iterations,
        total_time_ms=elapsed * 1000,
        avg_time_ms=(elapsed * 1000) / iterations,
        ops_per_second=iterations / elapsed,
    )
```

---

## 5. 测试运行指南

### 5.1 安装依赖

```bash
pip install pytest pytest-asyncio pytest-cov
```

### 5.2 运行所有测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行并生成覆盖率报告
pytest tests/ --cov=opspilot --cov-report=html

# 只运行特定模块
pytest tests/runtime/ -v
pytest tests/chains/ -v
pytest tests/integration/ -v
```

### 5.3 运行性能测试

```bash
pytest tests/benchmarks/ -v -s
```

### 5.4 运行特定测试

```bash
# 运行单个测试文件
pytest tests/runtime/test_sandbox.py -v

# 运行单个测试类
pytest tests/integration/test_e2e_business.py::TestSupplierQueryFlow -v

# 运行单个测试用例
pytest tests/utils/test_exceptions.py::TestOpsPilotError::test_basic_error -v
```

### 5.5 常用参数

| 参数 | 说明 |
|------|------|
| `-v` | 详细输出 |
| `-s` | 显示 print 输出 |
| `-x` | 首个失败即停止 |
| `--tb=short` | 简短错误回溯 |
| `--cov=opspilot` | 覆盖率测试 |
| `--cov-report=html` | HTML 覆盖率报告 |

---

## 6. 模拟数据示例

### 6.1 ERP 数据示例

```python
from tests.fixtures import MOCK_SUPPLIERS, MOCK_INVENTORY, generate_mock_order

# 查询华南地区供应商
south_suppliers = [s for s in MOCK_SUPPLIERS if s["region"] == "华南"]
# 结果: [{"id": "SUP001", "name": "华南电子科技有限公司", ...}]

# 创建采购订单
order = generate_mock_order(
    supplier_id="SUP001",
    products=[{"sku": "SKU001", "quantity": 100}],
)
# 结果: {"order_id": "PO20260217...", "total_amount": 2.00, ...}
```

### 6.2 合规检查示例

```python
from tests.fixtures import check_compliance

# 检查金额合规性
result = check_compliance(
    check_type="amount_limit",
    data={"amount": 60000}
)
# 结果: {"is_compliant": True, "matched_rules": ["RULE001"], ...}
```

### 6.3 LLM Mock 示例

```python
from tests.fixtures import MockLLMClient, IntentMockLLMClient

# 基础 Mock
client = MockLLMClient(responses={"供应商": "找到 5 家供应商"})
response = await client.generate("查询供应商")  # → "找到 5 家供应商"

# 意图识别 Mock
intent_client = IntentMockLLMClient()
response = await intent_client.generate("查询华南供应商")  # → "INTENT: query_supplier"
```

---

## 7. 测试最佳实践

### 7.1 测试命名规范

```python
# 测试文件: test_{module_name}.py
# 测试类: Test{ClassName}
# 测试方法: test_{scenario}_{expected_result}

class TestLocalSandbox:
    def test_execute_simple_python_returns_result(self):
        """测试执行简单 Python 代码返回正确结果"""
        pass
    
    def test_execute_with_timeout_raises_error(self):
        """测试超时执行抛出错误"""
        pass
```

### 7.2 使用 Fixtures

```python
import pytest
from tests.fixtures import MOCK_SUPPLIERS, MockLLMClient

@pytest.fixture
def mock_llm():
    return MockLLMClient()

def test_with_fixture(mock_llm):
    """使用 pytest fixture"""
    assert mock_llm is not None
```

### 7.3 异步测试

```python
@pytest.mark.asyncio
async def test_async_operation():
    """异步测试需要 @pytest.mark.asyncio 装饰器"""
    result = await some_async_function()
    assert result is not None
```

---

## 8. 持续集成

### 8.1 GitHub Actions 配置

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -e ".[dev]"
      - run: pytest tests/ --cov=opspilot --cov-report=xml
      - uses: codecov/codecov-action@v3
```

### 8.2 测试覆盖率目标

| 模块 | 目标覆盖率 | 当前状态 |
|------|-----------|---------|
| `runtime/` | 80% | ✅ |
| `chains/` | 80% | ✅ |
| `core/` | 80% | ✅ |
| `utils/` | 90% | ✅ |
| 整体 | 75% | 🔄 进行中 |

---

## 9. 更新日志

| 日期 | 更新内容 |
|------|---------|
| 2026-02-17 | 创建测试文档，添加 Runtime/Chains 测试、性能基准测试 |
