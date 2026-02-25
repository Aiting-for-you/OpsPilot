import { describe, it, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { Dashboard } from '../Dashboard'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      gcTime: 0,
    },
  },
})

const renderWithProviders = (ui: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {ui}
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('Dashboard', () => {
  it('renders dashboard page', async () => {
    renderWithProviders(<Dashboard />)
    
    await waitFor(() => {
      // Check if page renders
      const headings = screen.getAllByRole('heading')
      expect(headings.length).toBeGreaterThan(0)
    }, { timeout: 3000 })
  })
})
