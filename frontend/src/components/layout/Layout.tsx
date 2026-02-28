import { ReactNode, useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  LayoutDashboard,
  Wrench,
  Database,
  Users,
  Settings,
  Menu,
  X,
  Activity,
  Clock,
  BarChart3,
  Monitor,
  Cpu,
  Brain,
  DollarSign,
  MessageSquare,
  ChevronDown,
  Bell,
  Home,
  Zap,
  FileText,
  Package,
} from 'lucide-react';
import { LanguageSwitcher } from '../LanguageSwitcher';

interface LayoutProps {
  children: ReactNode;
}

// 导航配置 - 首页和仪表盘并列
const navItems = [
  { path: '/', icon: Home, labelKey: 'nav.home' },
  { path: '/dashboard', icon: LayoutDashboard, labelKey: 'nav.dashboard' },
];

// 分组导航
const navGroups = [
  {
    title: 'operation',
    label: 'nav.operation',
    items: [
      { path: '/tasks', icon: Activity, labelKey: 'nav.tasks' },
      { path: '/tools', icon: Wrench, labelKey: 'nav.tools' },
      { path: '/sop', icon: FileText, labelKey: 'nav.sop' },
      { path: '/scheduler', icon: Clock, labelKey: 'nav.scheduler' },
      { path: '/data-viewer', icon: Database, labelKey: 'nav.dataViewer' },
    ]
  },
  {
    title: 'monitor',
    label: 'nav.monitor',
    items: [
      { path: '/monitoring', icon: Monitor, labelKey: 'nav.monitoring' },
      { path: '/tracing', icon: Activity, labelKey: 'nav.tracing' },
      { path: '/analytics', icon: BarChart3, labelKey: 'nav.analytics' },
    ]
  },
  {
    title: 'optimization',
    label: 'nav.optimization',
    items: [
      { path: '/agents', icon: Users, labelKey: 'nav.agents' },
      { path: '/tool-optimization', icon: Zap, labelKey: 'nav.toolOptimization' },
      { path: '/memory-optimization', icon: Brain, labelKey: 'nav.memoryOptimization' },
    ]
  },
  {
    title: 'business',
    label: 'nav.business',
    items: [
      { path: '/pricing', icon: DollarSign, labelKey: 'nav.pricing' },
      { path: '/customer-service', icon: MessageSquare, labelKey: 'nav.customerService' },
      { path: '/skills-manager', icon: Package, labelKey: 'nav.skillsManager' },
    ]
  },
];

// 设置直接显示在导航栏

export function Layout({ children }: LayoutProps) {
  const { t } = useTranslation();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航栏 */}
      <header className="fixed top-0 left-0 right-0 h-14 bg-white border-b border-gray-200 z-50">
        <div className="h-full px-4 flex items-center justify-between">
          {/* 左侧：Logo + 导航 */}
          <div className="flex items-center gap-4">
            {/* Logo */}
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
                <svg viewBox="0 0 24 24" className="w-5 h-5 text-white" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <span className="font-semibold text-gray-900 text-lg">OpsPilot</span>
            </div>

            {/* 桌面导航 */}
            <nav className="hidden md:flex items-center gap-1 ml-4">
              {/* 首页 + 仪表盘 - 并列显示 */}
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={`px-3 py-1.5 text-sm rounded-md flex items-center gap-2 transition-colors ${
                      isActive
                        ? 'text-blue-600 bg-blue-50 font-medium'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {t(item.labelKey)}
                  </NavLink>
                );
              })}

              {/* 分组下拉菜单 */}
              {navGroups.map((group) => (
                <div key={group.title} className="relative group">
                  <button className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md flex items-center gap-1 transition-colors">
                    {t(group.label)}
                    <ChevronDown className="w-3 h-3" />
                  </button>
                  {/* 下拉菜单 */}
                  <div className="absolute top-full left-0 mt-1 py-1 bg-white border border-gray-200 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all min-w-[160px]">
                    {group.items.map((item) => {
                      const Icon = item.icon;
                      const isActive = location.pathname === item.path;
                      return (
                        <NavLink
                          key={item.path}
                          to={item.path}
                          className={`flex items-center gap-2 px-3 py-2 text-sm transition-colors ${
                            isActive
                              ? 'text-blue-600 bg-blue-50'
                              : 'text-gray-700 hover:bg-gray-50'
                          }`}
                        >
                          <Icon className="w-4 h-4" />
                          {t(item.labelKey)}
                        </NavLink>
                      );
                    })}
                  </div>
                </div>
              ))}

              {/* 设置链接 */}
              <NavLink
                to="/settings"
                className={({ isActive }) =>
                  `flex items-center gap-2 px-3 py-1.5 text-sm rounded-md transition-colors ${
                    isActive ? 'text-blue-600 bg-blue-50' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`
                }
              >
                <Settings className="w-4 h-4" />
                {t('nav.settings')}
              </NavLink>
            </nav>
          </div>

          {/* 右侧：语言切换 */}
          <div className="flex items-center gap-2">
            <LanguageSwitcher />

            {/* 移动端菜单按钮 */}
            <button 
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* 移动端导航菜单 */}
        {mobileMenuOpen && (
          <div className="md:hidden absolute top-14 left-0 right-0 bg-white border-b border-gray-200 shadow-lg max-h-[calc(100vh-3.5rem)] overflow-y-auto">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 transition-colors ${
                    isActive
                      ? 'text-blue-600 bg-blue-50'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="text-sm font-medium">{t(item.labelKey)}</span>
                </NavLink>
              );
            })}
            {navGroups.map((group) => (
              <div key={group.title}>
                <div className="px-4 py-2 text-xs font-medium text-gray-400 uppercase bg-gray-50">
                  {t(group.label)}
                </div>
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;
                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`flex items-center gap-3 px-4 py-3 transition-colors ${
                        isActive
                          ? 'text-blue-600 bg-blue-50'
                          : 'text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                      <span className="text-sm font-medium">{t(item.labelKey)}</span>
                    </NavLink>
                  );
                })}
              </div>
            ))}
          </div>
        )}
      </header>

      {/* 主内容区 */}
      <main className="pt-14 min-h-screen">
        <div className="p-6">
          {children}
        </div>
      </main>
    </div>
  );
}