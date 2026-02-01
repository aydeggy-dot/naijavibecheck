'use client';

/**
 * Celebrities listing page
 */

import { useState } from 'react';
import { Plus, Search, Filter, Users } from 'lucide-react';
import { MainLayout } from '@/components/layout/MainLayout';
import { CelebrityCard } from '@/components/celebrities/CelebrityCard';
import { Button } from '@/components/common/Button';
import { Card } from '@/components/common/Card';
import { useCelebrities } from '@/hooks/useApi';

const categories = [
  'All',
  'Music',
  'Actor',
  'Comedian',
  'Influencer',
  'Sports',
  'Politics',
  'Other',
];

export default function CelebritiesPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [searchQuery, setSearchQuery] = useState('');

  const { data, isLoading, error } = useCelebrities({
    category: selectedCategory === 'All' ? undefined : selectedCategory,
    limit: 50,
  });

  const celebrities = data?.items || [];

  // Filter by search query
  const filteredCelebrities = celebrities.filter((celebrity) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      celebrity.username.toLowerCase().includes(query) ||
      celebrity.display_name?.toLowerCase().includes(query)
    );
  });

  return (
    <MainLayout title="Celebrities">
      {/* Header Actions */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search celebrities..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border bg-white py-2 pl-10 pr-4 text-sm focus:border-[#008751] focus:outline-none focus:ring-1 focus:ring-[#008751]"
          />
        </div>

        {/* Add Button */}
        <Button leftIcon={<Plus className="h-4 w-4" />}>Add Celebrity</Button>
      </div>

      {/* Category Filter */}
      <div className="mb-6 flex flex-wrap gap-2">
        {categories.map((category) => (
          <button
            key={category}
            onClick={() => setSelectedCategory(category)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
              selectedCategory === category
                ? 'bg-[#008751] text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {category}
          </button>
        ))}
      </div>

      {/* Stats */}
      <div className="mb-6 flex items-center gap-4 text-sm text-gray-500">
        <div className="flex items-center gap-2">
          <Users className="h-4 w-4" />
          <span>
            {filteredCelebrities.length} {filteredCelebrities.length === 1 ? 'celebrity' : 'celebrities'}
          </span>
        </div>
        {data?.total && data.total > filteredCelebrities.length && (
          <span>({data.total} total)</span>
        )}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="grid gap-4 md:grid-cols-2">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="h-40 animate-pulse rounded-xl bg-gray-100"
            />
          ))}
        </div>
      )}

      {/* Error State */}
      {error && (
        <Card className="text-center py-12">
          <p className="text-red-500">Failed to load celebrities</p>
          <p className="text-sm text-gray-500 mt-2">
            {error.message || 'Please try again later'}
          </p>
        </Card>
      )}

      {/* Empty State */}
      {!isLoading && !error && filteredCelebrities.length === 0 && (
        <Card className="text-center py-12">
          <Users className="mx-auto h-12 w-12 text-gray-300" />
          <p className="mt-4 text-gray-500">No celebrities found</p>
          <p className="text-sm text-gray-400 mt-1">
            {searchQuery
              ? 'Try adjusting your search'
              : 'Add your first celebrity to get started'}
          </p>
          <Button className="mt-4" leftIcon={<Plus className="h-4 w-4" />}>
            Add Celebrity
          </Button>
        </Card>
      )}

      {/* Celebrity Grid */}
      {!isLoading && !error && filteredCelebrities.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2">
          {filteredCelebrities.map((celebrity) => (
            <CelebrityCard key={celebrity.id} celebrity={celebrity} />
          ))}
        </div>
      )}
    </MainLayout>
  );
}
