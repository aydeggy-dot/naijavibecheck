'use client';

/**
 * Sidebar navigation component
 */

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Users,
  FileText,
  TrendingUp,
  Image,
  Send,
  Settings,
  Activity,
  BarChart3,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Celebrities', href: '/celebrities', icon: Users },
  { name: 'Posts', href: '/posts', icon: FileText },
  { name: 'Viral Tracker', href: '/viral', icon: TrendingUp },
  { name: 'Analysis', href: '/analysis', icon: BarChart3 },
  { name: 'Content', href: '/content', icon: Image },
  { name: 'Publishing', href: '/publishing', icon: Send },
  { name: 'Analytics', href: '/analytics', icon: Activity },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex h-full w-64 flex-col bg-[#1A1A2E] text-white">
      {/* Logo */}
      <div className="flex h-16 items-center justify-center border-b border-gray-700">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#008751]">
            <span className="text-xl font-bold">NV</span>
          </div>
          <span className="text-xl font-bold">
            Naija<span className="text-[#008751]">Vibe</span>Check
          </span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href ||
            (item.href !== '/' && pathname.startsWith(item.href));

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-[#008751] text-white'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-gray-700 p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#008751]">
            <span className="text-sm font-bold">NG</span>
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium">Lagos Time</p>
            <p className="text-xs text-gray-400">WAT (UTC+1)</p>
          </div>
        </div>
      </div>
    </div>
  );
}
