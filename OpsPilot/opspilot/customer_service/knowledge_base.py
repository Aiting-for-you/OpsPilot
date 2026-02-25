"""
工单知识库

职责：存储和管理常见问题解决方案，支持语义检索
"""
from typing import Optional, Dict, Any, List
from enum import Enum
import json
from datetime import datetime


class KnowledgeCategory(str, Enum):
    """知识类别"""
    ORDER = "order"           # 订单问题
    LOGISTICS = "logistics"   # 物流问题
    REFUND = "refund"        # 退款问题
    PRODUCT = "product"       # 产品咨询
    COMPLAINT = "complaint"   # 投诉处理
    TECHNICAL = "technical"   # 技术问题
    POLICY = "policy"         # 政策规则
    OTHER = "other"           # 其他


class KnowledgeBase:
    """
    知识库管理
    
    提供知识存储、检索、更新功能
    """
    
    def __init__(self):
        # 知识存储
        self.knowledge_store: Dict[str, Dict[str, Any]] = {}
        # 索引缓存
        self.index_cache: Dict[str, List[str]] = {}
        # 初始化Mock数据
        self._init_mock_data()
    
    def _init_mock_data(self):
        """初始化Mock知识数据"""
        mock_knowledge = [
            {
                "id": "KB001",
                "category": KnowledgeCategory.ORDER.value,
                "title": "订单状态查询",
                "keywords": ["订单状态", "查询订单", "订单进度"],
                "problem": "如何查询订单状态？",
                "solution": "您可以通过以下方式查询订单状态：\n1. 登录APP → 我的 → 订单列表\n2. 拨打客服热线400-xxx-xxxx\n3. 登录官网 → 我的订单",
                "applicable_scenarios": ["订单问题", "物流查询"],
                "satisfaction_rate": 0.95,
                "usage_count": 1523,
            },
            {
                "id": "KB002",
                "category": KnowledgeCategory.ORDER.value,
                "title": "订单修改",
                "keywords": ["修改订单", "更改地址", "修改电话"],
                "problem": "如何修改已提交的订单？",
                "solution": "订单未发货前可修改：\n1. 登录APP → 订单详情 → 修改订单\n2. 联系客服协助修改\n注意：已发货订单无法修改",
                "applicable_scenarios": ["订单修改", "地址变更"],
                "satisfaction_rate": 0.88,
                "usage_count": 892,
            },
            {
                "id": "KB003",
                "category": KnowledgeCategory.REFUND.value,
                "title": "退款流程",
                "keywords": ["退款", "申请退款", "退货退款"],
                "problem": "如何申请退款？",
                "solution": "退款申请流程：\n1. APP → 订单 → 申请退款\n2. 选择退款原因\n3. 提交审核（1-3个工作日）\n4. 退款原路返回",
                "applicable_scenarios": ["退款申请", "退货"],
                "satisfaction_rate": 0.92,
                "usage_count": 2341,
            },
            {
                "id": "KB004",
                "category": KnowledgeCategory.LOGISTICS.value,
                "title": "物流查询",
                "keywords": ["物流", "快递", "运输", "发货"],
                "problem": "如何查询物流信息？",
                "solution": "查询物流方式：\n1. APP订单详情查看\n2. 点击物流单号跳转快递官网\n3. 短信物流通知链接",
                "applicable_scenarios": ["物流查询", "快递查询"],
                "satisfaction_rate": 0.97,
                "usage_count": 3892,
            },
            {
                "id": "KB005",
                "category": KnowledgeCategory.TECHNICAL.value,
                "title": "账户登录问题",
                "keywords": ["登录", "验证码", "密码", "账户异常"],
                "problem": "无法登录账号怎么办？",
                "solution": "登录问题解决方案：\n1. 确认网络正常\n2. 清除缓存后重试\n3. 验证码问题：点击重新发送\n4. 密码找回：通过手机号重置\n5. 仍无法解决请联系客服",
                "applicable_scenarios": ["登录问题", "账户异常"],
                "satisfaction_rate": 0.85,
                "usage_count": 1234,
            },
            {
                "id": "KB006",
                "category": KnowledgeCategory.COMPLAINT.value,
                "title": "投诉处理",
                "keywords": ["投诉", "差评", "不满", "服务投诉"],
                "problem": "如何提交投诉？",
                "solution": "投诉提交方式：\n1. APP → 客服 → 投诉建议\n2. 拨打客服热线\n3. 发送邮件至 complaint@company.com\n我们会在24小时内处理并回复",
                "applicable_scenarios": ["客户投诉", "服务反馈"],
                "satisfaction_rate": 0.78,
                "usage_count": 456,
            },
            {
                "id": "KB007",
                "category": KnowledgeCategory.POLICY.value,
                "title": "7天无理由退货",
                "keywords": ["7天无理由", "退货政策", "退货规则"],
                "problem": "7天无理由退货规则",
                "solution": "7天无理由退货说明：\n1. 商品完好未使用\n2. 包装完整\n3. 附件齐全\n4. 运费说明：非质量问题运费自理\n5. 特殊商品除外",
                "applicable_scenarios": ["退货政策", "售后规则"],
                "satisfaction_rate": 0.91,
                "usage_count": 1876,
            },
            {
                "id": "KB008",
                "category": KnowledgeCategory.PRODUCT.value,
                "title": "产品咨询",
                "keywords": ["产品信息", "规格", "参数", "功能"],
                "problem": "如何了解产品详细信息？",
                "solution": "了解产品方式：\n1. 商品详情页查看\n2. 产品说明书\n3. 咨询在线客服\n4. 拨打产品咨询热线",
                "applicable_scenarios": ["产品咨询", "产品信息"],
                "satisfaction_rate": 0.89,
                "usage_count": 987,
            },
        ]
        
        # 存入知识库
        for kb in mock_knowledge:
            self.knowledge_store[kb["id"]] = kb
        
        # 构建索引
        self._build_index()
    
    def _build_index(self):
        """构建关键词索引"""
        self.index_cache = {}
        
        for kb_id, kb_data in self.knowledge_store.items():
            # 按类别索引
            category = kb_data.get("category", "other")
            if category not in self.index_cache:
                self.index_cache[category] = []
            self.index_cache[category].append(kb_id)
            
            # 按关键词索引
            for keyword in kb_data.get("keywords", []):
                if keyword not in self.index_cache:
                    self.index_cache[keyword] = []
                if kb_id not in self.index_cache[keyword]:
                    self.index_cache[keyword].append(kb_id)
    
    async def search_solution(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        搜索解决方案
        
        Args:
            query: 查询内容
            category: 可选，按类别筛选
            top_k: 返回结果数量
        """
        query_lower = query.lower()
        query_keywords = query_lower.split()
        
        # 计算相关性分数
        scored_results = []
        
        for kb_id, kb_data in self.knowledge_store.items():
            # 类别过滤
            if category and kb_data.get("category") != category:
                continue
            
            score = 0.0
            
            # 标题匹配
            if any(kw in kb_data.get("title", "").lower() for kw in query_keywords):
                score += 3.0
            
            # 关键词匹配
            for kw in query_keywords:
                if kw in kb_data.get("keywords", []):
                    score += 2.0
                if kw in kb_data.get("problem", "").lower():
                    score += 1.0
                if kw in kb_data.get("solution", "").lower():
                    score += 0.5
            
            # 全文包含度
            full_text = f"{kb_data.get('title', '')} {kb_data.get('problem', '')} {kb_data.get('solution', '')}"
            if query_lower in full_text:
                score += 2.0
            
            if score > 0:
                # 增加使用次数权重
                usage_weight = min(kb_data.get("usage_count", 0) / 10000, 0.5)
                score += usage_weight
                
                scored_results.append({
                    "id": kb_id,
                    "score": score,
                    **kb_data,
                })
        
        # 按分数排序
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        
        return scored_results[:top_k]
    
    async def add_knowledge(self, knowledge: Dict[str, Any]) -> str:
        """添加知识"""
        kb_id = f"KB{len(self.knowledge_store) + 1:03d}"
        knowledge["id"] = kb_id
        knowledge["created_at"] = datetime.now().isoformat()
        knowledge["usage_count"] = 0
        knowledge["satisfaction_rate"] = 0.0
        
        self.knowledge_store[kb_id] = knowledge
        self._build_index()
        
        return kb_id
    
    async def update_knowledge(
        self,
        kb_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """更新知识"""
        if kb_id not in self.knowledge_store:
            return False
        
        self.knowledge_store[kb_id].update(updates)
        self.knowledge_store[kb_id]["updated_at"] = datetime.now().isoformat()
        
        self._build_index()
        return True
    
    async def delete_knowledge(self, kb_id: str) -> bool:
        """删除知识"""
        if kb_id not in self.knowledge_store:
            return False
        
        del self.knowledge_store[kb_id]
        self._build_index()
        return True
    
    def get_knowledge(self, kb_id: str) -> Optional[Dict[str, Any]]:
        """获取知识详情"""
        return self.knowledge_store.get(kb_id)
    
    def list_knowledge(
        self,
        category: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """列出知识"""
        results = []
        
        for kb_data in self.knowledge_store.values():
            if category and kb_data.get("category") != category:
                continue
            results.append(kb_data)
        
        # 按使用次数排序
        results.sort(key=lambda x: x.get("usage_count", 0), reverse=True)
        
        return results[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        categories = {}
        total_usage = 0
        
        for kb_data in self.knowledge_store.values():
            cat = kb_data.get("category", "other")
            categories[cat] = categories.get(cat, 0) + 1
            total_usage += kb_data.get("usage_count", 0)
        
        return {
            "total_knowledge": len(self.knowledge_store),
            "by_category": categories,
            "total_usage_count": total_usage,
            "avg_satisfaction_rate": sum(
                kb.get("satisfaction_rate", 0)
                for kb in self.knowledge_store.values()
            ) / max(len(self.knowledge_store), 1),
        }


# 全局知识库实例
_knowledge_base: Optional[KnowledgeBase] = None


def get_knowledge_base() -> KnowledgeBase:
    """获取知识库实例"""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase()
    return _knowledge_base
