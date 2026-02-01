'use client';

/**
 * Generated content listing page
 */

import { useState } from 'react';
import { Image, Filter, Plus } from 'lucide-react';
import { MainLayout } from '@/components/layout/MainLayout';
import { ContentCard } from '@/components/content/ContentCard';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { useGeneratedContent } from '@/hooks/useApi';

const statusFilters = [
  { value: '', label: 'All' },
  { value: 'draft', label: 'Draft' },
  { value: 'pending_review', label: 'Pending Review' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'published', label: 'Published' },
];

const typeFilters = [
  { value: '', label: 'All Types' },
  { value: 'image', label: 'Image' },
  { value: 'carousel', label: 'Carousel' },
  { value: 'video', label: 'Video' },
  { value: 'reel', label: 'Reel' },
];

export default function ContentPage() {
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');

  const { data, isLoading, error } = useGeneratedContent({
    status: statusFilter || undefined,
    content_type: typeFilter || undefined,
    limit: 50,
  });

  const content = data?.items || [];

  return (
    <MainLayout title="Generated Content">
      {/* Header Actions */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        {/* Filters */}
        <div className="flex items-center gap-3">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border bg-white px-3 py-2 text-sm focus:border-[#008751] focus:outline-none focus:ring-1 focus:ring-[#008751]"
          >
            {statusFilters.map((filter) => (
              <option key={filter.value} value={filter.value}>
                {filter.label}
              </option>
            ))}
          </select>

          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="rounded-lg border bg-white px-3 py-2 text-sm focus:border-[#008751] focus:outline-none focus:ring-1 focus:ring-[#008751]"
          >
            {typeFilters.map((filter) => (
              <option key={filter.value} value={filter.value}>
                {filter.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="mb-6 flex items-center gap-4 text-sm text-gray-500">
        <div className="flex items-center gap-2">
          <Image className="h-4 w-4" />
          <span>
            {content.length} {content.length === 1 ? 'item' : 'items'}
          </span>
        </div>
        {data?.total && data.total > content.length && (
          <span>({data.total} total)</span>
        )}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {[...Array(8)].map((_, i) => (
            <div
              key={i}
              className="h-72 animate-pulse rounded-xl bg-gray-100"
            />
          ))}
        </div>
      )}

      {/* Error State */}
      {error && (
        <Card className="text-center py-12">
          <p className="text-red-500">Failed to load content</p>
          <p className="text-sm text-gray-500 mt-2">
            {error.message || 'Please try again later'}
          </p>
        </Card>
      )}

      {/* Empty State */}
      {!isLoading && !error && content.length === 0 && (
        <Card className="text-center py-12">
          <Image className="mx-auto h-12 w-12 text-gray-300" />
          <p className="mt-4 text-gray-500">No content found</p>
          <p className="text-sm text-gray-400 mt-1">
            {statusFilter || typeFilter
              ? 'Try adjusting your filters'
              : 'Generated content will appear here'}
          </p>
        </Card>
      )}

      {/* Content Grid */}
      {!isLoading && !error && content.length > 0 && (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {content.map((item) => (
            <ContentCard key={item.id} content={item} />
          ))}
        </div>
      )}
    </MainLayout>
  );
}
