'use client';

/**
 * Recent activity showing latest analyses and content
 */

import Link from 'next/link';
import { Activity, FileText, Image, CheckCircle, XCircle, Clock } from 'lucide-react';
import { useRecentAnalyses, usePublishingQueue } from '@/hooks/useApi';
import { Card, CardTitle } from '@/components/common/Card';
import { StatusBadge, SentimentBadge } from '@/components/common/Badge';
import { formatRelativeTime, truncate } from '@/lib/utils';

export function RecentActivity() {
  const { data: analyses, isLoading: analysesLoading } = useRecentAnalyses({ limit: 5 });
  const { data: queue, isLoading: queueLoading } = usePublishingQueue();

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Recent Analyses */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-blue-500" />
            <CardTitle>Recent Analyses</CardTitle>
          </div>
          <Link href="/analysis" className="text-sm text-[#008751] hover:underline">
            View all
          </Link>
        </div>

        {analysesLoading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-14 animate-pulse rounded-lg bg-gray-100" />
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {analyses?.slice(0, 5).map((analysis) => (
              <Link
                key={analysis.id}
                href={`/analysis/${analysis.id}`}
                className="flex items-center gap-3 rounded-lg p-3 hover:bg-gray-50 transition-colors"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50">
                  <FileText className="h-5 w-5 text-blue-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {truncate(analysis.summary || 'Post analysis', 50)}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <SentimentBadge sentiment={analysis.overall_sentiment} />
                    <span className="text-xs text-gray-500">
                      {formatRelativeTime(analysis.analyzed_at)}
                    </span>
                  </div>
                </div>
              </Link>
            ))}
            {(!analyses || analyses.length === 0) && (
              <p className="text-center text-gray-500 py-4">
                No analyses yet
              </p>
            )}
          </div>
        )}
      </Card>

      {/* Publishing Queue */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Image className="h-5 w-5 text-purple-500" />
            <CardTitle>Publishing Queue</CardTitle>
          </div>
          <Link href="/publishing" className="text-sm text-[#008751] hover:underline">
            View all
          </Link>
        </div>

        {queueLoading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-14 animate-pulse rounded-lg bg-gray-100" />
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {/* Queue Stats */}
            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="rounded-lg bg-yellow-50 p-3 text-center">
                <p className="text-2xl font-bold text-yellow-600">
                  {queue?.counts.pending || 0}
                </p>
                <p className="text-xs text-yellow-700">Pending</p>
              </div>
              <div className="rounded-lg bg-blue-50 p-3 text-center">
                <p className="text-2xl font-bold text-blue-600">
                  {queue?.counts.approved || 0}
                </p>
                <p className="text-xs text-blue-700">Approved</p>
              </div>
              <div className="rounded-lg bg-green-50 p-3 text-center">
                <p className="text-2xl font-bold text-green-600">
                  {queue?.counts.published || 0}
                </p>
                <p className="text-xs text-green-700">Published</p>
              </div>
            </div>

            {/* Recent Items */}
            {queue?.pending_review.slice(0, 3).map((content) => (
              <Link
                key={content.id}
                href={`/content/${content.id}`}
                className="flex items-center gap-3 rounded-lg p-3 hover:bg-gray-50 transition-colors border border-yellow-100"
              >
                <Clock className="h-5 w-5 text-yellow-500" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {content.title}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatRelativeTime(content.created_at)}
                  </p>
                </div>
                <StatusBadge status={content.status} />
              </Link>
            ))}

            {queue?.approved.slice(0, 2).map((content) => (
              <Link
                key={content.id}
                href={`/content/${content.id}`}
                className="flex items-center gap-3 rounded-lg p-3 hover:bg-gray-50 transition-colors border border-blue-100"
              >
                <CheckCircle className="h-5 w-5 text-blue-500" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {content.title}
                  </p>
                  <p className="text-xs text-gray-500">
                    Scheduled: {content.scheduled_for ? formatRelativeTime(content.scheduled_for) : 'Not set'}
                  </p>
                </div>
                <StatusBadge status={content.status} />
              </Link>
            ))}

            {(!queue?.pending_review.length && !queue?.approved.length) && (
              <p className="text-center text-gray-500 py-4">
                Queue is empty
              </p>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}
