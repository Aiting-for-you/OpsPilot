import { useState } from 'react';
import { 
  Activity, 
  Clock, 
  Zap, 
  ChevronDown, 
  ChevronRight,
  Cpu,
  MessageSquare,
  Wrench,
  CheckCircle,
  XCircle,
  Network
} from 'lucide-react';
import type { TraceSpan } from '../types';

// Mock trace data
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
      { name: 'agent.input', timestamp: Date.now() - 4800, attributes: { data: 'Query inventory' } },
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
  const [spans] = useState<TraceSpan[]>(mockSpans);
  const [selectedSpan, setSelectedSpan] = useState<TraceSpan | null>(null);
  const [expandedSpans, setExpandedSpans] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<'all' | 'llm' | 'agent' | 'tool'>('all');

  // Filter spans
  const filteredSpans = spans.filter(span => {
    if (filter === 'all') return true;
    if (filter === 'llm') return span.name.startsWith('llm.');
    if (filter === 'agent') return span.name.startsWith('agent.');
    if (filter === 'tool') return span.name.startsWith('tool.');
    return true;
  });

  // Get root spans
  const rootSpans = filteredSpans.filter(s => !s.parent_id);

  // Get child spans
  const getChildSpans = (parentId: string): TraceSpan[] => {
    return filteredSpans.filter(s => s.parent_id === parentId);
  };

  // Toggle expand
  const toggleExpand = (spanId: string) => {
    const newExpanded = new Set(expandedSpans);
    if (newExpanded.has(spanId)) {
      newExpanded.delete(spanId);
    } else {
      newExpanded.add(spanId);
    }
    setExpandedSpans(newExpanded);
  };

  // Calculate timeline position
  const getTimelinePosition = (span: TraceSpan): { left: number; width: number } => {
    const rootSpan = spans.find(s => !s.parent_id);
    if (!rootSpan) return { left: 0, width: 100 };
    
    const totalDuration = rootSpan.duration_ms;
    const startOffset = span.start_time - rootSpan.start_time;
    const left = (startOffset / totalDuration) * 100;
    const width = (span.duration_ms / totalDuration) * 100;
    
    return { left: Math.max(0, left), width: Math.min(100 - left, width) };
  };

  // Get span icon
  const getSpanIcon = (name: string) => {
    if (name.startsWith('llm.')) return <MessageSquare className="w-4 h-4 text-warning" />;
    if (name.startsWith('agent.')) return <Cpu className="w-4 h-4 text-electric" />;
    if (name.startsWith('tool.')) return <Wrench className="w-4 h-4 text-success" />;
    return <Activity className="w-4 h-4 text-steel-500" />;
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    if (status === 'OK') return <CheckCircle className="w-4 h-4 text-success" />;
    if (status === 'ERROR') return <XCircle className="w-4 h-4 text-error" />;
    return <Clock className="w-4 h-4 text-steel-500" />;
  };

  // Span detail panel
  const SpanDetail = ({ span }: { span: TraceSpan }) => (
    <div className="space-y-4">
      <div className="flex items-center justify-between p-3 rounded-lg bg-navy-1000/50 border border-steel-800/50">
        <div className="flex items-center gap-2">
          {getSpanIcon(span.name)}
          <span className="font-display text-sm font-medium text-text-primary">{span.name}</span>
        </div>
        {getStatusIcon(span.status)}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 rounded-lg bg-navy-1000/50 border border-steel-800/50">
          <div className="text-xs text-steel-500 mb-1">Span ID</div>
          <div className="font-mono text-xs text-electric">{span.span_id}</div>
        </div>
        <div className="p-3 rounded-lg bg-navy-1000/50 border border-steel-800/50">
          <div className="text-xs text-steel-500 mb-1">Duration</div>
          <div className="font-mono text-xs text-text-secondary">{span.duration_ms.toFixed(2)}ms</div>
        </div>
      </div>

      {/* Attributes */}
      {Object.keys(span.attributes).length > 0 && (
        <div>
          <div className="label mb-2">Attributes</div>
          <div className="p-3 rounded-lg bg-navy-1000/50 border border-steel-800/50 font-mono text-xs space-y-1">
            {Object.entries(span.attributes).map(([key, value]) => (
              <div key={key} className="flex">
                <span className="text-electric">{key}:</span>
                <span className="text-steel-400 ml-2">
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
          <div className="label mb-2">Events</div>
          <div className="space-y-2">
            {span.events.map((event, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-navy-1000/50 border border-steel-800/50">
                <div className="flex items-center gap-2">
                  <Zap className="w-3 h-3 text-warning" />
                  <span className="text-xs text-text-primary">{event.name}</span>
                </div>
                {Object.keys(event.attributes).length > 0 && (
                  <div className="mt-2 font-mono text-xs text-steel-500">
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

  // Span tree node
  const SpanNode = ({ span, depth = 0 }: { span: TraceSpan; depth?: number }) => {
    const children = getChildSpans(span.span_id);
    const isExpanded = expandedSpans.has(span.span_id);
    const timeline = getTimelinePosition(span);

    return (
      <div className="border-l border-steel-800/50 ml-3">
        <div
          className={`
            flex items-center gap-3 py-2.5 px-3 cursor-pointer transition-all
            ${selectedSpan?.span_id === span.span_id 
              ? 'bg-electric/5 border-l-2 border-l-electric -ml-0.5 pl-2.5' 
              : 'hover:bg-navy-1000/30'
            }
          `}
          style={{ paddingLeft: `${depth * 16 + 12}px` }}
          onClick={() => setSelectedSpan(span)}
        >
          {children.length > 0 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleExpand(span.span_id);
              }}
              className="text-steel-500 hover:text-electric transition-colors"
            >
              {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            </button>
          )}
          {children.length === 0 && <div className="w-4" />}
          
          {getSpanIcon(span.name)}
          <span className="text-sm text-text-secondary flex-1 truncate">{span.name}</span>
          <span className="font-mono text-xs text-steel-500">{span.duration_ms.toFixed(1)}ms</span>
          {getStatusIcon(span.status)}
        </div>

        {/* Timeline bar */}
        <div 
          className="h-1 bg-navy-1000/50 relative mb-1 rounded-full overflow-hidden"
          style={{ marginLeft: `${depth * 16 + 28}px`, marginRight: '16px' }}
        >
          <div
            className={`absolute h-full rounded-full ${
              span.status === 'OK' ? 'bg-electric' : 
              span.status === 'ERROR' ? 'bg-error' : 'bg-steel-600'
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
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-electric/10 flex items-center justify-center">
            <Network className="w-4 h-4 text-electric" />
          </div>
          <div>
            <h1 className="font-display text-sm font-semibold text-text-primary uppercase tracking-wide">
              Tracing Analysis
            </h1>
            <p className="text-xs text-steel-500">OpenTelemetry integration · LLM/Agent/Tool traces</p>
          </div>
        </div>
        <div className="flex gap-2">
          {(['all', 'llm', 'agent', 'tool'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-md text-xs font-mono uppercase transition-all ${
                filter === f
                  ? 'bg-electric/20 text-electric border border-electric/30'
                  : 'bg-navy-1000/50 text-steel-500 border border-steel-800/50 hover:border-steel-700'
              }`}
            >
              {f}
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
          <div className="stat-label">Duration</div>
          <div className="stat-value">{spans.find(s => !s.parent_id)?.duration_ms.toFixed(0) || 0}ms</div>
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
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Span Tree */}
        <div className="lg:col-span-8 card">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-8 h-8 rounded-lg bg-success/10 flex items-center justify-center">
              <Activity className="w-4 h-4 text-success" />
            </div>
            <h2 className="font-display text-sm font-semibold text-text-primary uppercase tracking-wide">
              Call Chain
            </h2>
          </div>
          <div className="space-y-1">
            {rootSpans.map(span => (
              <SpanNode key={span.span_id} span={span} />
            ))}
          </div>
        </div>

        {/* Detail Panel */}
        <div className="lg:col-span-4 card">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-8 h-8 rounded-lg bg-warning/10 flex items-center justify-center">
              <Zap className="w-4 h-4 text-warning" />
            </div>
            <h2 className="font-display text-sm font-semibold text-text-primary uppercase tracking-wide">
              Details
            </h2>
          </div>
          {selectedSpan ? (
            <SpanDetail span={selectedSpan} />
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-steel-500">
              <Activity className="w-10 h-10 mb-3 opacity-20" />
              <p className="text-sm">Select a span to view details</p>
            </div>
          )}
        </div>
      </div>

      {/* Waterfall View */}
      <div className="card">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-8 h-8 rounded-lg bg-electric/10 flex items-center justify-center">
            <Clock className="w-4 h-4 text-electric" />
          </div>
          <h2 className="font-display text-sm font-semibold text-text-primary uppercase tracking-wide">
            Timeline View
          </h2>
        </div>
        
        {/* Time markers */}
        <div className="flex justify-between text-xs text-steel-600 mb-3 font-mono px-44">
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
              <div key={span.span_id} className="flex items-center gap-3">
                <div className="w-40 text-xs text-steel-400 truncate font-mono">
                  {span.name}
                </div>
                <div className="flex-1 h-6 bg-navy-1000/50 rounded relative overflow-hidden">
                  <div
                    className={`absolute h-full rounded flex items-center px-2 text-xs ${
                      span.status === 'OK' ? 'bg-electric' : 
                      span.status === 'ERROR' ? 'bg-error' : 'bg-steel-600'
                    }`}
                    style={{ left: `${timeline.left}%`, width: `${Math.max(timeline.width, 2)}%` }}
                  >
                    {timeline.width > 10 && (
                      <span className="text-navy-950 font-mono truncate">{span.duration_ms.toFixed(0)}ms</span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
