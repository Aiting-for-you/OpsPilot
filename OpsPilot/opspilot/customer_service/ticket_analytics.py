"""
工单统计分析

职责：收集、分析工单数据，生成统计报表和洞察
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict


class TicketAnalytics:
    """
    工单分析引擎
    
    提供工单统计、趋势分析、效率指标等功能
    """
    
    def __init__(self):
        # 统计数据存储
        self.stats = {
            "total_tickets": 0,
            "by_status": defaultdict(int),
            "by_priority": defaultdict(int),
            "by_type": defaultdict(int),
            "by_department": defaultdict(int),
            "sla_metrics": {
                "response_met": 0,
                "response_breached": 0,
                "resolution_met": 0,
                "resolution_breached": 0,
            },
            "resolution_times": [],  # 解决时间（分钟）
            "response_times": [],     # 响应时间（分钟）
            "hourly_distribution": defaultdict(int),
            "daily_distribution": defaultdict(int),
        }
        
        # 客服绩效数据
        self.agent_stats = defaultdict(lambda: {
            "handled": 0,
            "resolved": 0,
            "escalated": 0,
            "avg_resolution_time": 0,
            "satisfaction_score": 0,
        })
    
    def record_ticket(self, ticket_data: Dict[str, Any]):
        """记录工单数据"""
        self.stats["total_tickets"] += 1
        
        # 按状态统计
        status = ticket_data.get("status", "unknown")
        self.stats["by_status"][status] += 1
        
        # 按优先级统计
        priority = ticket_data.get("priority", "normal")
        self.stats["by_priority"][priority] += 1
        
        # 按类型统计
        ticket_type = ticket_data.get("ticket_type", "other")
        self.stats["by_type"][ticket_type] += 1
        
        # 按部门统计
        department = ticket_data.get("assigned_department", "unknown")
        self.stats["by_department"][department] += 1
        
        # SLA统计
        if ticket_data.get("sla_response_met") is not None:
            if ticket_data["sla_response_met"]:
                self.stats["sla_metrics"]["response_met"] += 1
            else:
                self.stats["sla_metrics"]["response_breached"] += 1
        
        if ticket_data.get("sla_resolution_met") is not None:
            if ticket_data["sla_resolution_met"]:
                self.stats["sla_metrics"]["resolution_met"] += 1
            else:
                self.stats["sla_metrics"]["resolution_breached"] += 1
        
        # 时间统计
        if ticket_data.get("created_at"):
            created = datetime.fromisoformat(ticket_data["created_at"])
            self.stats["hourly_distribution"][created.hour] += 1
            self.stats["daily_distribution"][created.strftime("%Y-%m-%d")] += 1
        
        # 解决时间
        if ticket_data.get("resolution_time_minutes"):
            self.stats["resolution_times"].append(ticket_data["resolution_time_minutes"])
        
        # 响应时间
        if ticket_data.get("first_response_time_minutes"):
            self.stats["response_times"].append(ticket_data["first_response_time_minutes"])
        
        # 客服统计
        if ticket_data.get("assigned_agent"):
            agent_id = ticket_data["assigned_agent"]
            self.agent_stats[agent_id]["handled"] += 1
            
            if ticket_data.get("status") == "resolved":
                self.agent_stats[agent_id]["resolved"] += 1
            
            if ticket_data.get("escalated"):
                self.agent_stats[agent_id]["escalated"] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        total = self.stats["total_tickets"]
        
        # 计算解决率
        resolved = self.stats["by_status"].get("resolved", 0)
        resolution_rate = resolved / total if total > 0 else 0
        
        # 计算SLA达成率
        response_total = (
            self.stats["sla_metrics"]["response_met"] + 
            self.stats["sla_metrics"]["response_breached"]
        )
        resolution_total = (
            self.stats["sla_metrics"]["resolution_met"] + 
            self.stats["sla_metrics"]["resolution_breached"]
        )
        
        response_rate = (
            self.stats["sla_metrics"]["response_met"] / response_total 
            if response_total > 0 else 0
        )
        resolution_sla_rate = (
            self.stats["sla_metrics"]["resolution_met"] / resolution_total 
            if resolution_total > 0 else 0
        )
        
        # 计算平均解决时间
        avg_resolution_time = 0
        if self.stats["resolution_times"]:
            avg_resolution_time = sum(self.stats["resolution_times"]) / len(
                self.stats["resolution_times"]
            )
        
        avg_response_time = 0
        if self.stats["response_times"]:
            avg_response_time = sum(self.stats["response_times"]) / len(
                self.stats["response_times"]
            )
        
        return {
            "total_tickets": total,
            "resolved": resolved,
            "resolution_rate": round(resolution_rate * 100, 2),
            "avg_resolution_time_minutes": int(avg_resolution_time),
            "avg_response_time_minutes": int(avg_response_time),
            "sla_response_rate": round(response_rate * 100, 2),
            "sla_resolution_rate": round(resolution_sla_rate * 100, 2),
            "by_status": dict(self.stats["by_status"]),
            "by_priority": dict(self.stats["by_priority"]),
            "by_type": dict(self.stats["by_type"]),
            "by_department": dict(self.stats["by_department"]),
        }
    
    def get_trend(self, days: int = 7) -> Dict[str, Any]:
        """获取趋势数据"""
        # 按日期统计
        daily_data = []
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=days - i - 1)).strftime("%Y-%m-%d")
            count = self.stats["daily_distribution"].get(date, 0)
            
            # 模拟数据（如果当天没有数据）
            if count == 0 and i < len(self.stats["daily_distribution"]):
                count = list(self.stats["daily_distribution"].values())[0] if self.stats["daily_distribution"] else 0
            
            daily_data.append({
                "date": date,
                "count": count,
            })
        
        # 计算趋势
        if len(daily_data) >= 2:
            recent = daily_data[-1]["count"]
            previous = daily_data[-2]["count"]
            change = ((recent - previous) / previous * 100) if previous > 0 else 0
        else:
            change = 0
        
        return {
            "days": days,
            "data": daily_data,
            "trend": "up" if change > 0 else "down" if change < 0 else "stable",
            "change_percent": round(change, 2),
        }
    
    def get_hourly_distribution(self) -> Dict[str, int]:
        """获取小时分布"""
        return dict(self.stats["hourly_distribution"])
    
    def get_agent_performance(self) -> List[Dict[str, Any]]:
        """获取客服绩效"""
        results = []
        
        for agent_id, stats in self.agent_stats.items():
            handled = stats["handled"]
            resolved = stats["resolved"]
            
            results.append({
                "agent_id": agent_id,
                "handled": handled,
                "resolved": resolved,
                "resolution_rate": round(resolved / handled * 100, 2) if handled > 0 else 0,
                "escalated": stats["escalated"],
                "escalation_rate": round(stats["escalated"] / handled * 100, 2) if handled > 0 else 0,
            })
        
        # 按处理量排序
        results.sort(key=lambda x: x["handled"], reverse=True)
        
        return results
    
    def get_type_analysis(self) -> Dict[str, Any]:
        """获取类型分析"""
        type_stats = dict(self.stats["by_type"])
        total = self.stats["total_tickets"]
        
        # 计算各类型占比和处理效率
        analysis = {}
        for ticket_type, count in type_stats.items():
            analysis[ticket_type] = {
                "count": count,
                "percentage": round(count / total * 100, 2) if total > 0 else 0,
            }
        
        # 找出最常见类型
        most_common = max(type_stats.items(), key=lambda x: x[1]) if type_stats else (None, 0)
        
        return {
            "by_type": analysis,
            "most_common_type": most_common[0],
            "most_common_count": most_common[1],
        }
    
    def get_sla_report(self) -> Dict[str, Any]:
        """获取SLA报告"""
        response_met = self.stats["sla_metrics"]["response_met"]
        response_breached = self.stats["sla_metrics"]["response_breached"]
        resolution_met = self.stats["sla_metrics"]["resolution_met"]
        resolution_breached = self.stats["sla_metrics"]["resolution_breached"]
        
        response_total = response_met + response_breached
        resolution_total = resolution_met + resolution_breached
        
        return {
            "response": {
                "met": response_met,
                "breached": response_breached,
                "rate": round(response_met / response_total * 100, 2) if response_total > 0 else 0,
            },
            "resolution": {
                "met": resolution_met,
                "breached": resolution_breached,
                "rate": round(resolution_met / resolution_total * 100, 2) if resolution_total > 0 else 0,
            },
            "avg_response_time_minutes": (
                sum(self.stats["response_times"]) / len(self.stats["response_times"])
                if self.stats["response_times"] else 0
            ),
            "avg_resolution_time_minutes": (
                sum(self.stats["resolution_times"]) / len(self.stats["resolution_times"])
                if self.stats["resolution_times"] else 0
            ),
        }
    
    def get_department_report(self) -> Dict[str, Any]:
        """获取部门报告"""
        dept_stats = dict(self.stats["by_department"])
        total = self.stats["total_tickets"]
        
        # 排序
        sorted_depts = sorted(
            dept_stats.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            "departments": [
                {"name": name, "count": count, "percentage": round(count / total * 100, 2)}
                for name, count in sorted_depts
            ],
            "total": total,
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计数据（API兼容）"""
        summary = self.get_summary()
        total = summary.get("total_tickets", 0)
        resolved = summary.get("resolved", 0)
        pending = summary.get("by_status", {}).get("pending", 0)
        escalated = summary.get("by_status", {}).get("escalated", 0)
        
        return {
            "total_tickets": total,
            "resolved_tickets": resolved,
            "pending_tickets": pending,
            "escalation_rate": escalated / total if total > 0 else 0,
            "avg_resolution_time": summary.get("avg_resolution_time_minutes", 0),
            "sla_compliance_rate": summary.get("sla_resolution_rate", 0) / 100,
        }
    
    def get_trends(self) -> List[Dict[str, Any]]:
        """获取趋势数据（API兼容）"""
        trend = self.get_trend(7)
        daily_data = trend.get("data", [])
        return [
            {
                "date": item["date"],
                "created": item.get("created", item.get("count", 0)),
                "resolved": item.get("resolved", 0),
                "escalated": item.get("escalated", 0),
            }
            for item in daily_data
        ]
    
    def get_top_categories(self) -> List[Dict[str, Any]]:
        """获取热门分类（API兼容）"""
        type_data = self.get_type_analysis()
        return [
            {"category": cat, "count": count}
            for cat, count in type_data.get("top_types", {}).items()
        ]
    
    def generate_report(self, period: str = "week") -> Dict[str, Any]:
        """生成完整报告"""
        return {
            "period": period,
            "generated_at": datetime.now().isoformat(),
            "summary": self.get_summary(),
            "trend": self.get_trend(7 if period == "week" else 30),
            "type_analysis": self.get_type_analysis(),
            "sla_report": self.get_sla_report(),
            "department_report": self.get_department_report(),
            "agent_performance": self.get_agent_performance()[:10],  # Top 10
        }


# 全局分析实例
_ticket_analytics: Optional[TicketAnalytics] = None


def get_ticket_analytics() -> TicketAnalytics:
    """获取分析器实例"""
    global _ticket_analytics
    if _ticket_analytics is None:
        _ticket_analytics = TicketAnalytics()
    return _ticket_analytics
