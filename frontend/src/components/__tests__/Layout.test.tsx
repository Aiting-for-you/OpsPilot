import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Layout } from '../layout/Layout'
import { BrowserRouter } from 'react-router-dom'

describe('Layout', () => {
  it('renders logo and title', () => {
    render(
      <BrowserRouter>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </BrowserRouter>
    )
    expect(screen.getByText('OpsPilot')).toBeInTheDocument()
  })

  it('renders navigation links', () => {
    render(
      <BrowserRouter>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </BrowserRouter>
    )
    expect(screen.getByText(/首页|home/i)).toBeInTheDocument()
    expect(screen.getByText(/仪表盘|dashboard/i)).toBeInTheDocument()
  })

  it('renders children content', () => {
    render(
      <BrowserRouter>
        <Layout>
          <div data-testid="children">Test Content</div>
        </Layout>
      </BrowserRouter>
    )
    expect(screen.getByTestId('children')).toBeInTheDocument()
  })

  it('renders settings link', () => {
    render(
      <BrowserRouter>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </BrowserRouter>
    )
    expect(screen.getByText(/设置|settings/i)).toBeInTheDocument()
  })
})
