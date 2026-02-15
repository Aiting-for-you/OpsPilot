import { useState, useEffect, useRef } from 'react';
import { 
  Activity, 
  Clock, 
  Zap, 
  ArrowRight, 
  ChevronDown, 
  ChevronRight,
  Cpu,
  MessageSquare,
  Wrench,
  AlertCircle,
  CheckCircle,
  XCircle
} from 'lucide-react';
import type { TraceSpan, LLMCallTrace, AgentCallTrace, ToolCallTrace, TraceEvent } from '../types';

// 模拟追踪数据
const mockSpans: TraceSpan[] = [
  {
    span_id: 'span-1',
    trace_id: 'trace-123',
    name: 'task.execute',
    start_time: Date.now() - 5000,
    end_time: Date.now() - 100,
    duration_ms: 4900,
    status: 'OK',
    attributes: { task_id: 'task-001', intent: 'query_stock' },
    events: [],
  },
  {
    span_id: 'span-2',
    trace_id: 'trace-123',
    name: 'agent.call.IntentAgent',
    start_time: Date.now() - 4800,
    end_time: Date.now() - 4600,
    duration_ms: 200,
    status: 'OK',
    parent_id: 'span-1',
    attributes: { agent_name: 'IntentAgent', model: 'gpt-4' },
    events: [
      { name: 'agent.input', timestamp: Date.now() - 4800, attributes: { data: '查询库存' } },
      { name: 'agent.output', timestamp: Date.now() - 4600, attributes: { intent: 'query_stock' } },
    ],
  },
  {
    span_id: 'span-3',
    trace_id: 'trace-123',
    name: 'llm.call.gpt-4',
    start_time: Date.now() - 4750,
    end_time: Date.now() - 4650,
    duration_ms: 100,
    status: 'OK',
    parent_id: 'span-2',
    attributes: { 
      'llm.model': 'gpt-4',
      'llm.prompt_tokens': 150,
      'llm.completion_tokens': 50,
      'llm.total_tokens': 200,
      'llm.latency_ms': 100,
    },
    events: [],
  },
  {
    span_id: 'span-4',
    trace_id: 'trace-123',
    name: 'agent.call.ExecAgent',
    start_time: Date.now() - 4500,
    end_time: Date.now() - 2000,
    duration_ms: 2500,
    status: 'OK',
    parent_id: 'span-1',
    attributes: { agent_name: 'ExecAgent' },
    events: [],
  },
  {
    span_id: 'span-5',
    trace_id: 'trace-123',
    name: 'tool.call.query_erp',
    start_time: Date.now() - 4400,
    end_time: Date.now() - 2100,
    duration_ms: 2300,
    status: 'OK',
    parent_id: 'span-4',
    attributes: { 
      'tool.name': 'query_erp',
      'tool.success': true,
    },
    events: [
      { name: 'tool.params', timestamp: Date.now() - 4400, attributes: { query: 'SELECT * FROM inventory' } },
      { name: 'tool.result', timestamp: Date.now() - 2100, attributes: { rows: 150 } },
    ],
  },
];

