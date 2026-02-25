# 测试数据 Fixtures 文档

本文档说明 OpsPilot 测试中使用的模拟数据结构和用途。

---

## 📁 目录结构

```
tests/fixtures/
├── __init__.py          # 导出所有 fixtures
├── erp_data.py          # ERP 系统模拟数据
├── compliance_data.py   # 合规系统模拟数据
├── llm_mock.py          # LLM Mock 客户端
└── README.md            # 本文档
```

---

## 🏢 ERP 数据 (`erp_data.py`)

### 1. 供应商数据 (`MOCK_SUPPLIERS`)

模拟 5 家不同区域的供应商：

| ID | 名称 | 区域 | 评分 | 主营类别 |
|----|------|------|------|---------|
| SUP001 | 华南电子科技有限公司 | 华南 | 4.8 | 电子元器件 |
| SUP002 | 华东精密制造有限公司 | 华东 | 4.5 | 机械加工 |
| SUP003 | 华北物流供应链股份有限公司 | 华北 | 4.6 | 物流包装 |
| SUP004 | 西南化工材料有限公司 | 西南 | 4.2 | 化工材料 |
| SUP005 | 东北机械装备集团 | 东北 | 4.0 | 重型装备 |

**数据字段说明**：

```python
{
    "id": "SUP001",                    # 供应商ID
    "name": "华南电子科技有限公司",      # 全称
    "short_name": "华南电子",           # 简称
    "region": "华南",                   # 区域
    "province": "广东省",               # 省份
    "city": "深圳市",                   # 城市
    "address": "南山区科技园南区",       # 详细地址
    "rating": 4.8,                     # 评分 (1-5)
    "rating_count": 256,               # 评分人数
    "products": ["电子元件", "芯片"],    # 产品类别
    "main_category": "电子元器件",      # 主营类别
    "contact": "张伟",                  # 联系人
    "phone": "138****1234",            # 电话（脱敏）
    "email": "zhang.wei@huanan-elec.com",
    "payment_terms": "月结30天",        # 付款条款
    "min_order_amount": 500.0,         # 最低起订金额
    "delivery_days": 3,                # 交货周期（天）
    "certifications": ["ISO9001"],      # 资质认证
    "status": "active",                # 状态
    "cooperation_years": 5,            # 合作年限
}
```

### 2. 产品数据 (`MOCK_PRODUCTS`)

模拟 10 个产品 SKU，覆盖 5 个类别：

| SKU | 名称 | 类别 | 单价 | 安全库存 |
|-----|------|------|------|---------|
| SKU001 | 电阻100Ω | 电子元器件 | ¥0.02 | 10,000 |
| SKU002 | 电容10μF | 电子元器件 | ¥0.05 | 5,000 |
| SKU003 | 芯片STM32F103C8T6 | 电子元器件 | ¥8.50 | 200 |
| SKU004 | 温湿度传感器DHT11 | 电子元器件 | ¥3.80 | 500 |
| SKU005 | 轴承6205-2RS | 机械零件 | ¥12.00 | 100 |
| SKU006 | 铝合金型材4040 | 机械零件 | ¥85.00 | 50 |
| SKU007 | 瓦楞纸箱400×300×200 | 包装材料 | ¥4.50 | 500 |
| SKU008 | 木托盘1200×1000 | 包装材料 | ¥120.00 | 100 |
| SKU009 | 工业润滑油L-HM46 | 化工材料 | ¥1,800.00 | 10 |
| SKU010 | 清洗剂WD-40 | 化工材料 | ¥25.00 | 100 |

### 3. 库存数据 (`MOCK_INVENTORY`)

每个 SKU 对应的库存信息：

```python
{
    "SKU001": {
        "quantity": 50000,      # 总数量
        "available": 48000,     # 可用数量
        "reserved": 2000,       # 预留数量
        "warehouse": "WH001",   # 仓库ID
        "location": "A-01-01",  # 库位
        "last_updated": "2026-02-15T10:00:00",
    },
    # ...
}
```

### 4. 仓库数据 (`MOCK_WAREHOUSES`)

| ID | 名称 | 区域 | 容量(m²) | 类型 |
|----|------|------|---------|------|
| WH001 | 深圳仓库 | 华南 | 50,000 | 原材料仓 |
| WH002 | 上海仓库 | 华东 | 30,000 | 成品仓 |
| WH003 | 北京仓库 | 华北 | 20,000 | 包装材料仓 |

### 5. 采购订单 (`MOCK_PURCHASE_ORDERS` + `generate_mock_order()`)

动态生成采购订单：

```python
from tests.fixtures import generate_mock_order

order = generate_mock_order(
    supplier_id="SUP001",
    products=[{"sku": "SKU001", "quantity": 1000}],
    status="created",
    created_by="test_user"
)

# 返回:
{
    "order_id": "PO202602171430001234",
    "supplier_id": "SUP001",
    "supplier_name": "华南电子科技有限公司",
    "products": [...],
    "total_amount": 20.00,
    "status": "created",
    "need_approval": False,
    ...
}
```

### 6. 库存预警 (`get_low_stock_products()`)

```python
from tests.fixtures import get_low_stock_products

low_stock = get_low_stock_products(threshold_ratio=0.2)
# 返回库存低于安全库存 20% 的产品列表
```

---

## ⚖️ 合规数据 (`compliance_data.py`)

### 1. 政策数据 (`MOCK_POLICIES`)

