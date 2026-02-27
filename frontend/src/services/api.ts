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
  LLMConfigList,
  LLMProviderConfig,
  LLMConfigUpdateRequest,
  LLMTestResult,
  LLMProviderType,
  FetchModelsRequest,
  FetchModelsResponse,
  BatchAddModelsRequest,
  BatchAddModelsResponse,
  PricingNegotiateRequest,
  PricingNegotiateResponse,
  PricingHistoryResponse,
  AgentStatusResponse,
  TicketCreateRequest,
  TicketCreateResponse,
  TicketProcessRequest,
  TicketProcessResponse,
  TicketListResponse,
  Ticket, 
  CSAgentStatusResponse,
  TicketQueueStatus,
  TicketLifecycle,
  KnowledgeBaseResponse,
  KnowledgeBaseQueryRequest,
  TicketAnalyticsData,
  AgentInfo,
  AssignmentResult,
  EscalationRequest,
  EscalationRecord,
  FollowUpRecord,
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

  // ==================== 通用接口方法 ====================

  async get<T = any>(url: string, params?: any): Promise<{ data: T }> {
    const response = await this.client.get(url, { params });
    return response.data;
  }

  async post<T = any>(url: string, data?: any): Promise<{ data: T }> {
    const response = await this.client.post(url, data);
    return response.data;
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

  // ==================== LLM 配置接口 ====================

  async getLLMConfigs(): Promise<LLMConfigList> {
    const response = await this.client.get('/llm/config');
    return response.data;
  }

  async getLLMProviderConfig(provider: LLMProviderType): Promise<LLMProviderConfig> {
    const response = await this.client.get(`/llm/config/${provider}`);
    return response.data;
  }

  async updateLLMConfig(config: LLMConfigUpdateRequest): Promise<LLMProviderConfig> {
    const response = await this.client.put(`/llm/config/${config.provider}`, config);
    return response.data;
  }

  async testLLMConnection(provider: LLMProviderType): Promise<LLMTestResult> {
    const response = await this.client.post(`/llm/config/${provider}/test`);
    return response.data;
  }

  async setDefaultLLM(provider: LLMProviderType): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post(`/llm/config/${provider}/set-default`);
    return response.data;
  }

  // ==================== 模型列表获取 ====================

  async fetchModels(request: FetchModelsRequest): Promise<FetchModelsResponse> {
    const response = await this.client.post('/llm/models/fetch', request);
    return response.data;
  }

  async batchAddModels(request: BatchAddModelsRequest): Promise<BatchAddModelsResponse> {
    const response = await this.client.post('/llm/models/batch-add', request);
    return response.data;
  }

  // ==================== MCP Server 接口 ====================

  async getMCPServers(): Promise<{ success: boolean; servers: any[] }> {
    const response = await this.client.get('/mcp/servers');
    return response.data;
  }

  async getMCPServer(name: string): Promise<any> {
    const response = await this.client.get(`/mcp/servers/${encodeURIComponent(name)}`);
    return response.data;
  }

  async addMCPServer(server: any): Promise<any> {
    const response = await this.client.post('/mcp/servers', server);
    return response.data;
  }

  async updateMCPServer(name: string, server: any): Promise<any> {
    const response = await this.client.put(`/mcp/servers/${encodeURIComponent(name)}`, server);
    return response.data;
  }

  async deleteMCPServer(name: string): Promise<{ success: boolean; message: string }> {
    const response = await this.client.delete(`/mcp/servers/${encodeURIComponent(name)}`);
    return response.data;
  }

  async connectMCPServer(name: string): Promise<any> {
    const response = await this.client.post(`/mcp/servers/${encodeURIComponent(name)}/connect`);
    return response.data;
  }

  async disconnectMCPServer(name: string): Promise<any> {
    const response = await this.client.post(`/mcp/servers/${encodeURIComponent(name)}/disconnect`);
    return response.data;
  }

  async getMCPServerTools(name: string): Promise<{ success: boolean; server_name: string; tools: any[] }> {
    const response = await this.client.get(`/mcp/servers/${encodeURIComponent(name)}/tools`);
    return response.data;
  }

  async getAllMCPTools(): Promise<{ success: boolean; tools: any[] }> {
    const response = await this.client.get('/mcp/tools');
    return response.data;
  }

  async callMCPTool(toolName: string, args: any, serverName?: string): Promise<any> {
    const response = await this.client.post('/mcp/tools/call', {
      tool_name: toolName,
      arguments: args,
      server_name: serverName,
    });
    return response.data;
  }

  // ==================== 任务调度接口 ====================

  async getScheduledTasks(status?: string, tag?: string, limit?: number): Promise<any> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (tag) params.append('tag', tag);
    if (limit) params.append('limit', limit.toString());
    const response = await this.client.get(`/scheduler/tasks?${params.toString()}`);
    return response.data;
  }

  async getScheduledTask(taskId: string): Promise<any> {
    const response = await this.client.get(`/scheduler/tasks/${taskId}`);
    return response.data;
  }

  async createScheduledTask(task: any): Promise<any> {
    const response = await this.client.post('/scheduler/tasks', task);
    return response.data;
  }

  async cancelScheduledTask(taskId: string): Promise<any> {
    const response = await this.client.delete(`/scheduler/tasks/${taskId}`);
    return response.data;
  }

  async getSchedulerStats(): Promise<any> {
    const response = await this.client.get('/scheduler/stats');
    return response.data;
  }

  async startScheduler(): Promise<any> {
    const response = await this.client.post('/scheduler/start');
    return response.data;
  }

  async stopScheduler(): Promise<any> {
    const response = await this.client.post('/scheduler/stop');
    return response.data;
  }

  // ==================== 数据分析接口 ====================

  async getAnalyticsDashboard(startTime?: string, endTime?: string): Promise<any> {
    const params = new URLSearchParams();
    if (startTime) params.append('start_time', startTime);
    if (endTime) params.append('end_time', endTime);
    const response = await this.client.get(`/analytics/dashboard?${params.toString()}`);
    return response.data;
  }

  async getTaskStatistics(startTime?: string, endTime?: string): Promise<any> {
    const params = new URLSearchParams();
    if (startTime) params.append('start_time', startTime);
    if (endTime) params.append('end_time', endTime);
    const response = await this.client.get(`/analytics/tasks?${params.toString()}`);
    return response.data;
  }

  async getAgentPerformance(agentId?: string, startTime?: string, endTime?: string): Promise<any> {
    const params = new URLSearchParams();
    if (agentId) params.append('agent_id', agentId);
    if (startTime) params.append('start_time', startTime);
    if (endTime) params.append('end_time', endTime);
    const response = await this.client.get(`/analytics/agents?${params.toString()}`);
    return response.data;
  }

  async getToolAnalytics(toolName?: string, startTime?: string, endTime?: string): Promise<any> {
    const params = new URLSearchParams();
    if (toolName) params.append('tool_name', toolName);
    if (startTime) params.append('start_time', startTime);
    if (endTime) params.append('end_time', endTime);
    const response = await this.client.get(`/analytics/tools?${params.toString()}`);
    return response.data;
  }

  async getSystemMetrics(): Promise<any> {
    const response = await this.client.get('/analytics/system');
    return response.data;
  }

  // ==================== 定价接口 ====================

  async pricingNegotiate(request: PricingNegotiateRequest): Promise<PricingNegotiateResponse> {
    const response = await this.client.post('/pricing/negotiate', request);
    return response.data;
  }

  async getPricingHistory(productId?: string, limit: number = 20): Promise<PricingHistoryResponse> {
    const params = new URLSearchParams();
    if (productId) params.append('product_id', productId);
    params.append('limit', limit.toString());
    const response = await this.client.get(`/pricing/history?${params.toString()}`);
    return response.data;
  }

  async getPricingAgentStatus(): Promise<AgentStatusResponse> {
    const response = await this.client.get('/pricing/agents/status');
    return response.data;
  }

  // ==================== 客服工单接口 ====================

  async createTicket(request: TicketCreateRequest): Promise<TicketCreateResponse> {
    const response = await this.client.post('/customer-service/tickets', request);
    return response.data;
  }

  async processTicket(request: TicketProcessRequest): Promise<TicketProcessResponse> {
    const response = await this.client.post('/customer-service/tickets/process', request);
    return response.data;
  }

  async listTickets(status?: string, priority?: string, limit: number = 20): Promise<TicketListResponse> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (priority) params.append('priority', priority);
    params.append('limit', limit.toString());
    const response = await this.client.get(`/customer-service/tickets?${params.toString()}`);
    return response.data;
  }

  async getTicket(ticketId: string): Promise<{ success: boolean; ticket: Ticket }> {
    const response = await this.client.get(`/customer-service/tickets/${ticketId}`);
    return response.data;
  }

  async getCSAgentStatus(): Promise<CSAgentStatusResponse> {
    const response = await this.client.get('/customer-service/agents/status');
    return response.data;
  }

  // ==================== 工单队列 API ====================
  async getTicketQueueStatus(): Promise<TicketQueueStatus> {
    const response = await this.client.get('/customer-service/queue/status');
    return response.data;
  }

  // ==================== 生命周期管理 API ====================
  async getTicketLifecycle(ticketId: string): Promise<TicketLifecycle> {
    const response = await this.client.get(`/customer-service/tickets/${ticketId}/lifecycle`);
    return response.data;
  }

  async updateTicketStatus(ticketId: string, status: string, note?: string): Promise<{ success: boolean; message: string }> {
    const response = await this.client.patch(`/customer-service/tickets/${ticketId}/status`, { status, note });
    return response.data;
  }

  // ==================== 知识库 API ====================
  async queryKnowledgeBase(request: KnowledgeBaseQueryRequest): Promise<KnowledgeBaseResponse> {
    const response = await this.client.post('/customer-service/knowledge/query', request);
    return response.data;
  }

  // ==================== 统计分析 API ====================
  async getTicketAnalytics(startDate?: string, endDate?: string): Promise<TicketAnalyticsData> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    const response = await this.client.get(`/customer-service/analytics?${params.toString()}`);
    return response.data;
  }

  // ==================== 智能分配 API ====================
  async getAgentList(): Promise<{ success: boolean; agents: AgentInfo[] }> {
    const response = await this.client.get('/customer-service/agents');
    return response.data;
  }

  async assignTicket(ticketId: string, agentId?: string): Promise<AssignmentResult> {
    const response = await this.client.post('/customer-service/tickets/assign', { ticket_id: ticketId, agent_id: agentId });
    return response.data;
  }

  // ==================== 升级 API ====================
  async escalateTicket(request: EscalationRequest): Promise<{ success: boolean; escalation: EscalationRecord; message: string }> {
    const response = await this.client.post('/customer-service/tickets/escalate', request);
    return response.data;
  }

  // ==================== 跟进 API ====================
  async createFollowUp(ticketId: string, followUpType: string): Promise<{ success: boolean; follow_up: FollowUpRecord; message: string }> {
    const response = await this.client.post('/customer-service/tickets/followup', { ticket_id: ticketId, follow_up_type: followUpType });
    return response.data;
  }

  async submitSatisfactionSurvey(ticketId: string, score: number, feedback?: string): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post('/customer-service/tickets/feedback', { ticket_id: ticketId, score, feedback });
    return response.data;
  }

  // ==================== Observability APIs ====================

  async getObservabilityStatus(): Promise<{
    success: boolean;
    data: {
      studio: {
        available: boolean;
        initialized: boolean;
        dashboard_url: string | null;
      };
      langsmith: {
        available: boolean;
        initialized: boolean;
        project: string | null;
        project_url: string | null;
      };
    };
  }> {
    const response = await this.client.get('/observability/status');
    return response.data;
  }

  async startStudio(): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post('/observability/studio/start');
    return response.data;
  }

  async stopStudio(): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post('/observability/studio/stop');
    return response.data;
  }

  async startLangSmith(): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post('/observability/langsmith/start');
    return response.data;
  }

  async stopLangSmith(): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post('/observability/langsmith/stop');
    return response.data;
  }

  // ==================== Token Usage APIs ====================

  async getTokenUsage(): Promise<{
    success: boolean;
    data: {
      total: {
        prompt_tokens: number;
        completion_tokens: number;
        total_tokens: number;
        total_cost: number;
        record_count: number;
      };
    };
  }> {
    const response = await this.client.get('/tokens/usage');
    return response.data;
  }

  async getTokenByAgent(): Promise<{
    success: boolean;
    data: Record<string, {
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
      total_cost: number;
      call_count: number;
    }>;
  }> {
    const response = await this.client.get('/tokens/by-agent');
    return response.data;
  }

  async getTokenByModel(): Promise<{
    success: boolean;
    data: Record<string, {
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
      total_cost: number;
      call_count: number;
    }>;
  }> {
    const response = await this.client.get('/tokens/by-model');
    return response.data;
  }

  async resetTokenStats(): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post('/tokens/reset');
    return response.data;
  }

  // ==================== Notification APIs ====================

  async getNotificationStatus(): Promise<{
    success: boolean;
    configured: boolean;
    webhook_enabled: boolean;
    slack_enabled: boolean;
    email_enabled: boolean;
  }> {
    const response = await this.client.get('/notification/status');
    return response.data;
  }

  async configureNotification(config: {
    webhook_url?: string;
    slack_token?: string;
    slack_channel?: string;
    smtp_host?: string;
    smtp_port?: number;
    smtp_username?: string;
    smtp_password?: string;
    smtp_from_addr?: string;
  }): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post('/notification/config', config);
    return response.data;
  }
}

export const api = new ApiService();
export default api;
