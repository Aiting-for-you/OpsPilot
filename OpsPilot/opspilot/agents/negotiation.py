"""
Agent 博弈仲裁模块

实现多 Agent 协作中的博弈与仲裁机制：
- 多 Agent 提案与投票
- 权重投票机制
- 超时自动仲裁
- 人工介入触发
"""

from enum import Enum
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid
import asyncio
from collections import defaultdict

from opspilot.utils.exceptions import opspilotError


class NegotiationStatus(str, Enum):
    """博弈状态"""
    IN_PROGRESS = "in_progress"  # 进行中
    CONSENSUS = "consensus"       # 达成共识
    TIMEOUT = "timeout"           # 超时仲裁
    MANUAL = "manual"             # 人工介入
    CANCELLED = "cancelled"       # 已取消


class VoteType(str, Enum):
    """投票类型"""
    AGREE = "agree"      # 同意
    DISAGREE = "disagree" # 反对
    ABSTAIN = "abstain"   # 弃权


@dataclass
class AgentProposal:
    """Agent 提案"""
    agent_id: str
    agent_name: str
    agent_role: str  # agent 类型：compliance/finance/legal等
    
    # 提案内容
    proposal: str
    reasoning: str
    data: Dict[str, Any] = field(default_factory=dict)
    
    # 权重（根据专业领域）
    weight: float = 1.0
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "agent_role": self.agent_role,
            "proposal": self.proposal,
            "reasoning": self.reasoning,
            "data": self.data,
            "weight": self.weight,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class AgentVote:
    """Agent 投票"""
    agent_id: str
    agent_name: str
    vote: VoteType
    comment: Optional[str] = None
    weight: float = 1.0
    voted_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "vote": self.vote.value,
            "comment": self.comment,
            "weight": self.weight,
            "voted_at": self.voted_at.isoformat(),
        }


@dataclass
class NegotiationResult:
    """博弈结果"""
    negotiation_id: str
    status: NegotiationStatus
    
    # 提案列表
    proposals: List[AgentProposal] = field(default_factory=list)
    
    # 投票记录
    votes: List[AgentVote] = field(default_factory=list)
    
    # 最终决策
    final_decision: Optional[str] = None
    winner_proposal: Optional[AgentProposal] = None
    
    # 统计信息
    agree_weight: float = 0.0
    disagree_weight: float = 0.0
    divergence_score: float = 0.0  # 分歧值 (0-1)
    
    # 仲裁信息
    arbitrator: Optional[str] = None
    arbitration_reason: Optional[str] = None
    
    # 时间信息
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    rounds: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "negotiation_id": self.negotiation_id,
            "status": self.status.value,
            "proposals": [p.to_dict() for p in self.proposals],
            "votes": [v.to_dict() for v in self.votes],
            "final_decision": self.final_decision,
            "winner_proposal": self.winner_proposal.to_dict() if self.winner_proposal else None,
            "agree_weight": self.agree_weight,
            "disagree_weight": self.disagree_weight,
            "divergence_score": self.divergence_score,
            "arbitrator": self.arbitrator,
            "arbitration_reason": self.arbitration_reason,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "rounds": self.rounds,
        }


class NegotiationError(opspilotError):
    """博弈错误"""
    pass


