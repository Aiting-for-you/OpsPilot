import { describe, it, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { Tools } from '../Tools'
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
    getTools: vi.fn().mockResolvedValue({
      tools: [
        { name: 'SearchDatabase', description: 'Search database', input_schema: {} },
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

describe('Tools', () => {
  it('renders tools page', async () => {
    renderWithProviders(<Tools />)
    
    await waitFor(() => {
      const headings = screen.getAllByRole('heading')
      expect(headings.length).toBeGreaterThan(0)
    }, { timeout: 3000 })
  })
})
