import { ReactNode } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  LayoutDashboard,
  Wrench,
  GitBranch,
  Database,
  Users,
  Settings,
  Menu,
  X,
  Plane,
  Activity,
  ChevronLeft,
} from 'lucide-react';
import { useAppStore } from '../../store';
import { LanguageSwitcher } from '../LanguageSwitcher';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { t } = useTranslation();
  const { sidebarOpen, setSidebarOpen } = useAppStore();
  const location = useLocation();

  const navItems = [
    { path: '/', icon: LayoutDashboard, labelKey: 'nav.dashboard' },
    { path: '/tasks', icon: GitBranch, labelKey: 'nav.tasks' },
    { path: '/tools', icon: Wrench, labelKey: 'nav.tools' },
    { path: '/sop', icon: Database, labelKey: 'nav.sop' },
    { path: '/agents', icon: Users, labelKey: 'nav.agents' },
    { path: '/tracing', icon: Activity, labelKey: 'nav.tracing' },
    { path: '/settings', icon: Settings, labelKey: 'nav.settings' },
  ];

  const currentNav = navItems.find((item) => item.path === location.pathname);

  return (
    <div className="flex h-screen bg-navy-950 font-body">
      {/* ============================================
          Sidebar - Glass Panel with Electric Accent
          ============================================ */}
      <aside
        className={`
          ${sidebarOpen ? 'w-64' : 'w-20'}
          relative flex flex-col
          bg-gradient-to-b from-steel-950/90 to-navy-950/90
          backdrop-blur-xl
          border-r border-steel-800/50
          transition-all duration-300 ease-out
        `}
      >
        {/* Top Electric Line */}
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-electric/50 to-transparent" />
        
        {/* Logo Section */}
        <div className="relative h-16 flex items-center justify-between px-4 border-b border-steel-800/50">
          <div className="flex items-center gap-3">
            {/* Logo Icon */}
            <div className="relative">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-electric to-cyber-500 flex items-center justify-center clip-corner-sm">
                <Plane className="w-5 h-5 text-navy-950" />
              </div>
              {/* Glow Effect */}
              <div className="absolute inset-0 rounded-lg bg-electric/20 blur-md -z-10" />
            </div>
            
            {/* Logo Text */}
            {sidebarOpen && (
              <div className="animate-fade-in">
                <span className="font-display text-lg font-bold text-text-primary tracking-tight">
                  {t('common.appName')}
                </span>
                <div className="text-[10px] text-steel-500 tracking-widest uppercase -mt-1">
                  {t('common.controlCenter')}
                </div>
              </div>
            )}
          </div>
          
          {/* Toggle Button */}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1.5 rounded-md text-steel-500 hover:text-electric hover:bg-steel-800/50 transition-all"
          >
            {sidebarOpen ? <ChevronLeft size={18} /> : <Menu size={18} />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-3 overflow-y-auto scrollbar-custom">
          <div className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={`
                    group relative flex items-center gap-3 px-3 py-2.5 rounded-md
                    font-medium text-sm transition-all duration-150
                    ${isActive
                      ? 'text-electric bg-electric/5'
                      : 'text-steel-400 hover:text-steel-200 hover:bg-steel-800/30'
                    }
                    ${!sidebarOpen && 'justify-center px-2'}
                  `}
                >
                  {/* Active Indicator */}
                  {isActive && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 bg-electric rounded-r-full" />
                  )}
                  
                  {/* Icon */}
                  <Icon 
                    size={20} 
                    className={`
                      flex-shrink-0 transition-colors
                      ${isActive ? 'text-electric' : 'text-steel-500 group-hover:text-steel-300'}
                    `}
                  />
                  
                  {/* Label */}
                  {sidebarOpen && (
                    <span className="truncate">{t(item.labelKey)}</span>
                  )}
                  
                  {/* Hover Glow */}
                  {isActive && (
                    <div className="absolute inset-0 rounded-md bg-electric/5 pointer-events-none" />
                  )}
                </NavLink>
              );
            })}
          </div>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-steel-800/50">
          {sidebarOpen ? (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
                <span className="text-xs text-steel-500">{t('common.systemOnline')}</span>
              </div>
              <span className="font-mono text-xs text-steel-600">v0.1.0</span>
            </div>
          ) : (
            <div className="flex justify-center">
              <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
            </div>
          )}
        </div>
        
        {/* Bottom Electric Line */}
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-electric/30 to-transparent" />
      </aside>

      {/* ============================================
          Main Content Area
          ============================================ */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="relative h-14 flex items-center justify-between px-6 border-b border-steel-800/50 bg-navy-950/50 backdrop-blur-sm">
          {/* Page Title */}
          <div className="flex items-center gap-3">
            <div className="w-1 h-6 bg-electric rounded-full" />
            <h1 className="font-display text-sm font-semibold text-text-primary tracking-wide uppercase">
              {currentNav ? t(currentNav.labelKey) : t('common.appName')}
            </h1>
          </div>
          
          {/* Right Section */}
          <div className="flex items-center gap-4">
            {/* Language Switcher */}
            <LanguageSwitcher />
            
            {/* System Status */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-steel-900/50 border border-steel-800/50">
              <div className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
              <span className="text-xs text-steel-400 font-medium">{t('common.allSystemsOperational')}</span>
            </div>
            
            {/* Current Time */}
            <div className="font-mono text-xs text-steel-500">
              {new Date().toLocaleTimeString(i18n.language === 'zh-CN' ? 'zh-CN' : 'en-US', { hour: '2-digit', minute: '2-digit' })}
            </div>
          </div>
          
          {/* Top Gradient Line */}
          <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-steel-700/50 to-transparent" />
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-auto p-6 scrollbar-custom">
          {children}
        </div>
      </main>
    </div>
  );
}
