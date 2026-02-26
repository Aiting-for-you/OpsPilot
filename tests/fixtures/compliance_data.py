"""
合规系统模拟数据

模拟企业合规管理数据，包括：
- 采购政策
- 合规规则
- 审批流程
"""
from typing import Dict, Any, List
from datetime import datetime


# ==================== 政策数据 ====================

MOCK_POLICIES: List[Dict[str, Any]] = [
    {
        "id": "POL001",
        "title": "采购限额管理规定",
        "category": "采购限额",
        "version": "2.0",
        "content": """
## 采购限额管理

### 限额标准
1. 单笔采购金额 ≤ 5,000元：无需审批
2. 单笔采购金额 5,000-10,000元：部门经理审批
3. 单笔采购金额 10,000-50,000元：总监审批
4. 单笔采购金额 > 50,000元：VP审批

### 审批时限
- 部门经理：2个工作日
- 总监：3个工作日
- VP：5个工作日
        """.strip(),
        "effective_date": "2024-01-01",
        "expiry_date": None,
        "status": "active",
        "created_by": "采购部",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2025-06-01T00:00:00",
    },
    {
        "id": "POL002",
        "title": "供应商准入标准",
        "category": "供应商准入",
        "version": "1.5",
        "content": """
## 供应商准入标准

### 基本要求
1. 注册资本 ≥ 100万元
2. 经营年限 ≥ 2年
3. 无重大违法违规记录

### 评分标准
- 综合评分 ≥ 4.0分方可合作
- 评分 < 4.5分需签署质量保证协议
- 评分 < 4.0分不可合作

### 资质要求
- ISO9001 质量管理体系认证（必须）
- ISO14001 环境管理体系认证（推荐）
- 行业特定资质（按类别要求）
        """.strip(),
        "effective_date": "2024-01-01",
        "expiry_date": None,
        "status": "active",
        "created_by": "采购部",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2025-03-01T00:00:00",
    },
    {
        "id": "POL003",
        "title": "付款条款规范",
        "category": "付款条款",
        "version": "1.0",
        "content": """
## 付款条款规范

### 标准条款
- 月结30天：适用于合作1年以上的供应商
- 月结45天：适用于合作6个月-1年的供应商
- 月结60天：适用于战略合作供应商

### 特殊条款
- 预付款：需财务总监审批，最高50%
- 分期付款：单笔金额>10万可申请

### 付款条件
- 验收合格后启动付款流程
- 发票与订单金额一致
- 无质量争议
        """.strip(),
        "effective_date": "2024-01-01",
        "expiry_date": None,
        "status": "active",
        "created_by": "财务部",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": None,
    },
    {
        "id": "POL004",
        "title": "合同管理规范",
        "category": "合同管理",
        "version": "2.0",
        "content": """
## 合同管理规范

### 合同金额分级
1. ≤ 10万元：标准合同模板，部门经理签署
2. 10-50万元：法务审核，总监签署
3. > 50万元：法务审核，VP签署

### 合同要素
- 标的物明细
- 价格条款
- 交货条款
- 付款条款
- 违约责任
- 争议解决

### 合同归档
- 签署后3个工作日内归档
- 保存期限：合同终止后5年
        """.strip(),
        "effective_date": "2024-06-01",
        "expiry_date": None,
        "status": "active",
        "created_by": "法务部",
        "created_at": "2024-06-01T00:00:00",
        "updated_at": None,
    },
    {
        "id": "POL005",
        "title": "紧急采购流程",
        "category": "紧急采购",
        "version": "1.0",
        "content": """
## 紧急采购流程

### 紧急采购定义
- 生产设备故障急需维修配件
- 客户订单急需物料
- 突发事件应急采购

### 审批简化
- 可先采购后补审批
- 最高金额限制：50,000元
- 需24小时内补齐审批手续

### 供应商选择
- 优先选择现有合格供应商
- 新供应商需紧急资质审核
        """.strip(),
        "effective_date": "2024-01-01",
        "expiry_date": None,
        "status": "active",
        "created_by": "采购部",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": None,
    },
]


# ==================== 合规规则数据 ====================

