import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Wrench, Play, Loader2, CheckCircle, AlertCircle, Zap, Terminal, Code, Clock } from 'lucide-react';
import { api } from '../services/api';
import { useAppStore } from '../store';
import { Tool } from '../types';

export function Tools() {
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null);
  const [params, setParams] = useState<string>('{}');
  const { tools, setTools } = useAppStore();

  // Fetch tools list
  const { isLoading } = useQuery({
    queryKey: ['tools'],
    queryFn: async () => {
      const data = await api.getTools();
      setTools(data.tools);
      return data;
    },
  });

  // Call tool mutation
  const callToolMutation = useMutation({
    mutationFn: () => {
      if (!selectedTool) throw new Error('No tool selected');
      let parsedParams = {};
      try {
        parsedParams = JSON.parse(params);
      } catch {
        throw new Error('Invalid JSON params');
      }
      return api.callTool(selectedTool.name, parsedParams);
    },
  });

  const handleCallTool = () => {
    callToolMutation.mutate();
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Tools List */}
        <div className="lg:col-span-4 card">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-8 h-8 rounded-lg bg-electric/10 flex items-center justify-center">
              <Wrench className="w-4 h-4 text-electric" />
            </div>
            <div>
              <h2 className="font-display text-sm font-semibold text-text-primary uppercase tracking-wide">
                Tool Registry
              </h2>
              <p className="text-xs text-steel-500">{tools.length} tools available</p>
            </div>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-6 h-6 border-2 border-electric border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="space-y-2 max-h-[500px] overflow-y-auto scrollbar-custom">
              {tools.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-steel-500">
                  <Wrench className="w-8 h-8 mb-2 opacity-30" />
                  <p className="text-sm">No tools registered</p>
                </div>
              ) : (
                tools.map((tool) => (
                  <div
                    key={tool.name}
                    onClick={() => {
                      setSelectedTool(tool);
                      setParams('{}');
                    }}
                    className={`
                      group p-3 rounded-lg cursor-pointer border transition-all duration-150
                      ${selectedTool?.name === tool.name
                        ? 'bg-electric/5 border-electric/30'
                        : 'bg-navy-1000/50 border-steel-800/50 hover:border-steel-700'
                      }
                    `}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <div className={`w-1.5 h-1.5 rounded-full ${
                        selectedTool?.name === tool.name ? 'bg-electric' : 'bg-steel-600'
                      }`} />
                      <span className="font-display text-sm font-medium text-text-primary">
                        {tool.name}
                      </span>
                    </div>
                    <p className="text-xs text-steel-500 line-clamp-2 ml-3.5">
                      {tool.description}
                    </p>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Tool Execution Panel */}
        <div className="lg:col-span-8 card">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-8 h-8 rounded-lg bg-success/10 flex items-center justify-center">
              <Terminal className="w-4 h-4 text-success" />
            </div>
            <h2 className="font-display text-sm font-semibold text-text-primary uppercase tracking-wide">
              Tool Execution
            </h2>
          </div>

          {!selectedTool ? (
            <div className="flex flex-col items-center justify-center py-16 text-steel-500">
              <Wrench className="w-12 h-12 mb-3 opacity-20" />
              <p className="text-sm">Select a tool to execute</p>
            </div>
          ) : (
            <div className="space-y-5">
              {/* Tool Info */}
              <div className="p-4 rounded-lg bg-navy-1000/50 border border-electric/20">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 rounded-full bg-electric" />
                  <span className="font-display text-sm font-semibold text-electric">
                    {selectedTool.name}
                  </span>
                </div>
                <p className="text-sm text-steel-400 ml-4">
                  {selectedTool.description}
                </p>
              </div>

              {/* Input Schema */}
              {selectedTool.input_schema && (
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Code className="w-4 h-4 text-steel-500" />
                    <span className="label mb-0">Input Schema</span>
                  </div>
                  <pre className="code-block max-h-40 text-xs">
                    {JSON.stringify(selectedTool.input_schema, null, 2)}
                  </pre>
                </div>
              )}

              {/* Params Input */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="w-4 h-4 text-steel-500" />
                  <span className="label mb-0">Parameters (JSON)</span>
                </div>
                <textarea
                  value={params}
                  onChange={(e) => setParams(e.target.value)}
                  className="input h-32 font-mono text-sm resize-none"
                  placeholder='{"key": "value"}'
                />
              </div>

              {/* Execute Button */}
              <button
                onClick={handleCallTool}
                disabled={callToolMutation.isPending}
                className="btn-primary w-full"
              >
                {callToolMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Executing...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Execute Tool
                  </>
                )}
              </button>

              {/* Result */}
              {callToolMutation.data && (
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    {callToolMutation.data.success ? (
                      <CheckCircle className="w-4 h-4 text-success" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-error" />
                    )}
                    <span className="label mb-0">Execution Result</span>
                  </div>
                  
                  <div className="p-4 rounded-lg bg-navy-1000/50 border border-steel-800/50 space-y-3">
                    {/* Latency */}
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-steel-500">Execution Time</span>
                      <span className="font-mono text-xs text-electric">
                        {callToolMutation.data.latency_ms}ms
                      </span>
                    </div>
                    
                    {/* Fallback Mode */}
                    {callToolMutation.data.fallback_mode && (
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-steel-500">Fallback Mode</span>
                        <span className="font-mono text-xs text-warning">
                          {callToolMutation.data.fallback_mode}
                        </span>
                      </div>
                    )}
                    
                    {/* Result Data */}
                    <pre className="code-block text-sm max-h-60">
                      {JSON.stringify(callToolMutation.data.result, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {/* Error */}
              {callToolMutation.isError && (
                <div className="p-4 rounded-lg bg-error/10 border border-error/30 text-error text-sm">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertCircle className="w-4 h-4" />
                    <span className="font-medium">Execution Failed</span>
                  </div>
                  <pre className="text-xs opacity-80 overflow-auto">
                    {String(callToolMutation.error)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
