import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { 
  Play,
  Plus,
  Zap,
  Database,
  Clock,
  Activity,
  Settings,
  MessageSquare,
  Users,
  BarChart3,
  Wrench,
  FileText,
} from 'lucide-react';

export function Home() {
  const { t } = useTranslation();
  const [taskInput, setTaskInput] = useState('');

  // 简洁的快捷功能
  const quickFeatures = [
    { label: t('home.newTask'), icon: Plus, path: '/tasks', desc: t('home.newTaskDesc'), color: 'blue' },
    { label: t('home.tools'), icon: Zap, path: '/tools', desc: t('home.toolsDesc'), color: 'purple' },
    { label: t('home.sop'), icon: FileText, path: '/sop', desc: t('home.sopDesc'), color: 'green' },
    { label: t('home.schedule'), icon: Clock, path: '/scheduler', desc: t('home.scheduleDesc'), color: 'orange' },
  ];

  // 导航入口
  const navEntries = [
    { label: t('home.tasks'), icon: Activity, path: '/tasks', count: 0 },
    { label: t('home.agents'), icon: Users, path: '/agents', count: 5 },
    { label: t('home.monitoring'), icon: BarChart3, path: '/analytics', count: 0 },
    { label: t('home.settings'), icon: Settings, path: '/settings', count: 0 },
  ];

  const colorMap: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-600 border-blue-200 hover:bg-blue-100',
    purple: 'bg-purple-50 text-purple-600 border-purple-200 hover:bg-purple-100',
    green: 'bg-green-50 text-green-600 border-green-200 hover:bg-green-100',
    orange: 'bg-orange-50 text-orange-600 border-orange-200 hover:bg-orange-100',
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* 欢迎区域 */}
      <div className="text-center py-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-600 mb-4">
          <svg viewBox="0 0 24 24" className="w-8 h-8 text-white" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <h1 className="text-3xl font-bold text-gray-900">{t('home.welcome')}</h1>
        <p className="text-gray-500 mt-2">{t('home.subtitle')}</p>
      </div>

      {/* 快速任务输入 */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex gap-3">
          <input
            type="text"
            value={taskInput}
            onChange={(e) => setTaskInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && taskInput && window.location.assign(`/tasks?input=${encodeURIComponent(taskInput)}`)}
            placeholder={t('home.taskPlaceholder')}
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <Link
            to={taskInput ? `/tasks?input=${encodeURIComponent(taskInput)}` : '/tasks'}
            className="btn btn-primary"
          >
            <Play className="w-5 h-5" />
            {t('home.execute')}
          </Link>
        </div>
      </div>

      {/* 快捷功能卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {quickFeatures.map((feature) => {
          const Icon = feature.icon;
          return (
            <Link
              key={feature.path}
              to={feature.path}
              className={`flex flex-col items-center gap-3 p-6 rounded-xl border-2 transition-all hover:shadow-md ${colorMap[feature.color]}`}
            >
              <Icon className="w-8 h-8" />
              <div className="text-center">
                <div className="font-medium text-gray-900">{feature.label}</div>
                <div className="text-xs text-gray-500 mt-1">{feature.desc}</div>
              </div>
            </Link>
          );
        })}
      </div>

      {/* 导航入口 */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('home.quickNav')}</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {navEntries.map((entry) => {
            const Icon = entry.icon;
            return (
              <Link
                key={entry.path}
                to={entry.path}
                className="flex items-center gap-3 p-4 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors"
              >
                <Icon className="w-5 h-5 text-gray-600" />
                <span className="font-medium text-gray-700">{entry.label}</span>
              </Link>
            );
          })}
        </div>
      </div>

      {/* 底部信息 */}
      <div className="text-center text-sm text-gray-400 py-4">
        <p>OpsPilot {t('home.version')} v1.0.0 · {t('home.aiOps')}</p>
      </div>
    </div>
  );
}
