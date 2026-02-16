import { useQuery } from '@tanstack/react-query';
import { Activity, CheckCircle, Clock, AlertTriangle, Zap, Database, TrendingUp, Cpu, Server } from 'lucide-react';
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

  // Calculate stats
  const activeTasks = tasks.filter((t) => 
    !terminalStates.includes(t.state as typeof terminalStates[number])
  ).length;
  const completedTasks = tasks.filter((t) => t.state === TaskState.SUCCESS).length;
  const failedTasks = tasks.filter((t) => t.state === TaskState.FAILED).length;
  const successRate = tasks.length > 0 
    ? Math.round((completedTasks / tasks.length) * 100) 
    : 100;

  const stats = [
    {
      label: 'Active Tasks',
      value: activeTasks,
      icon: Activity,
      color: 'text-electric',
      trend: '+12%',
    },
    {
      label: 'Completed',
      value: completedTasks,
      icon: CheckCircle,
      color: 'text-success',
      trend: '+8%',
    },
    {
      label: 'Avg Time',
      value: '2.3s',
      icon: Clock,
      color: 'text-warning',
      trend: '-15%',
    },
    {
      label: 'Success Rate',
      value: `${successRate}%`,
      icon: TrendingUp,
      color: 'text-success',
      trend: '+5%',
    },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* ============================================
          Stats Grid - Key Metrics
          ============================================ */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div 
              key={index} 
              className="stat-card group"
              style={{ animationDelay: `${index * 50}ms` }}
            >
              {/* Icon */}
              <div className={`
                w-10 h-10 rounded-lg flex items-center justify-center mb-3
                bg-navy-1000 border border-steel-800
                group-hover:border-electric/30 transition-colors
              `}>
                <Icon className={`w-5 h-5 ${stat.color}`} />
              </div>
              
              {/* Value */}
              <div className="stat-value">{stat.value}</div>
              
              {/* Label */}
              <div className="stat-label">{stat.label}</div>
              
              {/* Trend */}
              <div className="flex items-center gap-1 mt-2">
                <span className={`text-xs font-mono ${stat.trend.startsWith('+') ? 'text-success' : 'text-error'}`}>
                  {stat.trend}
                </span>
                <span className="text-xs text-steel-600">vs last hour</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* ============================================
          Main Content Grid
          ============================================ */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Agent Status Panel */}
        <div className="lg:col-span-7 card">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-electric/10 flex items-center justify-center">
                <Zap className="w-4 h-4 text-electric" />
              </div>
              <div>
                <h2 className="font-display text-sm font-semibold text-text-primary uppercase tracking-wide">
                  Agent Status
                </h2>
                <p className="text-xs text-steel-500">{agents.length} agents active</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
              <span className="text-xs text-steel-400 font-mono">LIVE</span>
            </div>
          </div>

          {/* Agent List */}
          <div className="space-y-2">
            {agents.map((agent, idx) => (
              <div
                key={agent.name}
                className="flex items-center justify-between p-3 rounded-lg bg-navy-1000/50 border border-steel-800/50 hover:border-steel-700 transition-all"
                style={{ animationDelay: `${idx * 30}ms` }}
              >
                <div className="flex items-center gap-3">
                  {/* Status Dot */}
                  <div className={`status-dot status-${agent.status}`} />
                  
                  {/* Agent Info */}
                  <div>
                    <div className="font-display text-sm font-medium text-text-primary">
                      {agent.name}
                    </div>
                    <div className="text-xs text-steel-500">{agent.role}</div>
                  </div>
                </div>
                
                {/* Status Badge */}
                <span className={`badge badge-${agent.status}`}>
                  {agent.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* System Health Panel */}
        <div className="lg:col-span-5 card">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-success/10 flex items-center justify-center">
                <Database className="w-4 h-4 text-success" />
              </div>
              <div>
                <h2 className="font-display text-sm font-semibold text-text-primary uppercase tracking-wide">
                  System Health
                </h2>
                <p className="text-xs text-steel-500">All services running</p>
              </div>
            </div>
          </div>

          {healthLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="w-6 h-6 border-2 border-electric border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="space-y-4">
              {/* Overall Status */}
              <div className="flex items-center justify-between p-3 rounded-lg bg-navy-1000/50 border border-steel-800/50">
                <span className="text-steel-400 text-sm">Overall Status</span>
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${
                    health?.status === 'healthy' ? 'bg-success' : 
                    health?.status === 'degraded' ? 'bg-warning' : 'bg-error'
                  }`} />
                  <span className={`font-display text-sm font-medium ${
                    health?.status === 'healthy' ? 'text-success' : 
                    health?.status === 'degraded' ? 'text-warning' : 'text-error'
                  }`}>
                    {health?.status?.toUpperCase() || 'HEALTHY'}
                  </span>
                </div>
              </div>

              {/* Version */}
              <div className="flex items-center justify-between p-3 rounded-lg bg-navy-1000/50 border border-steel-800/50">
                <span className="text-steel-400 text-sm">Version</span>
                <span className="font-mono text-sm text-text-secondary">
                  {health?.version || 'v0.1.0'}
                </span>
              </div>

              {/* Components */}
              {health?.components && typeof health.components === 'object' && (
                Object.entries(health.components).map(([name, status]) => (
                  <div
                    key={name}
                    className="flex items-center justify-between p-3 rounded-lg bg-navy-1000/50 border border-steel-800/50"
                  >
                    <div className="flex items-center gap-2">
                      {name.includes('redis') || name.includes('memory') ? (
                        <Server className="w-4 h-4 text-steel-500" />
                      ) : (
                        <Cpu className="w-4 h-4 text-steel-500" />
                      )}
                      <span className="text-steel-400 text-sm capitalize">{name.replace(/_/g, ' ')}</span>
                    </div>
                    <span className={`font-mono text-xs ${status ? 'text-success' : 'text-error'}`}>
                      {status ? 'ONLINE' : 'OFFLINE'}
                    </span>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>

      {/* ============================================
          Recent Tasks Table
          ============================================ */}
      <div className="card">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-warning/10 flex items-center justify-center">
              <Activity className="w-4 h-4 text-warning" />
            </div>
            <div>
              <h2 className="font-display text-sm font-semibold text-text-primary uppercase tracking-wide">
                Recent Tasks
              </h2>
              <p className="text-xs text-steel-500">Last {Math.min(tasks.length, 10)} operations</p>
            </div>
          </div>
        </div>

        {tasks.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-steel-500">
            <Activity className="w-10 h-10 mb-3 opacity-30" />
            <p className="text-sm">No tasks recorded yet</p>
            <p className="text-xs text-steel-600 mt-1">Create a new task to get started</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-steel-800/50">
                  <th className="text-left text-xs font-mono text-steel-500 uppercase tracking-wider pb-3 pr-4">
                    Task ID
                  </th>
                  <th className="text-left text-xs font-mono text-steel-500 uppercase tracking-wider pb-3 pr-4">
                    Intent
                  </th>
                  <th className="text-left text-xs font-mono text-steel-500 uppercase tracking-wider pb-3 pr-4">
                    Status
                  </th>
                  <th className="text-left text-xs font-mono text-steel-500 uppercase tracking-wider pb-3">
                    Created
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-steel-800/30">
                {tasks.slice(0, 10).map((task) => (
                  <tr 
                    key={task.task_id}
                    className="hover:bg-navy-1000/30 transition-colors"
                  >
                    <td className="py-3 pr-4">
                      <span className="font-mono text-sm text-electric">
                        {task.task_id.slice(0, 8)}
                      </span>
                      <span className="font-mono text-sm text-steel-600">
                        {task.task_id.slice(8, 12)}
                      </span>
                    </td>
                    <td className="py-3 pr-4">
                      <span className="text-sm text-text-secondary">
                        {task.intent || '—'}
                      </span>
                    </td>
                    <td className="py-3 pr-4">
                      <span className={`badge badge-${
                        task.state === TaskState.SUCCESS ? 'success' :
                        task.state === TaskState.FAILED ? 'error' :
                        task.state === TaskState.RUNNING ? 'processing' : 'idle'
                      }`}>
                        {taskStateLabels[task.state]}
                      </span>
                    </td>
                    <td className="py-3">
                      <span className="font-mono text-xs text-steel-500">
                        {new Date(task.created_at).toLocaleTimeString('zh-CN', {
                          hour: '2-digit',
                          minute: '2-digit',
                          second: '2-digit'
                        })}
                      </span>
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
