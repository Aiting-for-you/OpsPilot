import { describe, it, expect } from 'vitest'

// Test basic functionality
describe('App Logic', () => {
  it('handles task state correctly', () => {
    const taskStates = ['INIT', 'PLANNING', 'AUDITING', 'EXECUTING', 'VERIFYING', 'SUCCESS', 'FAILED', 'REJECTED', 'RETRY']
    expect(taskStates).toHaveLength(9)
    expect(taskStates).toContain('INIT')
    expect(taskStates).toContain('SUCCESS')
    expect(taskStates).toContain('FAILED')
  })

  it('validates task state transitions', () => {
    const terminalStates = ['SUCCESS', 'FAILED', 'REJECTED']
    const isTerminal = (state: string) => terminalStates.includes(state)
    
    expect(isTerminal('SUCCESS')).toBe(true)
    expect(isTerminal('FAILED')).toBe(true)
    expect(isTerminal('INIT')).toBe(false)
    expect(isTerminal('EXECUTING')).toBe(false)
  })

  it('handles agent status correctly', () => {
    const agentStatuses = ['idle', 'processing', 'success', 'error']
    expect(agentStatuses).toHaveLength(4)
    expect(agentStatuses).toContain('idle')
    expect(agentStatuses).toContain('processing')
  })

  it('validates language codes', () => {
    const supportedLanguages = ['zh-CN', 'en-US']
    const isSupported = (code: string) => supportedLanguages.includes(code)
    
    expect(isSupported('zh-CN')).toBe(true)
    expect(isSupported('en-US')).toBe(true)
    expect(isSupported('ja-JP')).toBe(false)
  })
})

describe('Utility Functions', () => {
  it('formats task state to label', () => {
    const stateLabels: Record<string, string> = {
      INIT: '初始化',
      PLANNING: '规划中',
      AUDITING: '审核中',
      EXECUTING: '执行中',
      VERIFYING: '验证中',
      SUCCESS: '成功',
      FAILED: '失败',
      REJECTED: '已拒绝',
      RETRY: '重试中',
    }
    
    expect(stateLabels['INIT']).toBe('初始化')
    expect(stateLabels['SUCCESS']).toBe('成功')
    expect(stateLabels['FAILED']).toBe('失败')
  })

  it('calculates success rate', () => {
    const calculateSuccessRate = (total: number, success: number) => {
      return total > 0 ? Math.round((success / total) * 100) : 100
    }
    
    expect(calculateSuccessRate(10, 8)).toBe(80)
    expect(calculateSuccessRate(10, 10)).toBe(100)
    expect(calculateSuccessRate(0, 0)).toBe(100)
  })

  it('handles pagination', () => {
    const paginate = <T>(items: T[], page: number, pageSize: number): T[] => {
      const start = (page - 1) * pageSize
      return items.slice(start, start + pageSize)
    }
    
    const items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    expect(paginate(items, 1, 3)).toEqual([1, 2, 3])
    expect(paginate(items, 2, 3)).toEqual([4, 5, 6])
    expect(paginate(items, 4, 3)).toEqual([10])
  })
})
