import React from 'react';
import { Search, Sun, Moon, RotateCcw, Bell, Menu, LayoutDashboard } from 'lucide-react';
import { useTheme } from '../theme';

interface HeaderProps {
  onRefresh: () => void;
  isRefreshing: boolean;
  onToggleDashboard?: () => void;
}

export function Header({ onRefresh, isRefreshing, onToggleDashboard }: HeaderProps) {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="h-16 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-[#1C1C22] flex items-center justify-between px-4 sm:px-6 lg:px-8 transition-colors duration-200 z-20">
      <div className="flex items-center gap-4">
        <button className="lg:hidden text-slate-500 hover:text-slate-900 dark:hover:text-white">
          <Menu className="h-5 w-5" />
        </button>
        <div className="hidden sm:flex items-center text-sm font-medium text-slate-500 dark:text-slate-400">
          <span className="hover:text-slate-900 dark:hover:text-white cursor-pointer transition-colors">IRP Command Center</span>
          <span className="mx-2 text-slate-300 dark:text-slate-600">/</span>
          <span className="text-slate-900 dark:text-white font-semibold flex items-center gap-2">
            AI Operations Copilot
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-4">
        <div className="relative hidden md:block w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 dark:text-slate-500" />
          <input
            type="text"
            placeholder="Search assets, incidents..."
            className="w-full pl-9 pr-4 py-2 bg-slate-100 dark:bg-[#2A2A35] border-transparent rounded-full text-sm placeholder:text-slate-400 dark:placeholder:text-slate-500 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white dark:focus:bg-[#1C1C22] transition-all"
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 text-xs text-slate-400 dark:text-slate-500 font-medium">
            <kbd className="font-sans px-1.5 py-0.5 rounded-md bg-white dark:bg-[#1C1C22] border border-slate-200 dark:border-slate-700 shadow-sm">⌘</kbd>
            <kbd className="font-sans px-1.5 py-0.5 rounded-md bg-white dark:bg-[#1C1C22] border border-slate-200 dark:border-slate-700 shadow-sm">K</kbd>
          </div>
        </div>

        <button
          onClick={toggleTheme}
          className="p-2 text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-500/10 rounded-full transition-colors"
          aria-label="Toggle theme"
        >
          {theme === 'light' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </button>
        
        <button
          onClick={onRefresh}
          className={`p-2 text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-500/10 rounded-full transition-all hidden sm:block ${isRefreshing ? 'animate-spin text-emerald-600 dark:text-emerald-400' : ''}`}
          aria-label="Refresh dashboard"
        >
          <RotateCcw className="h-5 w-5" />
        </button>

        <button className="relative p-2 text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-500/10 rounded-full transition-colors">
          <Bell className="h-5 w-5" />
          <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-amber-500 border border-white dark:border-[#1C1C22]"></span>
        </button>

        {/* Mobile Dashboard Toggle */}
        <button 
          onClick={onToggleDashboard}
          className="lg:hidden p-2 text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-500/10 rounded-full transition-colors ml-1"
        >
          <LayoutDashboard className="h-5 w-5" />
        </button>
      </div>
    </header>
  );
}
