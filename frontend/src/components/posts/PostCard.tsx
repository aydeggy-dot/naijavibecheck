'use client';

/**
 * Post card component
 */

import Link from 'next/link';
import {
  Heart,
  MessageCircle,
  Share2,
  Eye,
  Flame,
  BarChart3,
  ExternalLink,
} from 'lucide-react';
import { Post } from '@/types';
import { Badge, ViralBadge } from '@/components/common/Badge';
import { Button } from '@/components/common/Button';
import {
  formatNumber,
  formatRelativeTime,
  truncate,
  formatPercent,
} from '@/lib/utils';

interface PostCardProps {
  post: Post;
  showCelebrity?: boolean;
}

export function PostCard({ post, showCelebrity = true }: PostCardProps) {
  return (
    <div className="rounded-xl bg-white border border-gray-100 overflow-hidden hover:shadow-md transition-shadow">
      {/* Media Preview */}
      <div className="relative">
        {post.thumbnail_url ? (
          <img
            src={post.thumbnail_url}
            alt=""
            className="h-48 w-full object-cover"
          />
        ) : (
          <div className="h-48 w-full bg-gradient-to-br from-[#008751] to-[#006b40] flex items-center justify-center">
            <span className="text-white text-lg font-bold">No Image</span>
          </div>
        )}

        {/* Post type badge */}
        <div className="absolute top-3 left-3">
          <Badge variant="default" className="bg-black/50 text-white border-0">
            {post.post_type}
          </Badge>
        </div>

        {/* Viral indicator */}
        {post.is_viral && (
          <div className="absolute top-3 right-3">
            <div className="flex items-center gap-1 rounded-full bg-orange-500 px-2 py-1 text-xs font-medium text-white">
              <Flame className="h-3 w-3" />
              Viral
            </div>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Celebrity info */}
        {showCelebrity && post.celebrity && (
          <Link
            href={`/celebrities/${post.celebrity.id}`}
            className="mb-2 flex items-center gap-2 text-sm text-gray-600 hover:text-[#008751]"
          >
            {post.celebrity.profile_pic_url ? (
              <img
                src={post.celebrity.profile_pic_url}
                alt=""
                className="h-6 w-6 rounded-full object-cover"
              />
            ) : (
              <div className="h-6 w-6 rounded-full bg-gray-200" />
            )}
            <span className="font-medium">
              @{post.celebrity.username}
            </span>
          </Link>
        )}

        {/* Caption */}
        <p className="text-sm text-gray-700 line-clamp-3">
          {truncate(post.caption || 'No caption', 150)}
        </p>

        {/* Stats */}
        <div className="mt-4 flex items-center gap-4 text-sm text-gray-500">
          <div className="flex items-center gap-1">
            <Heart className="h-4 w-4" />
            <span>{formatNumber(post.like_count)}</span>
          </div>
          <div className="flex items-center gap-1">
            <MessageCircle className="h-4 w-4" />
            <span>{formatNumber(post.comment_count)}</span>
          </div>
          {post.share_count > 0 && (
            <div className="flex items-center gap-1">
              <Share2 className="h-4 w-4" />
              <span>{formatNumber(post.share_count)}</span>
            </div>
          )}
          {post.view_count && (
            <div className="flex items-center gap-1">
              <Eye className="h-4 w-4" />
              <span>{formatNumber(post.view_count)}</span>
            </div>
          )}
        </div>

        {/* Bottom row */}
        <div className="mt-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ViralBadge score={post.viral_score} />
            {post.engagement_rate !== null && (
              <span className="text-xs text-gray-400">
                {formatPercent(post.engagement_rate)} engagement
              </span>
            )}
          </div>
          <span className="text-xs text-gray-400">
            {formatRelativeTime(post.posted_at)}
          </span>
        </div>

        {/* Actions */}
        <div className="mt-4 flex items-center gap-2 border-t pt-4">
          <Link href={`/posts/${post.id}`} className="flex-1">
            <Button variant="outline" size="sm" className="w-full">
              <BarChart3 className="h-4 w-4 mr-2" />
              View Analysis
            </Button>
          </Link>
          <a
            href={`https://instagram.com/p/${post.platform_post_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-lg p-2 hover:bg-gray-100"
            title="View on Instagram"
          >
            <ExternalLink className="h-4 w-4 text-gray-500" />
          </a>
        </div>
      </div>
    </div>
  );
}
