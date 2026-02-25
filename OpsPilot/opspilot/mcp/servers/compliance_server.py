"""
合规 MCP Server

提供合规相关工具：
- 政策查询
- 合规检查
- 风险评估

使用真实数据库连接
"""
import json
from typing import Any, Dict, List, Optional

from opspilot.mcp.base import MCPServerBase
from opspilot.db.crud import PolicyCRUD
from opspilot.db.connection import get_database_pool


class ComplianceMCPServer(MCPServerBase):
    """
    合规系统 MCP Server

    提供：
    - 政策查询（数据库）
    - 合规检查（规则引擎）
    - 风险评估
    """

    def __init__(self):
        super().__init__(
            name="compliance-tools",
            version="1.0.0",
            description="合规系统工具集：政策查询、合规检查、风险评估",
        )
        self._vector_store = None
        # 注册工具
        self._register_tools()

    async def _get_vector_store(self):
        """获取向量存储实例（延迟导入）"""
        if self._vector_store is None:
            try:
                from opspilot.db.vector_store import PolicyVectorStore
                self._vector_store = PolicyVectorStore()
            except Exception as e:
                print(f"Warning: Vector store not available: {e}")
        return self._vector_store

    def _register_tools(self) -> None:
        """注册所有合规工具"""

        # ==================== 政策查询工具 ====================

        @self.tool(
            name="query_policy",
            description="查询合规政策，支持按关键词、类别筛选",
            input_schema={
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "string",
                        "description": "关键词搜索",
                    },
                    "category": {
                        "type": "string",
                        "description": "政策类别：采购/财务/质量/环保",
                    },
                    "status": {
                        "type": "string",
                        "description": "状态：active/archived",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量限制，默认 10",
                    },
                },
            },
        )
        async def query_policy(params: Dict[str, Any]) -> Dict[str, Any]:
            policies = await PolicyCRUD.get_list(
                category=params.get("category"),
                status=params.get("status", "active"),
                limit=params.get("limit", 10),
            )

            # 关键词过滤
            keywords = params.get("keywords", "").lower()
            if keywords:
                filtered = []
                for p in policies:
                    if (keywords in p.title.lower() or
                        keywords in (p.content or "").lower() or
                        keywords in (p.keywords or "").lower()):
                        filtered.append(p)
                policies = filtered

            return {
                "policies": [
                    {
                        "policy_id": p.policy_id,
                        "title": p.title,
                        "category": p.category,
                        "effective_date": p.effective_date.isoformat() if p.effective_date else None,
                        "status": p.status,
                        "summary": (p.content[:200] + "...") if p.content and len(p.content) > 200 else p.content,
                    }
                    for p in policies
                ],
                "total": len(policies),
            }

        @self.tool(
            name="get_policy",
            description="根据ID获取政策详情",
            input_schema={
                "type": "object",
                "required": ["policy_id"],
                "properties": {
                    "policy_id": {
                        "type": "string",
                        "description": "政策ID",
                    },
                },
            },
        )
        async def get_policy(params: Dict[str, Any]) -> Dict[str, Any]:
            policy = await PolicyCRUD.get_by_id(params["policy_id"])
            if not policy:
                return {"error": "政策不存在", "error_code": "NOT_FOUND"}

            return {
                "policy_id": policy.policy_id,
                "title": policy.title,
                "category": policy.category,
                "content": policy.content,
                "keywords": policy.keywords,
                "effective_date": policy.effective_date.isoformat() if policy.effective_date else None,
                "expiry_date": policy.expiry_date.isoformat() if policy.expiry_date else None,
                "status": policy.status,
            }

        @self.tool(
            name="search_policy_semantic",
            description="语义搜索政策（使用向量检索）",
            input_schema={
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回数量，默认 5",
                    },
                },
            },
        )
        async def search_policy_semantic(params: Dict[str, Any]) -> Dict[str, Any]:
            query = params["query"]
            top_k = params.get("top_k", 5)

            vector_store = await self._get_vector_store()
            if vector_store:
                try:
                    results = vector_store.search_policies(query, n_results=top_k)
                    return {
                        "policies": [
                            {
                                "policy_id": r.get("metadata", {}).get("policy_id", ""),
                                "title": r.get("metadata", {}).get("title", ""),
                                "content": r.get("content", ""),
                                "relevance": 1 - r.get("distance", 0),
                            }
                            for r in results
                        ],
                        "mode": "vector_search",
                        "total": len(results),
                    }
                except Exception as e:
                    pass  # 降级到数据库搜索

            # 降级：数据库文本搜索
            policies = await PolicyCRUD.search(query, limit=top_k)
            return {
                "policies": [
                    {
                        "policy_id": p.policy_id,
                        "title": p.title,
                        "content": p.content[:500] if p.content else "",
                    }
                    for p in policies
                ],
                "mode": "text_search",
                "total": len(policies),
            }

        # ==================== 合规检查工具 ====================

        @self.tool(
            name="check_compliance",
            description="检查操作是否符合合规要求",
            input_schema={
                "type": "object",
                "required": ["check_type", "params"],
                "properties": {
                    "check_type": {
                        "type": "string",
                        "description": "检查类型：amount_limit/supplier_rating/product_category",
                    },
                    "params": {
                        "type": "object",
                        "description": "检查参数",
                    },
                },
            },
        )
        async def check_compliance(params: Dict[str, Any]) -> Dict[str, Any]:
            check_type = params["check_type"]
            check_params = params.get("params", {})

            if check_type == "amount_limit":
                return await self._check_amount_limit(check_params)
            elif check_type == "supplier_rating":
                return await self._check_supplier_rating(check_params)
            elif check_type == "product_category":
                return await self._check_product_category(check_params)
            else:
                return {
                    "error": f"未知的检查类型: {check_type}",
                    "error_code": "INVALID_CHECK_TYPE",
                }

        @self.tool(
            name="assess_risk",
            description="评估业务操作风险",
            input_schema={
                "type": "object",
                "required": ["operation_type"],
                "properties": {
                    "operation_type": {
                        "type": "string",
                        "description": "操作类型：purchase/production/sales",
                    },
                    "context": {
                        "type": "object",
                        "description": "操作上下文",
                    },
                },
            },
        )
        async def assess_risk(params: Dict[str, Any]) -> Dict[str, Any]:
            operation_type = params["operation_type"]
            context = params.get("context", {})

            # 基于操作类型的风险评估
            risks = []

            if operation_type == "purchase":
                # 检查金额风险
                amount = context.get("amount", 0)
                if amount > 100000:
                    risks.append({
                        "type": "high_value",
                        "level": "high",
                        "description": "大额采购需要高级审批",
                        "mitigation": "提交给财务总监审批",
                    })
                elif amount > 50000:
                    risks.append({
                        "type": "medium_value",
                        "level": "medium",
                        "description": "中等金额采购需要经理审批",
                        "mitigation": "提交给部门经理审批",
                    })

                # 检查供应商风险
                supplier_rating = context.get("supplier_rating", 5)
                if supplier_rating < 3.5:
                    risks.append({
                        "type": "supplier_rating",
                        "level": "high",
                        "description": f"供应商评分过低: {supplier_rating}",
                        "mitigation": "建议选择其他供应商或进行现场审核",
                    })

            elif operation_type == "production":
                # 检查产能风险
                capacity = context.get("capacity_usage", 0)
                if capacity > 0.9:
                    risks.append({
                        "type": "capacity",
                        "level": "medium",
                        "description": f"产能利用率过高: {capacity*100:.1f}%",
                        "mitigation": "考虑外协或扩产",
                    })

            # 计算总体风险等级
            if any(r["level"] == "high" for r in risks):
                overall_level = "high"
            elif any(r["level"] == "medium" for r in risks):
                overall_level = "medium"
            else:
                overall_level = "low"

            return {
                "operation_type": operation_type,
                "overall_risk_level": overall_level,
                "risks": risks,
                "recommendations": [r["mitigation"] for r in risks],
            }

        @self.tool(
            name="health_check",
            description="检查服务器健康状态",
            input_schema={
                "type": "object",
                "properties": {},
            },
        )
        async def health_check(params: Dict[str, Any]) -> Dict[str, Any]:
            try:
                pool = await get_database_pool()
                result = await pool.fetchval("SELECT 1")
                return {
                    "status": "healthy",
                    "server": self.name,
                    "version": self.version,
                    "database": "connected",
                    "vector_store": "available" if self._vector_store else "unavailable",
                }
            except Exception as e:
                return {
                    "status": "unhealthy",
                    "server": self.name,
                    "error": str(e),
                }

    # ==================== 内部检查方法 ====================

    async def _check_amount_limit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """检查金额限制"""
        amount = params.get("amount", 0)
        department = params.get("department", "general")

        # 规则：不同金额级别需要不同审批
        if amount > 100000:
            return {
                "compliant": False,
                "reason": "金额超过10万，需要财务总监审批",
                "required_approval": "cfo",
                "rules_applied": ["amount_limit_high"],
            }
        elif amount > 50000:
            return {
                "compliant": False,
                "reason": "金额超过5万，需要部门经理审批",
                "required_approval": "manager",
                "rules_applied": ["amount_limit_medium"],
            }
        elif amount > 10000:
            return {
                "compliant": True,
                "reason": "金额在正常范围内，但建议备案",
                "required_approval": None,
                "rules_applied": ["amount_limit_low"],
            }
        else:
            return {
                "compliant": True,
                "reason": "金额在自动审批范围内",
                "required_approval": None,
                "rules_applied": ["amount_limit_auto"],
            }

    async def _check_supplier_rating(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """检查供应商评分"""
        from opspilot.db.crud import SupplierCRUD

        supplier_id = params.get("supplier_id")
        if not supplier_id:
            return {"error": "缺少supplier_id", "error_code": "MISSING_PARAM"}

        supplier = await SupplierCRUD.get_by_id(supplier_id)
        if not supplier:
            return {"error": "供应商不存在", "error_code": "SUPPLIER_NOT_FOUND"}

        rating = float(supplier.rating)

        if rating >= 4.5:
            return {
                "compliant": True,
                "reason": f"供应商评分优秀: {rating}",
                "supplier_id": supplier_id,
                "supplier_name": supplier.name,
                "rating": rating,
            }
        elif rating >= 3.5:
            return {
                "compliant": True,
                "reason": f"供应商评分合格: {rating}",
                "supplier_id": supplier_id,
                "supplier_name": supplier.name,
                "rating": rating,
                "warning": "建议定期评估供应商表现",
            }
        else:
            return {
                "compliant": False,
                "reason": f"供应商评分过低: {rating}，不满足合作要求",
                "supplier_id": supplier_id,
                "supplier_name": supplier.name,
                "rating": rating,
                "required_action": "需要特殊审批或更换供应商",
            }

    async def _check_product_category(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """检查产品类别合规性"""
        category = params.get("category", "")
        restricted_categories = ["危险品", "管制物品", "特殊材料"]

        if category in restricted_categories:
            return {
                "compliant": False,
                "reason": f"产品类别 '{category}' 需要特殊资质",
                "category": category,
                "required_docs": ["安全许可证", "经营资质"],
            }
        else:
            return {
                "compliant": True,
                "reason": "产品类别符合要求",
                "category": category,
            }


# 便捷函数：创建并运行 Server
def run_server(mode: str = "stdio", **kwargs):
    """启动 Compliance MCP Server"""
    server = ComplianceMCPServer()
    server.run(mode=mode, **kwargs)


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    run_server(mode=mode)
