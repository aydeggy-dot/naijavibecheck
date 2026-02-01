'use client';

/**
 * Posts listing page
 */

import { useState } from 'react';
import { Search, Filter, FileText, SlidersHorizontal } from 'lucide-react';
import { MainLayout } from '@/components/layout/MainLayout';
import { PostCard } from '@/components/posts/PostCard';
import { Card } from '@/components/common/Card';
import { usePosts } from '@/hooks/useApi';

export default function PostsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [showViralOnly, setShowViralOnly] = useState(false);
  const [minViralScore, setMinViralScore] = useState<number | undefined>(undefined);

  const { data, isLoading, error } = usePosts({
    is_viral: showViralOnly || undefined,
    min_viral_score: minViralScore,
    limit: 50,
  });

  const posts = data?.items || [];

  return (
    <MainLayout title="Posts">
      {/* Header Actions */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search posts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border bg-white py-2 pl-10 pr-4 text-sm focus:border-[#008751] focus:outline-none focus:ring-1 focus:ring-[#008751]"
          />
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={showViralOnly}
              onChange={(e) => setShowViralOnly(e.target.checked)}
              className="rounded border-gray-300 text-[#008751] focus:ring-[#008751]"
            />
            <span>Viral only</span>
          </label>

          <select
            value={minViralScore ?? ''}
            onChange={(e) =>
              setMinViralScore(e.target.value ? Number(e.target.value) : undefined)
            }
            className="rounded-lg border bg-white px-3 py-2 text-sm focus:border-[#008751] focus:outline-none focus:ring-1 focus:ring-[#008751]"
          >
            <option value="">All scores</option>
            <option value="40">Score 40+</option>
            <option value="60">Score 60+</option>
            <option value="80">Score 80+</option>
          </select>
        </div>
      </div>

      {/* Stats */}
      <div className="mb-6 flex items-center gap-4 text-sm text-gray-500">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4" />
          <span>
            {posts.length} {posts.length === 1 ? 'post' : 'posts'}
          </span>
        </div>
        {data?.total && data.total > posts.length && (
          <span>({data.total} total)</span>
        )}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(9)].map((_, i) => (
            <div
              key={i}
              className="h-80 animate-pulse rounded-xl bg-gray-100"
            />
          ))}
        </div>
      )}

      {/* Error State */}
      {error && (
        <Card className="text-center py-12">
          <p className="text-red-500">Failed to load posts</p>
          <p className="text-sm text-gray-500 mt-2">
            {error.message || 'Please try again later'}
          </p>
        </Card>
      )}

      {/* Empty State */}
      {!isLoading && !error && posts.length === 0 && (
        <Card className="text-center py-12">
          <FileText className="mx-auto h-12 w-12 text-gray-300" />
          <p className="mt-4 text-gray-500">No posts found</p>
          <p className="text-sm text-gray-400 mt-1">
            {showViralOnly || minViralScore
              ? 'Try adjusting your filters'
              : 'Posts will appear here once celebrities are scraped'}
          </p>
        </Card>
      )}

      {/* Posts Grid */}
      {!isLoading && !error && posts.length > 0 && (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {posts.map((post) => (
            <PostCard key={post.id} post={post} />
          ))}
        </div>
      )}
    </MainLayout>
  );
}
