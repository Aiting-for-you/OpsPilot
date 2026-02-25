import { describe, it, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { Agents } from '../Agents'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi } from 'vitest'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      gcTime: 0,
    },
  },
})

vi.mock('../services/api', () => ({
  api: {
    getAgents: vi.fn().mockResolvedValue({
      agents: [
        { name: 'Orchestrator', role: 'Orchestration', status: 'idle' },
      ],
    }),
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

describe('Agents', () => {
  it('renders agents page', async () => {
    renderWithProviders(<Agents />)
    
    await waitFor(() => {
      // Just check if page renders without error
      const headings = screen.getAllByRole('heading')
      expect(headings.length).toBeGreaterThan(0)
    }, { timeout: 3000 })
  })
})
