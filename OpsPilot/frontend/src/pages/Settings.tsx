import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Settings as SettingsIcon, Save, RefreshCw, Check, X, Eye, EyeOff, Zap, Server, Key, Plus, List, Download, Cpu, Shield, Info, Globe, Link } from 'lucide-react';
import { api } from '../services/api';
import { LLMProviderConfig, LLMProviderType, LLMTestResult, ModelInfo } from '../types';
import { MCPServerSettings } from '../components/MCPServerSettings';
import { ProviderSettings } from '../components/ProviderSettings';

// Provider display info
const PROVIDER_INFO: Record<LLMProviderType, { nameKey: string; color: string }> = {
  openai: { nameKey: 'settings.providers.openai', color: '#10a37f' },
  azure_openai: { nameKey: 'settings.providers.azure', color: '#0078d4' },
  claude: { nameKey: 'settings.providers.claude', color: '#d97706' },
  qwen: { nameKey: 'settings.providers.qwen', color: '#ff6a00' },
  ernie: { nameKey: 'settings.providers.wenxin', color: '#2932e1' },
  zhipu: { nameKey: 'settings.providers.zhipu', color: '#3b82f6' },
  deepseek: { nameKey: 'settings.providers.deepseek', color: '#8b5cf6' },
  custom: { nameKey: 'settings.providers.custom', color: '#6b7280' },
};

