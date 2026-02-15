import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Play, RefreshCw, Search, ChevronRight, Clock, CheckCircle, XCircle } from 'lucide-react';
import { api } from '../services/api';
import { useAppStore, taskStateLabels, taskStateColors } from '../store';
import { TaskState, Task, TaskResult } from '../types';

export function Tasks() {
  const [input, setInput] = useState('');
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const queryClient = useQueryClient();
  const { addTask, tasks } = useAppStore();

  // 创建任务
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

  // 查询任务状态
  const { refetch: refetchTask } = useQuery({
    queryKey: ['task', selectedTask?.task_id],
    queryFn: () => api.getTaskStatus(selectedTask?.task_id || ''),
    enabled: !!selectedTask,
    refetchInterval: (data) => {
      if (data?.state && ![TaskState.SUCCESS, TaskState.FAILED, TaskState.REJECTED].includes(data.state)) {
        return 2000;
      }
      return false;
    },
  });

  // 获取任务结果
  const { data: taskResult } = useQuery({
    queryKey: ['task-result', selectedTask?.task_id],
    queryFn: () => api.getTaskResult(selectedTask?.task_id || ''),
    enabled: !!selectedTask && [TaskState.SUCCESS, TaskState.FAILED].includes(selectedTask.state),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      createTaskMutation.mutate(input.trim());
    }
  };

  return (
    <div className="space-y-6">
      {/* Task Input */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">创建任务</h2>
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="输入任务指令，如：查询供应商库存..."
            className="input flex-1"
          />
          <button
            type="submit"
            disabled={createTaskMutation.isPending || !input.trim()}
            className="btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {createTaskMutation.isPending ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            执行
          </button>
        </form>
      </div>

      {/* Tasks List and Detail */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Task List */}
        <div className="lg:col-span-1 card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">任务列表</h2>
            <button
              onClick={() => queryClient.invalidateQueries({ queryKey: ['tasks'] })}
              className="text-dark-400 hover:text-white"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
          <div className="space-y-2 max-h-[500px] overflow-auto scrollbar-thin">
            {tasks.length === 0 ? (
              <div className="text-center py-8 text-dark-400">暂无任务</div>
            ) : (
              tasks.map((task) => (
                <div
                  key={task.task_id}
                  onClick={() => setSelectedTask(task)}
                  className={`p-3 rounded-lg cursor-pointer transition-colors ${
                    selectedTask?.task_id === task.task_id
                      ? 'bg-primary-600 text-white'
                      : 'bg-dark-700 hover:bg-dark-600 text-dark-100'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-sm">
                      {task.task_id.slice(0, 8)}
                    </span>
                    <ChevronRight className="w-4 h-4" />
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`text-xs ${taskStateColors[task.state]}`}>
                      {taskStateLabels[task.state]}
                    </span>
                    <span className="text-xs text-dark-400">
                      {new Date(task.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Task Detail */}
        <div className="lg:col-span-2 card">
          <h2 className="text-lg font-semibold text-white mb-4">任务详情</h2>
          {!selectedTask ? (
            <div className="text-center py-12 text-dark-400">
              选择一个任务查看详情
            </div>
          ) : (
            <div className="space-y-4">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="label">任务ID</div>
                  <div className="font-mono text-sm text-dark-100">
                    {selectedTask.task_id}
                  </div>
                </div>
                <div>
                  <div className="label">状态</div>
                  <div className={taskStateColors[selectedTask.state]}>
                    {taskStateLabels[selectedTask.state]}
                  </div>
                </div>
                <div>
                  <div className="label">意图</div>
                  <div className="text-dark-100">
                    {selectedTask.intent || '-'}
                  </div>
                </div>
                <div>
                  <div className="label">创建时间</div>
                  <div className="text-dark-100">
                    {new Date(selectedTask.created_at).toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Execution Trace */}
              {taskResult?.execution_trace && (
                <div>
                  <div className="label mb-2">执行轨迹</div>
                  <div className="space-y-2">
                    {taskResult.execution_trace.map((trace, idx) => (
                      <div
                        key={idx}
                        className="flex items-start gap-3 p-3 bg-dark-700 rounded-lg"
                      >
                        <div
                          className={`mt-1 ${
                            trace.status === 'success'
                              ? 'text-green-400'
                              : trace.status === 'failed'
                              ? 'text-red-400'
                              : 'text-yellow-400'
                          }`}
                        >
                          {trace.status === 'success' ? (
                            <CheckCircle className="w-4 h-4" />
                          ) : trace.status === 'failed' ? (
                            <XCircle className="w-4 h-4" />
                          ) : (
                            <Clock className="w-4 h-4" />
                          )}
                        </div>
                        <div className="flex-1">
                          <div className="text-dark-100">{trace.action}</div>
                          <div className="text-xs text-dark-400">
                            {new Date(trace.timestamp).toLocaleTimeString()}
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
                  <div className="label mb-2">执行结果</div>
                  <pre className="p-4 bg-dark-700 rounded-lg overflow-auto text-sm text-dark-100">
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
