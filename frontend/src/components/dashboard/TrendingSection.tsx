'use client';

/**
 * Trending section showing viral content
 */

import Link from 'next/link';
import { TrendingUp, ArrowUpRight, ArrowDownRight, Flame } from 'lucide-react';
import { useTrending, useViralPosts } from '@/hooks/useApi';
import { Card, CardTitle } from '@/components/common/Card';
import { Badge, ViralBadge } from '@/components/common/Badge';
import { formatNumber, truncate, formatRelativeTime } from '@/lib/utils';

export function TrendingSection() {
  const { data: trending, isLoading: trendingLoading } = useTrending({ limit: 5 });
  const { data: viralPosts, isLoading: viralLoading } = useViralPosts({ limit: 5 });

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Trending Celebrities */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-[#008751]" />
            <CardTitle>Trending Celebrities</CardTitle>
          </div>
          <Link
            href="/celebrities"
            className="text-sm text-[#008751] hover:underline"
          >
            View all
          </Link>
        </div>

        {trendingLoading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 animate-pulse rounded-lg bg-gray-100" />
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {trending?.slice(0, 5).map((item, index) => (
              <div
                key={item.id}
                className="flex items-center gap-3 rounded-lg p-3 hover:bg-gray-50 transition-colors"
              >
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-gray-100 text-sm font-medium text-gray-600">
                  {index + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate">
                    {item.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    Score: {item.score.toFixed(0)}
                  </p>
                </div>
                <div className="flex items-center">
                  {item.change >= 0 ? (
                    <ArrowUpRight className="h-4 w-4 text-green-500" />
                  ) : (
                    <ArrowDownRight className="h-4 w-4 text-red-500" />
                  )}
                  <span
                    className={`text-sm font-medium ${
                      item.change >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}
                  >
                    {item.change >= 0 ? '+' : ''}
                    {item.change}%
                  </span>
                </div>
              </div>
            ))}
            {(!trending || trending.length === 0) && (
              <p className="text-center text-gray-500 py-4">
                No trending data yet
              </p>
            )}
          </div>
        )}
      </Card>

      {/* Viral Posts */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Flame className="h-5 w-5 text-orange-500" />
            <CardTitle>Viral Posts</CardTitle>
          </div>
          <Link href="/viral" className="text-sm text-[#008751] hover:underline">
            View all
          </Link>
        </div>

        {viralLoading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-16 animate-pulse rounded-lg bg-gray-100" />
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {viralPosts?.slice(0, 5).map((post) => (
              <Link
                key={post.id}
                href={`/posts/${post.id}`}
                className="block rounded-lg p-3 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start gap-3">
                  {post.thumbnail_url && (
                    <img
                      src={post.thumbnail_url}
                      alt=""
                      className="h-12 w-12 rounded-lg object-cover"
                    />
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 line-clamp-2">
                      {truncate(post.caption || 'No caption', 80)}
                    </p>
                    <div className="mt-1 flex items-center gap-2 text-xs text-gray-500">
                      <span>{formatNumber(post.like_count)} likes</span>
                      <span>•</span>
                      <span>{formatNumber(post.comment_count)} comments</span>
                      <span>•</span>
                      <span>{formatRelativeTime(post.posted_at)}</span>
                    </div>
                  </div>
                  <ViralBadge score={post.viral_score} />
                </div>
              </Link>
            ))}
            {(!viralPosts || viralPosts.length === 0) && (
              <p className="text-center text-gray-500 py-4">
                No viral posts detected yet
              </p>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}
