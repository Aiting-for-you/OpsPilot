# OpsPilot 虚拟数据文档

本文档说明 OpsPilot 数据库中的虚拟数据结构和用途。

---

## 📊 数据概览

| 表名 | 记录数 | 说明 |
|------|--------|------|
| suppliers | 50 | 供应商信息 |
| products | 100 | 产品信息 |
| inventory | 477 | 库存记录 |
| orders | 200 | 采购订单 |
| logistics | 200 | 物流轨迹 |
| customs_declarations | 100 | 报关记录 |
| platform_orders | 50 | 跨境平台订单 |
| policies | 50 | 政策文档 |
| warehouses | 5 | 仓库信息 |
| exchange_rates | 8 | 汇率数据 |
| **总计** | **1240** | - |

---

## 🗄️ 数据库配置

### PostgreSQL 连接

```yaml
host: localhost
port: 5432
user: postgres
password: cyx0414
database: opspilot
```

### Redis 连接

```yaml
host: localhost
port: 6379
```

### ChromaDB 存储

```yaml
persist_directory: ./data/chroma
collections:
  - policies (政策文档向量库)
  - products (产品向量库)
  - suppliers (供应商向量库)
```

---

## 📋 数据详情

### 1. 供应商 (suppliers)

| 字段 | 类型 | 说明 |
|------|------|------|
| supplier_id | VARCHAR(20) | 供应商ID (SUP001-SUP050) |
| name | VARCHAR(200) | 公司名称 |
| rating | DECIMAL(2,1) | 评分 (3.5-5.0) |
| region | VARCHAR(50) | 区域 (华南/华东/华北/西南/东北) |
| main_category | VARCHAR(100) | 主营类别 |

**数据分布**：
- 华南: 10 家
- 华东: 10 家
- 华北: 10 家
- 西南: 10 家
- 东北: 10 家

### 2. 产品 (products)

| 字段 | 类型 | 说明 |
|------|------|------|
| sku | VARCHAR(50) | 产品SKU (SKU0001-SKU0100) |
| name | VARCHAR(200) | 产品名称 |
| category | VARCHAR(100) | 类别 |
| sub_category | VARCHAR(100) | 子类别 |
| base_price | DECIMAL(10,2) | 基础价格 |

**类别分布**：
- 电子元器件: 电阻、电容、芯片
- 机械零件: 轴承、齿轮、螺丝
- 包装材料: 纸箱、托盘
- 化工材料: 润滑油、清洗剂

### 3. 库存 (inventory)

| 字段 | 类型 | 说明 |
|------|------|------|
| sku | VARCHAR(50) | 产品SKU |
| warehouse_id | VARCHAR(20) | 仓库ID |
| quantity | INTEGER | 总数量 (0-10000) |
| available | INTEGER | 可用数量 |
| reserved | INTEGER | 预留数量 |

**仓库分布**：
- WH001: 深圳仓库
- WH002: 上海仓库
- WH003: 北京仓库
- WH004: 成都仓库
- WH005: 广州仓库

### 4. 订单 (orders)

| 字段 | 类型 | 说明 |
|------|------|------|
| order_id | VARCHAR(30) | 订单ID (ORD20260217XXXX) |
| supplier_id | VARCHAR(20) | 供应商ID |
| items | JSONB | 订单项列表 |
| total_amount | DECIMAL(12,2) | 总金额 |
| status | VARCHAR(30) | 订单状态 |

**状态分布**：
- created: 新建
- approved: 已审批
- shipping: 配送中
- completed: 已完成

### 5. 物流 (logistics)

| 字段 | 类型 | 说明 |
|------|------|------|
| tracking_no | VARCHAR(50) | 运单号 |
| order_id | VARCHAR(30) | 关联订单 |
| carrier | VARCHAR(100) | 承运商 |
| status | VARCHAR(30) | 物流状态 |

**承运商**：
- 顺丰速运 (SF)
- 中通快递 (ZT)
- 京东物流 (JD)

### 6. 报关 (customs_declarations)

| 字段 | 类型 | 说明 |
|------|------|------|
| declaration_no | VARCHAR(30) | 报关单号 |
| order_id | VARCHAR(30) | 关联订单 |
| customs_office | VARCHAR(100) | 海关 |
| status | VARCHAR(30) | 报关状态 |

**海关分布**：
- 深圳海关 (5301)
- 上海海关 (2200)
- 广州海关 (5100)

### 7. 平台订单 (platform_orders)

| 字段 | 类型 | 说明 |
|------|------|------|
| platform_order_id | VARCHAR(50) | 平台订单ID |
| platform | VARCHAR(50) | 平台名称 |
| total_amount | DECIMAL(12,2) | 订单金额 |
| status | VARCHAR(30) | 订单状态 |

**平台分布**：
- Amazon
- AliExpress
- Shopify
- eBay

### 8. 政策文档 (policies)

| 字段 | 类型 | 说明 |
|------|------|------|
| policy_id | VARCHAR(20) | 政策ID (POL001-POL050) |
| title | VARCHAR(200) | 政策标题 |
| category | VARCHAR(50) | 政策类别 |
| content | TEXT | 政策内容 |

**政策类别**：
- 采购限额
- 供应商准入
- 付款条款
- 合同管理
- 紧急采购

---

## 🔧 使用方式

### 数据库连接

```python
from opspilot.db import get_database_pool, SupplierCRUD, ProductCRUD

async def main():
    pool = await get_database_pool()
    
    # 查询供应商
    suppliers = await SupplierCRUD.get_list(region="华南")
    
    # 查询产品
    products = await ProductCRUD.get_list(category="电子元器件")
```

### 缓存操作

```python
from opspilot.db import get_cache

cache = get_cache()

# 设置缓存
cache.set("key", {"data": "value"}, ttl=3600)

# 获取缓存
data = cache.get("key")
```

### 向量搜索

```python
from opspilot.db import get_vector_store

store = get_vector_store("policy")

# 搜索政策
results = store.search_policies("采购限额", n_results=5)
```

---

## 📁 相关文件

| 文件路径 | 说明 |
|---------|------|
| `config/database.yaml` | 数据库配置 |
| `data/init/*.sql` | 数据库初始化脚本 |
| `scripts/init_data.py` | 数据生成脚本 |
| `opspilot/db/connection.py` | 数据库连接管理 |
| `opspilot/db/models.py` | ORM 模型定义 |
| `opspilot/db/crud.py` | CRUD 操作封装 |
| `opspilot/db/vector_store.py` | ChromaDB 向量存储 |
| `opspilot/db/cache.py` | Redis 缓存管理 |
