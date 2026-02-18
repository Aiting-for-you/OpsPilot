import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Clock, 
  Play, 
  Pause, 
  Plus, 
  Trash2, 
  RefreshCw, 
  Calendar,
  AlertCircle,
  CheckCircle,
  XCircle,
  Timer,
  Zap,
  Settings,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { api } from '../services/api';
import { format } from 'date-fns';

interface ScheduledTask {
  task_id: string;
  name: string;
  task_type: string;
  priority: string;
  status: string;
  created_at: string;
  scheduled_time?: string;
  started_at?: string;
  completed_at?: string;
  retry_count: number;
  error_message?: string;
  tags: string[];
}

interface SchedulerStats {
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  cancelled_tasks: number;
  running_tasks: int;
  queued_tasks: number;
}

export function Scheduler() {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [expandedTask, setExpandedTask] = useState<string | null>(null);

  // Fetch scheduled tasks
  const { data: tasksData, isLoading: tasksLoading } = useQuery({
    queryKey: ['scheduled-tasks', filterStatus],
    queryFn: () => api.getScheduledTasks(filterStatus === 'all' ? undefined : filterStatus),
    refetchInterval: 5000,
  });

  // Fetch scheduler stats
  const { data: stats } = useQuery({
    queryKey: ['scheduler-stats'],
    queryFn: () => api.getSchedulerStats(),
    refetchInterval: 5000,
  });

  // Cancel task mutation
  const cancelMutation = useMutation({
    mutationFn: (taskId: string) => api.cancelScheduledTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-tasks'] });
      queryClient.invalidateQueries({ queryKey: ['scheduler-stats'] });
    },
  });

  // Start scheduler mutation
  const startMutation = useMutation({
    mutationFn: () => api.startScheduler(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduler-stats'] });
    },
  });

  // Stop scheduler mutation
  const stopMutation = useMutation({
    mutationFn: () => api.stopScheduler(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduler-stats'] });
    },
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-success" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-error" />;
      case 'running':
        return <RefreshCw className="w-4 h-4 text-electric animate-spin" />;
      case 'queued':
        return <Timer className="w-4 h-4 text-warning" />;
      case 'cancelled':
        return <XCircle className="w-4 h-4 text-steel-500" />;
      default:
        return <Clock className="w-4 h-4 text-steel-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'badge-idle',
      queued: 'badge-idle',
      running: 'badge-processing',
      completed: 'badge-success',
      failed: 'badge-error',
      cancelled: 'badge-idle',
      retrying: 'badge-processing',
    };
    return colors[status] || 'badge-idle';
  };

  const getPriorityBadge = (priority: string) => {
    const colors: Record<string, string> = {
      low: 'bg-steel-700 text-steel-300',
      normal: 'bg-blue-900/50 text-blue-400',
      high: 'bg-orange-900/50 text-orange-400',
      urgent: 'bg-red-900/50 text-red-400',
    };
    return colors[priority] || colors.normal;
  };

  const tasks = tasksData?.tasks || [];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* ============================================
          Header Section
          ============================================ */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-text-primary">
            任务调度器
          </h1>
          <p className="text-sm text-steel-500 mt-1">
            管理定时任务、周期性任务和任务队列
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => startMutation.mutate()}
            disabled={startMutation.isPending}
            className="btn-secondary flex items-center gap-2"
          >
            <Play className="w-4 h-4" />
            启动
          </button>
          <button
            onClick={() => stopMutation.mutate()}
            disabled={stopMutation.isPending}
            className="btn-secondary flex items-center gap-2"
          >
            <Pause className="w-4 h-4" />
            停止
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            新建任务
          </button>
        </div>
      </div>

      {/* ============================================
          Stats Grid
          ============================================ */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
        {[
          { label: '总任务数', value: stats?.total_tasks || 0, icon: Clock, color: 'text-electric' },
          { label: '已完成', value: stats?.completed_tasks || 0, icon: CheckCircle, color: 'text-success' },
          { label: '失败', value: stats?.failed_tasks || 0, icon: XCircle, color: 'text-error' },
          { label: '已取消', value: stats?.cancelled_tasks || 0, icon: XCircle, color: 'text-steel-500' },
          { label: '运行中', value: stats?.running_tasks || 0, icon: RefreshCw, color: 'text-warning' },
          { label: '队列中', value: stats?.queued_tasks || 0, icon: Timer, color: 'text-blue-400' },
        ].map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className="stat-card">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center mb-2 bg-navy-1000 border border-steel-800`}>
                <Icon className={`w-4 h-4 ${stat.color}`} />
              </div>
              <div className="stat-value text-2xl">{stat.value}</div>
              <div className="stat-label">{stat.label}</div>
            </div>
          );
        })}
      </div>

      {/* ============================================
          Filter Section
          ============================================ */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-steel-400">状态筛选:</span>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="input-field text-sm py-1.5 px-3"
            >
              <option value="all">全部</option>
              <option value="pending">待执行</option>
              <option value="queued">队列中</option>
              <option value="running">运行中</option>
              <option value="completed">已完成</option>
              <option value="failed">失败</option>
              <option value="cancelled">已取消</option>
            </select>
          </div>
        </div>

        {/* ============================================
            Tasks List
            ============================================ */}
        {tasksLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="w-8 h-8 border-2 border-electric border-t-transparent rounded-full animate-spin" />
          </div>
        ) : tasks.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-steel-500">
            <Clock className="w-12 h-12 mb-3 opacity-30" />
            <p className="text-sm">暂无调度任务</p>
            <p className="text-xs text-steel-600 mt-1">点击"新建任务"创建第一个任务</p>
          </div>
        ) : (
          <div className="space-y-2">
            {tasks.map((task: ScheduledTask) => (
              <div
                key={task.task_id}
                className="border border-steel-800 rounded-lg overflow-hidden"
              >
                {/* Task Header */}
                <div
                  className="flex items-center justify-between p-4 bg-navy-1000/50 hover:bg-navy-1000 transition-colors cursor-pointer"
                  onClick={() => setExpandedTask(expandedTask === task.task_id ? null : task.task_id)}
                >
                  <div className="flex items-center gap-4">
                    {getStatusIcon(task.status)}
                    
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-display font-medium text-text-primary">
                          {task.name}
                        </span>
                        <span className={`badge text-xs ${getPriorityBadge(task.priority)}`}>
                          {task.priority}
                        </span>
                        <span className={`badge text-xs ${getStatusBadge(task.status)}`}>
                          {task.status}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="text-xs text-steel-500 font-mono">
                          ID: {task.task_id.slice(0, 12)}
                        </span>
                        <span className="text-xs text-steel-500">
                          类型: {task.task_type}
                        </span>
                        {task.tags.length > 0 && (
                          <div className="flex items-center gap-1">
                            {task.tags.slice(0, 2).map((tag, i) => (
                              <span key={i} className="text-xs px-1.5 py-0.5 rounded bg-steel-800 text-steel-400">
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <div className="text-xs text-steel-400">
                        创建: {format(new Date(task.created_at), 'MM-dd HH:mm:ss')}
                      </div>
                      {task.scheduled_time && (
                        <div className="text-xs text-electric">
                          定时: {format(new Date(task.scheduled_time), 'MM-dd HH:mm:ss')}
                        </div>
                      )}
                    </div>
                    {expandedTask === task.task_id ? (
                      <ChevronUp className="w-4 h-4 text-steel-500" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-steel-500" />
                    )}
                  </div>
                </div>

                {/* Expanded Details */}
                {expandedTask === task.task_id && (
                  <div className="p-4 bg-navy-1100 border-t border-steel-800 space-y-3">
                    {/* Time Info */}
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <div className="text-xs text-steel-500 mb-1">开始时间</div>
                        <div className="text-sm text-text-secondary font-mono">
                          {task.started_at ? format(new Date(task.started_at), 'yyyy-MM-dd HH:mm:ss') : '—'}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-steel-500 mb-1">完成时间</div>
                        <div className="text-sm text-text-secondary font-mono">
                          {task.completed_at ? format(new Date(task.completed_at), 'yyyy-MM-dd HH:mm:ss') : '—'}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-steel-500 mb-1">重试次数</div>
                        <div className="text-sm text-text-secondary">
                          {task.retry_count} 次
                        </div>
                      </div>
                    </div>

                    {/* Error Message */}
                    {task.error_message && (
                      <div className="p-3 rounded-lg bg-error/10 border border-error/20">
                        <div className="flex items-start gap-2">
                          <AlertCircle className="w-4 h-4 text-error mt-0.5" />
                          <div className="flex-1">
                            <div className="text-xs text-error font-medium mb-1">错误信息</div>
                            <div className="text-sm text-error/80">{task.error_message}</div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex items-center gap-2 pt-2">
                      {task.status === 'pending' || task.status === 'queued' ? (
                        <button
                          onClick={() => cancelMutation.mutate(task.task_id)}
                          disabled={cancelMutation.isPending}
                          className="btn-secondary text-error hover:bg-error/10 text-sm"
                        >
                          <Trash2 className="w-3.5 h-3.5 mr-1.5" />
                          取消任务
                        </button>
                      ) : null}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ============================================
          Create Task Modal
          ============================================ */}
      {showCreateModal && (
        <CreateTaskModal onClose={() => setShowCreateModal(false)} />
      )}
    </div>
  );
}

// Create Task Modal Component
function CreateTaskModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    name: '',
    target: '',
    priority: 'normal',
    task_type: 'one_time',
    scheduled_time: '',
    interval: '',
    max_retries: 3,
    retry_interval: 60,
    tags: '',
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => api.createScheduledTask(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-tasks'] });
      queryClient.invalidateQueries({ queryKey: ['scheduler-stats'] });
      onClose();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      ...formData,
      interval: formData.interval ? parseInt(formData.interval) : undefined,
      scheduled_time: formData.scheduled_time || undefined,
      tags: formData.tags.split(',').map(t => t.trim()).filter(Boolean),
    });
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-navy-1100 border border-steel-800 rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-steel-800">
          <h2 className="text-lg font-display font-semibold text-text-primary">
            创建调度任务
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Task Name */}
          <div>
            <label className="label">任务名称</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input-field"
              placeholder="例如: 每日库存检查"
              required
            />
          </div>

          {/* Target Function */}
          <div>
            <label className="label">目标函数</label>
            <input
              type="text"
              value={formData.target}
              onChange={(e) => setFormData({ ...formData, target: e.target.value })}
              className="input-field"
              placeholder="例如: check_inventory"
              required
            />
          </div>

          {/* Task Type & Priority */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">任务类型</label>
              <select
                value={formData.task_type}
                onChange={(e) => setFormData({ ...formData, task_type: e.target.value })}
                className="input-field"
              >
                <option value="one_time">一次性任务</option>
                <option value="scheduled">定时任务</option>
                <option value="recurring">周期性任务</option>
              </select>
            </div>
            <div>
              <label className="label">优先级</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="input-field"
              >
                <option value="low">低</option>
                <option value="normal">普通</option>
                <option value="high">高</option>
                <option value="urgent">紧急</option>
              </select>
            </div>
          </div>

          {/* Scheduled Time */}
          {formData.task_type === 'scheduled' && (
            <div>
              <label className="label">执行时间</label>
              <input
                type="datetime-local"
                value={formData.scheduled_time}
                onChange={(e) => setFormData({ ...formData, scheduled_time: e.target.value })}
                className="input-field"
              />
            </div>
          )}

          {/* Interval */}
          {formData.task_type === 'recurring' && (
            <div>
              <label className="label">执行间隔（秒）</label>
              <input
                type="number"
                value={formData.interval}
                onChange={(e) => setFormData({ ...formData, interval: e.target.value })}
                className="input-field"
                placeholder="例如: 3600 (每小时)"
              />
            </div>
          )}

          {/* Retry Settings */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">最大重试次数</label>
              <input
                type="number"
                value={formData.max_retries}
                onChange={(e) => setFormData({ ...formData, max_retries: parseInt(e.target.value) })}
                className="input-field"
                min="0"
                max="10"
              />
            </div>
            <div>
              <label className="label">重试间隔（秒）</label>
              <input
                type="number"
                value={formData.retry_interval}
                onChange={(e) => setFormData({ ...formData, retry_interval: parseInt(e.target.value) })}
                className="input-field"
                min="1"
              />
            </div>
          </div>

          {/* Tags */}
          <div>
            <label className="label">标签（用逗号分隔）</label>
            <input
              type="text"
              value={formData.tags}
              onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
              className="input-field"
              placeholder="例如: monitoring, inventory, auto"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-steel-800">
            <button type="button" onClick={onClose} className="btn-secondary">
              取消
            </button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? '创建中...' : '创建任务'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
