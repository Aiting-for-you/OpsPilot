import { describe, it, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { PricingManagement } from '../PricingManagement'
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
    getPricingAgentsStatus: vi.fn().mockResolvedValue({
      agents: {
        MarketAgent: { status: 'active', weight: 0.3, description: 'Market analysis' },
        CostAgent: { status: 'active', weight: 0.3, description: 'Cost calculation' },
        CompetitorAgent: { status: 'active', weight: 0.2, description: 'Competitor analysis' },
        CustomerAgent: { status: 'active', weight: 0.2, description: 'Customer value analysis' },
      },
    }),
    negotiatePrice: vi.fn().mockResolvedValue({
      trace_id: 'trace-1',
      product_id: 'prod-1',
      final_price: 99.99,
      confidence: 0.95,
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

describe('PricingManagement', () => {
  it('renders pricing page', async () => {
    renderWithProviders(<PricingManagement />)
    
    await waitFor(() => {
      const headings = screen.getAllByRole('heading')
      expect(headings.length).toBeGreaterThan(0)
    }, { timeout: 3000 })
  })
})
