import { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Save, RefreshCw, Check, X, Eye, EyeOff, Zap, Server, Key, Plus, List, Download } from 'lucide-react';
import { api } from '../services/api';
import { LLMProviderConfig, LLMProviderType, LLMTestResult, ModelInfo } from '../types';

// 提供商显示信息
const PROVIDER_INFO: Record<LLMProviderType, { name: string; icon: string; color: string }> = {
  openai: { name: 'OpenAI', icon: '🤖', color: '#10a37f' },
  azure_openai: { name: 'Azure OpenAI', icon: '☁️', color: '#0078d4' },
  claude: { name: 'Anthropic Claude', icon: '🧠', color: '#d97706' },
  qwen: { name: '通义千问', icon: '🔮', color: '#ff6a00' },
  ernie: { name: '文心一言', icon: '📝', color: '#2932e1' },
  zhipu: { name: '智谱AI', icon: '🎯', color: '#3b82f6' },
  deepseek: { name: 'DeepSeek', icon: '🚀', color: '#8b5cf6' },
  custom: { name: '自定义模型', icon: '⚙️', color: '#6b7280' },
};

export function Settings() {
  const [providers, setProviders] = useState<LLMProviderConfig[]>([]);
  const [defaultProvider, setDefaultProvider] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<LLMTestResult | null>(null);
  const [expandedProvider, setExpandedProvider] = useState<string | null>(null);
  
  // 编辑状态
  const [editConfig, setEditConfig] = useState<Record<string, {
    api_key: string;
    api_base: string;
    model_name: string;
    temperature: number;
    max_tokens: number;
    top_p: number;
    is_enabled: boolean;
  }>>({});
  
  // 显示密码状态
  const [showApiKey, setShowApiKey] = useState<Record<string, boolean>>({});
  
  // 模型获取相关状态
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

  // 加载配置
  useEffect(() => {
    loadConfigs();
  }, []);

  const loadConfigs = async () => {
    try {
      setLoading(true);
      const data = await api.getLLMConfigs();
      setProviders(data.providers);
      setDefaultProvider(data.default_provider || null);
      
      // 初始化编辑状态
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
      console.error('加载配置失败:', error);
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
      console.error('保存配置失败:', error);
      alert('保存配置失败');
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
      console.error('测试连接失败:', error);
      setTestResult({ success: false, message: '测试连接失败' });
    } finally {
      setTesting(null);
    }
  };

  const handleSetDefault = async (provider: LLMProviderType) => {
    try {
      await api.setDefaultLLM(provider);
      setDefaultProvider(provider);
    } catch (error) {
      console.error('设置默认失败:', error);
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

  // 获取模型列表
  const handleFetchModels = async () => {
    if (!fetchApiBase || !fetchApiKey) {
      setFetchError('请填写 API Base URL 和 API Key');
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
        // 默认选中前 5 个模型
        const defaultSelected = new Set(result.models.slice(0, 5).map(m => m.id));
        setSelectedModels(defaultSelected);
        setDefaultModelSelect(result.models[0].id);
      } else {
        setFetchError(result.error || '未获取到模型列表');
      }
    } catch (error) {
      console.error('获取模型列表失败:', error);
      setFetchError('获取模型列表失败');
    } finally {
      setFetching(false);
    }
  };

  // 切换模型选择
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

  // 全选/取消全选
  const toggleSelectAll = () => {
    if (selectedModels.size === fetchedModels.length) {
      setSelectedModels(new Set());
    } else {
      setSelectedModels(new Set(fetchedModels.map(m => m.id)));
    }
  };

  // 批量添加模型
  const handleBatchAddModels = async () => {
    if (selectedModels.size === 0) {
      alert('请至少选择一个模型');
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
        alert(`成功添加 ${result.added_count} 个模型`);
        setShowFetchModal(false);
        setFetchedModels([]);
        setSelectedModels(new Set());
        await loadConfigs();
        // 展开自定义模型配置
        setExpandedProvider('custom');
      } else {
        alert(result.error || '添加失败');
      }
    } catch (error) {
      console.error('批量添加失败:', error);
      alert('批量添加失败');
    } finally {
      setBatchAdding(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-primary-400" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <SettingsIcon className="w-5 h-5 text-primary-400" />
          <h1 className="text-lg font-semibold text-white">大模型配置</h1>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => {
              setFetchApiBase('');
              setFetchApiKey('');
              setFetchedModels([]);
              setSelectedModels(new Set());
              setFetchError(null);
              setShowFetchModal(true);
            }}
            className="btn-secondary flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            获取模型列表
          </button>
          <button
            onClick={loadConfigs}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            刷新
          </button>
        </div>
      </div>

      {/* 说明 */}
      <div className="card bg-dark-800/50 border-dark-700">
        <p className="text-dark-300 text-sm">
          配置您的大模型 API 密钥，支持 OpenAI、Claude、通义千问、文心一言等主流模型。
          使用"获取模型列表"功能可自动从 API 端点获取可用模型并批量添加。
        </p>
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
              <div className="flex items-center gap-3">
                <span className="text-2xl">{info.icon}</span>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-white font-medium">{info.name}</h3>
                    {provider.is_default && (
                      <span className="px-2 py-0.5 bg-primary-600 text-white text-xs rounded">
                        默认
                      </span>
                    )}
                    {provider.is_enabled && provider.api_key_masked && (
                      <span className="px-2 py-0.5 bg-green-600/20 text-green-400 text-xs rounded">
                        已配置
                      </span>
                    )}
                    <span className="text-dark-500 text-xs">
                      {provider.available_models.length} 个模型
                    </span>
                  </div>
                  <p className="text-dark-400 text-sm">
                    {provider.api_key_masked || '未配置 API Key'}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {!provider.is_enabled && (
                  <span className="text-dark-500 text-sm">未启用</span>
                )}
                <span className="text-dark-500">{isExpanded ? '▼' : '▶'}</span>
              </div>
            </div>

            {/* Expanded Content */}
            {isExpanded && (
              <div className="mt-4 pt-4 border-t border-dark-700 space-y-4">
                {/* API Key */}
                <div>
                  <label className="block text-dark-300 text-sm mb-1">
                    <Key className="w-4 h-4 inline mr-1" />
                    API Key
                  </label>
                  <div className="relative">
                    <input
                      type={showApiKey[provider.provider] ? 'text' : 'password'}
                      value={config.api_key || ''}
                      onChange={(e) => updateEditConfig(provider.provider, 'api_key', e.target.value)}
                      placeholder={provider.api_key_masked || '输入 API Key'}
                      className="input w-full pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowApiKey((prev) => ({ ...prev, [provider.provider]: !prev[provider.provider] }))}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-dark-400 hover:text-white"
                    >
                      {showApiKey[provider.provider] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* API Base URL */}
                <div>
                  <label className="block text-dark-300 text-sm mb-1">
                    <Server className="w-4 h-4 inline mr-1" />
                    API Base URL {provider.provider === 'custom' && <span className="text-red-400">*</span>}
                  </label>
                  <input
                    type="text"
                    value={config.api_base || ''}
                    onChange={(e) => updateEditConfig(provider.provider, 'api_base', e.target.value)}
                    placeholder={provider.api_base || '自定义 API 端点'}
                    className="input w-full"
                  />
                  <p className="text-dark-500 text-xs mt-1">
                    {provider.provider === 'custom' 
                      ? '自定义模型需要填写完整的 API 端点地址'
                      : '留空使用默认地址，可填写代理地址'}
                  </p>
                </div>

                {/* Model Selection */}
                <div>
                  <label className="block text-dark-300 text-sm mb-1">
                    <Zap className="w-4 h-4 inline mr-1" />
                    模型
                  </label>
                  <select
                    value={config.model_name || provider.default_model}
                    onChange={(e) => updateEditConfig(provider.provider, 'model_name', e.target.value)}
                    className="input w-full"
                  >
                    {provider.available_models.length > 0 ? (
                      provider.available_models.map((model) => (
                        <option key={model} value={model}>
                          {model}
                        </option>
                      ))
                    ) : (
                      <option value={config.model_name || ''}>
                        {config.model_name || '请输入模型名称'}
                      </option>
                    )}
                  </select>
                  {provider.provider === 'custom' && (
                    <input
                      type="text"
                      value={config.model_name || ''}
                      onChange={(e) => updateEditConfig(provider.provider, 'model_name', e.target.value)}
                      placeholder="输入模型名称"
                      className="input w-full mt-2"
                    />
                  )}
                </div>

                {/* Parameters */}
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-dark-300 text-sm mb-1">Temperature</label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="2"
                      value={config.temperature ?? 0.7}
                      onChange={(e) => updateEditConfig(provider.provider, 'temperature', parseFloat(e.target.value))}
                      className="input w-full"
                    />
                  </div>
                  <div>
                    <label className="block text-dark-300 text-sm mb-1">Max Tokens</label>
                    <input
                      type="number"
                      min="1"
                      value={config.max_tokens ?? 4096}
                      onChange={(e) => updateEditConfig(provider.provider, 'max_tokens', parseInt(e.target.value))}
                      className="input w-full"
                    />
                  </div>
                  <div>
                    <label className="block text-dark-300 text-sm mb-1">Top P</label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="1"
                      value={config.top_p ?? 1}
                      onChange={(e) => updateEditConfig(provider.provider, 'top_p', parseFloat(e.target.value))}
                      className="input w-full"
                    />
                  </div>
                </div>

                {/* Enable Toggle */}
                <div className="flex items-center justify-between">
                  <label className="text-dark-300">启用此提供商</label>
                  <button
                    onClick={() => updateEditConfig(provider.provider, 'is_enabled', !config.is_enabled)}
                    className={`w-12 h-6 rounded-full transition-colors ${
                      config.is_enabled ? 'bg-primary-600' : 'bg-dark-600'
                    }`}
                  >
                    <div
                      className={`w-5 h-5 rounded-full bg-white transition-transform ${
                        config.is_enabled ? 'translate-x-6' : 'translate-x-0.5'
                      }`}
                    />
                  </button>
                </div>

                {/* Test Result */}
                {testResult && (
                  <div
                    className={`p-3 rounded flex items-center gap-2 ${
                      testResult.success
                        ? 'bg-green-900/20 text-green-400'
                        : 'bg-red-900/20 text-red-400'
                    }`}
                  >
                    {testResult.success ? <Check className="w-4 h-4" /> : <X className="w-4 h-4" />}
                    <span>{testResult.message}</span>
                    {testResult.latency_ms && (
                      <span className="text-dark-400 text-sm">({testResult.latency_ms}ms)</span>
                    )}
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center justify-between pt-2">
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleTestConnection(provider.provider)}
                      disabled={isTesting || saving}
                      className="btn-secondary flex items-center gap-2"
                    >
                      {isTesting ? (
                        <RefreshCw className="w-4 h-4 animate-spin" />
                      ) : (
                        <Zap className="w-4 h-4" />
                      )}
                      测试连接
                    </button>
                    {!provider.is_default && config.is_enabled && (
                      <button
                        onClick={() => handleSetDefault(provider.provider)}
                        className="btn-secondary"
                      >
                        设为默认
                      </button>
                    )}
                  </div>
                  <button
                    onClick={() => handleSaveConfig(provider.provider)}
                    disabled={saving}
                    className="btn-primary flex items-center gap-2"
                  >
                    {saving ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Save className="w-4 h-4" />
                    )}
                    保存配置
                  </button>
                </div>
              </div>
            )}
          </div>
        );
      })}

      {/* Fetch Models Modal */}
      {showFetchModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-dark-800 rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <List className="w-5 h-5" />
                获取模型列表
              </h2>
              <button
                onClick={() => setShowFetchModal(false)}
                className="text-dark-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Input Fields */}
            <div className="space-y-4 mb-4">
              <div>
                <label className="block text-dark-300 text-sm mb-1">API 类型</label>
                <select
                  value={fetchProviderType}
                  onChange={(e) => setFetchProviderType(e.target.value)}
                  className="input w-full"
                >
                  <option value="openai">OpenAI 兼容格式</option>
                  <option value="deepseek">DeepSeek</option>
                  <option value="qwen">通义千问</option>
                </select>
              </div>
              <div>
                <label className="block text-dark-300 text-sm mb-1">API Base URL</label>
                <input
                  type="text"
                  value={fetchApiBase}
                  onChange={(e) => setFetchApiBase(e.target.value)}
                  placeholder="https://api.openai.com/v1"
                  className="input w-full"
                />
              </div>
              <div>
                <label className="block text-dark-300 text-sm mb-1">API Key</label>
                <input
                  type="password"
                  value={fetchApiKey}
                  onChange={(e) => setFetchApiKey(e.target.value)}
                  placeholder="sk-xxxxx"
                  className="input w-full"
                />
              </div>
              <button
                onClick={handleFetchModels}
                disabled={fetching}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                {fetching ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Download className="w-4 h-4" />
                )}
                获取模型列表
              </button>
            </div>

            {/* Error */}
            {fetchError && (
              <div className="p-3 rounded bg-red-900/20 text-red-400 mb-4">
                {fetchError}
              </div>
            )}

            {/* Model List */}
            {fetchedModels.length > 0 && (
              <div className="flex-1 overflow-hidden flex flex-col">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-dark-300 text-sm">
                    找到 {fetchedModels.length} 个模型，已选择 {selectedModels.size} 个
                  </span>
                  <button
                    onClick={toggleSelectAll}
                    className="text-primary-400 text-sm hover:underline"
                  >
                    {selectedModels.size === fetchedModels.length ? '取消全选' : '全选'}
                  </button>
                </div>

                {/* Default Model Selection */}
                <div className="mb-2">
                  <label className="block text-dark-300 text-sm mb-1">默认模型</label>
                  <select
                    value={defaultModelSelect}
                    onChange={(e) => setDefaultModelSelect(e.target.value)}
                    className="input w-full"
                  >
                    <option value="">不设置默认</option>
                    {Array.from(selectedModels).map((modelId) => (
                      <option key={modelId} value={modelId}>
                        {modelId}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Model Grid */}
                <div className="flex-1 overflow-y-auto border border-dark-700 rounded p-2">
                  <div className="grid grid-cols-2 gap-2">
                    {fetchedModels.map((model) => (
                      <div
                        key={model.id}
                        onClick={() => toggleModelSelection(model.id)}
                        className={`p-2 rounded cursor-pointer border transition-colors ${
                          selectedModels.has(model.id)
                            ? 'border-primary-500 bg-primary-500/10'
                            : 'border-dark-600 hover:border-dark-500'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <div
                            className={`w-4 h-4 rounded border flex items-center justify-center ${
                              selectedModels.has(model.id)
                                ? 'border-primary-500 bg-primary-500'
                                : 'border-dark-500'
                            }`}
                          >
                            {selectedModels.has(model.id) && (
                              <Check className="w-3 h-3 text-white" />
                            )}
                          </div>
                          <span className="text-dark-100 text-sm truncate">{model.id}</span>
                        </div>
                        {model.owned_by && (
                          <p className="text-dark-500 text-xs ml-6 truncate">
                            {model.owned_by}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Batch Add Button */}
                <div className="mt-4">
                  <button
                    onClick={handleBatchAddModels}
                    disabled={batchAdding || selectedModels.size === 0}
                    className="btn-primary w-full flex items-center justify-center gap-2"
                  >
                    {batchAdding ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Plus className="w-4 h-4" />
                    )}
                    批量添加 {selectedModels.size} 个模型到自定义配置
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* About Section */}
      <div className="card">
        <h2 className="text-lg font-medium text-white mb-4">关于</h2>
        <div className="space-y-2 text-dark-300">
          <div className="flex justify-between">
            <span>版本</span>
            <span className="text-dark-100">v0.1.0</span>
          </div>
          <div className="flex justify-between">
            <span>构建日期</span>
            <span className="text-dark-100">2026-02-15</span>
          </div>
          <div className="flex justify-between">
            <span>技术栈</span>
            <span className="text-dark-100">React + TypeScript + Tailwind CSS</span>
          </div>
        </div>
      </div>
    </div>
  );
}
