import React from 'react';
import { TrendingUp, TrendingDown, AlertTriangle, ShieldAlert, Activity, Clock } from 'lucide-react';

interface Stat {
  title: string;
  value: string;
  change: string;
  isPositive: boolean;
  colorType: 'green' | 'amber' | 'dark';
}

export function StatCards() {
  const stats: Stat[] = [
    {
      title: 'Active Incidents',
      value: '24',
      change: '+12.5%',
      isPositive: false,
      colorType: 'green',
    },
    {
      title: 'MTTR',
      value: '2.4 hrs',
      change: '-15.2%',
      isPositive: true,
      colorType: 'dark',
    },
    {
      title: 'Active Alerts',
      value: '1,492',
      change: '+5.4%',
      isPositive: false,
      colorType: 'amber',
    },
    {
      title: 'Threat Level',
      value: 'Elevated',
      change: '+1',
      isPositive: false,
      colorType: 'dark',
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 lg:gap-4">
      {stats.map((stat, i) => {
        let bgClass = '';
        let textClass = '';
        let iconBg = '';
        let Icon = TrendingUp;

        if (stat.colorType === 'green') {
          bgClass = 'bg-emerald-500 text-white shadow-emerald-500/20';
          textClass = 'text-emerald-50';
          iconBg = 'bg-white/20 text-white';
          Icon = Activity;
        } else if (stat.colorType === 'amber') {
          bgClass = 'bg-amber-500 text-white shadow-amber-500/20';
          textClass = 'text-amber-50';
          iconBg = 'bg-white/20 text-white';
          Icon = AlertTriangle;
        } else {
          bgClass = 'bg-slate-900 dark:bg-[#2A2A35] text-white shadow-slate-900/10 dark:shadow-none';
          textClass = 'text-slate-400';
          iconBg = 'bg-slate-800 dark:bg-slate-700 text-white';
          Icon = i === 1 ? Clock : ShieldAlert;
        }

        return (
          <div
            key={stat.title}
            className={`relative overflow-hidden rounded-[20px] p-4 sm:p-5 shadow-lg transition-all hover:scale-[1.02] ${bgClass}`}
          >
            <div className="flex justify-between items-start mb-3 sm:mb-4">
              <span className={`text-xs sm:text-sm font-medium tracking-wide ${textClass}`}>
                {stat.title}
              </span>
              <div className={`p-1.5 rounded-lg ${iconBg} hidden sm:block`}>
                <Icon className="h-3.5 w-3.5" />
              </div>
            </div>
            <div className="flex flex-col sm:flex-row sm:items-end justify-between mt-1 sm:mt-2 gap-1 sm:gap-0">
              <div className="text-2xl sm:text-3xl font-bold tracking-tight">{stat.value}</div>
              <div className="flex items-center gap-1 text-[11px] sm:text-sm font-medium opacity-90">
                {stat.change}
                {stat.isPositive ? (
                  <TrendingDown className="h-3 w-3 sm:h-4 sm:w-4" />
                ) : (
                  <TrendingUp className="h-3 w-3 sm:h-4 sm:w-4" />
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
