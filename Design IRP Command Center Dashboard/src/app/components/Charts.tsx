import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useTheme } from '../theme';

const data = [
  { name: 'Jan', incidents: 4000, alerts: 2400 },
  { name: 'Feb', incidents: 3000, alerts: 1398 },
  { name: 'Mar', incidents: 2000, alerts: 9800 },
  { name: 'Apr', incidents: 2780, alerts: 3908 },
  { name: 'May', incidents: 1890, alerts: 4800 },
  { name: 'Jun', incidents: 2390, alerts: 3800 },
  { name: 'Jul', incidents: 3490, alerts: 4300 },
];

export function Charts() {
  const { theme } = useTheme();

  return (
    <div className="bg-white dark:bg-[#2A2A35] rounded-3xl p-5 shadow-sm border border-slate-100 dark:border-slate-800/50 transition-colors duration-200">
      <div className="flex flex-col gap-4 mb-6">
        <div className="flex flex-wrap gap-4 text-sm font-semibold">
          <button className="text-emerald-600 dark:text-emerald-400 border-b-2 border-emerald-500 pb-1 px-1 transition-colors">
            Incidents
          </button>
          <button className="text-slate-400 dark:text-slate-500 hover:text-slate-900 dark:hover:text-slate-300 pb-1 px-1 transition-colors">
            Alerts
          </button>
        </div>
        <select className="bg-slate-50 dark:bg-[#1C1C22] text-slate-700 dark:text-slate-300 text-xs font-medium px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 outline-none cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors w-full">
          <option>Last 6 Months</option>
          <option>Last Year</option>
          <option>Year to Date</option>
        </select>
      </div>

      <div className="w-full h-[220px]">
        <ResponsiveContainer width="100%" height={220} minWidth={100}>
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs key="defs">
              <linearGradient id="colorIncidents" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              key="grid"
              strokeDasharray="3 3"
              vertical={false}
              stroke={theme === 'light' ? '#f1f5f9' : '#334155'}
            />
            <XAxis
              key="xaxis"
              dataKey="name"
              axisLine={false}
              tickLine={false}
              tick={{ fill: theme === 'light' ? '#94a3b8' : '#64748b', fontSize: 11, fontWeight: 500 }}
              dy={10}
            />
            <YAxis
              key="yaxis"
              axisLine={false}
              tickLine={false}
              tick={{ fill: theme === 'light' ? '#94a3b8' : '#64748b', fontSize: 11, fontWeight: 500 }}
              dx={-10}
            />
            <Tooltip
              key="tooltip"
              contentStyle={{
                backgroundColor: theme === 'light' ? '#ffffff' : '#1e293b',
                borderRadius: '12px',
                border: theme === 'light' ? '1px solid #e2e8f0' : '1px solid #334155',
                color: theme === 'light' ? '#0f172a' : '#f8fafc',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
                fontWeight: 600,
                fontSize: '12px',
              }}
              itemStyle={{ color: '#10b981', fontWeight: 600 }}
              labelStyle={{ color: theme === 'light' ? '#64748b' : '#94a3b8', marginBottom: '2px' }}
            />
            <Area
              key="area"
              type="monotone"
              dataKey="incidents"
              stroke="#10b981"
              strokeWidth={3}
              fillOpacity={1}
              fill="url(#colorIncidents)"
              activeDot={{ r: 5, strokeWidth: 0, fill: '#10b981' }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
