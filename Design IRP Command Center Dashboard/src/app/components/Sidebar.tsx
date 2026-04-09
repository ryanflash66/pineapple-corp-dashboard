import React from 'react';
import { Shield, Home, Server, AlertCircle, FileText, Crosshair, Settings, Bell, Search, Sun, Moon, RotateCcw } from 'lucide-react';

export function Sidebar() {
  const navItems = [
    { name: 'Command Center', icon: Home, active: true },
    { name: 'Asset Inventory', icon: Server, active: false },
    { name: 'Active Incidents', icon: AlertCircle, active: false },
    { name: 'Playbooks', icon: FileText, active: false },
    { name: 'Threat Intel', icon: Crosshair, active: false },
    { name: 'Settings', icon: Settings, active: false },
  ];

  return (
    <aside className="hidden lg:flex flex-col w-[240px] border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-[#1C1C22] h-full transition-colors duration-200">
      <div className="flex items-center gap-3 px-6 h-16 border-b border-slate-200 dark:border-slate-800">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-600 dark:bg-emerald-500/30 dark:text-emerald-400">
          <Shield className="h-5 w-5" />
        </div>
        <span className="font-bold text-[15px] text-slate-900 dark:text-white tracking-tight">
          Pineapple Corp
        </span>
      </div>

      <div className="flex-1 py-6 px-4 overflow-y-auto space-y-1">
        <div className="mb-4 px-2 text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
          Operations
        </div>
        {navItems.map((item) => (
          <button
            key={item.name}
            className={`flex w-full items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
              item.active
                ? 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 hover:text-slate-900 dark:hover:bg-slate-800/50 dark:hover:text-white'
            }`}
          >
            <item.icon className={`h-[18px] w-[18px] ${item.active ? 'text-emerald-600 dark:text-emerald-500' : ''}`} />
            {item.name}
          </button>
        ))}
      </div>

      <div className="p-4 border-t border-slate-200 dark:border-slate-800">
        <button className="flex w-full items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-50 hover:text-slate-900 dark:hover:bg-slate-800/50 dark:hover:text-white transition-all">
          <div className="h-8 w-8 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden">
            <img src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-1.2.1&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80" alt="User Avatar" className="h-full w-full object-cover" />
          </div>
          <div className="flex flex-col items-start">
            <span className="text-sm font-medium text-slate-900 dark:text-white leading-none">Admin</span>
            <span className="text-xs text-slate-500 mt-1 leading-none">SecOps Lead</span>
          </div>
        </button>
      </div>
    </aside>
  );
}
