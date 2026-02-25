import { useState } from 'react';
import { useTranslation } from 'react-i18next';
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
  running_tasks: number;
  queued_tasks: number;
}

export function Scheduler() {
  const { t } = useTranslation();
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
        return <XCircle className="w-4 h-4 text-gray-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
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
      low: 'bg-gray-300 text-gray-700',
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
          <h1 className="text-2xl font-display font-bold text-gray-900">
            {t('scheduler.title')}
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {t('scheduler.subtitle')}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => startMutation.mutate()}
            disabled={startMutation.isPending}
            className="btn btn-secondary flex items-center gap-2"
          >
            <Play className="w-4 h-4" />
            {t('scheduler.start')}
          </button>
          <button
            onClick={() => stopMutation.mutate()}
            disabled={stopMutation.isPending}
            className="btn btn-secondary flex items-center gap-2"
          >
            <Pause className="w-4 h-4" />
            {t('scheduler.stop')}
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            {t('scheduler.createTask')}
          </button>
        </div>
      </div>

      {/* ============================================
          Stats Grid
          ============================================ */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
        {[
          { label: t('scheduler.totalTasks'), value: stats?.total_tasks || 0, icon: Clock, color: 'text-electric' },
          { label: t('scheduler.completed'), value: stats?.completed_tasks || 0, icon: CheckCircle, color: 'text-success' },
          { label: t('scheduler.failed'), value: stats?.failed_tasks || 0, icon: XCircle, color: 'text-error' },
          { label: t('scheduler.cancelled'), value: stats?.cancelled_tasks || 0, icon: XCircle, color: 'text-gray-500' },
          { label: t('scheduler.running'), value: stats?.running_tasks || 0, icon: RefreshCw, color: 'text-warning' },
          { label: t('scheduler.queued'), value: stats?.queued_tasks || 0, icon: Timer, color: 'text-blue-400' },
        ].map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className="stat-card">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center mb-2 bg-white border border-gray-200`}>
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
            <span className="text-sm text-gray-600">{t('scheduler.statusFilter')}:</span>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="input-field text-sm py-1.5 px-3"
            >
              <option value="all">{t('scheduler.all')}</option>
              <option value="pending">{t('scheduler.pending')}</option>
              <option value="queued">{t('scheduler.queued')}</option>
              <option value="running">{t('scheduler.running')}</option>
              <option value="completed">{t('scheduler.completed')}</option>
              <option value="failed">{t('scheduler.failed')}</option>
              <option value="cancelled">{t('scheduler.cancelled')}</option>
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
          <div className="flex flex-col items-center justify-center py-12 text-gray-500">
            <Clock className="w-12 h-12 mb-3 opacity-30" />
            <p className="text-sm">{t('scheduler.noScheduledTasks')}</p>
            <p className="text-xs text-gray-400 mt-1">{t('scheduler.clickToCreate')}</p>
          </div>
        ) : (
          <div className="space-y-2">
            {tasks.map((task: ScheduledTask) => (
              <div
                key={task.task_id}
                className="border border-gray-200 rounded-lg overflow-hidden"
              >
                {/* Task Header */}
                <div
                  className="flex items-center justify-between p-4 bg-white/50 hover:bg-white transition-colors cursor-pointer"
                  onClick={() => setExpandedTask(expandedTask === task.task_id ? null : task.task_id)}
                >
                  <div className="flex items-center gap-4">
                    {getStatusIcon(task.status)}
                    
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-display font-medium text-gray-900">
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
                        <span className="text-xs text-gray-500 font-mono">
                          ID: {task.task_id.slice(0, 12)}
                        </span>
                        <span className="text-xs text-gray-500">
                          {t('scheduler.type')}: {task.task_type}
                        </span>
                        {task.tags.length > 0 && (
                          <div className="flex items-center gap-1">
                            {task.tags.slice(0, 2).map((tag, i) => (
                              <span key={i} className="text-xs px-1.5 py-0.5 rounded bg-gray-200 text-gray-600">
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
                      <div className="text-xs text-gray-600">
                        {t('scheduler.created')}: {format(new Date(task.created_at), 'MM-dd HH:mm:ss')}
                      </div>
                      {task.scheduled_time && (
                        <div className="text-xs text-electric">
                          {t('scheduler.scheduled')}: {format(new Date(task.scheduled_time), 'MM-dd HH:mm:ss')}
                        </div>
                      )}
                    </div>
                    {expandedTask === task.task_id ? (
                      <ChevronUp className="w-4 h-4 text-gray-500" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-gray-500" />
                    )}
                  </div>
                </div>

                {/* Expanded Details */}
                {expandedTask === task.task_id && (
                  <div className="p-4 bg-gray-100 border-t border-gray-200 space-y-3">
                    {/* Time Info */}
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <div className="text-xs text-gray-500 mb-1">{t('scheduler.startTime')}</div>
                        <div className="text-sm text-gray-600 font-mono">
                          {task.started_at ? format(new Date(task.started_at), 'yyyy-MM-dd HH:mm:ss') : '—'}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500 mb-1">{t('scheduler.completionTime')}</div>
                        <div className="text-sm text-gray-600 font-mono">
                          {task.completed_at ? format(new Date(task.completed_at), 'yyyy-MM-dd HH:mm:ss') : '—'}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500 mb-1">{t('scheduler.retryCount')}</div>
                        <div className="text-sm text-gray-600">
                          {task.retry_count} {t('analytics.calls')}
                        </div>
                      </div>
                    </div>

                    {/* Error Message */}
                    {task.error_message && (
                      <div className="p-3 rounded-lg bg-error/10 border border-error/20">
                        <div className="flex items-start gap-2">
                          <AlertCircle className="w-4 h-4 text-error mt-0.5" />
                          <div className="flex-1">
                            <div className="text-xs text-error font-medium mb-1">{t('scheduler.errorMessage')}</div>
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
                          className="btn btn-secondary text-error hover:bg-error/10 text-sm"
                        >
                          <Trash2 className="w-3.5 h-3.5 mr-1.5" />
                          {t('scheduler.cancelTask')}
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
  const { t } = useTranslation();
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
      <div className="bg-gray-100 border border-gray-200 rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-display font-semibold text-gray-900">
            {t('scheduler.createScheduleTask')}
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Task Name */}
          <div>
            <label className="label">{t('scheduler.taskName')}</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input-field"
              placeholder={t('scheduler.taskNamePlaceholder')}
              required
            />
          </div>

          {/* Target Function */}
          <div>
            <label className="label">{t('scheduler.targetFunction')}</label>
            <input
              type="text"
              value={formData.target}
              onChange={(e) => setFormData({ ...formData, target: e.target.value })}
              className="input-field"
              placeholder={t('scheduler.functionPlaceholder')}
              required
            />
          </div>

          {/* Task Type & Priority */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">{t('scheduler.taskType')}</label>
              <select
                value={formData.task_type}
                onChange={(e) => setFormData({ ...formData, task_type: e.target.value })}
                className="input-field"
              >
                <option value="one_time">{t('scheduler.oneTime')}</option>
                <option value="scheduled">{t('scheduler.scheduledTask')}</option>
                <option value="recurring">{t('scheduler.recurring')}</option>
              </select>
            </div>
            <div>
              <label className="label">{t('scheduler.priority')}</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="input-field"
              >
                <option value="low">{t('tasks.low')}</option>
                <option value="normal">{t('scheduler.normal')}</option>
                <option value="high">{t('tasks.high')}</option>
                <option value="urgent">{t('scheduler.urgent')}</option>
              </select>
            </div>
          </div>

          {/* Scheduled Time */}
          {formData.task_type === 'scheduled' && (
            <div>
              <label className="label">{t('scheduler.executionTime')}</label>
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
              <label className="label">{t('scheduler.interval')}</label>
              <input
                type="number"
                value={formData.interval}
                onChange={(e) => setFormData({ ...formData, interval: e.target.value })}
                className="input-field"
                placeholder={t('scheduler.intervalPlaceholder')}
              />
            </div>
          )}

          {/* Retry Settings */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">{t('scheduler.maxRetries')}</label>
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
              <label className="label">{t('scheduler.retryInterval')}</label>
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
            <label className="label">{t('scheduler.tags')}</label>
            <input
              type="text"
              value={formData.tags}
              onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
              className="input-field"
              placeholder={t('scheduler.tagsPlaceholder')}
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
            <button type="button" onClick={onClose} className="btn btn-secondary">
              {t('scheduler.cancel')}
            </button>
            <button type="submit" className="btn btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? t('scheduler.creating') : t('scheduler.create')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
