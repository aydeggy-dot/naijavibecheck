'use client';

/**
 * Celebrity card component
 */

import Link from 'next/link';
import { Instagram, RefreshCw, MoreVertical, ExternalLink } from 'lucide-react';
import { Celebrity } from '@/types';
import { Badge } from '@/components/common/Badge';
import { Button } from '@/components/common/Button';
import { formatNumber, formatRelativeTime, getInitials } from '@/lib/utils';
import { useScrapeCelebrity } from '@/hooks/useApi';

interface CelebrityCardProps {
  celebrity: Celebrity;
}

export function CelebrityCard({ celebrity }: CelebrityCardProps) {
  const scrapeMutation = useScrapeCelebrity();

  const handleScrape = () => {
    scrapeMutation.mutate(celebrity.id);
  };

  return (
    <div className="rounded-xl bg-white border border-gray-100 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-4">
        {/* Avatar */}
        {celebrity.profile_pic_url ? (
          <img
            src={celebrity.profile_pic_url}
            alt={celebrity.display_name || celebrity.username}
            className="h-16 w-16 rounded-full object-cover"
          />
        ) : (
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[#008751] text-white text-xl font-bold">
            {getInitials(celebrity.display_name || celebrity.username)}
          </div>
        )}

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <Link
              href={`/celebrities/${celebrity.id}`}
              className="text-lg font-semibold text-gray-900 hover:text-[#008751] truncate"
            >
              {celebrity.display_name || celebrity.username}
            </Link>
            {celebrity.is_active && (
              <span className="h-2 w-2 rounded-full bg-green-500" title="Active" />
            )}
          </div>

          <div className="flex items-center gap-2 text-gray-500">
            <Instagram className="h-4 w-4" />
            <span className="text-sm">@{celebrity.username}</span>
            {celebrity.category && (
              <Badge variant="secondary">{celebrity.category}</Badge>
            )}
          </div>

          {/* Stats */}
          <div className="mt-3 flex items-center gap-4 text-sm">
            <div>
              <span className="font-semibold text-gray-900">
                {formatNumber(celebrity.follower_count)}
              </span>
              <span className="ml-1 text-gray-500">followers</span>
            </div>
            <div>
              <span className="font-semibold text-gray-900">
                {formatNumber(celebrity.post_count)}
              </span>
              <span className="ml-1 text-gray-500">posts</span>
            </div>
          </div>

          {/* Last scraped */}
          <p className="mt-2 text-xs text-gray-400">
            Last scraped:{' '}
            {celebrity.last_scraped_at
              ? formatRelativeTime(celebrity.last_scraped_at)
              : 'Never'}
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleScrape}
            isLoading={scrapeMutation.isPending}
            leftIcon={<RefreshCw className="h-4 w-4" />}
          >
            Scrape
          </Button>
          <a
            href={`https://instagram.com/${celebrity.username}`}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-lg p-2 hover:bg-gray-100"
            title="View on Instagram"
          >
            <ExternalLink className="h-4 w-4 text-gray-500" />
          </a>
        </div>
      </div>

      {/* Bio */}
      {celebrity.bio && (
        <p className="mt-4 text-sm text-gray-600 line-clamp-2">{celebrity.bio}</p>
      )}
    </div>
  );
}
