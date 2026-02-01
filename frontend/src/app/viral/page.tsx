'use client';

/**
 * Viral tracker page
 */

import { Flame, TrendingUp, Clock, Zap } from 'lucide-react';
import { MainLayout } from '@/components/layout/MainLayout';
import { PostCard } from '@/components/posts/PostCard';
import { Card, CardTitle } from '@/components/common/Card';
import { StatsCard } from '@/components/dashboard/StatsCard';
import { useViralPosts, useTrending } from '@/hooks/useApi';
import { formatNumber } from '@/lib/utils';

export default function ViralTrackerPage() {
  const { data: viralPosts, isLoading: postsLoading } = useViralPosts({
    min_score: 50,
    limit: 20,
  });

  const { data: trending, isLoading: trendingLoading } = useTrending({
    type: 'posts',
    limit: 10,
  });

  // Calculate stats
  const avgViralScore =
    viralPosts && viralPosts.length > 0
      ? viralPosts.reduce((acc, p) => acc + (p.viral_score || 0), 0) /
        viralPosts.length
      : 0;

  const highlyViral = viralPosts?.filter((p) => (p.viral_score || 0) >= 80) || [];
  const newViral = viralPosts?.filter((p) => {
    const posted = new Date(p.posted_at);
    const now = new Date();
    const hoursSincePosted = (now.getTime() - posted.getTime()) / (1000 * 60 * 60);
    return hoursSincePosted < 24;
  }) || [];

  return (
    <MainLayout title="Viral Tracker">
      {/* Stats */}
      <div className="mb-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total Viral"
          value={viralPosts?.length || 0}
          icon={Flame}
          color="yellow"
        />
        <StatsCard
          title="Highly Viral (80+)"
          value={highlyViral.length}
          icon={Zap}
          color="red"
        />
        <StatsCard
          title="New Today"
          value={newViral.length}
          icon={Clock}
          color="green"
        />
        <StatsCard
          title="Avg Viral Score"
          value={`${avgViralScore.toFixed(0)}%`}
          icon={TrendingUp}
          color="blue"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Content - Viral Posts */}
        <div className="lg:col-span-2">
          <Card padding="none">
            <div className="border-b p-4">
              <div className="flex items-center gap-2">
                <Flame className="h-5 w-5 text-orange-500" />
                <CardTitle>Viral Posts</CardTitle>
              </div>
              <p className="mt-1 text-sm text-gray-500">
                Posts with viral score 50% or higher
              </p>
            </div>

            <div className="p-4">
              {postsLoading ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  {[...Array(6)].map((_, i) => (
                    <div
                      key={i}
                      className="h-80 animate-pulse rounded-xl bg-gray-100"
                    />
                  ))}
                </div>
              ) : viralPosts && viralPosts.length > 0 ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  {viralPosts.map((post) => (
                    <PostCard key={post.id} post={post} />
                  ))}
                </div>
              ) : (
                <div className="py-12 text-center">
                  <Flame className="mx-auto h-12 w-12 text-gray-300" />
                  <p className="mt-4 text-gray-500">No viral posts yet</p>
                  <p className="text-sm text-gray-400">
                    Viral posts will appear here when detected
                  </p>
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Sidebar - Trending */}
        <div className="space-y-6">
          {/* Top Viral */}
          <Card>
            <div className="flex items-center gap-2 mb-4">
              <Zap className="h-5 w-5 text-yellow-500" />
              <CardTitle>Top Viral</CardTitle>
            </div>

            <div className="space-y-3">
              {highlyViral.slice(0, 5).map((post, index) => (
                <div
                  key={post.id}
                  className="flex items-center gap-3 rounded-lg p-2 hover:bg-gray-50"
                >
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-orange-100 text-sm font-medium text-orange-600">
                    {index + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      @{post.celebrity?.username || 'Unknown'}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatNumber(post.like_count)} likes
                    </p>
                  </div>
                  <span className="text-sm font-bold text-orange-500">
                    {post.viral_score?.toFixed(0)}%
                  </span>
                </div>
              ))}
              {highlyViral.length === 0 && (
                <p className="text-center text-sm text-gray-500 py-4">
                  No highly viral posts
                </p>
              )}
            </div>
          </Card>

          {/* New Viral */}
          <Card>
            <div className="flex items-center gap-2 mb-4">
              <Clock className="h-5 w-5 text-green-500" />
              <CardTitle>New Today</CardTitle>
            </div>

            <div className="space-y-3">
              {newViral.slice(0, 5).map((post) => (
                <div
                  key={post.id}
                  className="flex items-center gap-3 rounded-lg p-2 hover:bg-gray-50"
                >
                  {post.thumbnail_url ? (
                    <img
                      src={post.thumbnail_url}
                      alt=""
                      className="h-10 w-10 rounded-lg object-cover"
                    />
                  ) : (
                    <div className="h-10 w-10 rounded-lg bg-gray-100" />
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      @{post.celebrity?.username || 'Unknown'}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatNumber(post.comment_count)} comments
                    </p>
                  </div>
                  <span className="text-sm font-bold text-green-500">
                    {post.viral_score?.toFixed(0)}%
                  </span>
                </div>
              ))}
              {newViral.length === 0 && (
                <p className="text-center text-sm text-gray-500 py-4">
                  No new viral posts today
                </p>
              )}
            </div>
          </Card>
        </div>
      </div>
    </MainLayout>
  );
}