export function Tracing() {
  const [spans, setSpans] = useState<TraceSpan[]>(mockSpans);
  const [selectedSpan, setSelectedSpan] = useState<TraceSpan | null>(null);
  const [expandedSpans, setExpandedSpans] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<'all' | 'llm' | 'agent' | 'tool'>('all');

  // 过滤 spans
  const filteredSpans = spans.filter(span => {
    if (filter === 'all') return true;
    if (filter === 'llm') return span.name.startsWith('llm.');
    if (filter === 'agent') return span.name.startsWith('agent.');
    if (filter === 'tool') return span.name.startsWith('tool.');
    return true;
  });

  // 获取顶层 spans
  const rootSpans = filteredSpans.filter(s => !s.parent_id);

  // 获取子 spans
  const getChildSpans = (parentId: string): TraceSpan[] => {
    return filteredSpans.filter(s => s.parent_id === parentId);
  };

  // 切换展开状态
  const toggleExpand = (spanId: string) => {
    const newExpanded = new Set(expandedSpans);
    if (newExpanded.has(spanId)) {
      newExpanded.delete(spanId);
    } else {
      newExpanded.add(spanId);
    }
    setExpandedSpans(newExpanded);
  };

  // 计算时间轴位置
  const getTimelinePosition = (span: TraceSpan): { left: number; width: number } => {
    const rootSpan = spans.find(s => !s.parent_id);
    if (!rootSpan) return { left: 0, width: 100 };
    
    const totalDuration = rootSpan.duration_ms;
    const startOffset = span.start_time - rootSpan.start_time;
    const left = (startOffset / totalDuration) * 100;
    const width = (span.duration_ms / totalDuration) * 100;
    
    return { left: Math.max(0, left), width: Math.min(100 - left, width) };
  };

  // 获取 span 图标
  const getSpanIcon = (name: string) => {
    if (name.startsWith('llm.')) return <MessageSquare className="w-4 h-4 text-purple-400" />;
    if (name.startsWith('agent.')) return <Cpu className="w-4 h-4 text-blue-400" />;
    if (name.startsWith('tool.')) return <Wrench className="w-4 h-4 text-green-400" />;
    return <Activity className="w-4 h-4 text-gray-400" />;
  };

  // 获取状态图标
  const getStatusIcon = (status: string) => {
    if (status === 'OK') return <CheckCircle className="w-4 h-4 text-green-400" />;
    if (status === 'ERROR') return <XCircle className="w-4 h-4 text-red-400" />;
    return <Clock className="w-4 h-4 text-gray-400" />;
  };

  // Span 详情面板
  const SpanDetail = ({ span }: { span: TraceSpan }) => (
    <div className="p-4 bg-dark-800 rounded-lg space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {getSpanIcon(span.name)}
          <span className="text-white font-medium">{span.name}</span>
        </div>
        {getStatusIcon(span.status)}
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-dark-400">Span ID</span>
          <p className="text-dark-200 font-mono text-xs">{span.span_id}</p>
        </div>
        <div>
          <span className="text-dark-400">Duration</span>
          <p className="text-dark-200">{span.duration_ms.toFixed(2)}ms</p>
        </div>
      </div>

      {/* Attributes */}
      {Object.keys(span.attributes).length > 0 && (
        <div>
          <h4 className="text-dark-400 text-sm mb-2">Attributes</h4>
          <div className="bg-dark-900 rounded p-2 font-mono text-xs space-y-1">
            {Object.entries(span.attributes).map(([key, value]) => (
              <div key={key} className="flex">
                <span className="text-primary-400">{key}:</span>
                <span className="text-dark-300 ml-2">
                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Events */}
      {span.events.length > 0 && (
        <div>
          <h4 className="text-dark-400 text-sm mb-2">Events</h4>
          <div className="space-y-2">
            {span.events.map((event, idx) => (
              <div key={idx} className="bg-dark-900 rounded p-2">
                <div className="flex items-center gap-2 text-sm">
                  <Zap className="w-3 h-3 text-yellow-400" />
                  <span className="text-dark-200">{event.name}</span>
                </div>
                {Object.keys(event.attributes).length > 0 && (
                  <div className="mt-1 font-mono text-xs text-dark-400">
                    {JSON.stringify(event.attributes)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  // Span 树节点
  const SpanNode = ({ span, depth = 0 }: { span: TraceSpan; depth?: number }) => {
    const children = getChildSpans(span.span_id);
    const isExpanded = expandedSpans.has(span.span_id);
    const timeline = getTimelinePosition(span);

    return (
      <div className="border-l-2 border-dark-700 ml-2">
        <div
          className={`flex items-center gap-2 py-2 px-3 hover:bg-dark-700 cursor-pointer ${
            selectedSpan?.span_id === span.span_id ? 'bg-dark-700' : ''
          }`}
          style={{ paddingLeft: `${depth * 16 + 12}px` }}
          onClick={() => setSelectedSpan(span)}
        >
          {children.length > 0 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleExpand(span.span_id);
              }}
              className="text-dark-400 hover:text-white"
            >
              {isExpanded ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
            </button>
          )}
          {children.length === 0 && <div className="w-4" />}
          
          {getSpanIcon(span.name)}
          <span className="text-dark-200 text-sm flex-1">{span.name}</span>
          <span className="text-dark-400 text-xs">{span.duration_ms.toFixed(1)}ms</span>
          {getStatusIcon(span.status)}
        </div>

        {/* Timeline bar */}
        <div 
          className="h-1 bg-dark-800 relative mb-1"
          style={{ marginLeft: `${depth * 16 + 24}px`, marginRight: '12px' }}
        >
          <div
            className={`absolute h-full rounded ${
              span.status === 'OK' ? 'bg-primary-500' : 
              span.status === 'ERROR' ? 'bg-red-500' : 'bg-gray-500'
            }`}
            style={{ left: `${timeline.left}%`, width: `${timeline.width}%` }}
          />
        </div>

        {/* Children */}
        {isExpanded && children.map(child => (
          <SpanNode key={child.span_id} span={child} depth={depth + 1} />
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">追踪分析</h1>
          <p className="text-dark-400 text-sm mt-1">
            OpenTelemetry 集成 · LLM/Agent/Tool 调用链追踪
          </p>
        </div>
        <div className="flex gap-2">
          {(['all', 'llm', 'agent', 'tool'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded text-sm ${
                filter === f
                  ? 'bg-primary-500 text-white'
                  : 'bg-dark-700 text-dark-300 hover:text-white'
              }`}
            >
              {f === 'all' ? '全部' : f.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="stat-card">
          <div className="stat-label">Total Spans</div>
          <div className="stat-value">{spans.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Duration</div>
          <div className="stat-value">
            {spans.find(s => !s.parent_id)?.duration_ms.toFixed(0) || 0}ms
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">LLM Calls</div>
          <div className="stat-value">{spans.filter(s => s.name.startsWith('llm.')).length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Tool Calls</div>
          <div className="stat-value">{spans.filter(s => s.name.startsWith('tool.')).length}</div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Span Tree */}
        <div className="lg:col-span-2 card">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-5 h-5 text-primary-400" />
            <h2 className="text-lg font-semibold text-white">调用链</h2>
          </div>
          <div className="space-y-1">
            {rootSpans.map(span => (
              <SpanNode key={span.span_id} span={span} />
            ))}
          </div>
        </div>

        {/* Detail Panel */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Zap className="w-5 h-5 text-primary-400" />
            <h2 className="text-lg font-semibold text-white">详情</h2>
          </div>
          {selectedSpan ? (
            <SpanDetail span={selectedSpan} />
          ) : (
            <div className="text-center py-8 text-dark-400">
              <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>选择一个 Span 查看详情</p>
            </div>
          )}
        </div>
      </div>

      {/* Waterfall View */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Clock className="w-5 h-5 text-primary-400" />
          <h2 className="text-lg font-semibold text-white">时间轴视图</h2>
        </div>
        <div className="relative">
          {/* Time markers */}
          <div className="flex justify-between text-xs text-dark-500 mb-2">
            <span>0ms</span>
            <span>1s</span>
            <span>2s</span>
            <span>3s</span>
            <span>4s</span>
            <span>5s</span>
          </div>
          
          {/* Spans */}
          <div className="space-y-2">
            {filteredSpans.map(span => {
              const timeline = getTimelinePosition(span);
              return (
                <div key={span.span_id} className="flex items-center gap-2">
                  <div className="w-40 text-sm text-dark-300 truncate">
                    {span.name}
                  </div>
                  <div className="flex-1 h-6 bg-dark-800 rounded relative">
                    <div
                      className={`absolute h-full rounded flex items-center px-2 text-xs ${
                        span.status === 'OK' ? 'bg-primary-600' : 
                        span.status === 'ERROR' ? 'bg-red-600' : 'bg-gray-600'
                      }`}
                      style={{ left: `${timeline.left}%`, width: `${Math.max(timeline.width, 2)}%` }}
                    >
                      {timeline.width > 10 && (
                        <span className="text-white truncate">{span.duration_ms.toFixed(0)}ms</span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
