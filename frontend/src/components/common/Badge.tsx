/**
 * Badge component for status indicators
 */

import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'info' | 'secondary';

interface BadgeProps {
  children: ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

const variantClasses: Record<BadgeVariant, string> = {
  default: 'bg-gray-100 text-gray-700',
  success: 'bg-green-100 text-green-700',
  warning: 'bg-yellow-100 text-yellow-700',
  error: 'bg-red-100 text-red-700',
  info: 'bg-blue-100 text-blue-700',
  secondary: 'bg-purple-100 text-purple-700',
};

export function Badge({ children, variant = 'default', className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        variantClasses[variant],
        className
      )}
    >
      {children}
    </span>
  );
}

// Pre-configured badges for common use cases
export function StatusBadge({ status }: { status: string }) {
  const getVariant = (): BadgeVariant => {
    switch (status?.toLowerCase()) {
      case 'published':
        return 'success';
      case 'approved':
        return 'info';
      case 'pending_review':
        return 'warning';
      case 'rejected':
        return 'error';
      case 'draft':
      default:
        return 'default';
    }
  };

  const formatStatus = (s: string) => {
    return s.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
  };

  return <Badge variant={getVariant()}>{formatStatus(status)}</Badge>;
}

export function SentimentBadge({ sentiment }: { sentiment: string }) {
  const getVariant = (): BadgeVariant => {
    switch (sentiment?.toLowerCase()) {
      case 'positive':
        return 'success';
      case 'negative':
        return 'error';
      case 'mixed':
        return 'warning';
      case 'neutral':
      default:
        return 'default';
    }
  };

  return <Badge variant={getVariant()}>{sentiment}</Badge>;
}

export function ViralBadge({ score }: { score: number | null | undefined }) {
  if (score === null || score === undefined) return null;

  const getVariant = (): BadgeVariant => {
    if (score >= 80) return 'success';
    if (score >= 60) return 'info';
    if (score >= 40) return 'warning';
    return 'default';
  };

  return (
    <Badge variant={getVariant()}>
      {score >= 70 ? '🔥' : ''} {score.toFixed(0)}%
    </Badge>
  );
}