export function Settings() {
  const { t } = useTranslation();
  const [providers, setProviders] = useState<LLMProviderConfig[]>([]);
  const [defaultProvider, setDefaultProvider] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<LLMTestResult | null>(null);
  const [expandedProvider, setExpandedProvider] = useState<string | null>(null);
  
  const [editConfig, setEditConfig] = useState<Record<string, {
    api_key: string;
    api_base: string;
    model_name: string;
    temperature: number;
    max_tokens: number;
    top_p: number;
    is_enabled: boolean;
  }>>({});
  
  const [showApiKey, setShowApiKey] = useState<Record<string, boolean>>({});
  const [showFetchModal, setShowFetchModal] = useState(false);
  const [fetchApiBase, setFetchApiBase] = useState('');
  const [fetchApiKey, setFetchApiKey] = useState('');
  const [fetchProviderType, setFetchProviderType] = useState<string>('openai');
  const [fetching, setFetching] = useState(false);
  const [fetchedModels, setFetchedModels] = useState<ModelInfo[]>([]);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [selectedModels, setSelectedModels] = useState<Set<string>>(new Set());
  const [batchAdding, setBatchAdding] = useState(false);
  const [defaultModelSelect, setDefaultModelSelect] = useState<string>('');
  
  // Tab state
  const [activeTab, setActiveTab] = useState<'llm' | 'mcp' | 'providers'>('llm');

  useEffect(() => {
    loadConfigs();
  }, []);

  const loadConfigs = async () => {
    try {
      setLoading(true);
      const data = await api.getLLMConfigs();
      setProviders(data.providers);
      setDefaultProvider(data.default_provider || null);
      
      const editState: Record<string, any> = {};
      data.providers.forEach((p) => {
        editState[p.provider] = {
          api_key: '',
          api_base: p.api_base,
          model_name: p.model_name || p.default_model,
          temperature: p.temperature,
          max_tokens: p.max_tokens,
          top_p: p.top_p,
          is_enabled: p.is_enabled,
        };
      });
      setEditConfig(editState);
    } catch (error) {
      console.error('Failed to load configs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfig = async (provider: LLMProviderType) => {
    try {
      setSaving(true);
      const config = editConfig[provider];
      
      await api.updateLLMConfig({
        provider,
        api_key: config.api_key,
        api_base: config.api_base || undefined,
        model_name: config.model_name || undefined,
        temperature: config.temperature,
        max_tokens: config.max_tokens,
        top_p: config.top_p,
        is_enabled: config.is_enabled,
        is_default: provider === defaultProvider,
      });
      
      await loadConfigs();
      setTestResult(null);
    } catch (error) {
      console.error('Failed to save config:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async (provider: LLMProviderType) => {
    try {
      setTesting(provider);
      setTestResult(null);
      
      const config = editConfig[provider];
      if (config.api_key) {
        await api.updateLLMConfig({
          provider,
          api_key: config.api_key,
          api_base: config.api_base || undefined,
          model_name: config.model_name || undefined,
          is_enabled: true,
        });
      }
      
      const result = await api.testLLMConnection(provider);
      setTestResult(result);
    } catch (error) {
      console.error('Test failed:', error);
      setTestResult({ success: false, message: t('settings.connectionFailed') });
    } finally {
      setTesting(null);
    }
  };

  const handleSetDefault = async (provider: LLMProviderType) => {
    try {
      await api.setDefaultLLM(provider);
      setDefaultProvider(provider);
    } catch (error) {
      console.error('Failed to set default:', error);
    }
  };

  const updateEditConfig = (provider: string, field: string, value: any) => {
    setEditConfig((prev) => ({
      ...prev,
      [provider]: {
        ...prev[provider],
        [field]: value,
      },
    }));
  };

  const handleFetchModels = async () => {
    if (!fetchApiBase || !fetchApiKey) {
      setFetchError(t('errors.validationError'));
      return;
    }

    try {
      setFetching(true);
      setFetchError(null);
      setFetchedModels([]);
      setSelectedModels(new Set());
      
      const result = await api.fetchModels({
        api_base: fetchApiBase,
        api_key: fetchApiKey,
        provider_type: fetchProviderType,
      });

      if (result.success && result.models.length > 0) {
        setFetchedModels(result.models);
        const defaultSelected = new Set(result.models.slice(0, 5).map(m => m.id));
        setSelectedModels(defaultSelected);
        setDefaultModelSelect(result.models[0].id);
      } else {
        setFetchError(result.error || t('common.noData'));
      }
    } catch (error) {
      console.error('Failed to fetch models:', error);
      setFetchError(t('errors.serverError'));
    } finally {
      setFetching(false);
    }
  };

  const toggleModelSelection = (modelId: string) => {
    setSelectedModels((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(modelId)) {
        newSet.delete(modelId);
      } else {
        newSet.add(modelId);
      }
      return newSet;
    });
  };

  const toggleSelectAll = () => {
    if (selectedModels.size === fetchedModels.length) {
      setSelectedModels(new Set());
    } else {
      setSelectedModels(new Set(fetchedModels.map(m => m.id)));
    }
  };

  const handleBatchAddModels = async () => {
    if (selectedModels.size === 0) {
      return;
    }

    try {
      setBatchAdding(true);
      
      const result = await api.batchAddModels({
        provider: 'custom' as LLMProviderType,
        api_key: fetchApiKey,
        api_base: fetchApiBase,
        models: Array.from(selectedModels),
        set_default: defaultModelSelect || undefined,
      });

      if (result.success) {
        setShowFetchModal(false);
        setFetchedModels([]);
        setSelectedModels(new Set());
        await loadConfigs();
        setExpandedProvider('custom');
      }
    } catch (error) {
      console.error('Batch add failed:', error);
    } finally {
      setBatchAdding(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-electric border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      {/* Header with Tabs */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-electric/10 flex items-center justify-center">
            <Cpu className="w-4 h-4 text-electric" />
          </div>
          <div>
            <h1 className="font-display text-sm font-semibold text-text-primary uppercase tracking-wide">
              {t('settings.title') || 'Settings'}
            </h1>
            <p className="text-xs text-steel-500">
              {activeTab === 'llm' ? t('settings.provider') : 'External MCP Servers'}
            </p>
          </div>
        </div>
        
        {/* Tab Buttons */}
        <div className="flex items-center gap-1 p-1 bg-navy-1000/50 rounded-lg border border-steel-800/50">
          <button
            onClick={() => setActiveTab('llm')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded text-xs font-medium transition-all ${
              activeTab === 'llm'
                ? 'bg-electric text-navy-950'
                : 'text-steel-400 hover:text-text-primary'
            }`}
          >
            <Zap className="w-3.5 h-3.5" />
            LLM
          </button>
          <button
            onClick={() => setActiveTab('mcp')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded text-xs font-medium transition-all ${
              activeTab === 'mcp'
                ? 'bg-electric text-navy-950'
                : 'text-steel-400 hover:text-text-primary'
            }`}
          >
            <Link className="w-3.5 h-3.5" />
            MCP
          </button>
          <button
            onClick={() => setActiveTab('providers')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded text-xs font-medium transition-all ${
              activeTab === 'providers'
                ? 'bg-electric text-navy-950'
                : 'text-steel-400 hover:text-text-primary'
            }`}
          >
            <Shield className="w-3.5 h-3.5" />
            Providers
          </button>
        </div>
      </div>

      {/* Providers Tab Content */}
      {activeTab === 'providers' && (
        <ProviderSettings />
      )}

      {/* LLM Tab Content */}
      {activeTab === 'llm' && (
        <>
          {/* Action Buttons */}
          <div className="flex justify-end gap-2">
            <button
              onClick={() => {
                setFetchApiBase('');
                setFetchApiKey('');
                setFetchedModels([]);
                setSelectedModels(new Set());
                setFetchError(null);
                setShowFetchModal(true);
              }}
              className="btn-secondary"
            >
              <Download className="w-4 h-4" />
              {t('settings.fetchModels')}
            </button>
            <button onClick={loadConfigs} className="btn-secondary">
              <RefreshCw className="w-4 h-4" />
              {t('common.refresh') || 'Refresh'}
            </button>
          </div>

      {/* Info Banner */}
      <div className="p-4 rounded-lg bg-navy-1000/50 border border-steel-800/50">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-electric flex-shrink-0 mt-0.5" />
          <p className="text-sm text-steel-400">
            {t('settings.llmConfig')} - {t('settings.apiKey')} & {t('settings.model')}
          </p>
        </div>
      </div>

      {/* Provider Cards */}
      {providers.map((provider) => {
        const info = PROVIDER_INFO[provider.provider] || PROVIDER_INFO.custom;
        const isExpanded = expandedProvider === provider.provider;
        const config = editConfig[provider.provider] || {};
        const isTesting = testing === provider.provider;

        return (
          <div key={provider.provider} className="card">
            {/* Provider Header */}
            <div
              className="flex items-center justify-between cursor-pointer"
              onClick={() => setExpandedProvider(isExpanded ? null : provider.provider)}
            >
              <div className="flex items-center gap-4">
                <div 
                  className="w-10 h-10 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: `${info.color}20` }}
                >
                  <Zap className="w-5 h-5" style={{ color: info.color }} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-display text-sm font-semibold text-text-primary">
                      {t(info.nameKey)}
                    </span>
                    {provider.is_default && (
                      <span className="px-2 py-0.5 bg-electric/20 text-electric text-xs rounded font-mono">
                        DEFAULT
                      </span>
                    )}
                    {provider.is_enabled && provider.api_key_masked && (
                      <span className="px-2 py-0.5 bg-success/20 text-success text-xs rounded font-mono">
                        {t('settings.enabled').toUpperCase()}
                      </span>
                    )}
                    <span className="text-xs text-steel-600">
                      {provider.available_models.length} models
                    </span>
                  </div>
                  <p className="text-xs text-steel-500 mt-0.5">
                    {provider.api_key_masked || t('common.noData')}
                  </p>
                </div>
              </div>
              <span className="text-steel-500 text-xs font-mono">
                {isExpanded ? 'CLOSE' : 'EXPAND'}
              </span>
            </div>

            {/* Expanded Content */}
            {isExpanded && (
              <div className="mt-5 pt-5 border-t border-steel-800/50 space-y-4">
                {/* API Key */}
                <div>
                  <label className="label">
                    <Key className="w-3 h-3 inline mr-1" />
                    {t('settings.apiKey')}
                  </label>
                  <div className="relative">
                    <input
                      type={showApiKey[provider.provider] ? 'text' : 'password'}
                      value={config.api_key || ''}
                      onChange={(e) => updateEditConfig(provider.provider, 'api_key', e.target.value)}
                      placeholder={provider.api_key_masked || t('settings.apiKey')}
                      className="input pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowApiKey((prev) => ({ ...prev, [provider.provider]: !prev[provider.provider] }))}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-steel-500 hover:text-electric transition-colors"
                    >
                      {showApiKey[provider.provider] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* API Base URL */}
                <div>
                  <label className="label">
                    <Server className="w-3 h-3 inline mr-1" />
                    {t('settings.apiBase')}
                    {provider.provider === 'custom' && <span className="text-error ml-1">*</span>}
                  </label>
                  <input
                    type="text"
                    value={config.api_base || ''}
                    onChange={(e) => updateEditConfig(provider.provider, 'api_base', e.target.value)}
                    placeholder={provider.api_base || t('settings.apiBase')}
                    className="input"
                  />
                </div>

                {/* Model Selection */}
                <div>
                  <label className="label">
                    <Zap className="w-3 h-3 inline mr-1" />
                    {t('settings.model')}
                  </label>
                  <select
                    value={config.model_name || provider.default_model}
                    onChange={(e) => updateEditConfig(provider.provider, 'model_name', e.target.value)}
                    className="input"
                  >
                    {provider.available_models.length > 0 ? (
                      provider.available_models.map((model) => (
                        <option key={model} value={model}>{model}</option>
                      ))
                    ) : (
                      <option value={config.model_name || ''}>{config.model_name || t('settings.model')}</option>
                    )}
                  </select>
                </div>

                {/* Parameters */}
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="label">{t('settings.temperature')}</label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="2"
                      value={config.temperature ?? 0.7}
                      onChange={(e) => updateEditConfig(provider.provider, 'temperature', parseFloat(e.target.value))}
                      className="input"
                    />
                  </div>
                  <div>
                    <label className="label">{t('settings.maxTokens')}</label>
                    <input
                      type="number"
                      min="1"
                      value={config.max_tokens ?? 4096}
                      onChange={(e) => updateEditConfig(provider.provider, 'max_tokens', parseInt(e.target.value))}
                      className="input"
                    />
                  </div>
                  <div>
                    <label className="label">{t('settings.topP')}</label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="1"
                      value={config.top_p ?? 1}
                      onChange={(e) => updateEditConfig(provider.provider, 'top_p', parseFloat(e.target.value))}
                      className="input"
                    />
                  </div>
                </div>

                {/* Enable Toggle */}
                <div className="flex items-center justify-between p-3 rounded-lg bg-navy-1000/50 border border-steel-800/50">
                  <span className="text-sm text-steel-400">{t('settings.enabled')}</span>
                  <button
                    onClick={() => updateEditConfig(provider.provider, 'is_enabled', !config.is_enabled)}
                    className={`w-11 h-6 rounded-full transition-colors relative ${
                      config.is_enabled ? 'bg-electric' : 'bg-steel-700'
                    }`}
                  >
                    <div
                      className={`w-5 h-5 rounded-full bg-text-primary absolute top-0.5 transition-transform ${
                        config.is_enabled ? 'translate-x-5' : 'translate-x-0.5'
                      }`}
                    />
                  </button>
                </div>

                {/* Test Result */}
                {testResult && (
                  <div className={`p-3 rounded-lg flex items-center gap-2 ${
                    testResult.success ? 'bg-success/10 text-success' : 'bg-error/10 text-error'
                  }`}>
                    {testResult.success ? <Check className="w-4 h-4" /> : <X className="w-4 h-4" />}
                    <span className="text-sm">{testResult.success ? t('settings.connectionSuccess') : t('settings.connectionFailed')}</span>
                    {testResult.latency_ms && (
                      <span className="text-xs opacity-70 ml-auto font-mono">{testResult.latency_ms}ms</span>
                    )}
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center justify-between pt-2">
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleTestConnection(provider.provider)}
                      disabled={isTesting || saving}
                      className="btn-secondary"
                    >
                      {isTesting ? (
                        <RefreshCw className="w-4 h-4 animate-spin" />
                      ) : (
                        <Zap className="w-4 h-4" />
                      )}
                      {t('settings.testConnection')}
                    </button>
                    {!provider.is_default && config.is_enabled && (
                      <button
                        onClick={() => handleSetDefault(provider.provider)}
                        className="btn-secondary"
                      >
                        <Shield className="w-4 h-4" />
                        {t('settings.setDefault')}
                      </button>
                    )}
                  </div>
                  <button
                    onClick={() => handleSaveConfig(provider.provider)}
                    disabled={saving}
                    className="btn-primary"
                  >
                    {saving ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Save className="w-4 h-4" />
                    )}
                    {t('common.save')}
                  </button>
                </div>
              </div>
            )}
          </div>
        );
      })}

      {/* Fetch Models Modal */}
      {showFetchModal && (
        <div className="fixed inset-0 bg-navy-1000/80 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-navy-950 border border-steel-800 rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-electric/10 flex items-center justify-center">
                  <List className="w-4 h-4 text-electric" />
                </div>
                <h2 className="font-display text-sm font-semibold text-text-primary uppercase tracking-wide">
                  {t('settings.fetchModels')}
                </h2>
              </div>
              <button
                onClick={() => setShowFetchModal(false)}
                className="p-1 rounded text-steel-500 hover:text-electric transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Input Fields */}
            <div className="space-y-4 mb-5">
              <div>
                <label className="label">API Type</label>
                <select
                  value={fetchProviderType}
                  onChange={(e) => setFetchProviderType(e.target.value)}
                  className="input"
                >
                  <option value="openai">OpenAI Compatible</option>
                  <option value="deepseek">DeepSeek</option>
                  <option value="qwen">Tongyi Qwen</option>
                </select>
              </div>
              <div>
                <label className="label">{t('settings.apiBase')}</label>
                <input
                  type="text"
                  value={fetchApiBase}
                  onChange={(e) => setFetchApiBase(e.target.value)}
                  placeholder="https://api.openai.com/v1"
                  className="input"
                />
              </div>
              <div>
                <label className="label">{t('settings.apiKey')}</label>
                <input
                  type="password"
                  value={fetchApiKey}
                  onChange={(e) => setFetchApiKey(e.target.value)}
                  placeholder="sk-xxxxx"
                  className="input"
                />
              </div>
              <button
                onClick={handleFetchModels}
                disabled={fetching}
                className="btn-primary w-full"
              >
                {fetching ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Download className="w-4 h-4" />
                )}
                {t('settings.fetchModels')}
              </button>
            </div>

            {/* Error */}
            {fetchError && (
              <div className="p-3 rounded-lg bg-error/10 text-error text-sm mb-4">
                {fetchError}
              </div>
            )}

            {/* Model List */}
            {fetchedModels.length > 0 && (
              <div className="flex-1 overflow-hidden flex flex-col">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs text-steel-500">
                    {fetchedModels.length} models, {selectedModels.size} selected
                  </span>
                  <button
                    onClick={toggleSelectAll}
                    className="text-xs text-electric hover:underline"
                  >
                    {selectedModels.size === fetchedModels.length ? 'Deselect All' : 'Select All'}
                  </button>
                </div>

                {/* Default Model */}
                <div className="mb-3">
                  <label className="label">{t('settings.model')} (Default)</label>
                  <select
                    value={defaultModelSelect}
                    onChange={(e) => setDefaultModelSelect(e.target.value)}
                    className="input"
                  >
                    <option value="">No default</option>
                    {Array.from(selectedModels).map((modelId) => (
                      <option key={modelId} value={modelId}>{modelId}</option>
                    ))}
                  </select>
                </div>

                {/* Model Grid */}
                <div className="flex-1 overflow-y-auto border border-steel-800/50 rounded-lg p-3 scrollbar-custom">
                  <div className="grid grid-cols-2 gap-2">
                    {fetchedModels.map((model) => (
                      <div
                        key={model.id}
                        onClick={() => toggleModelSelection(model.id)}
                        className={`p-2 rounded-lg cursor-pointer border transition-all ${
                          selectedModels.has(model.id)
                            ? 'border-electric bg-electric/5'
                            : 'border-steel-800/50 hover:border-steel-700'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <div className={`w-4 h-4 rounded border flex items-center justify-center ${
                            selectedModels.has(model.id)
                              ? 'border-electric bg-electric'
                              : 'border-steel-600'
                          }`}>
                            {selectedModels.has(model.id) && <Check className="w-3 h-3 text-navy-950" />}
                          </div>
                          <span className="text-xs text-text-secondary truncate font-mono">{model.id}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Batch Add */}
                <div className="mt-4">
                  <button
                    onClick={handleBatchAddModels}
                    disabled={batchAdding || selectedModels.size === 0}
                    className="btn-primary w-full"
                  >
                    {batchAdding ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Plus className="w-4 h-4" />
                    )}
                    {t('settings.batchAdd')} ({selectedModels.size})
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
        </>
      )}

      {/* MCP Tab Content */}
      {activeTab === 'mcp' && <MCPServerSettings />}

      {/* Language Settings - Only show on LLM tab */}
      {activeTab === 'llm' && (
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-lg bg-electric/10 flex items-center justify-center">
            <Globe className="w-4 h-4 text-electric" />
          </div>
          <div>
            <h2 className="font-display text-sm font-semibold text-text-primary uppercase tracking-wide">
              {t('settings.languageSettings')}
            </h2>
            <p className="text-xs text-steel-500">{t('settings.selectLanguage')}</p>
          </div>
        </div>
        
        <div className="p-4 rounded-lg bg-navy-1000/50 border border-steel-800/50">
          <p className="text-sm text-steel-400 mb-3">
            {t('settings.selectLanguage')}
          </p>
          <div className="flex items-center gap-2 text-sm text-steel-500">
            <span>🌐</span>
            <span>{t('settings.language')}: </span>
            <span className="text-electric">
              {t('settings.selectLanguage') === '选择语言' ? '简体中文' : 'English'}
            </span>
          </div>
          <p className="text-xs text-steel-600 mt-2">
            {t('settings.languageSettings')} - {t('settings.selectLanguage')}
          </p>
        </div>
      </div>
      )}

      {/* About Section - Only show on LLM tab */}
      {activeTab === 'llm' && (
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-lg bg-steel-800/50 flex items-center justify-center">
            <Info className="w-4 h-4 text-steel-500" />
          </div>
          <h2 className="font-display text-sm font-semibold text-text-primary uppercase tracking-wide">
            About
          </h2>
        </div>
        <div className="grid grid-cols-3 gap-4">
          <div className="p-3 rounded-lg bg-navy-1000/50 border border-steel-800/50">
            <div className="text-xs text-steel-500 mb-1">{t('common.version')}</div>
            <div className="font-mono text-sm text-electric">v0.1.0</div>
          </div>
          <div className="p-3 rounded-lg bg-navy-1000/50 border border-steel-800/50">
            <div className="text-xs text-steel-500 mb-1">Build Date</div>
            <div className="font-mono text-sm text-text-secondary">2026-02-16</div>
          </div>
          <div className="p-3 rounded-lg bg-navy-1000/50 border border-steel-800/50">
            <div className="text-xs text-steel-500 mb-1">Tech Stack</div>
            <div className="font-mono text-xs text-text-secondary">React + TypeScript</div>
          </div>
        </div>
      </div>
      )}
    </div>
  );
}
