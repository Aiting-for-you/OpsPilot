import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { LanguageSwitcher } from '../LanguageSwitcher'
import i18n from '../../i18n'
import { BrowserRouter } from 'react-router-dom'

describe('LanguageSwitcher', () => {
  beforeEach(() => {
    i18n.changeLanguage('zh-CN')
  })

  it('renders language switcher button', () => {
    render(
      <BrowserRouter>
        <LanguageSwitcher />
      </BrowserRouter>
    )
    // Check for globe icon presence (there should be one)
    const buttons = screen.getAllByRole('button')
    expect(buttons.length).toBeGreaterThan(0)
  })

  it('shows dropdown when clicked', async () => {
    render(
      <BrowserRouter>
        <LanguageSwitcher />
      </BrowserRouter>
    )
    const button = screen.getAllByRole('button')[0]
    fireEvent.click(button)
    
    await waitFor(() => {
      expect(screen.getByText('简体中文')).toBeInTheDocument()
      expect(screen.getByText('English')).toBeInTheDocument()
    })
  })

  it('changes language when option is clicked', async () => {
    render(
      <BrowserRouter>
        <LanguageSwitcher />
      </BrowserRouter>
    )
    const button = screen.getAllByRole('button')[0]
    fireEvent.click(button)
    
    await waitFor(() => {
      const englishButton = screen.getByText('English')
      fireEvent.click(englishButton)
    })
    
    expect(i18n.language).toBe('en-US')
  })
})
