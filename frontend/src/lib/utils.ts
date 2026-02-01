/**
 * Utility functions for NaijaVibeCheck
 */

import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format, formatDistanceToNow, parseISO } from 'date-fns';

// Tailwind class merging utility
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Format numbers with K/M suffixes
export function formatNumber(num: number | null | undefined): string {
  if (num === null || num === undefined) return '0';
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1).replace(/\.0$/, '') + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1).replace(/\.0$/, '') + 'K';
  }
  return num.toString();
}

// Format percentage
export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return '0%';
  return `${(value * 100).toFixed(1)}%`;
}

// Format date
export function formatDate(date: string | Date | null | undefined): string {
  if (!date) return 'N/A';
  const d = typeof date === 'string' ? parseISO(date) : date;
  return format(d, 'MMM d, yyyy');
}

// Format datetime
export function formatDateTime(date: string | Date | null | undefined): string {
  if (!date) return 'N/A';
  const d = typeof date === 'string' ? parseISO(date) : date;
  return format(d, 'MMM d, yyyy h:mm a');
}

// Format relative time
export function formatRelativeTime(date: string | Date | null | undefined): string {
  if (!date) return 'N/A';
  const d = typeof date === 'string' ? parseISO(date) : date;
  return formatDistanceToNow(d, { addSuffix: true });
}

// Get sentiment color
export function getSentimentColor(sentiment: string): string {
  switch (sentiment?.toLowerCase()) {
    case 'positive':
      return 'text-green-600 bg-green-100';
    case 'negative':
      return 'text-red-600 bg-red-100';
    case 'neutral':
      return 'text-gray-600 bg-gray-100';
    case 'mixed':
      return 'text-yellow-600 bg-yellow-100';
    default:
      return 'text-gray-600 bg-gray-100';
  }
}

// Get status color
export function getStatusColor(status: string): string {
  switch (status?.toLowerCase()) {
    case 'published':
      return 'text-green-600 bg-green-100';
    case 'approved':
      return 'text-blue-600 bg-blue-100';
    case 'pending_review':
      return 'text-yellow-600 bg-yellow-100';
    case 'draft':
      return 'text-gray-600 bg-gray-100';
    case 'rejected':
      return 'text-red-600 bg-red-100';
    default:
      return 'text-gray-600 bg-gray-100';
  }
}

// Get viral score color
export function getViralScoreColor(score: number | null | undefined): string {
  if (score === null || score === undefined) return 'text-gray-500';
  if (score >= 80) return 'text-green-600';
  if (score >= 60) return 'text-blue-600';
  if (score >= 40) return 'text-yellow-600';
  return 'text-gray-500';
}

// Truncate text
export function truncate(text: string | null | undefined, length: number = 100): string {
  if (!text) return '';
  if (text.length <= length) return text;
  return text.substring(0, length).trim() + '...';
}

// Generate initials from name
export function getInitials(name: string | null | undefined): string {
  if (!name) return '??';
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .substring(0, 2);
}

// Platform icon name
export function getPlatformIcon(platform: string): string {
  switch (platform?.toLowerCase()) {
    case 'instagram':
      return 'instagram';
    case 'twitter':
    case 'x':
      return 'twitter';
    case 'tiktok':
      return 'music-2';
    default:
      return 'globe';
  }
}

// NaijaVibeCheck brand colors
export const brandColors = {
  primary: {
    green: '#008751',
    white: '#FFFFFF',
  },
  accent: {
    gold: '#FFD700',
    coral: '#FF6B6B',
  },
  neutral: {
    dark: '#1A1A2E',
    gray: '#4A4A5A',
    light: '#F5F5F5',
  },
};
