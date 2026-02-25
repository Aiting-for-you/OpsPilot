import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useAppStore } from '../index'
import { TaskState } from '../../types'

describe('useAppStore', () => {
  it('initializes with default state', () => {
    const { result } = renderHook(() => useAppStore())
    
    expect(result.current.tasks).toEqual([])
    expect(result.current.tools).toEqual([])
    expect(result.current.agents).toHaveLength(5)
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('adds a task', () => {
    const { result } = renderHook(() => useAppStore())
    
    const newTask = {
      task_id: 'test-1',
      state: TaskState.INIT,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    
    act(() => {
      result.current.addTask(newTask)
    })
    
    expect(result.current.tasks).toHaveLength(1)
    expect(result.current.tasks[0].task_id).toBe('test-1')
  })

  it('updates a task', () => {
    const { result } = renderHook(() => useAppStore())
    
    const newTask = {
      task_id: 'test-2',
      state: TaskState.INIT,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    
    act(() => {
      result.current.addTask(newTask)
      result.current.updateTask('test-2', { state: TaskState.SUCCESS })
    })
    
    expect(result.current.tasks[0].state).toBe(TaskState.SUCCESS)
  })

  it('sets tools', () => {
    const { result } = renderHook(() => useAppStore())
    
    const tools = [
      { name: 'Tool1', description: 'Desc1', input_schema: {} },
      { name: 'Tool2', description: 'Desc2', input_schema: {} },
    ]
    
    act(() => {
      result.current.setTools(tools)
    })
    
    expect(result.current.tools).toHaveLength(2)
    expect(result.current.tools[0].name).toBe('Tool1')
  })

  it('sets loading state', () => {
    const { result } = renderHook(() => useAppStore())
    
    act(() => {
      result.current.setLoading(true)
    })
    
    expect(result.current.isLoading).toBe(true)
  })

  it('sets error state', () => {
    const { result } = renderHook(() => useAppStore())
    
    act(() => {
      result.current.setError('Test error')
    })
    
    expect(result.current.error).toBe('Test error')
  })

  it('clears error', () => {
    const { result } = renderHook(() => useAppStore())
    
    act(() => {
      result.current.setError('Test error')
      result.current.setError(null)
    })
    
    expect(result.current.error).toBeNull()
  })
})
