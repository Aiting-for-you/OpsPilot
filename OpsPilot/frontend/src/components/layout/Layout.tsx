import { ReactNode, useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
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
} from 'lucide-react';
import { useAppStore } from '../store';

interface LayoutProps {
  children: ReactNode;
}

const navItems = [
  { path: '/', icon: LayoutDashboard, label: '仪表盘' },
  { path: '/tasks', icon: GitBranch, label: '任务管理' },
  { path: '/tools', icon: Wrench, label: '工具调用' },
  { path: '/sop', icon: Database, label: 'SOP 执行' },
  { path: '/agents', icon: Users, label: 'Agent 监控' },
  { path: '/tracing', icon: Activity, label: '追踪分析' },
  { path: '/settings', icon: Settings, label: '设置' },
];

export function Layout({ children }: LayoutProps) {
  const { sidebarOpen, setSidebarOpen } = useAppStore();
  const location = useLocation();

  return (
    <div className="flex h-screen bg-dark-950">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? 'w-64' : 'w-20'
        } bg-dark-900 border-r border-dark-700 flex flex-col transition-all duration-300`}
      >
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-dark-700">
          <div className="flex items-center gap-2">
            <Plane className="w-8 h-8 text-primary-500" />
            {sidebarOpen && (
              <span className="text-xl font-bold text-white">OpsPilot</span>
            )}
          </div>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1 rounded-lg hover:bg-dark-700 text-dark-400 hover:text-white transition-colors"
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-2 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200
                  ${
                    isActive
                      ? 'bg-primary-600 text-white'
                      : 'text-dark-300 hover:bg-dark-800 hover:text-white'
                  }
                  ${!sidebarOpen && 'justify-center'}`}
              >
                <Icon size={20} />
                {sidebarOpen && <span>{item.label}</span>}
              </NavLink>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-dark-700">
          <div
            className={`text-center ${
              sidebarOpen ? 'text-sm' : 'text-xs'
            } text-dark-500`}
          >
            {sidebarOpen ? 'OpsPilot v0.1.0' : 'v0.1'}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 bg-dark-900 border-b border-dark-700 flex items-center justify-between px-6">
          <h1 className="text-lg font-semibold text-white">
            {navItems.find((item) => item.path === location.pathname)?.label ||
              'OpsPilot'}
          </h1>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-sm text-dark-400">系统正常</span>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-auto p-6 scrollbar-thin">
          {children}
        </div>
      </main>
    </div>
  );
}
