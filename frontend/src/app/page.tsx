'use client';

/**
 * Main Dashboard Page
 */

import {
  Users,
  FileText,
  MessageSquare,
  Flame,
  Image,
  Send,
  TrendingUp,
} from 'lucide-react';
import { MainLayout } from '@/components/layout/MainLayout';
import { StatsCard } from '@/components/dashboard/StatsCard';
import { TrendingSection } from '@/components/dashboard/TrendingSection';
import { RecentActivity } from '@/components/dashboard/RecentActivity';
import { useDashboardStats } from '@/hooks/useApi';

export default function DashboardPage() {
  const { data: stats, isLoading } = useDashboardStats();

  return (
    <MainLayout title="Dashboard">
      {/* Stats Grid */}
      <div className="mb-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Celebrities"
          value={stats?.total_celebrities || 0}
          icon={Users}
          color="green"
          change={12}
          changeLabel="this month"
        />
        <StatsCard
          title="Total Posts"
          value={stats?.total_posts || 0}
          icon={FileText}
          color="blue"
          change={8}
          changeLabel="this week"
        />
        <StatsCard
          title="Comments Analyzed"
          value={stats?.total_comments || 0}
          icon={MessageSquare}
          color="purple"
        />
        <StatsCard
          title="Viral Posts"
          value={stats?.viral_posts || 0}
          icon={Flame}
          color="yellow"
        />
      </div>

      {/* Secondary Stats */}
      <div className="mb-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Posts Today"
          value={stats?.posts_today || 0}
          icon={TrendingUp}
          color="green"
        />
        <StatsCard
          title="Pending Content"
          value={stats?.pending_content || 0}
          icon={Image}
          color="yellow"
        />
        <StatsCard
          title="Published Today"
          value={stats?.published_today || 0}
          icon={Send}
          color="blue"
        />
        <StatsCard
          title="Avg Engagement"
          value={`${((stats?.avg_engagement_rate || 0) * 100).toFixed(1)}%`}
          icon={TrendingUp}
          color="purple"
        />
      </div>

      {/* Trending Section */}
      <div className="mb-8">
        <TrendingSection />
      </div>

      {/* Recent Activity */}
      <RecentActivity />
    </MainLayout>
  );
}
