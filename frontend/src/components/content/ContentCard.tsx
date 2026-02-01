'use client';

/**
 * Generated content card component
 */

import Link from 'next/link';
import {
  Image,
  Layers,
  Video,
  Clock,
  CheckCircle,
  XCircle,
  Send,
  MoreVertical,
} from 'lucide-react';
import { GeneratedContent } from '@/types';
import { StatusBadge } from '@/components/common/Badge';
import { Button } from '@/components/common/Button';
import { formatRelativeTime, formatDateTime, truncate } from '@/lib/utils';
import { useApproveContent, useRejectContent, usePublishNow } from '@/hooks/useApi';

interface ContentCardProps {
  content: GeneratedContent;
  showActions?: boolean;
}

const contentTypeIcons = {
  image: Image,
  carousel: Layers,
  video: Video,
  reel: Video,
};

export function ContentCard({ content, showActions = true }: ContentCardProps) {
  const approveMutation = useApproveContent();
  const rejectMutation = useRejectContent();
  const publishMutation = usePublishNow();

  const Icon = contentTypeIcons[content.content_type] || Image;

  const handleApprove = () => {
    approveMutation.mutate({ contentId: content.id });
  };

  const handleReject = () => {
    rejectMutation.mutate({ contentId: content.id });
  };

  const handlePublishNow = () => {
    publishMutation.mutate(content.id);
  };

  const isPending = content.status === 'pending_review';
  const isApproved = content.status === 'approved';
  const isPublished = content.status === 'published';

  return (
    <div className="rounded-xl bg-white border border-gray-100 overflow-hidden hover:shadow-md transition-shadow">
      {/* Preview */}
      <div className="relative">
        {content.thumbnail_url ? (
          <img
            src={content.thumbnail_url}
            alt={content.title}
            className="h-48 w-full object-cover"
          />
        ) : (
          <div className="h-48 w-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <Icon className="h-12 w-12 text-white/80" />
          </div>
        )}

        {/* Content type badge */}
        <div className="absolute top-3 left-3">
          <div className="flex items-center gap-1 rounded-full bg-black/50 px-2 py-1 text-xs font-medium text-white">
            <Icon className="h-3 w-3" />
            {content.content_type}
          </div>
        </div>

        {/* Status */}
        <div className="absolute top-3 right-3">
          <StatusBadge status={content.status} />
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        <Link href={`/content/${content.id}`}>
          <h3 className="font-semibold text-gray-900 hover:text-[#008751] line-clamp-1">
            {content.title}
          </h3>
        </Link>

        {content.caption && (
          <p className="mt-2 text-sm text-gray-600 line-clamp-2">
            {truncate(content.caption, 100)}
          </p>
        )}

        {/* Hashtags */}
        {content.hashtags && content.hashtags.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {content.hashtags.slice(0, 3).map((tag, i) => (
              <span
                key={i}
                className="text-xs text-[#008751]"
              >
                #{tag}
              </span>
            ))}
            {content.hashtags.length > 3 && (
              <span className="text-xs text-gray-400">
                +{content.hashtags.length - 3} more
              </span>
            )}
          </div>
        )}

        {/* Schedule info */}
        <div className="mt-3 flex items-center gap-2 text-xs text-gray-500">
          <Clock className="h-3 w-3" />
          {content.scheduled_for ? (
            <span>Scheduled: {formatDateTime(content.scheduled_for)}</span>
          ) : content.published_at ? (
            <span>Published: {formatRelativeTime(content.published_at)}</span>
          ) : (
            <span>Created: {formatRelativeTime(content.created_at)}</span>
          )}
        </div>

        {/* Actions */}
        {showActions && (isPending || isApproved) && (
          <div className="mt-4 flex items-center gap-2 border-t pt-4">
            {isPending && (
              <>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleApprove}
                  isLoading={approveMutation.isPending}
                  leftIcon={<CheckCircle className="h-4 w-4" />}
                  className="flex-1"
                >
                  Approve
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleReject}
                  isLoading={rejectMutation.isPending}
                  leftIcon={<XCircle className="h-4 w-4" />}
                >
                  Reject
                </Button>
              </>
            )}

            {isApproved && (
              <Button
                variant="primary"
                size="sm"
                onClick={handlePublishNow}
                isLoading={publishMutation.isPending}
                leftIcon={<Send className="h-4 w-4" />}
                className="flex-1"
              >
                Publish Now
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
