import { useTranslation } from 'react-i18next';
import { useAppStore } from '../store';
import { GitBranch, MessageSquare, Activity, ArrowRight, Cpu, Network, Zap } from 'lucide-react';

export function Agents() {
  const { t } = useTranslation();
  const { agents } = useAppStore();

  // Mock message flow
  const messages = [
    { from: 'Orchestrator', to: 'IntentAgent', content: 'Dispatch: Query Stock', time: '10:23:45', type: 'dispatch' },
    { from: 'IntentAgent', to: 'Orchestrator', content: 'Intent识别完成: query_stock', time: '10:23:47', type: 'response' },
    { from: 'Orchestrator', to: 'PlanAgent', content: 'Create Execution Plan', time: '10:23:48', type: 'dispatch' },
    { from: 'PlanAgent', to: 'ExecAgent', content: 'Execute Tool: query_erp', time: '10:23:50', type: 'dispatch' },
    { from: 'ExecAgent', to: 'VerifyAgent', content: 'Request Verification', time: '10:23:55', type: 'dispatch' },
  ];

  // Translate status
  const getStatusLabel = (status: string) => {
    const statusMap: Record<string, string> = {
      idle: t('agents.statusIdle'),
      running: t('agents.statusRunning'),
      busy: t('agents.statusBusy'),
      error: t('agents.statusError'),
    };
    return statusMap[status] || status;
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* ============================================
          Agent Status Overview
          ============================================ */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {agents.map((agent, idx) => (
          <div 
            key={agent.name} 
            className="stat-card"
            style={{ animationDelay: `${idx * 50}ms` }}
          >
            {/* Status Indicator */}
            <div className={`status-dot status-${agent.status} mb-3`} />
            
            {/* Agent Name */}
            <div className="font-display text-sm font-semibold text-gray-900 text-center">
              {agent.name}
            </div>
            
            {/* Role */}
            <div className="stat-label">{agent.role}</div>
            
            {/* Status Badge */}
            <span className={`badge badge-${agent.status} mt-2`}>
              {getStatusLabel(agent.status)}
            </span>
          </div>
        ))}
      </div>

      {/* ============================================
          Main Content Grid
          ============================================ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Communication Flow */}
        <div className="card">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-8 h-8 rounded-lg bg-electric/10 flex items-center justify-center">
              <GitBranch className="w-4 h-4 text-electric" />
            </div>
            <div>
              <h2 className="font-display text-sm font-semibold text-gray-900 uppercase tracking-wide">
                {t('agents.communicationFlow')}
              </h2>
              <p className="text-xs text-gray-500">{t('agents.agentCollaborationTrace')}</p>
            </div>
          </div>

          <div className="space-y-2">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className="flex items-center gap-3 p-3 rounded-lg bg-white/50 border border-gray-200/50 hover:border-gray-300 transition-colors"
              >
                {/* Message Flow */}
                <div className="flex items-center gap-2 min-w-[180px]">
                  <span className="font-mono text-xs text-electric">{msg.from}</span>
                  <ArrowRight className="w-3 h-3 text-gray-400" />
                  <span className="font-mono text-xs text-warning">{msg.to}</span>
                </div>
                
                {/* Content */}
                <div className="flex-1 text-sm text-gray-700 truncate">
                  {msg.content}
                </div>
                
                {/* Timestamp */}
                <div className="font-mono text-xs text-gray-400">
                  {msg.time}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Message Hub */}
        <div className="card">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-8 h-8 rounded-lg bg-success/10 flex items-center justify-center">
              <MessageSquare className="w-4 h-4 text-success" />
            </div>
            <div>
              <h2 className="font-display text-sm font-semibold text-gray-900 uppercase tracking-wide">
                {t('agents.messageHub')}
              </h2>
              <p className="text-xs text-gray-500">{t('common.live')} event stream</p>
            </div>
          </div>

          <div className="flex flex-col items-center justify-center py-12 text-gray-500">
            <div className="w-16 h-16 rounded-xl bg-white/50 border border-gray-200/50 flex items-center justify-center mb-4">
              <Network className="w-8 h-8 opacity-30" />
            </div>
            <p className="text-sm font-medium">{t('agents.websocketConnection')}</p>
            <p className="text-xs text-gray-400 mt-1">{t('tracing.noTraces')}</p>
            
            {/* Connection Status */}
            <div className="flex items-center gap-2 mt-4 px-3 py-1.5 rounded-md bg-gray-100/50 border border-gray-200/50">
              <div className="w-1.5 h-1.5 rounded-full bg-warning animate-pulse" />
              <span className="text-xs text-gray-600">{t('common.loading')}</span>
            </div>
          </div>
        </div>
      </div>

      {/* ============================================
          Agent Details Table
          ============================================ */}
      <div className="card">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-8 h-8 rounded-lg bg-warning/10 flex items-center justify-center">
            <Cpu className="w-4 h-4 text-warning" />
          </div>
          <div>
            <h2 className="font-display text-sm font-semibold text-gray-900 uppercase tracking-wide">
              {t('agents.agentDetails')}
            </h2>
            <p className="text-xs text-gray-500">{t('agents.statistics')}</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200/50">
                <th className="text-left text-xs font-mono text-gray-500 uppercase tracking-wider pb-3 pr-4">
                  {t('agents.agentName')}
                </th>
                <th className="text-left text-xs font-mono text-gray-500 uppercase tracking-wider pb-3 pr-4">
                  {t('agents.role')}
                </th>
                <th className="text-left text-xs font-mono text-gray-500 uppercase tracking-wider pb-3 pr-4">
                  {t('agents.status')}
                </th>
                <th className="text-left text-xs font-mono text-gray-500 uppercase tracking-wider pb-3 pr-4">
                  {t('agents.currentTask')}
                </th>
                <th className="text-left text-xs font-mono text-gray-500 uppercase tracking-wider pb-3">
                  {t('agents.lastActivity')}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-steel-800/30">
              {agents.map((agent) => (
                <tr 
                  key={agent.name}
                  className="hover:bg-white/30 transition-colors"
                >
                  <td className="py-3 pr-4">
                    <div className="flex items-center gap-2">
                      <Zap className="w-4 h-4 text-electric" />
                      <span className="font-display text-sm font-medium text-gray-900">
                        {agent.name}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 pr-4">
                    <span className="text-sm text-gray-600">{agent.role}</span>
                  </td>
                  <td className="py-3 pr-4">
                    <span className={`badge badge-${agent.status}`}>
                      {getStatusLabel(agent.status)}
                    </span>
                  </td>
                  <td className="py-3 pr-4">
                    <span className="text-sm text-gray-600">
                      {agent.current_task || '—'}
                    </span>
                  </td>
                  <td className="py-3">
                    <span className="font-mono text-xs text-gray-500">
                      {agent.last_activity || '—'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
