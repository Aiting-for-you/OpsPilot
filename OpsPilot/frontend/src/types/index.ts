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

// ========================================
// OpenTelemetry Tracing Types (AgentScope Studio 兼容)
// ========================================

export interface TraceSpan {
  span_id: string;
  trace_id: string;
  name: string;
  start_time: number;
  end_time?: number;
  duration_ms: number;
  attributes: Record<string, any>;
  events: TraceEvent[];
  status: 'UNSET' | 'OK' | 'ERROR';
  parent_id?: string;
}

export interface TraceEvent {
  name: string;
  timestamp: number;
  attributes: Record<string, any>;
}

export interface LLMCallTrace {
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  latency_ms: number;
  prompt?: string;
  completion?: string;
}

export interface AgentCallTrace {
  agent_name: string;
  duration_ms: number;
  tools_used: string[];
  input?: any;
  output?: any;
}

export interface ToolCallTrace {
  tool_name: string;
  duration_ms: number;
  success: boolean;
  fallback_mode?: string;
  params?: any;
  result?: any;
}

// ========================================
// SSE Streaming Types (AgentScope Runtime 兼容)
// ========================================

export enum StreamEventType {
  TASK_START = 'task_start',
  TASK_PROGRESS = 'task_progress',
  TASK_COMPLETE = 'task_complete',
  TASK_ERROR = 'task_error',
  AGENT_START = 'agent_start',
  AGENT_MESSAGE = 'agent_message',
  AGENT_TOOL_CALL = 'agent_tool_call',
  AGENT_TOOL_RESULT = 'agent_tool_result',
  AGENT_COMPLETE = 'agent_complete',
  LLM_TOKEN = 'llm_token',
  LLM_COMPLETE = 'llm_complete',
  HEARTBEAT = 'heartbeat',
  INTERRUPT = 'interrupt',
  RESUME = 'resume',
}

export interface StreamEvent {
  event_type: StreamEventType;
  data: Record<string, any>;
  event_id: string;
  timestamp: number;
}

// ========================================
// A2A Protocol Types (AgentScope Runtime 兼容)
// ========================================

export interface AgentCard {
  agent_id: string;
  name: string;
  description: string;
  version: string;
  skills: AgentSkill[];
  endpoints: Record<string, string>;
  metadata: Record<string, any>;
  status: 'online' | 'offline' | 'busy' | 'error';
}

export interface AgentSkill {
  id: string;
  name: string;
  description: string;
  input_schema?: any;
  output_schema?: any;
  tags: string[];
}

export interface A2AMessage {
  message_id: string;
  conversation_id?: string;
  sender_id: string;
  receiver_id?: string;
  message_type: 'request' | 'response' | 'notification' | 'heartbeat';
  skill_id?: string;
  content?: any;
  metadata: Record<string, any>;
  timestamp: number;
  ttl: number;
}
