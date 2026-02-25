import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Home } from '../Home'
import { BrowserRouter } from 'react-router-dom'

describe('Home', () => {
  it('renders home page', () => {
    render(
      <BrowserRouter>
        <Home />
      </BrowserRouter>
    )
    // Check if page renders
    const headings = screen.getAllByRole('heading')
    expect(headings.length).toBeGreaterThan(0)
  })

  it('renders task input', () => {
    render(
      <BrowserRouter>
        <Home />
      </BrowserRouter>
    )
    const input = screen.getByPlaceholderText(/输入任务|task/i)
    expect(input).toBeInTheDocument()
  })

  it('has execute button', () => {
    render(
      <BrowserRouter>
        <Home />
      </BrowserRouter>
    )
    expect(screen.getByText(/执行|execute/i)).toBeInTheDocument()
  })
})
