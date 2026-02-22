import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Bell, Save, Check, X, Webhook, MessageSquare, Mail, Eye, EyeOff, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

interface NotificationConfig {
  webhook_url: string;
  slack_token: string;
  slack_channel: string;
  smtp_host: string;
  smtp_port: string;
  smtp_username: string;
  smtp_password: string;
  smtp_from_addr: string;
}

interface NotificationStatus {
  configured: boolean;
  webhook_enabled: boolean;
  slack_enabled: boolean;
  email_enabled: boolean;
}

export function NotificationSettings() {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<NotificationStatus | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [config, setConfig] = useState<NotificationConfig>({
    webhook_url: '',
    slack_token: '',
    slack_channel: '',
    smtp_host: '',
    smtp_port: '587',
    smtp_username: '',
    smtp_password: '',
    smtp_from_addr: '',
  });
  
  const [showPassword, setShowPassword] = useState(false);
  const [showToken, setShowToken] = useState(false);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      setLoading(true);
      const data = await api.get<NotificationStatus>('/notification/status');
      setStatus(data);
    } catch (err) {
      console.error('Failed to load notification status:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSaveSuccess(false);
      
      await api.post('/notification/config', {
        webhook_url: config.webhook_url || undefined,
        slack_token: config.slack_token || undefined,
        slack_channel: config.slack_channel || undefined,
        smtp_host: config.smtp_host || undefined,
        smtp_port: config.smtp_port ? parseInt(config.smtp_port) : undefined,
        smtp_username: config.smtp_username || undefined,
        smtp_password: config.smtp_password || undefined,
        smtp_from_addr: config.smtp_from_addr || undefined,
      });
      
      setSaveSuccess(true);
      await loadStatus();
      
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to save notification config');
    } finally {
      setSaving(false);
    }
  };

  const updateConfig = (key: keyof NotificationConfig, value: string) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="space-y-6">
      {/* Status Card */}
      <div className="bg-card border border-border rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">
          {t('settings.notification.status') || 'Notification Status'}
        </h3>
        {loading ? (
          <div className="flex items-center gap-2 text-gray-500">
            <RefreshCw className="w-4 h-4 animate-spin" />
            Loading...
          </div>
        ) : status ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className={`flex items-center gap-2 p-2 rounded ${status.configured ? 'bg-green-50' : 'bg-gray-50'}`}>
              <div className={`w-2 h-2 rounded-full ${status.configured ? 'bg-green-500' : 'bg-gray-400'}`} />
              <span className="text-xs text-gray-600">
                {status.configured ? 'Configured' : 'Not Configured'}
              </span>
            </div>
            <div className={`flex items-center gap-2 p-2 rounded ${status.webhook_enabled ? 'bg-green-50' : 'bg-gray-50'}`}>
              <Webhook className="w-4 h-4" />
              <span className="text-xs text-gray-600">Webhook</span>
              <span className={`text-xs ${status.webhook_enabled ? 'text-green-600' : 'text-gray-400'}`}>
                {status.webhook_enabled ? 'ON' : 'OFF'}
              </span>
            </div>
            <div className={`flex items-center gap-2 p-2 rounded ${status.slack_enabled ? 'bg-green-50' : 'bg-gray-50'}`}>
              <MessageSquare className="w-4 h-4" />
              <span className="text-xs text-gray-600">Slack</span>
              <span className={`text-xs ${status.slack_enabled ? 'text-green-600' : 'text-gray-400'}`}>
                {status.slack_enabled ? 'ON' : 'OFF'}
              </span>
            </div>
            <div className={`flex items-center gap-2 p-2 rounded ${status.email_enabled ? 'bg-green-50' : 'bg-gray-50'}`}>
              <Mail className="w-4 h-4" />
              <span className="text-xs text-gray-600">Email</span>
              <span className={`text-xs ${status.email_enabled ? 'text-green-600' : 'text-gray-400'}`}>
                {status.email_enabled ? 'ON' : 'OFF'}
              </span>
            </div>
          </div>
        ) : (
          <div className="text-xs text-gray-500">Unable to load status</div>
        )}
      </div>

      {/* Webhook Config */}
      <div className="bg-card border border-border rounded-lg p-4">
        <div className="flex items-center gap-2 mb-4">
          <Webhook className="w-5 h-5 text-blue-500" />
          <h3 className="text-sm font-semibold text-gray-900">
            {t('settings.notification.webhook') || 'Webhook'}
          </h3>
        </div>
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              {t('settings.notification.webhookUrl') || 'Webhook URL'}
            </label>
            <input
              type="url"
              value={config.webhook_url}
              onChange={(e) => updateConfig('webhook_url', e.target.value)}
              placeholder="https://example.com/webhook"
              className="w-full px-3 py-2 text-sm border border-border rounded bg-background text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-electric"
            />
            <p className="text-xs text-gray-500 mt-1">
              {t('settings.notification.webhookHint') || 'Will send POST request when approval events occur'}
            </p>
          </div>
        </div>
      </div>

      {/* Slack Config */}
      <div className="bg-card border border-border rounded-lg p-4">
        <div className="flex items-center gap-2 mb-4">
          <MessageSquare className="w-5 h-5 text-purple-500" />
          <h3 className="text-sm font-semibold text-gray-900">Slack</h3>
        </div>
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              {t('settings.notification.slackToken') || 'Bot Token'}
            </label>
            <div className="relative">
              <input
                type={showToken ? 'text' : 'password'}
                value={config.slack_token}
                onChange={(e) => updateConfig('slack_token', e.target.value)}
                placeholder="xoxb-..."
                className="w-full px-3 py-2 pr-10 text-sm border border-border rounded bg-background text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-electric"
              />
              <button
                type="button"
                onClick={() => setShowToken(!showToken)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showToken ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              {t('settings.notification.slackChannel') || 'Channel ID'}
            </label>
            <input
              type="text"
              value={config.slack_channel}
              onChange={(e) => updateConfig('slack_channel', e.target.value)}
              placeholder="C1234567890"
              className="w-full px-3 py-2 text-sm border border-border rounded bg-background text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-electric"
            />
          </div>
        </div>
      </div>

      {/* Email Config */}
      <div className="bg-card border border-border rounded-lg p-4">
        <div className="flex items-center gap-2 mb-4">
          <Mail className="w-5 h-5 text-orange-500" />
          <h3 className="text-sm font-semibold text-gray-900">
            {t('settings.notification.email') || 'Email (SMTP)'}
          </h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              {t('settings.notification.smtpHost') || 'SMTP Host'}
            </label>
            <input
              type="text"
              value={config.smtp_host}
              onChange={(e) => updateConfig('smtp_host', e.target.value)}
              placeholder="smtp.example.com"
              className="w-full px-3 py-2 text-sm border border-border rounded bg-background text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-electric"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              {t('settings.notification.smtpPort') || 'Port'}
            </label>
            <input
              type="text"
              value={config.smtp_port}
              onChange={(e) => updateConfig('smtp_port', e.target.value)}
              placeholder="587"
              className="w-full px-3 py-2 text-sm border border-border rounded bg-background text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-electric"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              {t('settings.notification.smtpUsername') || 'Username'}
            </label>
            <input
              type="text"
              value={config.smtp_username}
              onChange={(e) => updateConfig('smtp_username', e.target.value)}
              placeholder="user@example.com"
              className="w-full px-3 py-2 text-sm border border-border rounded bg-background text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-electric"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              {t('settings.notification.smtpPassword') || 'Password'}
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={config.smtp_password}
                onChange={(e) => updateConfig('smtp_password', e.target.value)}
                placeholder="••••••••"
                className="w-full px-3 py-2 pr-10 text-sm border border-border rounded bg-background text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-electric"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-gray-700 mb-1">
              {t('settings.notification.smtpFromAddr') || 'From Address'}
            </label>
            <input
              type="email"
              value={config.smtp_from_addr}
              onChange={(e) => updateConfig('smtp_from_addr', e.target.value)}
              placeholder="opsilot@example.com"
              className="w-full px-3 py-2 text-sm border border-border rounded bg-background text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-electric"
            />
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end gap-2">
        {saveSuccess && (
          <span className="flex items-center gap-1 text-green-600 text-sm">
            <Check className="w-4 h-4" />
            {t('settings.saved') || 'Saved!'}
          </span>
        )}
        {error && (
          <span className="flex items-center gap-1 text-red-600 text-sm">
            <X className="w-4 h-4" />
            {error}
          </span>
        )}
        <button
          onClick={handleSave}
          disabled={saving}
          className="btn btn-primary"
        >
          {saving ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          {t('settings.save') || 'Save'}
        </button>
      </div>
    </div>
  );
}
