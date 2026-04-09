import React from 'react';
import { MoreHorizontal, Server, Laptop, Smartphone, Database, Globe } from 'lucide-react';

export function AssetTable() {
  const assets = [
    {
      id: 1,
      name: 'prod-db-cluster-01',
      icon: Database,
      ip: '10.0.4.15',
      location: 'us-east-1',
      type: 'Database',
      status: 'Quarantined',
      statusColor: 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400',
    },
    {
      id: 2,
      name: 'web-frontend-node-a',
      icon: Server,
      ip: '192.168.1.100',
      location: 'eu-west-2',
      type: 'Compute',
      status: 'Secure',
      statusColor: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400',
    },
    {
      id: 3,
      name: 'exec-laptop-smith',
      icon: Laptop,
      ip: '172.16.0.42',
      location: 'Corporate HQ',
      type: 'Endpoint',
      status: 'Compromised',
      statusColor: 'bg-rose-100 text-rose-700 dark:bg-rose-500/20 dark:text-rose-400',
    },
    {
      id: 4,
      name: 'api-gateway-edge',
      icon: Globe,
      ip: '104.21.3.44',
      location: 'Global Edge',
      type: 'Network',
      status: 'Investigating',
      statusColor: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
    },
  ];

  return (
    <div className="bg-white dark:bg-[#2A2A35] rounded-3xl p-5 shadow-sm border border-slate-100 dark:border-slate-800/50 transition-colors duration-200">
      <div className="flex justify-between items-center mb-5">
        <h2 className="text-[15px] font-bold text-slate-900 dark:text-white tracking-tight">
          Impacted Assets
        </h2>
        <button className="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-400 transition-colors">
          <MoreHorizontal className="h-5 w-5" />
        </button>
      </div>

      <div className="space-y-2.5">
        {assets.map((asset) => (
          <div
            key={asset.id}
            className="group flex flex-col xl:flex-row xl:items-center justify-between p-3 rounded-2xl bg-slate-50/50 dark:bg-[#1C1C22]/50 hover:bg-slate-100 dark:hover:bg-[#1C1C22] border border-transparent hover:border-slate-200 dark:hover:border-slate-700 transition-all gap-3 xl:gap-0"
          >
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="h-10 w-10 shrink-0 rounded-xl bg-white dark:bg-[#2A2A35] shadow-sm flex items-center justify-center text-slate-500 dark:text-slate-400 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors border border-slate-100 dark:border-slate-800/50">
                <asset.icon className="h-4 w-4" />
              </div>
              <div className="min-w-0">
                <div className="font-semibold text-sm text-slate-900 dark:text-slate-200 truncate">
                  {asset.name}
                </div>
                <div className="text-[11px] sm:text-xs text-slate-500 dark:text-slate-400 truncate mt-0.5">
                  {asset.ip} • {asset.location}
                </div>
              </div>
            </div>
            <div className="shrink-0 flex items-center gap-3 self-end xl:self-auto">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400 hidden sm:block xl:hidden 2xl:block">
                {asset.type}
              </span>
              <span
                className={`inline-flex items-center justify-center px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wide uppercase min-w-[90px] ${asset.statusColor}`}
              >
                {asset.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
