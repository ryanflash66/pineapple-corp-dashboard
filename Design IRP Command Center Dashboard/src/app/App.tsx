import React, { useState } from 'react';
import { LayoutDashboard } from 'lucide-react';
import { ThemeProvider } from './theme';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { StatCards } from './components/StatCards';
import { Charts } from './components/Charts';
import { AssetTable } from './components/AssetTable';
import { CentralChat } from './components/CentralChat';

export default function App() {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isDashboardOpen, setIsDashboardOpen] = useState(false); // Mobile dashboard toggle

  const handleRefresh = () => {
    setIsRefreshing(true);
    // Simulate refresh
    setTimeout(() => setIsRefreshing(false), 1000);
  };

  return (
    <ThemeProvider>
      <div className="flex h-screen w-full bg-[#F8FAFC] dark:bg-[#15151A] text-slate-900 dark:text-slate-100 font-sans transition-colors duration-200 overflow-hidden">
        {/* Left Sidebar - Navigation */}
        <Sidebar />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0 min-h-0 h-full overflow-hidden relative">
          <Header 
            onRefresh={handleRefresh} 
            isRefreshing={isRefreshing} 
            onToggleDashboard={() => setIsDashboardOpen(!isDashboardOpen)} 
          />
          
          <div className="flex-1 flex overflow-hidden relative min-w-0 min-h-0">
            {/* Center Main Chat View */}
            <main className="flex-1 flex flex-col min-w-0 bg-white dark:bg-[#1C1C22] z-10 lg:rounded-tl-2xl border-t lg:border-t-0 lg:border-l border-slate-200 dark:border-slate-800/80 shadow-[0_0_40px_-15px_rgba(0,0,0,0.1)] overflow-hidden transition-all duration-300">
              <CentralChat />
            </main>

            {/* Right Context Dashboard */}
            {/* Desktop: always visible side panel. Mobile: sliding drawer */}
            <aside className={`
              fixed inset-y-0 right-0 z-40 w-[320px] sm:w-[580px] xl:w-[620px] 2xl:w-[680px]
              bg-[#F8FAFC] dark:bg-[#15151A] lg:static lg:block transition-transform duration-300 ease-in-out flex flex-col min-w-0
              ${isDashboardOpen ? 'translate-x-0 border-l border-slate-200 dark:border-slate-800' : 'translate-x-full lg:translate-x-0 lg:border-l lg:border-slate-200 dark:lg:border-slate-800'}
            `}>
              <div className="h-full overflow-y-auto overflow-x-hidden p-4 lg:p-6 scroll-smooth space-y-6 flex-1 min-h-0">
                <div className="flex items-center justify-between lg:hidden mb-2">
                  <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">Dashboard Overview</h2>
                  <button onClick={() => setIsDashboardOpen(false)} className="p-2 text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-lg">
                    Close
                  </button>
                </div>
                
                <div className="hidden lg:flex items-center gap-2 mb-4 px-1">
                  <LayoutDashboard className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                  <h2 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Command Overview</h2>
                </div>

                <StatCards />
                <Charts />
                <AssetTable />
              </div>
            </aside>

            {/* Mobile overlay for dashboard */}
            {isDashboardOpen && (
              <div 
                className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-30 lg:hidden"
                onClick={() => setIsDashboardOpen(false)}
              />
            )}
          </div>
        </div>
      </div>
    </ThemeProvider>
  );
}
