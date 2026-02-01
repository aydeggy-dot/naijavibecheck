/**
 * Stats card for dashboard metrics
 */

import { LucideIcon } from 'lucide-react';
import { cn, formatNumber } from '@/lib/utils';

interface StatsCardProps {
  title: string;
  value: number | string;
  icon: LucideIcon;
  change?: number;
  changeLabel?: string;
  color?: 'green' | 'blue' | 'yellow' | 'red' | 'purple';
}

const colorClasses = {
  green: {
    bg: 'bg-green-50',
    icon: 'bg-green-100 text-green-600',
    text: 'text-green-600',
  },
  blue: {
    bg: 'bg-blue-50',
    icon: 'bg-blue-100 text-blue-600',
    text: 'text-blue-600',
  },
  yellow: {
    bg: 'bg-yellow-50',
    icon: 'bg-yellow-100 text-yellow-600',
    text: 'text-yellow-600',
  },
  red: {
    bg: 'bg-red-50',
    icon: 'bg-red-100 text-red-600',
    text: 'text-red-600',
  },
  purple: {
    bg: 'bg-purple-50',
    icon: 'bg-purple-100 text-purple-600',
    text: 'text-purple-600',
  },
};

export function StatsCard({
  title,
  value,
  icon: Icon,
  change,
  changeLabel,
  color = 'green',
}: StatsCardProps) {
  const colors = colorClasses[color];
  const formattedValue = typeof value === 'number' ? formatNumber(value) : value;

  return (
    <div className={cn('rounded-xl p-6 border border-gray-100 bg-white')}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">{formattedValue}</p>
          {change !== undefined && (
            <p className="mt-2 flex items-center text-sm">
              <span
                className={cn(
                  'font-medium',
                  change >= 0 ? 'text-green-600' : 'text-red-600'
                )}
              >
                {change >= 0 ? '+' : ''}
                {change}%
              </span>
              {changeLabel && (
                <span className="ml-1 text-gray-500">{changeLabel}</span>
              )}
            </p>
          )}
        </div>
        <div className={cn('rounded-lg p-3', colors.icon)}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </div>
  );
}
