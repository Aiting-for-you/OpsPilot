import { useState } from 'react';
import { Settings as SettingsIcon, Save, RefreshCw } from 'lucide-react';

interface SettingSection {
  title: string;
  settings: {
    key: string;
    label: string;
    type: 'text' | 'number' | 'select' | 'switch';
    value: any;
    options?: { value: string; label: string }[];
  }[];
}

const defaultSettings: SettingSection[] = [
  {
    title: 'API 配置',
    settings: [
      { key: 'api_url', label: 'API 地址', type: 'text', value: 'http://localhost:8000/api/v1' },
      { key: 'timeout', label: '请求超时 (秒)', type: 'number', value: 30 },
    ],
  },
  {
    title: 'LLM 配置',
    settings: [
      { key: 'model', label: '模型', type: 'select', value: 'gpt-4', options: [
        { value: 'gpt-4', label: 'GPT-4' },
        { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
        { value: 'claude-3', label: 'Claude 3' },
      ]},
      { key: 'temperature', label: 'Temperature', type: 'number', value: 0.7 },
    ],
  },
  {
    title: 'Agent 配置',
    settings: [
      { key: 'max_retries', label: '最大重试次数', type: 'number', value: 3 },
      { key: 'enable_gui', label: '启用 GUI 降级', type: 'switch', value: true },
    ],
  },
];

export function Settings() {
  const [settings, setSettings] = useState(defaultSettings);
  const [saved, setSaved] = useState(false);

  const handleValueChange = (sectionIdx: number, settingIdx: number, value: any) => {
    setSettings((prev) => {
      const newSettings = [...prev];
      newSettings[sectionIdx] = {
        ...newSettings[sectionIdx],
        settings: newSettings[sectionIdx].settings.map((s, i) =>
          i === settingIdx ? { ...s, value } : s
        ),
      };
      return newSettings;
    });
    setSaved(false);
  };

  const handleSave = () => {
    // 保存到 localStorage
    const config = settings.reduce((acc, section) => {
      section.settings.forEach((s) => {
        acc[s.key] = s.value;
      });
      return acc;
    }, {} as Record<string, any>);
    localStorage.setItem('opspilot_config', JSON.stringify(config));
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <SettingsIcon className="w-5 h-5 text-primary-400" />
          <h1 className="text-lg font-semibold text-white">系统设置</h1>
        </div>
        <button
          onClick={handleSave}
          className="btn-primary flex items-center gap-2"
        >
          {saved ? (
            <>
              <RefreshCw className="w-4 h-4" />
              已保存
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              保存设置
            </>
          )}
        </button>
      </div>

      {/* Settings Sections */}
      {settings.map((section, sectionIdx) => (
        <div key={section.title} className="card">
          <h2 className="text-lg font-medium text-white mb-4">{section.title}</h2>
          <div className="space-y-4">
            {section.settings.map((setting, settingIdx) => (
              <div key={setting.key} className="flex items-center justify-between">
                <label className="text-dark-300">{setting.label}</label>
                {setting.type === 'text' && (
                  <input
                    type="text"
                    value={setting.value}
                    onChange={(e) => handleValueChange(sectionIdx, settingIdx, e.target.value)}
                    className="input w-64"
                  />
                )}
                {setting.type === 'number' && (
                  <input
                    type="number"
                    value={setting.value}
                    onChange={(e) => handleValueChange(sectionIdx, settingIdx, parseFloat(e.target.value))}
                    className="input w-32"
                  />
                )}
                {setting.type === 'select' && (
                  <select
                    value={setting.value}
                    onChange={(e) => handleValueChange(sectionIdx, settingIdx, e.target.value)}
                    className="input w-64"
                  >
                    {setting.options?.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                )}
                {setting.type === 'switch' && (
                  <button
                    onClick={() => handleValueChange(sectionIdx, settingIdx, !setting.value)}
                    className={`w-12 h-6 rounded-full transition-colors ${
                      setting.value ? 'bg-primary-600' : 'bg-dark-600'
                    }`}
                  >
                    <div
                      className={`w-5 h-5 rounded-full bg-white transition-transform ${
                        setting.value ? 'translate-x-6' : 'translate-x-0.5'
                      }`}
                    />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}

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
