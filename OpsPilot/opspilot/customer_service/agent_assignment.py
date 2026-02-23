"""
工单智能分配

职责：技能匹配、负载均衡、智能调度客服/Agent
"""
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime, timedelta
import random


class AgentSkill(str, Enum):
    """客服技能"""
    ORDER = "order"           # 订单处理
    LOGISTICS = "logistics"   # 物流处理
    REFUND = "refund"        # 退款处理
    COMPLAINT = "complaint"   # 投诉处理
    TECHNICAL = "technical"   # 技术支持
    SALES = "sales"          # 售前咨询
    GENERAL = "general"       # 一般咨询


class AgentStatus(str, Enum):
    """客服状态"""
    AVAILABLE = "available"     # 可用
    BUSY = "busy"             # 忙碌
    OFFLINE = "offline"       # 离线
    BREAK = "break"           # 休息


class CustomerServiceAgent:
    """
    客服代表
    
    代表可以处理工单的客服或Agent
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        skills: List[AgentSkill],
        max_concurrent: int = 5,
    ):
        self.agent_id = agent_id
        self.name = name
        self.skills = skills
        self.max_concurrent = max_concurrent
        self.status = AgentStatus.AVAILABLE
        self.current_load = 0
        self.total_handled = 0
        self.avg_rating = 4.5
        self.joined_at = datetime.now().isoformat()
        self.last_active = datetime.now().isoformat()
    
    def can_handle(self, required_skills: List[AgentSkill]) -> bool:
        """检查是否可以处理"""
        if self.status != AgentStatus.AVAILABLE:
            return False
        if self.current_load >= self.max_concurrent:
            return False
        # 检查技能匹配
        return any(skill in self.skills for skill in required_skills)
    
    def assign_ticket(self) -> bool:
        """分配工单"""
        if self.can_handle([]):
            self.current_load += 1
            self.last_active = datetime.now().isoformat()
            return True
        return False
    
    def release_ticket(self):
        """释放工单"""
        self.current_load = max(0, self.current_load - 1)
        if self.current_load == 0:
            self.status = AgentStatus.AVAILABLE
    
    def get_workload(self) -> float:
        """获取工作负载百分比"""
        return self.current_load / self.max_concurrent if self.max_concurrent > 0 else 0


class AgentAssignment:
    """
    智能分配器
    
    支持技能匹配、负载均衡、轮询分配
    """
    
    def __init__(self):
        # 客服池
        self.agents: Dict[str, CustomerServiceAgent] = {}
        
        # 分配策略
        self.strategy = "skill_load"  # skill_load / round_robin / least_loaded
        
        # 初始化默认客服
        self._init_default_agents()
    
    def _init_default_agents(self):
        """初始化默认客服"""
        default_agents = [
            {"id": "agent_001", "name": "张三", "skills": [AgentSkill.ORDER, AgentSkill.GENERAL]},
            {"id": "agent_002", "name": "李四", "skills": [AgentSkill.LOGISTICS, AgentSkill.GENERAL]},
            {"id": "agent_003", "name": "王五", "skills": [AgentSkill.REFUND, AgentSkill.ORDER]},
            {"id": "agent_004", "name": "赵六", "skills": [AgentSkill.COMPLAINT, AgentSkill.GENERAL]},
            {"id": "agent_005", "name": "钱七", "skills": [AgentSkill.TECHNICAL, AgentSkill.GENERAL]},
            {"id": "agent_006", "name": "孙八", "skills": [AgentSkill.SALES, AgentSkill.GENERAL]},
        ]
        
        for agent_data in default_agents:
            agent = CustomerServiceAgent(
                agent_id=agent_data["id"],
                name=agent_data["name"],
                skills=agent_data["skills"],
            )
            self.agents[agent_data["id"]] = agent
    
    def add_agent(
        self,
        agent_id: str,
        name: str,
        skills: List[AgentSkill],
        max_concurrent: int = 5,
    ) -> bool:
        """添加客服"""
        if agent_id in self.agents:
            return False
        
        agent = CustomerServiceAgent(agent_id, name, skills, max_concurrent)
        self.agents[agent_id] = agent
        return True
    
    def remove_agent(self, agent_id: str) -> bool:
        """移除客服"""
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        if agent.current_load > 0:
            return False
        
        del self.agents[agent_id]
        return True
    
    def assign(
        self,
        ticket_data: Dict[str, Any],
        required_skills: Optional[List[AgentSkill]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        分配工单
        
        Args:
            ticket_data: 工单数据
            required_skills: 所需技能
        
        Returns:
            分配结果，包含agent信息
        """
        required_skills = required_skills or []
        
        # 根据策略选择客服
        if self.strategy == "skill_load":
            agent = self._assign_by_skill_load(required_skills)
        elif self.strategy == "least_loaded":
            agent = self._assign_by_least_loaded(required_skills)
        elif self.strategy == "round_robin":
            agent = self._assign_by_round_robin(required_skills)
        else:
            agent = self._assign_by_skill_load(required_skills)
        
        if not agent:
            return {
                "success": False,
                "error": "没有可用的客服",
            }
        
        # 分配工单
        agent.assign_ticket()
        
        return {
            "success": True,
            "agent_id": agent.agent_id,
            "agent_name": agent.name,
            "assigned_at": datetime.now().isoformat(),
            "estimated_wait_time": self._estimate_wait_time(agent),
        }
    
    def release(self, agent_id: str) -> bool:
        """释放客服（工单处理完成）"""
        if agent_id not in self.agents:
            return False
        
        self.agents[agent_id].release_ticket()
        self.agents[agent_id].total_handled += 1
        return True
    
    def get_available_agents(
        self,
        required_skills: Optional[List[AgentSkill]] = None,
    ) -> List[Dict[str, Any]]:
        """获取可用客服列表"""
        required_skills = required_skills or []
        available = []
        
        for agent in self.agents.values():
            if agent.can_handle(required_skills):
                available.append({
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "skills": [s.value for s in agent.skills],
                    "current_load": agent.current_load,
                    "max_concurrent": agent.max_concurrent,
                    "workload": agent.get_workload(),
                    "total_handled": agent.total_handled,
                    "avg_rating": agent.avg_rating,
                })
        
        return available
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取客服状态"""
        if agent_id not in self.agents:
            return None
        
        agent = self.agents[agent_id]
        return {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "status": agent.status.value,
            "current_load": agent.current_load,
            "max_concurrent": agent.max_concurrent,
            "workload": agent.get_workload(),
            "total_handled": agent.total_handled,
            "avg_rating": agent.avg_rating,
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取分配统计"""
        total_agents = len(self.agents)
        available = sum(1 for a in self.agents.values() if a.status == AgentStatus.AVAILABLE)
        busy = sum(1 for a in self.agents.values() if a.status == AgentStatus.BUSY)
        total_load = sum(a.current_load for a in self.agents.values())
        total_capacity = sum(a.max_concurrent for a in self.agents.values())
        
        return {
            "total_agents": total_agents,
            "available": available,
            "busy": busy,
            "offline": total_agents - available - busy,
            "total_load": total_load,
            "total_capacity": total_capacity,
            "utilization_rate": total_load / total_capacity if total_capacity > 0 else 0,
            "total_handled": sum(a.total_handled for a in self.agents.values()),
        }
    
    def _assign_by_skill_load(self, required_skills: List[AgentSkill]) -> Optional[CustomerServiceAgent]:
        """技能+负载分配"""
        candidates = []
        
        for agent in self.agents.values():
            if not agent.can_handle(required_skills):
                continue
            
            # 计算技能匹配度
            skill_match = sum(1 for s in required_skills if s in agent.skills)
            if skill_match == 0 and required_skills:
                continue
            
            # 优先选择有匹配技能且负载低的
            score = skill_match * 10 - agent.get_workload() * 5
            candidates.append((score, agent))
        
        if not candidates:
            return None
        
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]
    
    def _assign_by_least_loaded(self, required_skills: List[AgentSkill]) -> Optional[CustomerServiceAgent]:
        """最少负载分配"""
        candidates = []
        
        for agent in self.agents.values():
            if not agent.can_handle(required_skills):
                continue
            candidates.append((agent.get_workload(), agent))
        
        if not candidates:
            return None
        
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]
    
    def _assign_by_round_robin(self, required_skills: List[AgentSkill]) -> Optional[CustomerServiceAgent]:
        """轮询分配"""
        # 按负载排序
        sorted_agents = sorted(
            self.agents.values(),
            key=lambda a: (a.status != AgentStatus.AVAILABLE, a.get_workload())
        )
        
        for agent in sorted_agents:
            if agent.can_handle(required_skills):
                return agent
        
        return None
    
    def _estimate_wait_time(self, agent: CustomerServiceAgent) -> int:
        """估算等待时间（分钟）"""
        # 简单估算：每个工单5分钟
        return agent.current_load * 5


# 全局分配器
_agent_assignment: Optional[AgentAssignment] = None


def get_agent_assignment() -> AgentAssignment:
    """获取分配器实例"""
    global _agent_assignment
    if _agent_assignment is None:
        _agent_assignment = AgentAssignment()
    return _agent_assignment
