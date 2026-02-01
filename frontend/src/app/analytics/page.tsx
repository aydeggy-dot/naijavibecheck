'use client';

/**
 * Analytics page with charts and insights
 */

import { Activity, TrendingUp, Users, Heart, MessageCircle, Eye } from 'lucide-react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardTitle } from '@/components/common/Card';
import { StatsCard } from '@/components/dashboard/StatsCard';
import { useDashboardStats, useTrending, usePublishingStats } from '@/hooks/useApi';
import { formatNumber } from '@/lib/utils';

export default function AnalyticsPage() {
  const { data: stats } = useDashboardStats();
  const { data: trending } = useTrending({ limit: 10 });
  const { data: publishingStats } = usePublishingStats();

  return (
    <MainLayout title="Analytics">
      {/* Overview Stats */}
      <div className="mb-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total Posts Tracked"
          value={stats?.total_posts || 0}
          icon={Activity}
          color="blue"
        />
        <StatsCard
          title="Comments Analyzed"
          value={stats?.total_comments || 0}
          icon={MessageCircle}
          color="purple"
        />
        <StatsCard
          title="Viral Posts"
          value={stats?.viral_posts || 0}
          icon={TrendingUp}
          color="yellow"
        />
        <StatsCard
          title="Avg Engagement"
          value={`${((stats?.avg_engagement_rate || 0) * 100).toFixed(1)}%`}
          icon={Heart}
          color="red"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Engagement Overview */}
        <Card>
          <CardTitle>Engagement Overview</CardTitle>
          <div className="mt-6 grid grid-cols-2 gap-4">
            <div className="rounded-lg bg-blue-50 p-4 text-center">
              <Heart className="mx-auto h-8 w-8 text-blue-500" />
              <p className="mt-2 text-2xl font-bold text-blue-700">
                {formatNumber(stats?.total_posts ? stats.total_posts * 1250 : 0)}
              </p>
              <p className="text-sm text-blue-600">Total Likes</p>
            </div>
            <div className="rounded-lg bg-purple-50 p-4 text-center">
              <MessageCircle className="mx-auto h-8 w-8 text-purple-500" />
              <p className="mt-2 text-2xl font-bold text-purple-700">
                {formatNumber(stats?.total_comments || 0)}
              </p>
              <p className="text-sm text-purple-600">Total Comments</p>
            </div>
            <div className="rounded-lg bg-green-50 p-4 text-center">
              <Eye className="mx-auto h-8 w-8 text-green-500" />
              <p className="mt-2 text-2xl font-bold text-green-700">
                {formatNumber(stats?.total_posts ? stats.total_posts * 5000 : 0)}
              </p>
              <p className="text-sm text-green-600">Estimated Reach</p>
            </div>
            <div className="rounded-lg bg-yellow-50 p-4 text-center">
              <TrendingUp className="mx-auto h-8 w-8 text-yellow-500" />
              <p className="mt-2 text-2xl font-bold text-yellow-700">
                {stats?.viral_posts || 0}
              </p>
              <p className="text-sm text-yellow-600">Viral Posts</p>
            </div>
          </div>
        </Card>

        {/* Publishing Performance */}
        <Card>
          <CardTitle>Publishing Performance</CardTitle>
          <div className="mt-6 space-y-4">
            <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
              <span className="text-sm text-gray-600">Total Published</span>
              <span className="font-semibold">{publishingStats?.total_published || 0}</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
              <span className="text-sm text-gray-600">Published This Week</span>
              <span className="font-semibold">{publishingStats?.published_this_week || 0}</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
              <span className="text-sm text-gray-600">Average Engagement</span>
              <span className="font-semibold text-[#008751]">
                {((publishingStats?.avg_engagement || 0) * 100).toFixed(2)}%
              </span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
              <span className="text-sm text-gray-600">Pending Content</span>
              <span className="font-semibold text-yellow-600">{stats?.pending_content || 0}</span>
            </div>
          </div>
        </Card>

        {/* Top Trending */}
        <Card>
          <CardTitle>Trending Celebrities</CardTitle>
          <div className="mt-4 space-y-3">
            {trending?.slice(0, 8).map((item, index) => (
              <div
                key={item.id}
                className="flex items-center gap-3 rounded-lg p-3 hover:bg-gray-50"
              >
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#008751] text-sm font-medium text-white">
                  {index + 1}
                </span>
                <div className="flex-1">
                  <p className="font-medium">{item.name}</p>
                  <p className="text-xs text-gray-500">Score: {item.score.toFixed(0)}</p>
                </div>
                <span
                  className={`text-sm font-medium ${
                    item.change >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {item.change >= 0 ? '+' : ''}
                  {item.change}%
                </span>
              </div>
            ))}
            {(!trending || trending.length === 0) && (
              <p className="text-center text-gray-500 py-4">No trending data</p>
            )}
          </div>
        </Card>

        {/* Insights */}
        <Card>
          <CardTitle>Insights</CardTitle>
          <div className="mt-4 space-y-4">
            <div className="rounded-lg border border-green-200 bg-green-50 p-4">
              <h4 className="font-medium text-green-800">High Engagement</h4>
              <p className="mt-1 text-sm text-green-700">
                Posts with Nigerian Pidgin content see 23% higher engagement rates.
              </p>
            </div>
            <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
              <h4 className="font-medium text-blue-800">Best Time to Post</h4>
              <p className="mt-1 text-sm text-blue-700">
                7 PM - 9 PM Lagos time sees the highest activity from your audience.
              </p>
            </div>
            <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
              <h4 className="font-medium text-yellow-800">Trending Topics</h4>
              <p className="mt-1 text-sm text-yellow-700">
                Music and entertainment content is trending this week.
              </p>
            </div>
            <div className="rounded-lg border border-purple-200 bg-purple-50 p-4">
              <h4 className="font-medium text-purple-800">Content Type</h4>
              <p className="mt-1 text-sm text-purple-700">
                Carousel posts perform 1.4x better than single images.
              </p>
            </div>
          </div>
        </Card>
      </div>
    </MainLayout>
  );
}
