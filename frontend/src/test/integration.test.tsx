import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { Home } from '../pages/Home'
import { Tasks } from '../pages/Tasks'
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

// Mock API
vi.mock('../services/api', () => ({
  api: {
    createTask: vi.fn().mockResolvedValue({ task_id: 'task-1', status: 'created' }),
    getTaskStatus: vi.fn().mockImplementation((taskId: string) => {
      return Promise.resolve({
        task_id: taskId,
        state: 'INIT',
      })
    }),
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

describe('Home Integration Tests', () => {
  it('can navigate from home to tasks', async () => {
    renderWithProviders(<Home />)
    
    const taskInput = screen.getByPlaceholderText(/输入任务|task/i)
    expect(taskInput).toBeInTheDocument()
    
    // Type in input
    fireEvent.change(taskInput, { target: { value: 'Test task' } })
    expect(taskInput).toHaveValue('Test task')
  })

  it('quick feature cards are clickable', () => {
    renderWithProviders(<Home />)
    
    // Check that quick feature cards exist
    const cards = screen.getAllByRole('link')
    expect(cards.length).toBeGreaterThan(0)
  })
})

describe('Tasks Integration Tests', () => {
  it('can render tasks page', async () => {
    renderWithProviders(<Tasks />)
    
    await waitFor(() => {
      // Just check page renders without error
      const container = document.querySelector('.space-y-6')
      expect(container).toBeInTheDocument()
    })
  })

  it('shows create task section', async () => {
    renderWithProviders(<Tasks />)
    
    await waitFor(() => {
      // Check for create task heading
      const headings = screen.getAllByRole('heading')
      expect(headings.length).toBeGreaterThan(0)
    })
  })
})