| ID | 标题 | 类别 | 版本 |
|----|------|------|------|
| POL001 | 采购限额管理规定 | 采购限额 | 2.0 |
| POL002 | 供应商准入标准 | 供应商准入 | 1.5 |
| POL003 | 付款条款规范 | 付款条款 | 1.0 |
| POL004 | 合同管理规范 | 合同管理 | 2.0 |
| POL005 | 紧急采购流程 | 紧急采购 | 1.0 |

### 2. 合规规则 (`MOCK_COMPLIANCE_RULES`)

| ID | 名称 | 类型 | 严重程度 |
|----|------|------|---------|
| RULE001 | 采购金额审批规则 | amount_limit | high |
| RULE002 | 供应商评分规则 | supplier_rating | high |
| RULE003 | 付款条款规则 | payment_terms | medium |
| RULE004 | 库存预警规则 | inventory_warning | medium |
| RULE005 | 供应商资质规则 | supplier_certification | high |

**规则条件示例**：

```python
{
    "conditions": [
        {"field": "amount", "operator": "<=", "value": 5000, "action": "no_approval"},
        {"field": "amount", "operator": "<=", "value": 10000, "action": "manager_approval"},
        ...
    ]
}
```

### 3. 审批流程 (`MOCK_APPROVAL_FLOWS`)

| ID | 名称 | 步骤数 | 适用条件 |
|----|------|-------|---------|
| FLOW001 | 标准采购审批流程 | 3 | 5,000-50,000元 |
| FLOW002 | 大额采购审批流程 | 5 | >50,000元 |
| FLOW003 | 紧急采购审批流程 | 2 | 紧急采购 ≤50,000元 |

### 4. 合规检查函数 (`check_compliance()`)

```python
from tests.fixtures import check_compliance

# 检查采购金额合规性
result = check_compliance(
    check_type="amount_limit",
    data={"amount": 60000}
)

# 返回:
{
    "check_type": "amount_limit",
    "is_compliant": True,
    "violations": [],
    "warnings": [...],
    "matched_rules": ["RULE001"],
}
```

---

## 🤖 LLM Mock (`llm_mock.py`)

### 1. 基础 Mock 客户端 (`MockLLMClient`)

```python
from tests.fixtures import MockLLMClient

client = MockLLMClient(
    default_response="默认响应",
    responses={"关键词": "对应响应"},
    latency_ms=100,
    error_rate=0.0,
)

# 使用
response = await client.generate("请帮我查询供应商")
```

### 2. 流式 Mock 客户端 (`MockStreamingLLMClient`)

```python
from tests.fixtures import MockStreamingLLMClient

client = MockStreamingLLMClient(
    default_response="流式响应文本",
    chunk_size=5,
    latency_ms_per_chunk=50,
)

# 使用
async for chunk in client.stream("查询供应商"):
    print(chunk)
```

### 3. 意图识别 Mock (`IntentMockLLMClient`)

预配置意图识别响应：

```python
from tests.fixtures import IntentMockLLMClient

client = IntentMockLLMClient()
response = await client.generate("查询华南地区的供应商")
# 返回: "INTENT: query_supplier"
```

### 4. 规划 Mock (`PlanningMockLLMClient`)

预配置规划场景响应：

```python
from tests.fixtures import PlanningMockLLMClient

client = PlanningMockLLMClient()
response = await client.generate("帮我查询供应商并下单")
# 返回 JSON 格式的执行步骤
```

### 5. Agent Mock (`AgentMockLLMClient`)

支持多轮对话：

```python
from tests.fixtures import AgentMockLLMClient

client = AgentMockLLMClient(agent_type="intent")
response = await client.chat("查询供应商")
# 返回: {"content": "...", "intent": "query_supplier", "confidence": 0.95}
```

---

## 📊 使用示例

### 在测试中使用

```python
import pytest
from tests.fixtures import (
    MOCK_SUPPLIERS,
    MOCK_PRODUCTS,
    MOCK_INVENTORY,
    generate_mock_order,
    MockLLMClient,
)

def test_supplier_query():
    """测试供应商查询"""
    suppliers = [s for s in MOCK_SUPPLIERS if s["region"] == "华南"]
    assert len(suppliers) == 1
    assert suppliers[0]["id"] == "SUP001"

@pytest.mark.asyncio
async def test_with_mock_llm():
    """使用 Mock LLM 测试"""
    client = MockLLMClient(
        responses={"测试": "响应内容"}
    )
    response = await client.generate("这是一个测试")
    assert response == "响应内容"
```

---

## 🔄 数据更新

模拟数据按以下规则生成：

| 数据类型 | 更新频率 | 备注 |
|---------|---------|------|
| 供应商 | 静态 | 可通过 `MOCK_SUPPLIERS.append()` 添加 |
| 产品/库存 | 静态 | 库存数量可修改 |
| 订单 | 动态 | 使用 `generate_mock_order()` 生成 |
| 合规检查 | 动态 | 使用 `check_compliance()` 执行 |

---

## 📝 数据覆盖场景

| 场景 | 使用数据 | 测试用例示例 |
|------|---------|-------------|
| 供应商查询 | `MOCK_SUPPLIERS` | 按区域/名称筛选 |
| 库存查询 | `MOCK_INVENTORY` | SKU 查询、库存预警 |
| 创建订单 | `generate_mock_order()` | 金额审批流程 |
| 合规检查 | `check_compliance()` | 金额/评分合规 |
| Agent 调用 | `MockLLMClient` | 意图识别、规划 |
