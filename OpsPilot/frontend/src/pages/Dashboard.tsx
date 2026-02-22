import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { 
  Play, 
  CheckCircle, 
  Clock, 
  AlertTriangle,
  Activity,
  Zap,
  Database,
  Server,
  Users,
  TrendingUp,
  ArrowRight,
  Plus,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { useAppStore, taskStateLabels } from '../store';
import { TaskState } from '../types';

const terminalStates = [TaskState.SUCCESS, TaskState.FAILED, TaskState.REJECTED];

export function Dashboard() {
  const { t, i18n } = useTranslation();
  const { agents, tasks } = useAppStore();
  const [taskInput, setTaskInput] = useState('');

  // Fetch health
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.healthCheck(),
    refetchInterval: 30000,
  });

  // Calculate stats
  const activeTasks = tasks.filter((t) => 
    !terminalStates.includes(t.state as typeof terminalStates[number])
  ).length;
  const completedTasks = tasks.filter((t) => t.state === TaskState.SUCCESS).length;
  const failedTasks = tasks.filter((t) => t.state === TaskState.FAILED).length;
  const successRate = tasks.length > 0 
    ? Math.round((completedTasks / tasks.length) * 100) 
    : 100;

  // Quick stats
  const stats = [
    { label: t('dashboard.activeTasks'), value: activeTasks, icon: Activity, color: 'blue' },
    { label: t('dashboard.completed'), value: completedTasks, icon: CheckCircle, color: 'green' },
    { label: t('dashboard.failed'), value: failedTasks, icon: AlertTriangle, color: 'red' },
    { label: t('dashboard.successRate'), value: `${successRate}%`, icon: TrendingUp, color: 'green' },
  ];

  // Quick actions
  const quickActions = [
    { label: t('dashboard.createTask'), icon: Plus, path: '/tasks', color: 'blue' },
    { label: t('dashboard.tools'), icon: Zap, path: '/tools', color: 'purple' },
    { label: t('dashboard.executeSOP'), icon: Database, path: '/sop', color: 'green' },
    { label: t('dashboard.scheduler'), icon: Clock, path: '/scheduler', color: 'orange' },
  ];

  // Service status
  const services = health?.components ? Object.entries(health.components) : [];

  return (
    <div className="space-y-6">
      {/* ============================================
          Welcome Banner + Quick Actions
          ============================================ */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{t('dashboard.welcome')}</h1>
            <p className="text-gray-500 mt-1">{t('dashboard.subtitle')}</p>
          </div>
          
          {/* Quick Create Task */}
          <div className="flex gap-2">
            <input
              type="text"
              value={taskInput}
              onChange={(e) => setTaskInput(e.target.value)}
              placeholder={t('dashboard.taskPlaceholder')}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <Link
              to={taskInput ? `/tasks?input=${encodeURIComponent(taskInput)}` : '/tasks'}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 font-medium"
            >
              <Play className="w-4 h-4" />
              {t('dashboard.execute')}
            </Link>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-6">
          {quickActions.map((action) => {
            const Icon = action.icon;
            const colorClasses = {
              blue: 'bg-blue-50 text-blue-600 hover:bg-blue-100',
              purple: 'bg-purple-50 text-purple-600 hover:bg-purple-100',
              green: 'bg-green-50 text-green-600 hover:bg-green-100',
              orange: 'bg-orange-50 text-orange-600 hover:bg-orange-100',
            };
            return (
              <Link
                key={action.path}
                to={action.path}
                className={`flex items-center gap-2 p-3 rounded-lg transition-colors ${colorClasses[action.color as keyof typeof colorClasses]}`}
              >
                <Icon className="w-5 h-5" />
                <span className="text-sm font-medium">{action.label}</span>
              </Link>
            );
          })}
        </div>
      </div>

      {/* ============================================
          Stats Cards
          ============================================ */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          const colorClasses = {
            blue: 'bg-blue-50 text-blue-600',
            green: 'bg-green-50 text-green-600',
            red: 'bg-red-50 text-red-600',
          };
          return (
            <div key={stat.label} className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <div className={`p-2 rounded-lg ${colorClasses[stat.color as keyof typeof colorClasses]}`}>
                  <Icon className="w-5 h-5" />
                </div>
              </div>
              <div className="mt-3">
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                <p className="text-sm text-gray-500">{stat.label}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* ============================================
          Two Column Layout: Task List + System Status
          ============================================ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Tasks */}
        <div className="bg-white rounded-xl border border-gray-200">
          <div className="flex items-center justify-between p-4 border-b border-gray-100">
            <h2 className="font-semibold text-gray-900">{t('dashboard.recentTasks')}</h2>
            <Link to="/tasks" className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1">
              {t('dashboard.viewAll')} <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="p-4">
            {tasks.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <Activity className="w-10 h-10 mx-auto mb-2 opacity-50" />
                <p className="text-sm">{t('dashboard.noTasksRecorded')}</p>
              </div>
            ) : (
              <div className="space-y-3">
                {tasks.slice(0, 5).map((task) => (
                  <div key={task.task_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${
                        task.state === TaskState.SUCCESS ? 'bg-green-500' :
                        task.state === TaskState.FAILED ? 'bg-red-500' :
                        task.state === TaskState.EXECUTING ? 'bg-blue-500 animate-pulse' :
                        'bg-gray-400'
                      }`} />
                      <div>
                        <p className="text-sm font-mono text-gray-900">{task.task_id.slice(0, 12)}...</p>
                        <p className="text-xs text-gray-500">{task.intent || t('dashboard.intentNotSpecified')}</p>
                      </div>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      task.state === TaskState.SUCCESS ? 'bg-green-100 text-green-700' :
                      task.state === TaskState.FAILED ? 'bg-red-100 text-red-700' :
                      task.state === TaskState.EXECUTING ? 'bg-blue-100 text-blue-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {t(`tasks.${task.state.toLowerCase()}` as any) || taskStateLabels[task.state]}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* System Status */}
        <div className="bg-white rounded-xl border border-gray-200">
          <div className="flex items-center justify-between p-4 border-b border-gray-100">
            <h2 className="font-semibold text-gray-900">{t('dashboard.systemStatus')}</h2>
            <Link to="/monitoring" className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1">
              {t('dashboard.viewMonitor')} <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="p-4">
            <div className="space-y-3">
              {/* 版本信息 */}
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-600">{t('dashboard.version')}</span>
                <span className="text-sm font-mono text-gray-900">{health?.version || 'v0.1.0'}</span>
              </div>
              
              {/* 服务状态 */}
              {services.map(([name, status]) => (
                <div key={name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${status ? 'bg-green-500' : 'bg-red-500'}`} />
                    <span className="text-sm text-gray-600 capitalize">{name.replace(/_/g, ' ')}</span>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    status ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}>
                    {status ? t('common.online') : t('common.offline')}
                  </span>
                </div>
              ))}

              {/* Agent Status */}
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-gray-500" />
                  <span className="text-sm text-gray-600">{t('dashboard.agentCount')}</span>
                </div>
                <span className="text-sm font-medium text-gray-900">{agents.length}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ============================================
          Agent Status
          ============================================ */}
      <div className="bg-white rounded-xl border border-gray-200">
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">{t('dashboard.agentStatus')}</h2>
          <Link to="/agents" className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1">
            {t('dashboard.viewDetails')} <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
        <div className="p-4">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {agents.map((agent) => (
              <div key={agent.name} className="p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <div className={`w-2 h-2 rounded-full ${
                    agent.status === 'success' ? 'bg-green-500' :
                    agent.status === 'processing' ? 'bg-blue-500 animate-pulse' :
                    agent.status === 'error' ? 'bg-red-500' :
                    'bg-gray-400'
                  }`} />
                  <span className="text-xs text-gray-500 capitalize">{agent.status}</span>
                </div>
                <p className="text-sm font-medium text-gray-900 truncate">{agent.name}</p>
                <p className="text-xs text-gray-500">{agent.role}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
