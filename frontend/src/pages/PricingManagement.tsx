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
      label: t('pricing.negotiationCount'),
      value: history?.total || 0,
      icon: Zap,
      color: 'text-electric',
    },
    {
      label: t('pricing.avgConfidence'),
      value: negotiationResult ? `${(negotiationResult.confidence * 100).toFixed(0)}%` : '-',
      icon: TrendingUp,
      color: 'text-success',
    },
    {
      label: t('pricing.avgPrice'),
      value: negotiationResult ? `¥${negotiationResult.final_price}` : '-',
      icon: DollarSign,
      color: 'text-warning',
    },
    {
      label: t('pricing.avgDuration'),
      value: negotiationResult ? `${negotiationResult.processing_time_ms.toFixed(0)}ms` : '-',
      icon: Clock,
      color: 'text-gray-500',
    },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold text-white">{t('pricing.title')}</h1>
        <p className="text-gray-500 mt-2">
                      {t('pricing.subtitle')}        </p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className="stat-card">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 bg-white border border-gray-200`}>
                <Icon className={`w-5 h-5 ${stat.color}`} />
              </div>
              <div className="text-2xl font-bold text-white">{stat.value}</div>
              <div className="text-sm text-gray-500">{stat.label}</div>
            </div>
          );
        })}
      </div>

      {/* 定价协商面板 */}
      <div className="card">
                    <h2 className="text-lg font-semibold text-white mb-4">{t('pricing.startNegotiation')}</h2>        
        <div className="flex gap-4 mb-4">
          <input
            type="text"
            value={productId}
            onChange={(e) => setProductId(e.target.value)}
                            placeholder={t('pricing.productIdPlaceholder')}            className="flex-1 px-4 py-2 bg-white border border-gray-200 rounded-lg text-white focus:outline-none focus:border-electric"
          />
          <button
            onClick={handleNegotiate}
            disabled={negotiateMutation.isPending}
            className="btn-primary flex items-center gap-2"
          >
            <Play className="w-4 h-4" />
                          {negotiateMutation.isPending ? t('pricing.negotiating') : t('pricing.startNegotiate')}          </button>
        </div>

        {/* 错误提示 */}
        {negotiateMutation.isError && (
          <div className="flex items-center gap-2 text-red-400 mb-4">
            <AlertCircle className="w-4 h-4" />
            {t('pricing.negotiationFailed')}: {negotiateMutation.error?.message}
          </div>
        )}

        {/* 协商结果 */}
        {negotiationResult && (
          <div className="space-y-4 mt-6">
            <h3 className="text-lg font-semibold text-white">{t('pricing.negotiationResult')}</h3>
            
            {/* 最终定价 */}
            <div className="bg-electric/10 border border-electric/30 rounded-lg p-4">
              <div className="text-sm text-gray-500">{t('pricing.finalPrice')}</div>
              <div className="text-4xl font-bold text-electric">
                ¥{negotiationResult.final_price}
              </div>
              <div className="text-sm text-gray-500 mt-2">
                {t('pricing.confidence')}: {(negotiationResult.confidence * 100).toFixed(0)}%
              </div>
            </div>

            {/* Agent投票详情 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(negotiationResult.agent_votes).map(([agentName, vote]) => {
                const agentVote = vote as AgentVote;
                return (
                  <div key={agentName} className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="text-sm font-medium text-white mb-2">{agentName}</div>
                    {agentVote.error ? (
                      <div className="text-red-400 text-sm">{t('pricing.error')}: {agentVote.error}</div>
                    ) : (
                      <>
                        <div className="text-2xl font-bold text-white">¥{agentVote.suggested_price}</div>
                        <div className="text-xs text-gray-500">{t('pricing.confidence')}: {(agentVote.confidence * 100).toFixed(0)}%</div>
                        <div className="text-xs text-gray-500 mt-2">{agentVote.reasoning}</div>
                      </>
                    )}
                  </div>
                );
              })}
            </div>

            {/* 博弈摘要 */}
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="text-sm font-medium text-white mb-2">{t('pricing.gameSummary')}</div>
              <div className="text-sm text-gray-700">{negotiationResult.negotiation_summary}</div>
              <div className="text-xs text-gray-500 mt-2">
                            {t('pricing.processingTime')}: {negotiationResult.processing_time_ms.toFixed(0)}ms |
                            {t('pricing.tokensUsed')}: {negotiationResult.tokens_used}              </div>
            </div>
          </div>
        )}
      </div>

      {/* Agent状态 */}
      {agentStatus && (
        <div className="card">
                      <h2 className="text-lg font-semibold text-white mb-4">{t('pricing.agentStatus')}</h2>          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(agentStatus.agents).map(([name, status]) => (
              <div key={name} className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Users className="w-4 h-4 text-electric" />
                  <div className="text-sm font-medium text-white">{name}</div>
                </div>
                <div className="text-xs text-gray-500">{t('pricing.status')}: {status.status}</div>
                {status.weight && <div className="text-xs text-gray-500">{t('pricing.weight')}: {(status.weight * 100).toFixed(0)}%</div>}
                {status.negotiations_completed !== undefined && (
                  <div className="text-xs text-gray-500">{t('pricing.negotiationsCompleted')}: {status.negotiations_completed}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 历史记录 */}
      {history && history.history.length > 0 && (
        <div className="card">
                      <h2 className="text-lg font-semibold text-white mb-4">{t('pricing.history')}</h2>          <div className="space-y-3">
            {history.history.slice(0, 5).map((item, index) => (
              <div key={index} className="bg-white border border-gray-200 rounded-lg p-3 flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-white">{item.product_id}</div>
                  <div className="text-xs text-gray-500">{item.timestamp}</div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-electric">¥{item.final_price}</div>
                  <div className="text-xs text-gray-500">{t('pricing.confidence')}: {(item.confidence * 100).toFixed(0)}%</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
