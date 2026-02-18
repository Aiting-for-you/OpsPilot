import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DollarSign, TrendingUp, Users, Zap, Play, Clock, AlertCircle } from 'lucide-react';
import { api } from '../services/api';
import type { PricingNegotiateRequest, AgentVote } from '../types';

export function PricingManagement() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  
  const [productId, setProductId] = useState('PROD001');
  const [negotiationResult, setNegotiationResult] = useState<any>(null);

  // 查询Agent状态
  const { data: agentStatus } = useQuery({
    queryKey: ['pricing-agent-status'],
    queryFn: () => api.getPricingAgentStatus(),
    refetchInterval: 10000,
  });

  // 查询历史记录
  const { data: history } = useQuery({
    queryKey: ['pricing-history'],
    queryFn: () => api.getPricingHistory(undefined, 10),
  });

  // 定价协商
  const negotiateMutation = useMutation({
    mutationFn: (request: PricingNegotiateRequest) => api.pricingNegotiate(request),
    onSuccess: (data) => {
      setNegotiationResult(data);
      queryClient.invalidateQueries({ queryKey: ['pricing-history'] });
    },
  });

  const handleNegotiate = () => {
    negotiateMutation.mutate({ product_id: productId });
  };

  // 统计卡片数据
  const stats = [
    {
      label: '协商次数',
      value: history?.total || 0,
      icon: Zap,
      color: 'text-electric',
    },
    {
      label: '平均置信度',
      value: negotiationResult ? `${(negotiationResult.confidence * 100).toFixed(0)}%` : '-',
      icon: TrendingUp,
      color: 'text-success',
    },
    {
      label: '平均价格',
      value: negotiationResult ? `¥${negotiationResult.final_price}` : '-',
      icon: DollarSign,
      color: 'text-warning',
    },
    {
      label: '平均处理时长',
      value: negotiationResult ? `${negotiationResult.processing_time_ms.toFixed(0)}ms` : '-',
      icon: Clock,
      color: 'text-steel-500',
    },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold text-white">多Agent博弈定价</h1>
        <p className="text-steel-500 mt-2">
          通过成本、市场、利润三方Agent博弈协商，实现智能动态定价
        </p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className="stat-card">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 bg-navy-1000 border border-steel-800`}>
                <Icon className={`w-5 h-5 ${stat.color}`} />
              </div>
              <div className="text-2xl font-bold text-white">{stat.value}</div>
              <div className="text-sm text-steel-500">{stat.label}</div>
            </div>
          );
        })}
      </div>

      {/* 定价协商面板 */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">启动定价协商</h2>
        
        <div className="flex gap-4 mb-4">
          <input
            type="text"
            value={productId}
            onChange={(e) => setProductId(e.target.value)}
            placeholder="输入产品ID"
            className="flex-1 px-4 py-2 bg-navy-1000 border border-steel-800 rounded-lg text-white focus:outline-none focus:border-electric"
          />
          <button
            onClick={handleNegotiate}
            disabled={negotiateMutation.isPending}
            className="btn-primary flex items-center gap-2"
          >
            <Play className="w-4 h-4" />
            {negotiateMutation.isPending ? '协商中...' : '开始协商'}
          </button>
        </div>

        {/* 错误提示 */}
        {negotiateMutation.isError && (
          <div className="flex items-center gap-2 text-red-400 mb-4">
            <AlertCircle className="w-4 h-4" />
            协商失败: {negotiateMutation.error?.message}
          </div>
        )}

        {/* 协商结果 */}
        {negotiationResult && (
          <div className="space-y-4 mt-6">
            <h3 className="text-lg font-semibold text-white">协商结果</h3>
            
            {/* 最终定价 */}
            <div className="bg-electric/10 border border-electric/30 rounded-lg p-4">
              <div className="text-sm text-steel-500">最终定价</div>
              <div className="text-4xl font-bold text-electric">
                ¥{negotiationResult.final_price}
              </div>
              <div className="text-sm text-steel-500 mt-2">
                置信度: {(negotiationResult.confidence * 100).toFixed(0)}%
              </div>
            </div>

            {/* Agent投票详情 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(negotiationResult.agent_votes).map(([agentName, vote]) => {
                const agentVote = vote as AgentVote;
                return (
                  <div key={agentName} className="bg-navy-1000 border border-steel-800 rounded-lg p-4">
                    <div className="text-sm font-medium text-white mb-2">{agentName}</div>
                    {agentVote.error ? (
                      <div className="text-red-400 text-sm">错误: {agentVote.error}</div>
                    ) : (
                      <>
                        <div className="text-2xl font-bold text-white">¥{agentVote.suggested_price}</div>
                        <div className="text-xs text-steel-500">置信度: {(agentVote.confidence * 100).toFixed(0)}%</div>
                        <div className="text-xs text-steel-500 mt-2">{agentVote.reasoning}</div>
                      </>
                    )}
                  </div>
                );
              })}
            </div>

            {/* 博弈摘要 */}
            <div className="bg-navy-1000 border border-steel-800 rounded-lg p-4">
              <div className="text-sm font-medium text-white mb-2">博弈摘要</div>
              <div className="text-sm text-steel-300">{negotiationResult.negotiation_summary}</div>
              <div className="text-xs text-steel-500 mt-2">
                处理时长: {negotiationResult.processing_time_ms.toFixed(0)}ms | 
                Token消耗: {negotiationResult.tokens_used}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Agent状态 */}
      {agentStatus && (
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">Agent状态</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(agentStatus.agents).map(([name, status]) => (
              <div key={name} className="bg-navy-1000 border border-steel-800 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Users className="w-4 h-4 text-electric" />
                  <div className="text-sm font-medium text-white">{name}</div>
                </div>
                <div className="text-xs text-steel-500">状态: {status.status}</div>
                {status.weight && <div className="text-xs text-steel-500">权重: {(status.weight * 100).toFixed(0)}%</div>}
                {status.negotiations_completed !== undefined && (
                  <div className="text-xs text-steel-500">完成协商: {status.negotiations_completed}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 历史记录 */}
      {history && history.history.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">协商历史</h2>
          <div className="space-y-3">
            {history.history.slice(0, 5).map((item, index) => (
              <div key={index} className="bg-navy-1000 border border-steel-800 rounded-lg p-3 flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-white">{item.product_id}</div>
                  <div className="text-xs text-steel-500">{item.timestamp}</div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-electric">¥{item.final_price}</div>
                  <div className="text-xs text-steel-500">置信度: {(item.confidence * 100).toFixed(0)}%</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
