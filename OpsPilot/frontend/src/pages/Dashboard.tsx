import { useQuery } from '@tanstack/react-query';
import { Activity, CheckCircle, Clock, AlertTriangle, Zap, Database } from 'lucide-react';
import { api } from '../services/api';
import { useAppStore, taskStateLabels } from '../store';
import { TaskState } from '../types';

const terminalStates = [TaskState.SUCCESS, TaskState.FAILED, TaskState.REJECTED];

export function Dashboard() {
  const { agents, tasks } = useAppStore();

  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.healthCheck(),
    refetchInterval: 30000,
  });

  const stats = [
    {
      label: '活跃任务',
      value: tasks.filter((t) => 
        !terminalStates.includes(t.state as typeof terminalStates[number])
      ).length,
      icon: Activity,
      color: 'text-blue-400',
    },
    {
      label: '完成任务',
      value: tasks.filter((t) => t.state === TaskState.SUCCESS).length,
      icon: CheckCircle,
      color: 'text-green-400',
    },
    {
      label: '平均耗时',
      value: '2.3s',
      icon: Clock,
      color: 'text-yellow-400',
    },
    {
      label: '失败率',
      value: '3.2%',
      icon: AlertTriangle,
      color: 'text-red-400',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className="stat-card">
              <Icon className={`w-8 h-8 ${stat.color} mb-2`} />
              <div className="stat-value">{stat.value}</div>
              <div className="stat-label">{stat.label}</div>
            </div>
          );
        })}
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent Status */}
        <div className="lg:col-span-2 card">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-primary-400" />
            Agent 状态
          </h2>
          <div className="space-y-3">
            {agents.map((agent) => (
              <div
                key={agent.name}
                className="flex items-center justify-between p-3 bg-dark-700 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      agent.status === 'idle'
                        ? 'bg-gray-400'
                        : agent.status === 'processing'
                        ? 'bg-yellow-400 animate-pulse'
                        : agent.status === 'success'
                        ? 'bg-green-400'
                        : 'bg-red-400'
                    }`}
                  />
                  <div>
                    <div className="text-white font-medium">{agent.name}</div>
                    <div className="text-sm text-dark-400">{agent.role}</div>
                  </div>
                </div>
                <span
                  className={`px-2 py-1 rounded text-xs ${
                    agent.status === 'idle'
                      ? 'bg-gray-700 text-gray-400'
                      : agent.status === 'processing'
                      ? 'bg-yellow-900 text-yellow-400'
                      : agent.status === 'success'
                      ? 'bg-green-900 text-green-400'
                      : 'bg-red-900 text-red-400'
                  }`}
                >
                  {agent.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* System Health */}
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Database className="w-5 h-5 text-primary-400" />
            系统状态
          </h2>
          {healthLoading ? (
            <div className="text-dark-400">加载中...</div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-dark-300">状态</span>
                <span
                  className={`font-medium ${
                    health?.status === 'healthy'
                      ? 'text-green-400'
                      : health?.status === 'degraded'
                      ? 'text-yellow-400'
                      : 'text-red-400'
                  }`}
                >
                  {health?.status || 'healthy'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-dark-300">版本</span>
                <span className="text-dark-100">{health?.version || 'v0.1.0'}</span>
              </div>
              {health?.components?.map((comp, idx) => (
                <div key={idx} className="flex items-center justify-between text-sm">
                  <span className="text-dark-400">{comp.name}</span>
                  <span className="text-dark-100">{comp.status}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recent Tasks */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">最近任务</h2>
        {tasks.length === 0 ? (
          <div className="text-center py-8 text-dark-400">
            暂无任务记录
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-dark-400 text-sm border-b border-dark-700">
                  <th className="pb-3">任务ID</th>
                  <th className="pb-3">意图</th>
                  <th className="pb-3">状态</th>
                  <th className="pb-3">创建时间</th>
                </tr>
              </thead>
              <tbody>
                {tasks.slice(0, 5).map((task) => (
                  <tr
                    key={task.task_id}
                    className="border-b border-dark-700 last:border-0"
                  >
                    <td className="py-3 font-mono text-sm text-dark-100">
                      {task.task_id.slice(0, 8)}...
                    </td>
                    <td className="py-3 text-dark-300">{task.intent || '-'}</td>
                    <td className="py-3">
                      <span className="px-2 py-1 rounded bg-dark-700 text-sm">
                        {taskStateLabels[task.state]}
                      </span>
                    </td>
                    <td className="py-3 text-dark-400 text-sm">
                      {new Date(task.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