MOCK_COMPLIANCE_RULES: List[Dict[str, Any]] = [
    {
        "id": "RULE001",
        "name": "采购金额审批规则",
        "type": "amount_limit",
        "description": "根据采购金额确定审批级别",
        "conditions": [
            {"field": "amount", "operator": "<=", "value": 5000, "action": "no_approval"},
            {"field": "amount", "operator": "<=", "value": 10000, "action": "manager_approval"},
            {"field": "amount", "operator": "<=", "value": 50000, "action": "director_approval"},
            {"field": "amount", "operator": ">", "value": 50000, "action": "vp_approval"},
        ],
        "severity": "high",
        "enabled": True,
    },
    {
        "id": "RULE002",
        "name": "供应商评分规则",
        "type": "supplier_rating",
        "description": "供应商评分必须达到准入标准",
        "conditions": [
            {"field": "rating", "operator": ">=", "value": 4.0, "action": "pass"},
            {"field": "rating", "operator": "<", "value": 4.0, "action": "block"},
        ],
        "severity": "high",
        "enabled": True,
    },
    {
        "id": "RULE003",
        "name": "付款条款规则",
        "type": "payment_terms",
        "description": "付款条款需符合公司财务政策",
        "conditions": [
            {"field": "payment_days", "operator": "<=", "value": 60, "action": "pass"},
            {"field": "payment_days", "operator": ">", "value": 60, "action": "require_approval"},
            {"field": "prepayment_ratio", "operator": "<=", "value": 0.5, "action": "pass"},
        ],
        "severity": "medium",
        "enabled": True,
    },
    {
        "id": "RULE004",
        "name": "库存预警规则",
        "type": "inventory_warning",
        "description": "库存低于安全库存时触发预警",
        "conditions": [
            {"field": "quantity", "operator": "<", "value": "safety_stock", "action": "warning"},
            {"field": "quantity", "operator": "<", "value": "safety_stock * 0.2", "action": "critical"},
        ],
        "severity": "medium",
        "enabled": True,
    },
    {
        "id": "RULE005",
        "name": "供应商资质规则",
        "type": "supplier_certification",
        "description": "供应商必须具备必要资质认证",
        "conditions": [
            {"field": "certifications", "operator": "contains", "value": "ISO9001", "action": "pass"},
        ],
        "severity": "high",
        "enabled": True,
    },
]


# ==================== 审批流程数据 ====================

MOCK_APPROVAL_FLOWS: List[Dict[str, Any]] = [
    {
        "id": "FLOW001",
        "name": "标准采购审批流程",
        "type": "purchase",
        "steps": [
            {
                "step": 1,
                "name": "部门经理审批",
                "role": "department_manager",
                "timeout_hours": 48,
                "auto_approve": False,
            },
            {
                "step": 2,
                "name": "采购部审核",
                "role": "procurement_reviewer",
                "timeout_hours": 24,
                "auto_approve": False,
            },
            {
                "step": 3,
                "name": "财务确认",
                "role": "finance_reviewer",
                "timeout_hours": 24,
                "auto_approve": False,
            },
        ],
        "applicable_conditions": {
            "amount_min": 5000,
            "amount_max": 50000,
        },
        "enabled": True,
    },
    {
        "id": "FLOW002",
        "name": "大额采购审批流程",
        "type": "purchase_large",
        "steps": [
            {
                "step": 1,
                "name": "部门经理审批",
                "role": "department_manager",
                "timeout_hours": 48,
                "auto_approve": False,
            },
            {
                "step": 2,
                "name": "总监审批",
                "role": "director",
                "timeout_hours": 72,
                "auto_approve": False,
            },
            {
                "step": 3,
                "name": "采购部审核",
                "role": "procurement_reviewer",
                "timeout_hours": 24,
                "auto_approve": False,
            },
            {
                "step": 4,
                "name": "财务审核",
                "role": "finance_manager",
                "timeout_hours": 48,
                "auto_approve": False,
            },
            {
                "step": 5,
                "name": "VP审批",
                "role": "vp",
                "timeout_hours": 120,
                "auto_approve": False,
            },
        ],
        "applicable_conditions": {
            "amount_min": 50000,
            "amount_max": None,
        },
        "enabled": True,
    },
    {
        "id": "FLOW003",
        "name": "紧急采购审批流程",
        "type": "emergency",
        "steps": [
            {
                "step": 1,
                "name": "主管审批",
                "role": "supervisor",
                "timeout_hours": 2,
                "auto_approve": False,
            },
            {
                "step": 2,
                "name": "采购经理确认",
                "role": "procurement_manager",
                "timeout_hours": 4,
                "auto_approve": True,  # 超时自动通过
            },
        ],
        "applicable_conditions": {
            "is_emergency": True,
            "amount_max": 50000,
        },
        "enabled": True,
    },
]


