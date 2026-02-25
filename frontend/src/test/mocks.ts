import { vi } from 'vitest'
import { TaskState, SystemHealth, LLMConfigList, Tool } from '../types'

// Mock API responses
export const mockHealth: SystemHealth = {
  status: 'healthy',
  components: [
    { name: 'database', status: 'healthy', latency_ms: 10 },
    { name: 'cache', status: 'healthy', latency_ms: 5 },
  ],
  version: '1.0.0',
}

export const mockLLMConfigs: LLMConfigList = {
  success: true,
  providers: [
    {
      provider: 'openai',
      name: 'OpenAI',
      api_key_masked: 'sk-***',
      api_base: 'https://api.openai.com/v1',
      model_name: 'gpt-4',
      default_model: 'gpt-4',
      available_models: ['gpt-4', 'gpt-3.5-turbo'],
      temperature: 0.7,
      max_tokens: 2000,
      top_p: 1,
      is_enabled: true,
      is_default: true,
    },
  ],
  default_provider: 'openai',
}

export const mockTools: Tool[] = [
  {
    name: 'SearchDatabase',
    description: 'Search database for information',
    input_schema: {
      type: 'object',
      properties: {
        query: { type: 'string' },
      },
    },
  },
  {
    name: 'CallAPI',
    description: 'Call external API',
    input_schema: {
      type: 'object',
      properties: {
        url: { type: 'string' },
        method: { type: 'string' },
      },
    },
  },
]

export const mockTasks = [
  {
    task_id: 'task-1',
    state: TaskState.SUCCESS,
    intent: 'Test task',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    task_id: 'task-2',
    state: TaskState.EXECUTING,
    intent: 'Another test',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
]

// Mock API functions
export const createApiMock = () => ({
  healthCheck: vi.fn().mockResolvedValue(mockHealth),
  getLLMConfigs: vi.fn().mockResolvedValue(mockLLMConfigs),
  getTools: vi.fn().mockResolvedValue({ tools: mockTools }),
  getTasks: vi.fn().mockResolvedValue({ tasks: mockTasks }),
  getTaskStatus: vi.fn().mockImplementation((taskId: string) => {
    const task = mockTasks.find((t) => t.task_id === taskId)
    return Promise.resolve(task || mockTasks[0])
  }),
  createTask: vi.fn().mockImplementation((input: string) => {
    return Promise.resolve({
      task_id: `task-${Date.now()}`,
      status: 'created',
    })
  }),
  testLLMConnection: vi.fn().mockResolvedValue({
    success: true,
    message: 'Connection successful',
    latency_ms: 100,
  }),
  updateLLMConfig: vi.fn().mockResolvedValue({ success: true }),
  getAgents: vi.fn().mockResolvedValue({
    agents: [
      { name: 'Orchestrator', role: 'Orchestration', status: 'idle' },
      { name: 'IntentAgent', role: 'Intent Recognition', status: 'idle' },
    ],
  }),
})
