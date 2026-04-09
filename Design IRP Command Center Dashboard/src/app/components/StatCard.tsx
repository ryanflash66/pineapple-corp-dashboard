import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  subtitle?: string;
  trend?: string;
  accentColor?: string;
}

export function StatCard({ title, value, icon: Icon, subtitle, trend, accentColor = 'border-amber-500' }: StatCardProps) {
  return (
    <div className={`bg-card rounded-lg p-5 border-l-4 ${accentColor} hover:bg-muted transition-colors shadow-sm`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <p className="text-muted-foreground text-sm mb-1">{title}</p>
          <p className="text-3xl font-semibold text-foreground">{value}</p>
        </div>
        <div className="p-2 bg-secondary rounded-lg">
          <Icon className="w-5 h-5 text-secondary-foreground" />
        </div>
      </div>
      {subtitle && (
        <p className="text-xs text-muted-foreground mt-2">{subtitle}</p>
      )}
      {trend && (
        <p className="text-xs text-green-500 dark:text-green-400 mt-1">{trend}</p>
      )}
    </div>
  );
}