'use client';

/**
 * Publishing queue and scheduling page
 */

import { Send, Clock, CheckCircle, Calendar, TrendingUp } from 'lucide-react';
import { MainLayout } from '@/components/layout/MainLayout';
import { ContentCard } from '@/components/content/ContentCard';
import { Card, CardTitle } from '@/components/common/Card';
import { StatsCard } from '@/components/dashboard/StatsCard';
import { Button } from '@/components/common/Button';
import {
  usePublishingQueue,
  useOptimalTimes,
  usePublishingStats,
  useAccountInfo,
} from '@/hooks/useApi';
import { formatNumber, formatDateTime } from '@/lib/utils';

export default function PublishingPage() {
  const { data: queue, isLoading: queueLoading } = usePublishingQueue();
  const { data: optimalTimes } = useOptimalTimes(5);
  const { data: stats, isLoading: statsLoading } = usePublishingStats();
  const { data: account } = useAccountInfo();

  return (
    <MainLayout title="Publishing">
      {/* Stats */}
      <div className="mb-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Pending Review"
          value={queue?.counts.pending || 0}
          icon={Clock}
          color="yellow"
        />
        <StatsCard
          title="Approved"
          value={queue?.counts.approved || 0}
          icon={CheckCircle}
          color="blue"
        />
        <StatsCard
          title="Published"
          value={stats?.total_published || 0}
          icon={Send}
          color="green"
        />
        <StatsCard
          title="This Week"
          value={stats?.published_this_week || 0}
          icon={TrendingUp}
          color="purple"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Pending Review */}
          <Card padding="none">
            <div className="border-b p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Clock className="h-5 w-5 text-yellow-500" />
                  <CardTitle>Pending Review</CardTitle>
                  <span className="rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-700">
                    {queue?.counts.pending || 0}
                  </span>
                </div>
              </div>
            </div>

            <div className="p-4">
              {queueLoading ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  {[...Array(4)].map((_, i) => (
                    <div
                      key={i}
                      className="h-72 animate-pulse rounded-xl bg-gray-100"
                    />
                  ))}
                </div>
              ) : queue?.pending_review && queue.pending_review.length > 0 ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  {queue.pending_review.map((content) => (
                    <ContentCard key={content.id} content={content} />
                  ))}
                </div>
              ) : (
                <div className="py-8 text-center">
                  <CheckCircle className="mx-auto h-12 w-12 text-gray-300" />
                  <p className="mt-4 text-gray-500">No content pending review</p>
                </div>
              )}
            </div>
          </Card>

          {/* Approved & Scheduled */}
          <Card padding="none">
            <div className="border-b p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Calendar className="h-5 w-5 text-blue-500" />
                  <CardTitle>Scheduled</CardTitle>
                  <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
                    {queue?.counts.approved || 0}
                  </span>
                </div>
              </div>
            </div>

            <div className="p-4">
              {queueLoading ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  {[...Array(2)].map((_, i) => (
                    <div
                      key={i}
                      className="h-72 animate-pulse rounded-xl bg-gray-100"
                    />
                  ))}
                </div>
              ) : queue?.approved && queue.approved.length > 0 ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  {queue.approved.map((content) => (
                    <ContentCard key={content.id} content={content} />
                  ))}
                </div>
              ) : (
                <div className="py-8 text-center">
                  <Calendar className="mx-auto h-12 w-12 text-gray-300" />
                  <p className="mt-4 text-gray-500">No scheduled content</p>
                </div>
              )}
            </div>
          </Card>

          {/* Recently Published */}
          <Card padding="none">
            <div className="border-b p-4">
              <div className="flex items-center gap-2">
                <Send className="h-5 w-5 text-green-500" />
                <CardTitle>Recently Published</CardTitle>
              </div>
            </div>

            <div className="p-4">
              {queueLoading ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  {[...Array(2)].map((_, i) => (
                    <div
                      key={i}
                      className="h-72 animate-pulse rounded-xl bg-gray-100"
                    />
                  ))}
                </div>
              ) : queue?.recently_published && queue.recently_published.length > 0 ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  {queue.recently_published.map((content) => (
                    <ContentCard
                      key={content.id}
                      content={content}
                      showActions={false}
                    />
                  ))}
                </div>
              ) : (
                <div className="py-8 text-center">
                  <Send className="mx-auto h-12 w-12 text-gray-300" />
                  <p className="mt-4 text-gray-500">No published content yet</p>
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Account Info */}
          {account && (
            <Card>
              <CardTitle>Instagram Account</CardTitle>
              <div className="mt-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Followers</span>
                  <span className="font-semibold">
                    {formatNumber(account.follower_count)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Following</span>
                  <span className="font-semibold">
                    {formatNumber(account.following_count)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Posts</span>
                  <span className="font-semibold">
                    {formatNumber(account.media_count)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Engagement Rate</span>
                  <span className="font-semibold text-[#008751]">
                    {(account.engagement_rate * 100).toFixed(2)}%
                  </span>
                </div>
              </div>
            </Card>
          )}

          {/* Optimal Times */}
          <Card>
            <div className="flex items-center gap-2 mb-4">
              <Clock className="h-5 w-5 text-[#008751]" />
              <CardTitle>Optimal Posting Times</CardTitle>
            </div>
            <p className="text-xs text-gray-500 mb-4">
              Best times to post for Nigerian audience (Lagos timezone)
            </p>

            <div className="space-y-3">
              {optimalTimes?.suggestions.slice(0, 5).map((time, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between rounded-lg bg-gray-50 p-3"
                >
                  <div>
                    <p className="text-sm font-medium">{time.day_name}</p>
                    <p className="text-xs text-gray-500">{time.hour}:00</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-[#008751]">
                      {(time.confidence * 100).toFixed(0)}%
                    </p>
                    <p className="text-xs text-gray-500">{time.reason}</p>
                  </div>
                </div>
              ))}
              {(!optimalTimes?.suggestions || optimalTimes.suggestions.length === 0) && (
                <p className="text-center text-sm text-gray-500 py-4">
                  No optimal times calculated yet
                </p>
              )}
            </div>
          </Card>

          {/* Publishing Tips */}
          <Card>
            <CardTitle>Publishing Tips</CardTitle>
            <ul className="mt-4 space-y-2 text-sm text-gray-600">
              <li className="flex items-start gap-2">
                <span className="text-[#008751]">•</span>
                Post during peak hours (8-9 AM, 1-2 PM, 7-9 PM Lagos time)
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#008751]">•</span>
                Weekends typically see higher engagement
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#008751]">•</span>
                Use trending Nigerian hashtags
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#008751]">•</span>
                Carousels get 1.4x more engagement than single images
              </li>
            </ul>
          </Card>
        </div>
      </div>
    </MainLayout>
  );
}