class AgentNegotiation:
    """
    Agent 博弈仲裁管理器
    
    实现多 Agent 协作中的博弈与决策机制：
    - 多 Agent 提案
    - 权重投票
    - 超时仲裁
    - 人工介入触发
    """
    
    def __init__(
        self,
        max_rounds: int = 5,
        timeout_seconds: int = 300,
        divergence_threshold: float = 0.7,
    ):
        """
        初始化博弈管理器
        
        Args:
            max_rounds: 最大博弈轮次
            timeout_seconds: 超时时间（秒）
            divergence_threshold: 分歧阈值（超过则人工介入）
        """
        self._max_rounds = max_rounds
        self._timeout_seconds = timeout_seconds
        self._divergence_threshold = divergence_threshold
        
        # Agent 权重配置（根据专业领域）
        self._agent_weights: Dict[str, float] = {
            "compliance": 1.5,  # 合规 Agent 权重更高
            "finance": 1.3,    # 财务 Agent 权重较高
            "legal": 1.5,      # 法务 Agent 权重较高
            "buyer": 1.0,      # 采购 Agent 标准权重
            "executor": 1.0,   # 执行 Agent 标准权重
        }
        
        # 存储博弈记录
        self._negotiations: Dict[str, NegotiationResult] = {}
    
    def set_agent_weight(self, agent_role: str, weight: float):
        """
        设置 Agent 权重
        
        Args:
            agent_role: Agent 角色
            weight: 权重值
        """
        self._agent_weights[agent_role] = weight
    
    def get_agent_weight(self, agent_role: str) -> float:
        """获取 Agent 权重"""
        return self._agent_weights.get(agent_role, 1.0)
    
    async def start_negotiation(
        self,
        task_id: str,
        context: Dict[str, Any],
        participants: List[Dict[str, Any]],
    ) -> NegotiationResult:
        """
        启动博弈流程
        
        Args:
            task_id: 任务ID
            context: 任务上下文
            participants: 参与者列表（包含 agent_id, agent_name, agent_role）
            
        Returns:
            NegotiationResult: 博弈结果
        """
        negotiation_id = str(uuid.uuid4())
        
        # 创建博弈记录
        result = NegotiationResult(
            negotiation_id=negotiation_id,
            status=NegotiationStatus.IN_PROGRESS,
        )
        
        self._negotiations[negotiation_id] = result
        
        try:
            # 开始博弈轮次
            for round_num in range(1, self._max_rounds + 1):
                result.rounds = round_num
                
                # 收集提案
                proposals = await self._collect_proposals(
                    participants, context, round_num
                )
                result.proposals.extend(proposals)
                
                # 收集投票
                votes = await self._collect_votes(
                    participants, proposals, round_num
                )
                result.votes.extend(votes)
                
                # 计算投票结果
                self._calculate_vote_result(result)
                
                # 检查是否达成共识
                if self._check_consensus(result):
                    result.status = NegotiationStatus.CONSENSUS
                    result.completed_at = datetime.now()
                    break
                
                # 检查是否需要人工介入
                if result.divergence_score > self._divergence_threshold:
                    result.status = NegotiationStatus.MANUAL
                    result.completed_at = datetime.now()
                    break
            
            # 超过最大轮次，自动仲裁
            if result.status == NegotiationStatus.IN_PROGRESS:
                result = await self._arbitrate(result, arbitrator="orchestrator")
                result.status = NegotiationStatus.TIMEOUT
                result.completed_at = datetime.now()
            
            return result
            
        except Exception as e:
            result.status = NegotiationStatus.CANCELLED
            result.completed_at = datetime.now()
            raise NegotiationError(f"博弈失败: {str(e)}")
    
    async def _collect_proposals(
        self,
        participants: List[Dict[str, Any]],
        context: Dict[str, Any],
        round_num: int,
    ) -> List[AgentProposal]:
        """
        收集 Agent 提案
        
        Args:
            participants: 参与者列表
            context: 任务上下文
            round_num: 轮次
            
        Returns:
            List[AgentProposal]: 提案列表
        """
        proposals = []
        
        # 这里应该调用实际的 Agent 生成提案
        # 当前返回空列表，实际使用时需要实现
        # for participant in participants:
        #     proposal = await self._generate_proposal(participant, context, round_num)
        #     proposals.append(proposal)
        
        return proposals
    
    async def _collect_votes(
        self,
        participants: List[Dict[str, Any]],
        proposals: List[AgentProposal],
        round_num: int,
    ) -> List[AgentVote]:
        """
        收集 Agent 投票
        
        Args:
            participants: 参与者列表
            proposals: 提案列表
            round_num: 轮次
            
        Returns:
            List[AgentVote]: 投票列表
        """
        votes = []
        
        # 这里应该调用实际的 Agent 进行投票
        # 当前返回空列表，实际使用时需要实现
        # for participant in participants:
        #     for proposal in proposals:
        #         vote = await self._vote_on_proposal(participant, proposal)
        #         votes.append(vote)
        
        return votes
    
    def _calculate_vote_result(self, result: NegotiationResult):
        """
        计算投票结果
        
        Args:
            result: 博弈结果
        """
        agree_weight = 0.0
        disagree_weight = 0.0
        total_weight = 0.0
        
        for vote in result.votes:
            if vote.vote == VoteType.AGREE:
                agree_weight += vote.weight
            elif vote.vote == VoteType.DISAGREE:
                disagree_weight += vote.weight
            
            total_weight += vote.weight
        
        result.agree_weight = agree_weight
        result.disagree_weight = disagree_weight
        
        # 计算分歧值 (0-1)
        if total_weight > 0:
            # 分歧值 = min(agree, disagree) / max(agree, disagree)
            # 值越接近 1，分歧越大
            if agree_weight > 0 and disagree_weight > 0:
                result.divergence_score = min(agree_weight, disagree_weight) / max(agree_weight, disagree_weight)
            else:
                result.divergence_score = 0.0
        else:
            result.divergence_score = 0.0
    
    def _check_consensus(self, result: NegotiationResult) -> bool:
        """
        检查是否达成共识
        
        Args:
            result: 博弈结果
            
        Returns:
            bool: 是否达成共识
        """
        # 简单规则：超过 2/3 权重同意即达成共识
        total_weight = result.agree_weight + result.disagree_weight
        if total_weight == 0:
            return False
        
        return result.agree_weight / total_weight >= 2/3
    
    async def _arbitrate(
        self,
        result: NegotiationResult,
        arbitrator: str = "orchestrator",
    ) -> NegotiationResult:
        """
        仲裁
        
        Args:
            result: 博弈结果
            arbitrator: 仲裁者
            
        Returns:
            NegotiationResult: 仲裁后的结果
        """
        # 仲裁逻辑：选择权重最高的提案
        if result.proposals:
            # 按权重排序提案
            weighted_proposals = defaultdict(float)
            for vote in result.votes:
                if vote.vote == VoteType.AGREE:
                    # 找到对应的提案
                    for proposal in result.proposals:
                        if proposal.agent_id == vote.agent_id:
                            weighted_proposals[proposal.proposal] += vote.weight
                            break
            
            # 选择权重最高的提案
            if weighted_proposals:
                winner_proposal_str = max(weighted_proposals.items(), key=lambda x: x[1])[0]
                
                # 找到对应的提案对象
                for proposal in result.proposals:
                    if proposal.proposal == winner_proposal_str:
                        result.winner_proposal = proposal
                        break
                
                result.final_decision = winner_proposal_str
        
        result.arbitrator = arbitrator
        result.arbitration_reason = f"超过最大轮次 {self._max_rounds}，自动仲裁"
        
        return result
    
    def get_negotiation(self, negotiation_id: str) -> Optional[NegotiationResult]:
        """获取博弈记录"""
        return self._negotiations.get(negotiation_id)
    
    def add_proposal(
        self,
        negotiation_id: str,
        proposal: AgentProposal,
    ) -> None:
        """
        添加提案（手动）
        
        Args:
            negotiation_id: 博弈ID
            proposal: 提案
        """
        result = self.get_negotiation(negotiation_id)
        if result:
            result.proposals.append(proposal)
    
    def add_vote(
        self,
        negotiation_id: str,
        vote: AgentVote,
    ) -> None:
        """
        添加投票（手动）
        
        Args:
            negotiation_id: 博弈ID
            vote: 投票
        """
        result = self.get_negotiation(negotiation_id)
        if result:
            result.votes.append(vote)
            # 重新计算结果
            self._calculate_vote_result(result)


# 全局博弈管理器实例
_negotiation_manager: Optional[AgentNegotiation] = None


def get_negotiation_manager() -> AgentNegotiation:
    """获取全局博弈管理器实例"""
    global _negotiation_manager
    if _negotiation_manager is None:
        _negotiation_manager = AgentNegotiation()
    return _negotiation_manager
