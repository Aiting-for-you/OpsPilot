import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { GitBranch, Play, Loader2, CheckCircle, XCircle, ChevronRight } from 'lucide-react';
import { api } from '../services/api';

interface SOPInfo {
  name: string;
  description: string;
  steps: { name: string; action: string }[];
}

const SOP_DETAILS: Record<string, SOPInfo> = {
  create_order: {
    name: 'create_order',
    description: '创建采购订单的标准化流程',
    steps: [
      { name: '意图识别', action: '识别用户订单需求' },
      { name: '供应商查询', action: '查询可用供应商' },
      { name: '价格对比', action: '对比不同供应商报价' },
      { name: '合规审核', action: '审核订单是否符合合规要求' },
      { name: '创建订单', action: '在 ERP 系统中创建订单' },
      { name: '结果验证', action: '验证订单创建是否成功' },
    ],
  },
  query_supplier: {
    name: 'query_supplier',
    description: '查询供应商信息的标准化流程',
    steps: [
      { name: '意图识别', action: '识别查询需求' },
      { name: '数据检索', action: '从数据库检索供应商信息' },
      { name: '结果组装', action: '组装查询结果' },
      { name: '结果返回', action: '返回查询结果' },
    ],
  },
};

export function SOP() {
  const [selectedSOP, setSelectedSOP] = useState<string | null>(null);
  const [variables, setVariables] = useState<string>('{}');
  const [executedSteps, setExecutedSteps] = useState<number>(0);

  // 获取 SOP 列表
  const { data: sopsList } = useQuery({
    queryKey: ['sops'],
    queryFn: () => api.getSOPs(),
  });

  // 执行 SOP
  const executeSOPMutation = useMutation({
    mutationFn: () => {
      if (!selectedSOP) throw new Error('No SOP selected');
      let parsedVars = {};
      try {
        parsedVars = JSON.parse(variables);
      } catch {
        throw new Error('Invalid JSON variables');
      }
      return api.executeSOP(selectedSOP, parsedVars);
    },
    onSuccess: (data) => {
      setExecutedSteps(data.steps_executed);
    },
  });

  const handleExecute = () => {
    setExecutedSteps(0);
    executeSOPMutation.mutate();
  };

  const sopInfo = selectedSOP ? SOP_DETAILS[selectedSOP] : null;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* SOP List */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <GitBranch className="w-5 h-5 text-primary-400" />
            <h2 className="text-lg font-semibold text-white">SOP 列表</h2>
          </div>
          <div className="space-y-2">
            {sopsList?.sops.map((sopName) => {
              const info = SOP_DETAILS[sopName];
              return (
                <div
                  key={sopName}
                  onClick={() => {
                    setSelectedSOP(sopName);
                    setVariables('{}');
                    setExecutedSteps(0);
                  }}
                  className={`p-3 rounded-lg cursor-pointer transition-colors ${
                    selectedSOP === sopName
                      ? 'bg-primary-600 text-white'
                      : 'bg-dark-700 hover:bg-dark-600 text-dark-100'
                  }`}
                >
                  <div className="font-medium">{sopName}</div>
                  <div className="text-sm text-dark-300 mt-1">
                    {info?.description || '无描述'}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* SOP Detail & Execution */}
        <div className="lg:col-span-2 card">
          <h2 className="text-lg font-semibold text-white mb-4">SOP 执行</h2>
          {!sopInfo ? (
            <div className="text-center py-12 text-dark-400">
              选择一个 SOP 进行执行
            </div>
          ) : (
            <div className="space-y-4">
              {/* SOP Info */}
              <div className="p-4 bg-dark-700 rounded-lg">
                <div className="text-white font-medium">{sopInfo.name}</div>
                <div className="text-dark-300 text-sm mt-1">
                  {sopInfo.description}
                </div>
              </div>

              {/* Steps Visualization */}
              <div>
                <div className="label mb-3">执行步骤</div>
                <div className="relative">
                  <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-dark-600" />
                  <div className="space-y-4">
                    {sopInfo.steps.map((step, idx) => {
                      const isCompleted = idx < executedSteps;
                      const isCurrent = idx === executedSteps && executeSOPMutation.isPending;
                      return (
                        <div key={idx} className="relative flex items-start gap-4 pl-10">
                          <div
                            className={`absolute left-2 w-5 h-5 rounded-full flex items-center justify-center ${
                              isCompleted
                                ? 'bg-green-500'
                                : isCurrent
                                ? 'bg-yellow-500 animate-pulse'
                                : 'bg-dark-600'
                            }`}
                          >
                            {isCompleted ? (
                              <CheckCircle className="w-3 h-3 text-white" />
                            ) : isCurrent ? (
                              <Loader2 className="w-3 h-3 text-white animate-spin" />
                            ) : (
                              <span className="text-xs text-dark-400">{idx + 1}</span>
                            )}
                          </div>
                          <div className="flex-1">
                            <div className="text-dark-100 font-medium">{step.name}</div>
                            <div className="text-dark-400 text-sm">{step.action}</div>
                          </div>
                          <ChevronRight className="w-4 h-4 text-dark-500" />
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Variables Input */}
              <div>
                <div className="label mb-2">变量 (JSON)</div>
                <textarea
                  value={variables}
                  onChange={(e) => setVariables(e.target.value)}
                  className="input h-24 font-mono text-sm"
                  placeholder='{"product": "电子元件A", "quantity": 100}'
                />
              </div>

              {/* Execute Button */}
              <button
                onClick={handleExecute}
                disabled={executeSOPMutation.isPending}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                {executeSOPMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    执行中...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    执行 SOP
                  </>
                )}
              </button>

              {/* Result */}
              {executeSOPMutation.data && (
                <div className="p-4 bg-dark-700 rounded-lg">
                  <div className="flex items-center gap-2 mb-3">
                    {executeSOPMutation.data.success ? (
                      <CheckCircle className="w-5 h-5 text-green-400" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-400" />
                    )}
                    <span className="text-white font-medium">
                      {executeSOPMutation.data.message}
                    </span>
                  </div>
                  <div className="text-sm text-dark-300">
                    已执行 {executeSOPMutation.data.steps_executed} 步
                  </div>
                  {executeSOPMutation.data.results.length > 0 && (
                    <pre className="mt-3 p-3 bg-dark-800 rounded text-xs text-dark-100 overflow-auto">
                      {JSON.stringify(executeSOPMutation.data.results, null, 2)}
                    </pre>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
