import { create } from 'zustand';
import { Task, Tool, AgentStatus, TaskState } from '../types';

interface AppState {
  // 任务状态
  currentTask: Task | null;
  tasks: Task[];
  
  // 工具状态
  tools: Tool[];
  selectedTool: Tool | null;
  
  // Agent 状态
  agents: AgentStatus[];
  
  // UI 状态
  sidebarOpen: boolean;
  activeTab: string;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setCurrentTask: (task: Task | null) => void;
  addTask: (task: Task) => void;
  updateTask: (taskId: string, updates: Partial<Task>) => void;
  setTools: (tools: Tool[]) => void;
  setSelectedTool: (tool: Tool | null) => void;
  setAgents: (agents: AgentStatus[]) => void;
  setSidebarOpen: (open: boolean) => void;
  setActiveTab: (tab: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // 初始状态
  currentTask: null,
  tasks: [],
  tools: [],
  selectedTool: null,
  agents: [
    { name: 'Orchestrator', role: '调度', status: 'idle' },
    { name: 'IntentAgent', role: '意图识别', status: 'idle' },
    { name: 'PlanAgent', role: '规划', status: 'idle' },
    { name: 'ExecAgent', role: '执行', status: 'idle' },
    { name: 'VerifyAgent', role: '验证', status: 'idle' },
  ],
  sidebarOpen: true,
  activeTab: 'dashboard',
  isLoading: false,
  error: null,
  
  // Actions
  setCurrentTask: (task) => set({ currentTask: task }),
  addTask: (task) => set((state) => ({ tasks: [task, ...state.tasks] })),
  updateTask: (taskId, updates) => set((state) => ({
    tasks: state.tasks.map((t) => t.task_id === taskId ? { ...t, ...updates } : t),
    currentTask: state.currentTask?.task_id === taskId 
      ? { ...state.currentTask, ...updates } 
      : state.currentTask,
  })),
  setTools: (tools) => set({ tools }),
  setSelectedTool: (tool) => set({ selectedTool: tool }),
  setAgents: (agents) => set({ agents }),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
}));

// 任务状态颜色映射
export const taskStateColors: Record<TaskState, string> = {
  [TaskState.INIT]: 'text-gray-400',
  [TaskState.PLANNING]: 'text-blue-400',
  [TaskState.AUDITING]: 'text-yellow-400',
  [TaskState.EXECUTING]: 'text-purple-400',
  [TaskState.VERIFYING]: 'text-cyan-400',
  [TaskState.SUCCESS]: 'text-green-400',
  [TaskState.FAILED]: 'text-red-400',
  [TaskState.REJECTED]: 'text-red-500',
  [TaskState.RETRY]: 'text-orange-400',
};

export const taskStateLabels: Record<TaskState, string> = {
  [TaskState.INIT]: '初始化',
  [TaskState.PLANNING]: '规划中',
  [TaskState.AUDITING]: '审核中',
  [TaskState.EXECUTING]: '执行中',
  [TaskState.VERIFYING]: '验证中',
  [TaskState.SUCCESS]: '成功',
  [TaskState.FAILED]: '失败',
  [TaskState.REJECTED]: '已拒绝',
  [TaskState.RETRY]: '重试中',
};
