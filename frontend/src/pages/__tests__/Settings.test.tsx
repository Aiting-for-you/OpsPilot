import { describe, it, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { Settings } from '../Settings'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi } from 'vitest'
import * as api from '../../services/api'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      gcTime: 0,
    },
  },
})

vi.mock('../../services/api', () => ({
  api: {
    getLLMConfigs: vi.fn().mockResolvedValue({
      success: true,
      providers: [
        {
          provider: 'openai',
          name: 'OpenAI',
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
    }),
    getMCPServers: vi.fn().mockResolvedValue({ servers: [] }),
    getNotificationSettings: vi.fn().mockResolvedValue({}),
  },
}))

const renderWithProviders = (ui: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {ui}
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('Settings', () => {
  it('renders settings page without error', async () => {
    // Just verify component renders without crashing
    const { container } = renderWithProviders(<Settings />)
    expect(container).toBeInTheDocument()
  })
})
