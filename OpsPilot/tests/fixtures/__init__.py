"""
测试数据 Fixtures

提供统一的测试数据模拟
"""
from tests.fixtures.erp_data import (
    MOCK_SUPPLIERS,
    MOCK_INVENTORY,
    MOCK_PRODUCTS,
    MOCK_WAREHOUSES,
    MOCK_PURCHASE_ORDERS,
    generate_mock_order,
)
from tests.fixtures.compliance_data import (
    MOCK_POLICIES,
    MOCK_COMPLIANCE_RULES,
    MOCK_APPROVAL_FLOWS,
)
from tests.fixtures.llm_mock import (
    MockLLMClient,
    MockStreamingLLMClient,
    create_mock_response,
)

__all__ = [
    # ERP 数据
    "MOCK_SUPPLIERS",
    "MOCK_INVENTORY",
    "MOCK_PRODUCTS",
    "MOCK_WAREHOUSES",
    "MOCK_PURCHASE_ORDERS",
    "generate_mock_order",
    # 合规数据
    "MOCK_POLICIES",
    "MOCK_COMPLIANCE_RULES",
    "MOCK_APPROVAL_FLOWS",
    # LLM Mock
    "MockLLMClient",
    "MockStreamingLLMClient",
    "create_mock_response",
]
