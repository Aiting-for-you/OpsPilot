import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery, useMutation } from '@tanstack/react-query';
import { GitBranch, Play, Loader2, CheckCircle, XCircle, ChevronRight, Zap, Terminal, CheckSquare } from 'lucide-react';
import { api } from '../services/api';

interface SOPInfo {
  name: string;
  description: string;
  steps: { name: string; action: string }[];
}

const SOP_DETAILS: Record<string, SOPInfo> = {
  create_order: {
    name: 'create_order',
    description: 'Standard workflow for creating purchase orders',
    steps: [
      { name: 'Intent Recognition', action: 'Identify user order requirements' },
      { name: 'Supplier Query', action: 'Query available suppliers' },
      { name: 'Price Comparison', action: 'Compare quotes from different suppliers' },
      { name: 'Compliance Check', action: 'Review order compliance requirements' },
      { name: 'Create Order', action: 'Create order in ERP system' },
      { name: 'Verification', action: 'Verify order creation success' },
    ],
  },
  query_supplier: {
    name: 'query_supplier',
    description: 'Standard workflow for querying supplier information',
    steps: [
      { name: 'Intent Recognition', action: 'Identify query requirements' },
      { name: 'Data Retrieval', action: 'Retrieve supplier info from database' },
      { name: 'Result Assembly', action: 'Assemble query results' },
      { name: 'Response', action: 'Return query results' },
    ],
  },
};

export function SOP() {
  const { t } = useTranslation();
  const [selectedSOP, setSelectedSOP] = useState<string | null>(null);
  const [variables, setVariables] = useState<string>('{}');
  const [executedSteps, setExecutedSteps] = useState<number>(0);

  // Fetch SOP list
  const { data: sopsList } = useQuery({
    queryKey: ['sops'],
    queryFn: () => api.getSOPs(),
  });

  // Execute SOP mutation
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
    <div className="space-y-6 animate-fade-in">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* SOP List */}
        <div className="lg:col-span-4 card">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-8 h-8 rounded-lg bg-electric/10 flex items-center justify-center">
              <GitBranch className="w-4 h-4 text-electric" />
            </div>
            <div>
              <h2 className="font-display text-sm font-semibold text-text-primary uppercase tracking-wide">
                {t('sop.sopLibrary')}
              </h2>
              <p className="text-xs text-steel-500">{t('sop.availableSOPs')}</p>
            </div>
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
                  className={`
                    p-3 rounded-lg cursor-pointer border transition-all
                    ${selectedSOP === sopName
                      ? 'bg-electric/5 border-electric/30'
                      : 'bg-navy-1000/50 border-steel-800/50 hover:border-steel-700'
                    }
                  `}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <div className={`w-1.5 h-1.5 rounded-full ${
                      selectedSOP === sopName ? 'bg-electric' : 'bg-steel-600'
                    }`} />
                    <span className="font-display text-sm font-medium text-text-primary">
                      {sopName}
                    </span>
                  </div>
                  <p className="text-xs text-steel-500 ml-3.5">
                    {info?.description || t('sop.description')}
                  </p>
                </div>
              );
            })}
          </div>
        </div>

        {/* SOP Execution */}
        <div className="lg:col-span-8 card">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-8 h-8 rounded-lg bg-success/10 flex items-center justify-center">
              <Terminal className="w-4 h-4 text-success" />
            </div>
            <h2 className="font-display text-sm font-semibold text-text-primary uppercase tracking-wide">
              {t('sop.executeSOP')}
            </h2>
          </div>

          {!sopInfo ? (
            <div className="flex flex-col items-center justify-center py-16 text-steel-500">
              <GitBranch className="w-12 h-12 mb-3 opacity-20" />
              <p className="text-sm">{t('sop.noSOPSelected')}</p>
            </div>
          ) : (
            <div className="space-y-5">
              {/* SOP Info */}
              <div className="p-4 rounded-lg bg-navy-1000/50 border border-electric/20">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 rounded-full bg-electric" />
                  <span className="font-display text-sm font-semibold text-electric">
                    {sopInfo.name}
                  </span>
                </div>
                <p className="text-sm text-steel-400 ml-4">
                  {sopInfo.description}
                </p>
              </div>

              {/* Steps Visualization */}
              <div>
                <div className="label mb-4">{t('sop.steps')}</div>
                <div className="relative">
                  {/* Vertical Line */}
                  <div className="absolute left-3.5 top-2 bottom-2 w-px bg-steel-800" />
                  
                  <div className="space-y-3">
                    {sopInfo.steps.map((step, idx) => {
                      const isCompleted = idx < executedSteps;
                      const isCurrent = idx === executedSteps && executeSOPMutation.isPending;
                      
                      return (
                        <div key={idx} className="relative flex items-start gap-4 pl-10">
                          {/* Step Indicator */}
                          <div
                            className={`
                              absolute left-1.5 w-5 h-5 rounded-full flex items-center justify-center
                              border-2 transition-all
                              ${isCompleted
                                ? 'bg-success border-success'
                                : isCurrent
                                ? 'bg-warning border-warning animate-pulse'
                                : 'bg-navy-1000 border-steel-700'
                              }
                            `}
                          >
                            {isCompleted ? (
                              <CheckCircle className="w-3 h-3 text-navy-950" />
                            ) : isCurrent ? (
                              <Loader2 className="w-3 h-3 text-navy-950 animate-spin" />
                            ) : (
                              <span className="text-xs text-steel-500 font-mono">{idx + 1}</span>
                            )}
                          </div>
                          
                          {/* Step Content */}
                          <div className="flex-1 p-3 rounded-lg bg-navy-1000/50 border border-steel-800/50">
                            <div className="font-display text-sm font-medium text-text-primary">
                              {step.name}
                            </div>
                            <div className="text-xs text-steel-500 mt-1">{step.action}</div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Variables Input */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="w-4 h-4 text-steel-500" />
                  <span className="label mb-0">{t('tools.parameters')} (JSON)</span>
                </div>
                <textarea
                  value={variables}
                  onChange={(e) => setVariables(e.target.value)}
                  className="input h-24 font-mono text-sm resize-none"
                  placeholder='{"product": "Electronics A", "quantity": 100}'
                />
              </div>

              {/* Execute Button */}
              <button
                onClick={handleExecute}
                disabled={executeSOPMutation.isPending}
                className="btn-primary w-full"
              >
                {executeSOPMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    {t('common.loading')}
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    {t('sop.startExecution')}
                  </>
                )}
              </button>

              {/* Result */}
              {executeSOPMutation.data && (
                <div className="p-4 rounded-lg bg-navy-1000/50 border border-steel-800/50">
                  <div className="flex items-center gap-2 mb-3">
                    {executeSOPMutation.data.success ? (
                      <CheckCircle className="w-4 h-4 text-success" />
                    ) : (
                      <XCircle className="w-4 h-4 text-error" />
                    )}
                    <span className="text-sm font-medium text-text-primary">
                      {executeSOPMutation.data.message}
                    </span>
                  </div>
                  <div className="text-xs text-steel-500 mb-3">
                    {t('sop.steps')} {executeSOPMutation.data.steps_executed}
                  </div>
                  {executeSOPMutation.data.results.length > 0 && (
                    <pre className="code-block text-xs max-h-40">
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
