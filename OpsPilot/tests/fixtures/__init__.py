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
from tests.fixtures.ecommerce_data import (
    MOCK_EXCHANGE_RATES,
    MOCK_LOGISTICS_TRACKING,
    MOCK_PLATFORM_ORDERS,
    MOCK_CUSTOMS_DECLARATIONS,
    get_exchange_rate,
    convert_currency,
    track_logistics,
    get_platform_order,
    get_customs_declaration,
    get_ecommerce_summary,
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
    # 跨境电商数据
    "MOCK_EXCHANGE_RATES",
    "MOCK_LOGISTICS_TRACKING",
    "MOCK_PLATFORM_ORDERS",
    "MOCK_CUSTOMS_DECLARATIONS",
    "get_exchange_rate",
    "convert_currency",
    "track_logistics",
    "get_platform_order",
    "get_customs_declaration",
    "get_ecommerce_summary",
]
