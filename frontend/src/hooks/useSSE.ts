import { useState, useEffect, useCallback, useRef } from 'react';
import type { StreamEvent, StreamEventType } from '../types';

interface UseSSEOptions {
  url: string;
  onEvent?: (event: StreamEvent) => void;
  onError?: (error: Error) => void;
  autoConnect?: boolean;
}

interface UseSSEReturn {
  events: StreamEvent[];
  isConnected: boolean;
  isConnecting: boolean;
  error: Error | null;
  connect: () => void;
  disconnect: () => void;
  clearEvents: () => void;
}

/**
 * SSE (Server-Sent Events) Hook
 * 
 * 用于实时接收 AgentScope Runtime 的流式输出
 */
export function useSSE(options: UseSSEOptions): UseSSEReturn {
  const { url, onEvent, onError, autoConnect = true } = options;
  
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    setIsConnected(false);
    setIsConnecting(false);
    reconnectAttempts.current = 0;
  }, []);

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    setIsConnecting(true);
    setError(null);

    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
      setIsConnecting(false);
      reconnectAttempts.current = 0;
    };

    eventSource.onerror = (err) => {
      setIsConnected(false);
      setIsConnecting(false);
      
      const error = new Error('SSE connection error');
      setError(error);
      onError?.(error);

      // Auto reconnect with exponential backoff
      if (reconnectAttempts.current < maxReconnectAttempts) {
        const delay = Math.min(
          1000 * Math.pow(2, reconnectAttempts.current),
          30000
        );
        
        reconnectTimeoutRef.current = window.setTimeout(() => {
          reconnectAttempts.current++;
          connect();
        }, delay);
      }
    };

    // Listen for all event types
    const eventTypes: StreamEventType[] = [
      'task_start' as StreamEventType,
      'task_progress' as StreamEventType,
      'task_complete' as StreamEventType,
      'task_error' as StreamEventType,
      'agent_start' as StreamEventType,
      'agent_message' as StreamEventType,
      'agent_tool_call' as StreamEventType,
      'agent_tool_result' as StreamEventType,
      'agent_complete' as StreamEventType,
      'llm_token' as StreamEventType,
      'llm_complete' as StreamEventType,
      'heartbeat' as StreamEventType,
    ];

    eventTypes.forEach((eventType) => {
      eventSource.addEventListener(eventType, (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          const event: StreamEvent = {
            event_type: eventType,
            data,
            event_id: e.lastEventId || crypto.randomUUID(),
            timestamp: Date.now(),
          };
          
          setEvents((prev) => [...prev, event]);
          onEvent?.(event);
        } catch (err) {
          console.error('Failed to parse SSE event:', err);
        }
      });
    });

    // Generic message handler
    eventSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        const event: StreamEvent = {
          event_type: 'task_progress' as StreamEventType,
          data,
          event_id: e.lastEventId || crypto.randomUUID(),
          timestamp: Date.now(),
        };
        
        setEvents((prev) => [...prev, event]);
        onEvent?.(event);
      } catch (err) {
        console.error('Failed to parse SSE message:', err);
      }
    };
  }, [url, onEvent, onError]);

  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    
    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    events,
    isConnected,
    isConnecting,
    error,
    connect,
    disconnect,
    clearEvents,
  };
}

/**
 * Task Stream Hook
 * 
 * 用于订阅特定任务的流式输出
 */
export function useTaskStream(taskId: string | null) {
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const url = taskId ? `${apiUrl}/api/v1/tasks/${taskId}/stream` : '';
  
  return useSSE({
    url,
    autoConnect: !!taskId,
  });
}
