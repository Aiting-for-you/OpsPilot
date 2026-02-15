import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Wrench, Play, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { api } from '../services/api';
import { useAppStore } from '../store';
import { Tool } from '../types';

export function Tools() {
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null);
  const [params, setParams] = useState<string>('{}');
  const { tools, setTools } = useAppStore();

  // 获取工具列表
  const { isLoading } = useQuery({
    queryKey: ['tools'],
    queryFn: async () => {
      const data = await api.getTools();
      setTools(data.tools);
      return data;
    },
  });

  // 调用工具
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
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tools List */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Wrench className="w-5 h-5 text-primary-400" />
            <h2 className="text-lg font-semibold text-white">工具列表</h2>
          </div>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-primary-400" />
            </div>
          ) : (
            <div className="space-y-2 max-h-[500px] overflow-auto scrollbar-thin">
              {tools.length === 0 ? (
                <div className="text-center py-8 text-dark-400">暂无工具</div>
              ) : (
                tools.map((tool) => (
                  <div
                    key={tool.name}
                    onClick={() => {
                      setSelectedTool(tool);
                      setParams('{}');
                    }}
                    className={`p-3 rounded-lg cursor-pointer transition-colors ${
                      selectedTool?.name === tool.name
                        ? 'bg-primary-600 text-white'
                        : 'bg-dark-700 hover:bg-dark-600 text-dark-100'
                    }`}
                  >
                    <div className="font-medium">{tool.name}</div>
                    <div className="text-sm text-dark-300 line-clamp-2 mt-1">
                      {tool.description}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Tool Detail & Execution */}
        <div className="lg:col-span-2 card">
          <h2 className="text-lg font-semibold text-white mb-4">工具调用</h2>
          {!selectedTool ? (
            <div className="text-center py-12 text-dark-400">
              选择一个工具进行调用
            </div>
          ) : (
            <div className="space-y-4">
              {/* Tool Info */}
              <div className="p-4 bg-dark-700 rounded-lg">
                <div className="text-white font-medium">{selectedTool.name}</div>
                <div className="text-dark-300 text-sm mt-1">
                  {selectedTool.description}
                </div>
              </div>

              {/* Input Schema */}
              {selectedTool.input_schema && (
                <div>
                  <div className="label mb-2">输入参数 Schema</div>
                  <pre className="p-4 bg-dark-700 rounded-lg overflow-auto text-xs text-dark-100 max-h-40">
                    {JSON.stringify(selectedTool.input_schema, null, 2)}
                  </pre>
                </div>
              )}

              {/* Params Input */}
              <div>
                <div className="label mb-2">参数 (JSON)</div>
                <textarea
                  value={params}
                  onChange={(e) => setParams(e.target.value)}
                  className="input h-32 font-mono text-sm"
                  placeholder='{"key": "value"}'
                />
              </div>

              {/* Execute Button */}
              <button
                onClick={handleCallTool}
                disabled={callToolMutation.isPending}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                {callToolMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    执行中...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    执行工具
                  </>
                )}
              </button>

              {/* Result */}
              {callToolMutation.data && (
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    {callToolMutation.data.success ? (
                      <CheckCircle className="w-4 h-4 text-green-400" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-red-400" />
                    )}
                    <span className="label mb-0">执行结果</span>
                  </div>
                  <div className="p-4 bg-dark-700 rounded-lg space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-dark-400">耗时</span>
                      <span className="text-dark-100">
                        {callToolMutation.data.latency_ms}ms
                      </span>
                    </div>
                    {callToolMutation.data.fallback_mode && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-dark-400">降级模式</span>
                        <span className="text-yellow-400">
                          {callToolMutation.data.fallback_mode}
                        </span>
                      </div>
                    )}
                    <pre className="text-sm text-dark-100 overflow-auto">
                      {JSON.stringify(callToolMutation.data.result, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {/* Error */}
              {callToolMutation.isError && (
                <div className="p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-400">
                  {String(callToolMutation.error)}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
