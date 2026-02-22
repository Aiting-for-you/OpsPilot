import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { 
  TrendingUp, 
  TrendingDown,
  Activity,
  CheckCircle,
  XCircle,
  Clock,
  Zap,
  Users,
  Wrench,
  BarChart3,
  PieChart,
  LineChart,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  RefreshCw,
  Calendar,
} from 'lucide-react';
import { api } from '../services/api';
import { format, subDays } from 'date-fns';

interface DailyTrendItem {
  date: string;
  count: number;
}

interface AgentPerformanceItem {
  agent_id?: string;
  agent_name: string;
  task_count?: number;
  total_tasks?: number;
  success_rate: number;
  avg_execution_time?: number;
}

interface ToolAnalyticsItem {
  tool_name: string;
  usage_count?: number;
  total_calls?: number;
  successful_calls?: number;
  failed_calls?: number;
  success_rate?: number;
  avg_duration?: number;
}

export function Analytics() {
  const { t } = useTranslation();
  const [dateRange, setDateRange] = useState<'7d' | '30d' | '90d'>('7d');

  // Fetch dashboard data
  const { data: dashboardData, isLoading } = useQuery({
    queryKey: ['analytics-dashboard', dateRange],
    queryFn: () => {
      const end = new Date();
      const start = subDays(end, dateRange === '7d' ? 7 : dateRange === '30d' ? 30 : 90);
      return api.getAnalyticsDashboard(
        start.toISOString(),
        end.toISOString()
      );
    },
    refetchInterval: 30000,
  });

  // Fetch system metrics
  const { data: systemMetrics } = useQuery({
    queryKey: ['system-metrics'],
    queryFn: () => api.getSystemMetrics(),
    refetchInterval: 10000,
  });

  const taskStats = dashboardData?.task_statistics;
  const agentPerformance = dashboardData?.agent_performance || [];
  const toolAnalytics = dashboardData?.tool_analytics || [];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* ============================================
          Header Section
          ============================================ */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-gray-900">
            {t('analytics.title')}
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {t('analytics.subtitle')}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value as '7d' | '30d' | '90d')}
            className="input-field text-sm py-2 px-3"
          >
            <option value="7d">{t('analytics.last7days')}</option>
            <option value="30d">{t('analytics.last30days')}</option>
            <option value="90d">{t('analytics.last90days')}</option>
          </select>
        </div>
      </div>

      {/* ============================================
          System Overview Cards
          ============================================ */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          {
            label: t('analytics.totalTasks'),
            value: taskStats?.total_tasks || 0,
            icon: Activity,
            color: 'text-electric',
            bgGradient: 'from-electric/20 to-electric/5',
            trend: '+12%',
            trendUp: true,
          },
          {
            label: t('analytics.successRate'),
            value: `${((taskStats?.success_rate || 0) * 100).toFixed(1)}%`,
            icon: CheckCircle,
            color: 'text-success',
            bgGradient: 'from-success/20 to-success/5',
            trend: '+5%',
            trendUp: true,
          },
          {
            label: t('analytics.avgExecutionTime'),
            value: `${(taskStats?.avg_execution_time || 0).toFixed(2)}s`,
            icon: Clock,
            color: 'text-warning',
            bgGradient: 'from-warning/20 to-warning/5',
            trend: '-8%',
            trendUp: true,
          },
          {
            label: t('analytics.activeAgents'),
            value: systemMetrics?.active_agents || 0,
            icon: Users,
            color: 'text-purple-400',
            bgGradient: 'from-purple-500/20 to-purple-500/5',
            trend: '0%',
            trendUp: null,
          },
        ].map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div
              key={index}
              className={`relative overflow-hidden rounded-xl p-5 bg-gradient-to-br ${stat.bgGradient} border border-gray-200/50`}
            >
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-3">
                  <div className={`w-10 h-10 rounded-lg bg-gray-100/80 flex items-center justify-center`}>
                    <Icon className={`w-5 h-5 ${stat.color}`} />
                  </div>
                  {stat.trendUp !== null && (
                    <div className={`flex items-center gap-1 text-xs ${
                      stat.trendUp ? 'text-success' : 'text-error'
                    }`}>
                      {stat.trendUp ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                      {stat.trend}
                    </div>
                  )}
                </div>
                <div className="text-3xl font-display font-bold text-gray-900 mb-1">
                  {stat.value}
                </div>
                <div className="text-sm text-gray-600">{stat.label}</div>
              </div>
              
              {/* Background decoration */}
              <div className="absolute -right-4 -bottom-4 w-24 h-24 opacity-10">
                <Icon className="w-full h-full" />
              </div>
            </div>
          );
        })}
      </div>

      {/* ============================================
          Charts Row
          ============================================ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Task Status Distribution */}
        <div className="card">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-electric/10 flex items-center justify-center">
                <PieChart className="w-4 h-4 text-electric" />
              </div>
              <div>
                <h2 className="font-display text-sm font-semibold text-gray-900 uppercase tracking-wide">
                  {t('analytics.taskStatusDistribution')}
                </h2>
                <p className="text-xs text-gray-500">{t('analytics.byStatus')}</p>
              </div>
            </div>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-6 h-6 border-2 border-electric border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="space-y-3">
              {[
                { label: t('analytics.completed'), value: taskStats?.completed_tasks || 0, color: 'bg-success', percentage: taskStats?.total_tasks ? ((taskStats.completed_tasks / taskStats.total_tasks) * 100).toFixed(1) : 0 },
                { label: t('analytics.failed'), value: taskStats?.failed_tasks || 0, color: 'bg-error', percentage: taskStats?.total_tasks ? ((taskStats.failed_tasks / taskStats.total_tasks) * 100).toFixed(1) : 0 },
                { label: t('analytics.running'), value: taskStats?.running_tasks || 0, color: 'bg-electric', percentage: taskStats?.total_tasks ? ((taskStats.running_tasks / taskStats.total_tasks) * 100).toFixed(1) : 0 },
                { label: t('analytics.pending'), value: taskStats?.pending_tasks || 0, color: 'bg-steel-500', percentage: taskStats?.total_tasks ? ((taskStats.pending_tasks / taskStats.total_tasks) * 100).toFixed(1) : 0 },
                { label: t('analytics.cancelled'), value: taskStats?.cancelled_tasks || 0, color: 'bg-gray-300', percentage: taskStats?.total_tasks ? ((taskStats.cancelled_tasks / taskStats.total_tasks) * 100).toFixed(1) : 0 },
              ].map((item, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">{item.label}</span>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm text-gray-900">{item.value}</span>
                      <span className="text-xs text-gray-500">({item.percentage}%)</span>
                    </div>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${item.color} transition-all duration-500`}
                      style={{ width: `${item.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Completion Trend */}
        <div className="card">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-success/10 flex items-center justify-center">
                <LineChart className="w-4 h-4 text-success" />
              </div>
              <div>
                <h2 className="font-display text-sm font-semibold text-gray-900 uppercase tracking-wide">
                  {t('analytics.completionTrend')}
                </h2>
                <p className="text-xs text-gray-500">{t('analytics.last7DaysCompletion')}</p>
              </div>
            </div>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-6 h-6 border-2 border-electric border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="h-48 flex items-end justify-between gap-2">
              {(taskStats?.daily_completion_trend || []).map((item: DailyTrendItem, index: number) => {
                const maxCount = Math.max(...(taskStats?.daily_completion_trend || []).map((d: DailyTrendItem) => d.count), 1);
                const height = (item.count / maxCount) * 100;
                return (
                  <div key={index} className="flex-1 flex flex-col items-center gap-2">
                    <div className="w-full flex flex-col items-center">
                      <span className="text-xs text-gray-600 mb-1">{item.count}</span>
                      <div className="w-full bg-gray-100 rounded-t relative overflow-hidden" style={{ height: `${Math.max(height, 5)}%` }}>
                        <div className="absolute inset-0 bg-gradient-to-t from-success to-success/50" />
                      </div>
                    </div>
                    <span className="text-xs text-gray-500 mt-2">
                      {format(new Date(item.date), 'MM/dd')}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* ============================================
          Agent Performance & Tool Analytics
          ============================================ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent Performance */}
        <div className="card">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center">
                <Users className="w-4 h-4 text-purple-400" />
              </div>
              <div>
                <h2 className="font-display text-sm font-semibold text-gray-900 uppercase tracking-wide">
                  {t('analytics.agentPerformanceRanking')}
                </h2>
                <p className="text-xs text-gray-500">{t('analytics.bySuccessRate')}</p>
              </div>
            </div>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-6 h-6 border-2 border-electric border-t-transparent rounded-full animate-spin" />
            </div>
          ) : agentPerformance.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-gray-500">
              <Users className="w-10 h-10 mb-3 opacity-30" />
              <p className="text-sm">{t('analytics.noAgentData')}</p>
            </div>
          ) : (
            <div className="space-y-3">
              {agentPerformance.slice(0, 5).map((agent: AgentPerformanceItem, index: number) => (
                <div
                  key={agent.agent_id}
                  className="flex items-center justify-between p-3 rounded-lg bg-white/50 border border-gray-200/50 hover:border-gray-300 transition-all"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center font-display font-bold text-sm ${
                      index === 0 ? 'bg-yellow-500/20 text-yellow-400' :
                      index === 1 ? 'bg-steel-400/20 text-gray-700' :
                      index === 2 ? 'bg-orange-500/20 text-orange-400' :
                      'bg-white text-gray-500'
                    }`}>
                      {index + 1}
                    </div>
                    <div>
                      <div className="font-display text-sm font-medium text-gray-900">
                        {agent.agent_name}
                      </div>
                      <div className="text-xs text-gray-500">
                        {agent.total_tasks} {t('analytics.tasks')}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center gap-2">
                      <span className={`text-lg font-display font-bold ${
                        agent.success_rate >= 0.8 ? 'text-success' :
                        agent.success_rate >= 0.5 ? 'text-warning' : 'text-error'
                      }`}>
                        {(agent.success_rate * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="text-xs text-gray-500">
                      {t('analytics.avgTime')} {(agent.avg_execution_time || 0).toFixed(2)}s
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Tool Analytics */}
        <div className="card">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-warning/10 flex items-center justify-center">
                <Wrench className="w-4 h-4 text-warning" />
              </div>
              <div>
                <h2 className="font-display text-sm font-semibold text-gray-900 uppercase tracking-wide">
                  {t('analytics.toolRanking')}
                </h2>
                <p className="text-xs text-gray-500">{t('analytics.byCallCount')}</p>
              </div>
            </div>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-6 h-6 border-2 border-electric border-t-transparent rounded-full animate-spin" />
            </div>
          ) : toolAnalytics.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-gray-500">
              <Wrench className="w-10 h-10 mb-3 opacity-30" />
              <p className="text-sm">{t('analytics.noToolData')}</p>
            </div>
          ) : (
            <div className="space-y-3">
              {toolAnalytics.slice(0, 5).map((tool: ToolAnalyticsItem, index: number) => (
                <div
                  key={tool.tool_name}
                  className="flex items-center justify-between p-3 rounded-lg bg-white/50 border border-gray-200/50 hover:border-gray-300 transition-all"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-white border border-gray-200 flex items-center justify-center">
                      <Wrench className="w-4 h-4 text-gray-600" />
                    </div>
                    <div>
                      <div className="font-display text-sm font-medium text-gray-900">
                        {tool.tool_name}
                      </div>
                      <div className="text-xs text-gray-500">
                        {tool.total_calls} {t('analytics.calls')}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-3 h-3 text-success" />
                      <span className="text-sm font-mono text-gray-600">
                        {tool.successful_calls}
                      </span>
                      <XCircle className="w-3 h-3 text-error ml-2" />
                      <span className="text-sm font-mono text-gray-600">
                        {tool.failed_calls}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {t('analytics.successRate')} {((tool.success_rate ?? 0) * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ============================================
          System Metrics
          ============================================ */}
      <div className="card">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-electric/10 flex items-center justify-center">
              <Activity className="w-4 h-4 text-electric" />
            </div>
            <div>
              <h2 className="font-display text-sm font-semibold text-gray-900 uppercase tracking-wide">
                {t('analytics.systemMetrics')}
              </h2>
              <p className="text-xs text-gray-500">
                {t('analytics.lastUpdated')}: {systemMetrics?.timestamp ? format(new Date(systemMetrics.timestamp), 'HH:mm:ss') : '—'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
            <span className="text-xs text-gray-600 font-mono">{t('analytics.realtime')}</span>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: t('analytics.taskQueue'), value: systemMetrics?.task_queue_size || 0, icon: Clock },
            { label: t('analytics.activeTasks'), value: systemMetrics?.active_tasks || 0, icon: Zap },
            { label: t('analytics.activeAgents'), value: systemMetrics?.active_agents || 0, icon: Users },
            { label: t('analytics.availableTools'), value: systemMetrics?.available_tools || 0, icon: Wrench },
          ].map((metric, index) => {
            const Icon = metric.icon;
            return (
              <div
                key={index}
                className="p-4 rounded-lg bg-white/50 border border-gray-200/50"
              >
                <div className="flex items-center gap-2 mb-2">
                  <Icon className="w-4 h-4 text-gray-500" />
                  <span className="text-xs text-gray-600">{metric.label}</span>
                </div>
                <div className="text-2xl font-display font-bold text-gray-900">
                  {metric.value}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
