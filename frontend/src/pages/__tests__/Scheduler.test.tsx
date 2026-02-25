import { describe, it, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { Scheduler } from '../Scheduler'
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

describe('Scheduler', () => {
  it('renders scheduler page', async () => {
    renderWithProviders(<Scheduler />)
    
    await waitFor(() => {
      const headings = screen.getAllByRole('heading')
      expect(headings.length).toBeGreaterThan(0)
    }, { timeout: 3000 })
  })
})
