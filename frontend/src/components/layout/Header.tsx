'use client';

/**
 * Header component with status indicators
 */

import { Bell, RefreshCw, Search, Wifi, WifiOff } from 'lucide-react';
import { useHealth } from '@/hooks/useApi';
import { cn } from '@/lib/utils';

interface HeaderProps {
  title?: string;
}

export function Header({ title = 'Dashboard' }: HeaderProps) {
  const { data: health, isLoading, isError, refetch } = useHealth();

  const isConnected = health?.status === 'ok' && health?.database === 'connected';

  return (
    <header className="flex h-16 items-center justify-between border-b bg-white px-6">
      {/* Title */}
      <h1 className="text-2xl font-bold text-gray-900">{title}</h1>

      {/* Actions */}
      <div className="flex items-center gap-4">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search..."
            className="w-64 rounded-lg border bg-gray-50 py-2 pl-10 pr-4 text-sm focus:border-[#008751] focus:outline-none focus:ring-1 focus:ring-[#008751]"
          />
        </div>

        {/* Refresh */}
        <button
          onClick={() => refetch()}
          className="rounded-lg p-2 hover:bg-gray-100"
          title="Refresh status"
        >
          <RefreshCw className={cn('h-5 w-5 text-gray-600', isLoading && 'animate-spin')} />
        </button>

        {/* Notifications */}
        <button className="relative rounded-lg p-2 hover:bg-gray-100">
          <Bell className="h-5 w-5 text-gray-600" />
          <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-red-500" />
        </button>

        {/* Connection Status */}
        <div
          className={cn(
            'flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium',
            isLoading
              ? 'bg-gray-100 text-gray-600'
              : isConnected
              ? 'bg-green-100 text-green-700'
              : 'bg-red-100 text-red-700'
          )}
        >
          {isLoading ? (
            <>
              <RefreshCw className="h-4 w-4 animate-spin" />
              <span>Connecting...</span>
            </>
          ) : isConnected ? (
            <>
              <Wifi className="h-4 w-4" />
              <span>Connected</span>
            </>
          ) : (
            <>
              <WifiOff className="h-4 w-4" />
              <span>Disconnected</span>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