def check_compliance(
    check_type: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    执行合规检查

    Args:
        check_type: 检查类型 (amount_limit/supplier_rating/payment_terms)
        data: 待检查数据

    Returns:
        检查结果
    """
    violations = []
    warnings = []
    matched_rules = []

    for rule in MOCK_COMPLIANCE_RULES:
        if rule["type"] != check_type or not rule["enabled"]:
            continue

        matched_rules.append(rule["id"])

        for condition in rule["conditions"]:
            field = condition["field"]
            operator = condition["operator"]
            expected = condition["value"]
            action = condition["action"]

            actual = data.get(field)
            if actual is None:
                continue

            # 特殊处理引用字段
            if isinstance(expected, str) and expected in data:
                expected = data[expected]
            elif isinstance(expected, str) and "*" in expected:
                # 计算表达式如 "safety_stock * 0.2"
                try:
                    base_field, multiplier = expected.split(" * ")
                    expected = data.get(base_field, 0) * float(multiplier)
                except:
                    continue

            # 执行比较
            passed = False
            if operator == "<=":
                passed = actual <= expected
            elif operator == "<":
                passed = actual < expected
            elif operator == ">=":
                passed = actual >= expected
            elif operator == ">":
                passed = actual > expected
            elif operator == "contains":
                passed = expected in actual if isinstance(actual, (list, str)) else False
            elif operator == "==":
                passed = actual == expected

            # 找到匹配条件后处理并跳出循环
            if passed:
                if action == "pass" or action == "no_approval":
                    # 通过，不添加违规
                    break
                elif action == "vp_approval":
                    # 需要 VP 审批，视为违规
                    violations.append({
                        "rule_id": rule["id"],
                        "rule_name": rule["name"],
                        "field": field,
                        "expected": expected,
                        "actual": actual,
                        "message": f"{rule['name']}: {field} 超过限额，需要 VP 审批",
                        "severity": rule["severity"],
                    })
                    break
                elif action in ["director_approval", "manager_approval"]:
                    # 需要高层审批，视为警告
                    warnings.append({
                        "rule_id": rule["id"],
                        "rule_name": rule["name"],
                        "field": field,
                        "message": f"{rule['name']}: {field} 需要 {action.replace('_', ' ')} 审批",
                        "severity": rule["severity"],
                    })
                    break
            else:
                # 条件不通过
                if action == "block":
                    violations.append({
                        "rule_id": rule["id"],
                        "rule_name": rule["name"],
                        "field": field,
                        "expected": expected,
                        "actual": actual,
                        "message": f"{rule['name']}: {field} 应满足 {operator} {expected}，实际为 {actual}",
                        "severity": rule["severity"],
                    })
                    break
                elif action == "pass":
                    # action 是 pass 但条件不通过，视为违规
                    violations.append({
                        "rule_id": rule["id"],
                        "rule_name": rule["name"],
                        "field": field,
                        "expected": expected,
                        "actual": actual,
                        "message": f"{rule['name']}: {field} 应满足 {operator} {expected}，实际为 {actual}",
                        "severity": rule["severity"],
                    })
                    break
                elif action in ["require_approval", "warning"]:
                    warnings.append({
                        "rule_id": rule["id"],
                        "rule_name": rule["name"],
                        "field": field,
                        "message": f"{rule['name']}: 需要额外审批或关注",
                        "severity": rule["severity"],
                    })
                    break

    return {
        "check_type": check_type,
        "is_compliant": len(violations) == 0,
        "violations": violations,
        "warnings": warnings,
        "matched_rules": matched_rules,
        "checked_at": datetime.now().isoformat(),
    }
