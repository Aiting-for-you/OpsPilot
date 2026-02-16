import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Play, RefreshCw, ChevronRight, Clock, CheckCircle, XCircle, Terminal, Zap, ArrowRight } from 'lucide-react';
import { api } from '../services/api';
import { useAppStore, taskStateLabels } from '../store';
import { TaskState, Task, TaskResult } from '../types';

const terminalStates = [TaskState.SUCCESS, TaskState.FAILED, TaskState.REJECTED] as const;

export function Tasks() {
  const { t, i18n } = useTranslation();
  const [input, setInput] = useState('');
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const queryClient = useQueryClient();
  const { addTask, tasks } = useAppStore();

  // Create task mutation
  const createTaskMutation = useMutation({
    mutationFn: (userInput: string) => api.createTask(userInput),
    onSuccess: (data) => {
      const newTask: Task = {
        task_id: data.task_id,
        state: TaskState.INIT,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      addTask(newTask);
      setInput('');
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  // Query task status
  const { refetch: refetchTask } = useQuery({
    queryKey: ['task', selectedTask?.task_id],
    queryFn: () => api.getTaskStatus(selectedTask?.task_id || ''),
    enabled: !!selectedTask,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && 'state' in data && !terminalStates.includes((data as any).state)) {
        return 2000;
      }
      return false;
    },
  });

  // Get task result
  const { data: taskResult } = useQuery({
    queryKey: ['task-result', selectedTask?.task_id],
    queryFn: () => api.getTaskResult(selectedTask?.task_id || ''),
    enabled: !!selectedTask && (selectedTask.state === TaskState.SUCCESS || selectedTask.state === TaskState.FAILED),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      createTaskMutation.mutate(input.trim());
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* ============================================
          Task Input Panel
          ============================================ */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-lg bg-electric/10 flex items-center justify-center">
            <Terminal className="w-4 h-4 text-electric" />
          </div>
          <div>
            <h2 className="font-display text-sm font-semibold text-text-primary uppercase tracking-wide">
              {t('tasks.createTask')}
            </h2>
            <p className="text-xs text-steel-500">{t('tasks.enterTask')}</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="flex gap-3">
          <div className="relative flex-1">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={t('tasks.placeholder')}
              className="input pr-10"
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-steel-600">
              <Zap className="w-4 h-4" />
            </div>
          </div>
          <button
            type="submit"
            disabled={createTaskMutation.isPending || !input.trim()}
            className="btn-primary min-w-[100px]"
          >
            {createTaskMutation.isPending ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <Play className="w-4 h-4" />
                {t('common.create')}
              </>
            )}
          </button>
        </form>
      </div>

      {/* ============================================
          Tasks Grid
          ============================================ */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Task List */}
        <div className="lg:col-span-4 card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-warning/10 flex items-center justify-center">
                <Clock className="w-4 h-4 text-warning" />
              </div>
              <h2 className="font-display text-sm font-semibold text-text-primary uppercase tracking-wide">
                {t('tasks.taskQueue')}
              </h2>
            </div>
            <button
              onClick={() => queryClient.invalidateQueries({ queryKey: ['tasks'] })}
              className="p-1.5 rounded-md text-steel-500 hover:text-electric hover:bg-steel-800/50 transition-all"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          <div className="space-y-2 max-h-[500px] overflow-y-auto scrollbar-custom">
            {tasks.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-steel-500">
                <Terminal className="w-8 h-8 mb-2 opacity-30" />
                <p className="text-sm">{t('tasks.noActiveTasks')}</p>
              </div>
            ) : (
              tasks.map((task, idx) => (
                <div
                  key={task.task_id}
                  onClick={() => setSelectedTask(task)}
                  className={`
                    group flex items-center justify-between p-3 rounded-lg cursor-pointer
                    border transition-all duration-150
                    ${selectedTask?.task_id === task.task_id
                      ? 'bg-electric/5 border-electric/30'
                      : 'bg-navy-1000/50 border-steel-800/50 hover:border-steel-700'
                    }
                  `}
                >
                  <div className="flex items-center gap-3">
                    <span className={`badge badge-${
                      task.state === TaskState.SUCCESS ? 'success' :
                      task.state === TaskState.FAILED ? 'error' :
                      task.state === TaskState.RUNNING ? 'processing' : 'idle'
                    }`}>
                      {taskStateLabels[task.state]}
                    </span>
                    <div>
                      <span className="font-mono text-sm text-electric">
                        {task.task_id.slice(0, 8)}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-steel-500 font-mono">
                      {new Date(task.created_at).toLocaleTimeString(i18n.language === 'zh-CN' ? 'zh-CN' : 'en-US', { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                    </span>
                    <ChevronRight className={`w-4 h-4 text-steel-600 group-hover:text-electric transition-colors ${
                      selectedTask?.task_id === task.task_id ? 'text-electric' : ''
                    }`} />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Task Detail */}
        <div className="lg:col-span-8 card">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-8 h-8 rounded-lg bg-success/10 flex items-center justify-center">
              <ArrowRight className="w-4 h-4 text-success" />
            </div>
            <h2 className="font-display text-sm font-semibold text-text-primary uppercase tracking-wide">
              {t('tasks.taskDetails')}
            </h2>
          </div>

          {!selectedTask ? (
            <div className="flex flex-col items-center justify-center py-16 text-steel-500">
              <Terminal className="w-12 h-12 mb-3 opacity-20" />
              <p className="text-sm">{t('tools.noToolSelected')}</p>
            </div>
          ) : (
            <div className="space-y-5">
              {/* Basic Info Grid */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 rounded-lg bg-navy-1000/50 border border-steel-800/50">
                  <div className="label">{t('dashboard.taskId')}</div>
                  <div className="font-mono text-sm text-electric break-all">
                    {selectedTask.task_id}
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-navy-1000/50 border border-steel-800/50">
                  <div className="label">{t('dashboard.status')}</div>
                  <span className={`badge badge-${
                    selectedTask.state === TaskState.SUCCESS ? 'success' :
                    selectedTask.state === TaskState.FAILED ? 'error' :
                    selectedTask.state === TaskState.RUNNING ? 'processing' : 'idle'
                  }`}>
                    {taskStateLabels[selectedTask.state]}
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-navy-1000/50 border border-steel-800/50">
                  <div className="label">{t('dashboard.intent')}</div>
                  <div className="text-text-secondary">
                    {selectedTask.intent || '—'}
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-navy-1000/50 border border-steel-800/50">
                  <div className="label">{t('dashboard.created')}</div>
                  <div className="font-mono text-sm text-text-secondary">
                    {new Date(selectedTask.created_at).toLocaleString(i18n.language === 'zh-CN' ? 'zh-CN' : 'en-US')}
                  </div>
                </div>
              </div>

              {/* Execution Trace */}
              {taskResult?.execution_trace && taskResult.execution_trace.length > 0 && (
                <div>
                  <div className="label mb-3">{t('tasks.steps')}</div>
                  <div className="space-y-2">
                    {taskResult.execution_trace.map((trace, idx) => (
                      <div
                        key={idx}
                        className="flex items-start gap-3 p-3 rounded-lg bg-navy-1000/50 border border-steel-800/50"
                      >
                        <div className={`mt-0.5 ${
                          trace.status === 'success' ? 'text-success' :
                          trace.status === 'failed' ? 'text-error' : 'text-warning'
                        }`}>
                          {trace.status === 'success' ? (
                            <CheckCircle className="w-4 h-4" />
                          ) : trace.status === 'failed' ? (
                            <XCircle className="w-4 h-4" />
                          ) : (
                            <Clock className="w-4 h-4" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-text-primary text-sm">{trace.action}</div>
                          <div className="font-mono text-xs text-steel-500 mt-1">
                            {new Date(trace.timestamp).toLocaleTimeString(i18n.language === 'zh-CN' ? 'zh-CN' : 'en-US')}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Result */}
              {taskResult?.result && (
                <div>
                  <div className="label mb-3">{t('tasks.results')}</div>
                  <pre className="code-block max-h-60 overflow-auto">
                    {JSON.stringify(taskResult.result, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
