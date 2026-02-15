import axios, { AxiosInstance } from 'axios';
import { 
  Task, 
  TaskResult, 
  Tool, 
  ToolCallResult, 
  SOPExecutionResult, 
  MemoryEntry, 
  SystemHealth,
  TraceSpan,
  AgentCard,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // ==================== 任务接口 ====================

  async createTask(userInput: string): Promise<{ task_id: string; status: string }> {
    const response = await this.client.post('/tasks', { user_input: userInput });
    return response.data;
  }

  async getTaskStatus(taskId: string): Promise<Task> {
    const response = await this.client.get(`/tasks/${taskId}`);
    return response.data;
  }

  async getTaskResult(taskId: string): Promise<TaskResult> {
    const response = await this.client.get(`/tasks/${taskId}/result`);
    return response.data;
  }

  // ==================== 工具接口 ====================

  async getTools(): Promise<{ tools: Tool[] }> {
    const response = await this.client.get('/tools');
    return response.data;
  }

  async callTool(toolName: string, params: any, taskId?: string): Promise<ToolCallResult> {
    const response = await this.client.post('/tools/call', {
      tool_name: toolName,
      params,
      task_id: taskId,
    });
    return response.data;
  }

  // ==================== SOP 接口 ====================

  async getSOPs(): Promise<{ sops: string[] }> {
    const response = await this.client.get('/sop/list');
    return response.data;
  }

  async executeSOP(sopName: string, variables: any): Promise<SOPExecutionResult> {
    const response = await this.client.post('/sop/execute', {
      sop_name: sopName,
      variables,
    });
    return response.data;
  }

  // ==================== 记忆接口 ====================

  async storeMemory(content: string, taskId?: string, metadata?: any): Promise<{ entry_id: string }> {
    const response = await this.client.post('/memory/store', {
      content,
      task_id: taskId,
      metadata,
    });
    return response.data;
  }

  async searchMemory(query: string, limit: number = 10): Promise<{ results: MemoryEntry[] }> {
    const response = await this.client.post('/memory/search', {
      query,
      limit,
    });
    return response.data;
  }

  // ==================== 知识库接口 ====================

  async queryKnowledge(query: string, limit: number = 5): Promise<{ results: any[] }> {
    const response = await this.client.post('/knowledge/query', {
      query,
      limit,
    });
    return response.data;
  }

  // ==================== 追踪接口 (OpenTelemetry) ====================

  async getTrace(traceId: string): Promise<{ spans: TraceSpan[] }> {
    const response = await this.client.get(`/tracing/trace/${traceId}`);
    return response.data;
  }

  async getTaskTrace(taskId: string): Promise<{ spans: TraceSpan[] }> {
    const response = await this.client.get(`/tracing/task/${taskId}`);
    return response.data;
  }

  // ==================== A2A 接口 ====================

  async discoverAgents(skillId?: string, tags?: string[]): Promise<{ agents: AgentCard[] }> {
    const params: any = {};
    if (skillId) params.skill_id = skillId;
    if (tags) params.tags = tags.join(',');
    const response = await this.client.get('/a2a/agents', { params });
    return response.data;
  }

  async getAgent(agentId: string): Promise<AgentCard> {
    const response = await this.client.get(`/a2a/agents/${agentId}`);
    return response.data;
  }

  async invokeAgentSkill(
    agentId: string,
    skillId: string,
    input: any
  ): Promise<{ result: any }> {
    const response = await this.client.post(`/a2a/agents/${agentId}/invoke`, {
      skill_id: skillId,
      input,
    });
    return response.data;
  }

  // ==================== 健康检查 ====================

  async healthCheck(): Promise<SystemHealth> {
    const response = await this.client.get('/health');
    return response.data;
  }
}

export const api = new ApiService();
export default api;
