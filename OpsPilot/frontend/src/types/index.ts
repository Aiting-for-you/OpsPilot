// API Types

export interface Task {
  task_id: string;
  state: TaskState;
  intent?: string;
  created_at: string;
  updated_at: string;
}

export enum TaskState {
  INIT = 'INIT',
  PLANNING = 'PLANNING',
  AUDITING = 'AUDITING',
  EXECUTING = 'EXECUTING',
  VERIFYING = 'VERIFYING',
  SUCCESS = 'SUCCESS',
  FAILED = 'FAILED',
  REJECTED = 'REJECTED',
  RETRY = 'RETRY',
}

export interface TaskResult {
  task_id: string;
  state: string;
  result?: any;
  execution_trace?: ExecutionTrace[];
}

export interface ExecutionTrace {
  step: number;
  action: string;
  timestamp: string;
  status: 'success' | 'failed' | 'pending';
  details?: any;
}

export interface Tool {
  name: string;
  description: string;
  input_schema: any;
}

export interface ToolCallResult {
  success: boolean;
  message: string;
  tool_name: string;
  result?: any;
  latency_ms: number;
  fallback_mode?: string;
}

export interface SOP {
  name: string;
  description: string;
  steps: SOPStep[];
}

export interface SOPStep {
  name: string;
  action: string;
  tool?: string;
  params?: any;
}

export interface SOPExecutionResult {
  success: boolean;
  message: string;
  sop_name: string;
  steps_executed: number;
  results: any[];
}

export interface MemoryEntry {
  id: string;
  content: string;
  created_at: string;
  score?: number;
  metadata?: any;
}

export interface AgentStatus {
  name: string;
  role: string;
  status: 'idle' | 'processing' | 'success' | 'error';
  current_task?: string;
  last_activity?: string;
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  components: {
    name: string;
    status: string;
    latency_ms?: number;
  }[];
  version: string;
}
