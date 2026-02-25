import { describe, it, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { Tasks } from '../Tasks'
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
    createTask: vi.fn().mockResolvedValue({ task_id: 'task-1', status: 'created' }),
    getTaskStatus: vi.fn().mockResolvedValue({}),
    getTaskResult: vi.fn().mockResolvedValue({}),
    getTasks: vi.fn().mockResolvedValue({ tasks: [] }),
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

describe('Tasks', () => {
  it('renders tasks page', async () => {
    renderWithProviders(<Tasks />)
    
    await waitFor(() => {
      const headings = screen.getAllByRole('heading')
      expect(headings.length).toBeGreaterThan(0)
    }, { timeout: 3000 })
  })
})
