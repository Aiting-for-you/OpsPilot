import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Ticket, 
  MessageSquare, 
  Send, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  Loader2,
  Users,
  Route,
  Wrench,
  Shield,
  TrendingUp,
  BarChart3,
  BookOpen,
  ArrowUpCircle,
  ArrowDownCircle,
  UserCheck,
  RefreshCw,
  Brain,
  Zap,
  AlertTriangle,
  Activity
} from 'lucide-react';
import { api } from '../services/api';
import type { Ticket as TicketType } from '../types';

type TabType = 'queue' | 'lifecycle' | 'knowledge' | 'analytics' | 'assignment';

export function TicketManagement() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<TabType>('queue');
  
  // 表单状态
  const [customerId, setCustomerId] = useState('');
  const [ticketContent, setTicketContent] = useState('');
  const [ticketPriority, setTicketPriority] = useState<'high' | 'normal' | 'low'>('normal');
  const [selectedTicket, setSelectedTicket] = useState<TicketType | null>(null);
  
  // 知识库搜索
  const [knowledgeQuery, setKnowledgeQuery] = useState('');
  
  // 创建工单
  const createTicketMutation = useMutation({
    mutationFn: () => api.createTicket({
      customer_id: customerId,
      content: ticketContent,
      priority: ticketPriority,
    }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] });
      setCustomerId('');
      setTicketContent('');
      setTicketPriority('normal');
      // 自动处理新创建的工单
      processTicketMutation.mutate({ ticket_id: data.ticket_id });
    },
  });
  
  // 处理工单
  const processTicketMutation = useMutation({
    mutationFn: (request: { ticket_id: string }) => api.processTicket(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] });
      queryClient.invalidateQueries({ queryKey: ['agentStatus'] });
    },
  });
  
  // 分配工单
  const assignTicketMutation = useMutation({
    mutationFn: (request: { ticketId: string; agentId?: string }) => 
      api.assignTicket(request.ticketId, request.agentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] });
    },
  });
  
  // 升级工单
  const escalateTicketMutation = useMutation({
    mutationFn: (request: { ticket_id: string; reason: string; escalate_to_expert?: boolean }) => 
      api.escalateTicket(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] });
    },
  });
  
  // 知识库搜索
  const knowledgeSearchMutation = useMutation({
    mutationFn: (query: string) => api.queryKnowledgeBase({ query, limit: 5 }),
  });
  
  // 查询工单列表
  const { data: ticketsData, isLoading: ticketsLoading } = useQuery({
    queryKey: ['tickets'],
    queryFn: () => api.listTickets(undefined, undefined, 20),
  });
  
  // 查询Agent状态
  const { data: agentStatus } = useQuery({
    queryKey: ['agentStatus'],
    queryFn: () => api.getCSAgentStatus(),
  });
  
  // 查询队列状态
  const { data: queueStatus } = useQuery({
    queryKey: ['queueStatus'],
    queryFn: () => api.getTicketQueueStatus(),
    enabled: activeTab === 'queue',
  });
  
  // 查询统计
  const { data: analyticsData } = useQuery({
    queryKey: ['ticketAnalytics'],
    queryFn: () => api.getTicketAnalytics(),
    enabled: activeTab === 'analytics',
  });
  
  // 查询Agent列表
  const { data: agentList } = useQuery({
    queryKey: ['agentList'],
    queryFn: () => api.getAgentList(),
    enabled: activeTab === 'assignment',
  });
  
  // 统计数据
  const tickets = ticketsData?.tickets || [];
  const totalTickets = tickets.length;
  const resolvedTickets = tickets.filter(t => t.status === 'resolved').length;
  const pendingTickets = tickets.filter(t => t.status === 'pending').length;
  
  const handleKnowledgeSearch = () => {
    if (knowledgeQuery.trim()) {
      knowledgeSearchMutation.mutate(knowledgeQuery);
    }
  };
  
  const getQueueColor = (queueType: string) => {
    switch (queueType) {
      case 'urgent': return 'text-red-600 bg-red-50';
      case 'escalated': return 'text-orange-600 bg-orange-50';
      case 'normal': return 'text-blue-600 bg-blue-50';
      case 'low': return 'text-gray-600 bg-gray-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };
  
  const formatTime = (minutes: number) => {
    if (minutes < 60) return `${minutes}${t('ticket.minutes')}`;
    if (minutes < 1440) return `${Math.round(minutes / 60)}${t('ticket.hours')}`;
    return `${Math.round(minutes / 1440)}${t('ticket.days')}`;
  };
  
  return (
    <div className="space-y-6">
      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="stat-card">
          <div className="stat-icon bg-blue-100 text-blue-600">
            <Ticket className="w-6 h-6" />
          </div>
          <div className="stat-content">
            <div className="stat-value">{totalTickets}</div>
            <div className="stat-label">{t('ticket.totalTickets')}</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon bg-green-100 text-green-600">
            <CheckCircle className="w-6 h-6" />
          </div>
          <div className="stat-content">
            <div className="stat-value">{resolvedTickets}</div>
            <div className="stat-label">{t('ticket.resolved')}</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon bg-yellow-100 text-yellow-600">
            <Clock className="w-6 h-6" />
          </div>
          <div className="stat-content">
            <div className="stat-value">{pendingTickets}</div>
            <div className="stat-label">{t('ticket.pending')}</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon bg-purple-100 text-purple-600">
            <Users className="w-6 h-6" />
          </div>
          <div className="stat-content">
            <div className="stat-value">{agentStatus?.agents ? Object.keys(agentStatus.agents).length : 0}</div>
            <div className="stat-label">{t('ticket.activeAgents')}</div>
          </div>
        </div>
      </div>
      
      {/* 标签页导航 */}
      <div className="flex border-b border-gray-200">
        <button
          onClick={() => setActiveTab('queue')}
          className={`px-4 py-2 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'queue' 
              ? 'border-blue-500 text-blue-600' 
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Route className="w-4 h-4" />
          {t('ticket.queueManagement')}
        </button>
        <button
          onClick={() => setActiveTab('lifecycle')}
          className={`px-4 py-2 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'lifecycle' 
              ? 'border-blue-500 text-blue-600' 
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Activity className="w-4 h-4" />
          {t('ticket.lifecycle')}
        </button>
        <button
          onClick={() => setActiveTab('knowledge')}
          className={`px-4 py-2 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'knowledge' 
              ? 'border-blue-500 text-blue-600' 
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          {t('ticket.knowledgeBase')}
        </button>
        <button
          onClick={() => setActiveTab('analytics')}
          className={`px-4 py-2 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'analytics' 
              ? 'border-blue-500 text-blue-600' 
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          {t('ticket.statistics')}
        </button>
        <button
          onClick={() => setActiveTab('assignment')}
          className={`px-4 py-2 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'assignment' 
              ? 'border-blue-500 text-blue-600' 
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <UserCheck className="w-4 h-4" />
          {t('ticket.smartAssignment')}
        </button>
      </div>
      
      {/* 队列管理 */}
      {activeTab === 'queue' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Route className="w-5 h-5 text-blue-600" />
              {t('ticket.queueStatus')}
            </h3>
            {queueStatus ? (
              <div className="space-y-3">
                {queueStatus.queues.map((queue) => (
                  <div key={queue.queue_type} className={`p-4 rounded-lg ${getQueueColor(queue.queue_type)}`}>
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-medium">
                        {queue.queue_type === 'urgent' && t('ticket.urgentQueue')}
                        {queue.queue_type === 'normal' && t('ticket.normalQueue')}
                        {queue.queue_type === 'low' && t('ticket.lowQueue')}
                        {queue.queue_type === 'escalated' && t('ticket.escalatedQueue')}
                      </span>
                      <span className="text-2xl font-bold">{queue.ticket_count}</span>
                    </div>
                    <div className="text-sm space-y-1">
                      <div className="flex justify-between">
                        <span>{t('ticket.avgWaitTime')}:</span>
                        <span>{formatTime(queue.avg_wait_time)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>{t('ticket.oldestTicket')}:</span>
                        <span>{formatTime(queue.oldest_ticket_age)}</span>
                      </div>
                    </div>
                  </div>
                ))}
                {queueStatus.sla_violations > 0 && (
                  <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                    <div className="flex items-center gap-2 text-red-600">
                      <AlertTriangle className="w-5 h-5" />
                      <span className="font-medium">
                        {t('ticket.slaViolations')}: {queueStatus.sla_violations}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
                {t('common.loading')}
              </div>
            )}
          </div>
          
          {/* 创建工单 */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Send className="w-5 h-5 text-green-600" />
              {t('ticket.createTicket')}
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('ticket.customerId')}
                </label>
                <input
                  type="text"
                  value={customerId}
                  onChange={(e) => setCustomerId(e.target.value)}
                  className="input-field"
                  placeholder={t('ticket.customerIdPlaceholder')}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('ticket.ticketContent')}
                </label>
                <textarea
                  value={ticketContent}
                  onChange={(e) => setTicketContent(e.target.value)}
                  className="input-field min-h-[100px]"
                  placeholder={t('ticket.contentPlaceholder')}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('ticket.priorityLabel')}
                </label>
                <select
                  value={ticketPriority}
                  onChange={(e) => setTicketPriority(e.target.value as any)}
                  className="input-field"
                >
                  <option value="low">{t('ticket.low')}</option>
                  <option value="normal">{t('ticket.normal')}</option>
                  <option value="high">{t('ticket.high')}</option>
                </select>
              </div>
              
              <button
                onClick={() => createTicketMutation.mutate()}
                disabled={!customerId || !ticketContent || createTicketMutation.isPending}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                {createTicketMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
                {t('ticket.createAndProcess')}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* 生命周期 */}
      {activeTab === 'lifecycle' && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-purple-600" />
            {t('ticket.lifecycle')}
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4">{t('ticket.ticketIdLabel')}</th>
                  <th className="text-left py-3 px-4">{t('ticket.customer')}</th>
                  <th className="text-left py-3 px-4">{t('ticket.statusLabel')}</th>
                  <th className="text-left py-3 px-4">{t('ticket.priorityLabel')}</th>
                  <th className="text-left py-3 px-4">{t('ticket.slaBreached')}</th>
                  <th className="text-left py-3 px-4">{t('ticket.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map((ticket) => (
                  <tr key={ticket.ticket_id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4 font-mono text-sm">{ticket.ticket_id}</td>
                    <td className="py-3 px-4">{ticket.customer_id}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded text-xs ${
                        ticket.status === 'resolved' ? 'bg-green-100 text-green-700' :
                        ticket.status === 'pending' ? 'bg-gray-100 text-gray-700' :
                        'bg-blue-100 text-blue-700'
                      }`}>
                        {ticket.status}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded text-xs ${
                        ticket.priority === 'high' ? 'bg-red-100 text-red-700' :
                        ticket.priority === 'low' ? 'bg-gray-100 text-gray-700' :
                        'bg-yellow-100 text-yellow-700'
                      }`}>
                        {ticket.priority}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      {ticket.status !== 'resolved' && (
                        <span className="text-red-500 flex items-center gap-1">
                          <AlertTriangle className="w-4 h-4" />
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 flex gap-2">
                      <button
                        onClick={() => escalateTicketMutation.mutate({ 
                          ticket_id: ticket.ticket_id, 
                          reason: 'Manual escalation',
                          escalate_to_expert: true 
                        })}
                        className="text-orange-600 hover:text-orange-800 text-sm flex items-center gap-1"
                      >
                        <ArrowUpCircle className="w-4 h-4" />
                        {t('ticket.escalate')}
                      </button>
                      <button
                        onClick={() => setSelectedTicket(ticket)}
                        className="text-blue-600 hover:text-blue-800 text-sm"
                      >
                        {t('ticket.viewDetails')}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      
      {/* 知识库 */}
      {activeTab === 'knowledge' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-indigo-600" />
              {t('ticket.searchKnowledge')}
            </h3>
            <div className="space-y-4">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={knowledgeQuery}
                  onChange={(e) => setKnowledgeQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleKnowledgeSearch()}
                  className="input-field flex-1"
                  placeholder={t('ticket.searchKnowledge')}
                />
                <button
                  onClick={handleKnowledgeSearch}
                  disabled={knowledgeSearchMutation.isPending}
                  className="btn-primary px-4"
                >
                  {knowledgeSearchMutation.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Search className="w-4 h-4" />
                  )}
                </button>
              </div>
              
              {knowledgeSearchMutation.data?.results && knowledgeSearchMutation.data.results.length > 0 && (
                <div className="space-y-3">
                  {knowledgeSearchMutation.data.results.map((result) => (
                    <div key={result.id} className="p-4 bg-gray-50 rounded-lg">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-medium text-gray-900">{result.title}</h4>
                        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                          {(result.relevance_score * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{result.content}</p>
                      <div className="flex gap-2">
                        {result.tags.map((tag) => (
                          <span key={tag} className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {knowledgeSearchMutation.data?.results?.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  {t('ticket.noResults')}
                </div>
              )}
            </div>
          </div>
          
          {/* Agent状态 */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Brain className="w-5 h-5 text-cyan-600" />
              {t('ticket.agentStatus')}
            </h3>
            <div className="space-y-3">
              {agentStatus?.agents && Object.entries(agentStatus.agents).map(([name, info]) => (
                <div key={name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${info.status === 'ready' ? 'bg-green-500' : 'bg-yellow-500'}`} />
                    <div>
                      <div className="font-medium capitalize">{name}</div>
                      <div className="text-sm text-gray-500">{info.description}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium">
                      {info.tickets_processed || info.tickets_routed || info.tickets_solved || info.tickets_reviewed || 0}
                    </div>
                    <div className="text-xs text-gray-500">{t('ticket.processed')}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      
      {/* 统计分析 */}
      {activeTab === 'analytics' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="stat-card">
              <div className="stat-icon bg-blue-100 text-blue-600">
                <TrendingUp className="w-6 h-6" />
              </div>
              <div className="stat-content">
                <div className="stat-value">{analyticsData?.statistics?.total_tickets || 0}</div>
                <div className="stat-label">{t('ticket.total')}</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon bg-green-100 text-green-600">
                <CheckCircle className="w-6 h-6" />
              </div>
              <div className="stat-content">
                <div className="stat-value">{analyticsData?.statistics?.resolved_tickets || 0}</div>
                <div className="stat-label">{t('ticket.resolved')}</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon bg-orange-100 text-orange-600">
                <ArrowUpCircle className="w-6 h-6" />
              </div>
              <div className="stat-content">
                <div className="stat-value">{analyticsData?.statistics?.escalation_rate ? `${(analyticsData.statistics.escalation_rate * 100).toFixed(1)}%` : '0%'}</div>
                <div className="stat-label">{t('ticket.escalationRate')}</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon bg-purple-100 text-purple-600">
                <Zap className="w-6 h-6" />
              </div>
              <div className="stat-content">
                <div className="stat-value">{analyticsData?.statistics?.sla_compliance_rate ? `${(analyticsData.statistics.sla_compliance_rate * 100).toFixed(1)}%` : '0%'}</div>
                <div className="stat-label">{t('ticket.slaCompliance')}</div>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* SLA报告 */}
            <div className="card">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Shield className="w-5 h-5 text-green-600" />
                {t('ticket.slaReport')}
              </h3>
              {analyticsData?.sla_report && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span>{t('ticket.totalSLA')}</span>
                    <span className="font-medium">{analyticsData.sla_report.total_sla}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                    <span className="text-green-700">{t('ticket.metSLA')}</span>
                    <span className="font-medium text-green-700">{analyticsData.sla_report.met_sla}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                    <span className="text-red-700">{t('ticket.breachedSLA')}</span>
                    <span className="font-medium text-red-700">{analyticsData.sla_report.breached_sla}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-4">
                    <div 
                      className="bg-green-500 h-4 rounded-full transition-all"
                      style={{ width: `${analyticsData.sla_report.compliance_rate * 100}%` }}
                    />
                  </div>
                  <div className="text-center text-sm text-gray-600">
                    {t('ticket.complianceRate')}: {(analyticsData.sla_report.compliance_rate * 100).toFixed(1)}%
                  </div>
                </div>
              )}
            </div>
            
            {/* Agent绩效 */}
            <div className="card">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-purple-600" />
                {t('ticket.agentPerformance')}
              </h3>
              {analyticsData?.agent_performance && analyticsData.agent_performance.length > 0 ? (
                <div className="space-y-3">
                  {analyticsData.agent_performance.map((agent) => (
                    <div key={agent.agent_name} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-medium">{agent.agent_name}</span>
                        <span className="text-sm bg-blue-100 text-blue-700 px-2 py-1 rounded">
                          {agent.tickets_handled} {t('ticket.ticketsHandled')}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span className="text-gray-500">{t('ticket.avgResolutionTime')}:</span>
                          <span className="ml-1">{agent.avg_resolution_time.toFixed(0)} min</span>
                        </div>
                        <div>
                          <span className="text-gray-500">{t('ticket.satisfactionScore')}:</span>
                          <span className="ml-1">{agent.satisfaction_score.toFixed(1)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  {t('ticket.noResults')}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      
      {/* 智能分配 */}
      {activeTab === 'assignment' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <UserCheck className="w-5 h-5 text-indigo-600" />
              {t('ticket.smartAssignment')}
            </h3>
            {agentList?.agents && agentList.agents.length > 0 ? (
              <div className="space-y-3">
                {agentList.agents.map((agent) => (
                  <div key={agent.agent_id} className="p-4 bg-gray-50 rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="font-medium">{agent.agent_name}</div>
                        <div className="text-sm text-gray-500">{agent.agent_id}</div>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs ${
                        agent.status === 'available' ? 'bg-green-100 text-green-700' :
                        agent.status === 'busy' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {agent.status}
                      </span>
                    </div>
                    <div className="text-sm">
                      <div className="flex justify-between mb-1">
                        <span className="text-gray-500">{t('ticket.ticketsHandled')}:</span>
                        <span>{agent.current_load}/{agent.max_load}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${
                            agent.current_load / agent.max_load > 0.8 ? 'bg-red-500' :
                            agent.current_load / agent.max_load > 0.5 ? 'bg-yellow-500' :
                            'bg-green-500'
                          }`}
                          style={{ width: `${(agent.current_load / agent.max_load) * 100}%` }}
                        />
                      </div>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {agent.skills.map((skill) => (
                        <span key={skill.skill_name} className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                          {skill.skill_name} ({skill.level})
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Users className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                {t('ticket.noResults')}
              </div>
            )}
          </div>
          
          {/* 待分配工单 */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <RefreshCw className="w-5 h-5 text-blue-600" />
              {t('ticket.ticketList')}
            </h3>
            <div className="space-y-3">
              {tickets.filter(t => t.status !== 'resolved').map((ticket) => (
                <div key={ticket.ticket_id} className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="font-mono text-sm">{ticket.ticket_id}</div>
                      <div className="text-sm text-gray-600">{ticket.content.substring(0, 50)}...</div>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs ${
                      ticket.priority === 'high' ? 'bg-red-100 text-red-700' :
                      ticket.priority === 'low' ? 'bg-gray-100 text-gray-700' :
                      'bg-yellow-100 text-yellow-700'
                    }`}>
                      {ticket.priority}
                    </span>
                  </div>
                  <button
                    onClick={() => assignTicketMutation.mutate({ ticketId: ticket.ticket_id })}
                    disabled={assignTicketMutation.isPending}
                    className="w-full btn-secondary text-sm flex items-center justify-center gap-1"
                  >
                    <UserCheck className="w-4 h-4" />
                    {t('ticket.assignNow')}
                  </button>
                </div>
              ))}
              {tickets.filter(t => t.status !== 'resolved').length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  {t('ticket.noTickets')}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      
      {/* 工单列表 */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Ticket className="w-5 h-5 text-blue-600" />
          {t('ticket.ticketList')}
        </h3>
        {ticketsLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          </div>
        ) : tickets.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            {t('ticket.noTickets')}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4">{t('ticket.ticketIdLabel')}</th>
                  <th className="text-left py-3 px-4">{t('ticket.customer')}</th>
                  <th className="text-left py-3 px-4">{t('ticket.type')}</th>
                  <th className="text-left py-3 px-4">{t('ticket.priorityLabel')}</th>
                  <th className="text-left py-3 px-4">{t('ticket.statusLabel')}</th>
                  <th className="text-left py-3 px-4">{t('ticket.department')}</th>
                  <th className="text-left py-3 px-4">{t('ticket.action')}</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map((ticket) => (
                  <tr key={ticket.ticket_id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4 font-mono text-sm">{ticket.ticket_id}</td>
                    <td className="py-3 px-4">{ticket.customer_id}</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-1 rounded text-xs bg-blue-100 text-blue-700">
                        {ticket.ticket_type}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded text-xs ${
                        ticket.priority === 'high' ? 'bg-red-100 text-red-700' :
                        ticket.priority === 'low' ? 'bg-gray-100 text-gray-700' :
                        'bg-yellow-100 text-yellow-700'
                      }`}>
                        {ticket.priority}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded text-xs ${
                        ticket.status === 'resolved' ? 'bg-green-100 text-green-700' :
                        ticket.status === 'pending' ? 'bg-gray-100 text-gray-700' :
                        'bg-blue-100 text-blue-700'
                      }`}>
                        {ticket.status}
                      </span>
                    </td>
                    <td className="py-3 px-4">{ticket.assigned_department || '-'}</td>
                    <td className="py-3 px-4">
                      <button
                        onClick={() => setSelectedTicket(ticket)}
                        className="text-blue-600 hover:text-blue-800 text-sm"
                      >
                        {t('ticket.viewDetails')}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      
      {/* 工单详情弹窗 */}
      {selectedTicket && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">{t('ticket.ticketDetails')}: {selectedTicket.ticket_id}</h3>
              <button
                onClick={() => setSelectedTicket(null)}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ×
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <div className="text-sm text-gray-500">{t('ticket.customerIdLabel')}</div>
                <div className="font-medium">{selectedTicket.customer_id}</div>
              </div>
              
              <div>
                <div className="text-sm text-gray-500">{t('ticket.ticketContent')}</div>
                <div className="font-medium">{selectedTicket.content}</div>
              </div>
              
              {selectedTicket.classification && Object.keys(selectedTicket.classification).length > 0 && (
                <div className="p-4 bg-blue-50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <MessageSquare className="w-4 h-4 text-blue-600" />
                    <span className="font-medium text-blue-700">{t('ticket.classificationResult')}</span>
                  </div>
                  <pre className="text-sm overflow-x-auto">{JSON.stringify(selectedTicket.classification, null, 2)}</pre>
                </div>
              )}
              
              {selectedTicket.routing && Object.keys(selectedTicket.routing).length > 0 && (
                <div className="p-4 bg-green-50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Route className="w-4 h-4 text-green-600" />
                    <span className="font-medium text-green-700">{t('ticket.routingInfo')}</span>
                  </div>
                  <pre className="text-sm overflow-x-auto">{JSON.stringify(selectedTicket.routing, null, 2)}</pre>
                </div>
              )}
              
              {selectedTicket.solution && Object.keys(selectedTicket.solution).length > 0 && (
                <div className="p-4 bg-purple-50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Wrench className="w-4 h-4 text-purple-600" />
                    <span className="font-medium text-purple-700">{t('ticket.solution')}</span>
                  </div>
                  <pre className="text-sm overflow-x-auto">{JSON.stringify(selectedTicket.solution, null, 2)}</pre>
                </div>
              )}
              
              {selectedTicket.review && Object.keys(selectedTicket.review).length > 0 && (
                <div className="p-4 bg-yellow-50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Shield className="w-4 h-4 text-yellow-600" />
                    <span className="font-medium text-yellow-700">{t('ticket.reviewResult')}</span>
                  </div>
                  <pre className="text-sm overflow-x-auto">{JSON.stringify(selectedTicket.review, null, 2)}</pre>
                </div>
              )}
            </div>
            
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setSelectedTicket(null)}
                className="btn-secondary"
              >
                {t('ticket.close')}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* 处理结果提示 */}
      {processTicketMutation.isSuccess && processTicketMutation.data && (
        <div className="fixed bottom-4 right-4 bg-green-100 text-green-800 px-4 py-3 rounded-lg shadow-lg">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5" />
            <span>{t('ticket.ticketCompleted')} {processTicketMutation.data.processing_time_ms.toFixed(0)}ms</span>
          </div>
        </div>
      )}
    </div>
  );
}

// 添加Search图标组件
function Search({ className }: { className?: string }) {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round"
      className={className}
    >
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  );
}