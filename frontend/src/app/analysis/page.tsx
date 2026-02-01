'use client';

/**
 * Analysis listing page
 */

import Link from 'next/link';
import { BarChart3, TrendingUp, MessageCircle, Sparkles } from 'lucide-react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardTitle } from '@/components/common/Card';
import { SentimentBadge } from '@/components/common/Badge';
import { Button } from '@/components/common/Button';
import { useRecentAnalyses } from '@/hooks/useApi';
import { formatRelativeTime, truncate, formatPercent } from '@/lib/utils';

export default function AnalysisPage() {
  const { data: analyses, isLoading, error } = useRecentAnalyses({ limit: 20 });

  return (
    <MainLayout title="Analysis">
      {/* Stats */}
      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="flex items-center gap-4">
          <div className="rounded-lg bg-blue-100 p-3">
            <BarChart3 className="h-6 w-6 text-blue-600" />
          </div>
          <div>
            <p className="text-2xl font-bold">{analyses?.length || 0}</p>
            <p className="text-sm text-gray-500">Total Analyses</p>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="rounded-lg bg-green-100 p-3">
            <TrendingUp className="h-6 w-6 text-green-600" />
          </div>
          <div>
            <p className="text-2xl font-bold">
              {analyses?.filter((a) => a.overall_sentiment === 'positive').length || 0}
            </p>
            <p className="text-sm text-gray-500">Positive</p>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="rounded-lg bg-red-100 p-3">
            <MessageCircle className="h-6 w-6 text-red-600" />
          </div>
          <div>
            <p className="text-2xl font-bold">
              {analyses?.filter((a) => a.overall_sentiment === 'negative').length || 0}
            </p>
            <p className="text-sm text-gray-500">Negative</p>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="rounded-lg bg-yellow-100 p-3">
            <Sparkles className="h-6 w-6 text-yellow-600" />
          </div>
          <div>
            <p className="text-2xl font-bold">
              {analyses?.filter((a) => a.overall_sentiment === 'mixed').length || 0}
            </p>
            <p className="text-sm text-gray-500">Mixed</p>
          </div>
        </Card>
      </div>

      {/* Analysis List */}
      <Card padding="none">
        <div className="border-b p-4">
          <div className="flex items-center justify-between">
            <CardTitle>Recent Analyses</CardTitle>
          </div>
        </div>

        {isLoading ? (
          <div className="p-4 space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-24 animate-pulse rounded-lg bg-gray-100" />
            ))}
          </div>
        ) : error ? (
          <div className="p-8 text-center">
            <p className="text-red-500">Failed to load analyses</p>
          </div>
        ) : analyses && analyses.length > 0 ? (
          <div className="divide-y">
            {analyses.map((analysis) => (
              <Link
                key={analysis.id}
                href={`/analysis/${analysis.id}`}
                className="block p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <SentimentBadge sentiment={analysis.overall_sentiment} />
                      <span className="text-xs text-gray-500">
                        {formatRelativeTime(analysis.analyzed_at)}
                      </span>
                    </div>

                    <p className="text-sm text-gray-700 line-clamp-2">
                      {truncate(analysis.summary || 'No summary available', 200)}
                    </p>

                    {/* Sentiment breakdown */}
                    <div className="mt-3 flex items-center gap-4 text-xs">
                      <div className="flex items-center gap-1">
                        <div className="h-2 w-2 rounded-full bg-green-500" />
                        <span className="text-gray-500">
                          {formatPercent(analysis.sentiment_breakdown.positive / 100)} positive
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <div className="h-2 w-2 rounded-full bg-red-500" />
                        <span className="text-gray-500">
                          {formatPercent(analysis.sentiment_breakdown.negative / 100)} negative
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <div className="h-2 w-2 rounded-full bg-gray-400" />
                        <span className="text-gray-500">
                          {formatPercent(analysis.sentiment_breakdown.neutral / 100)} neutral
                        </span>
                      </div>
                    </div>

                    {/* Key themes */}
                    {analysis.key_themes && analysis.key_themes.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {analysis.key_themes.slice(0, 4).map((theme, i) => (
                          <span
                            key={i}
                            className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
                          >
                            {theme}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Scores */}
                  <div className="text-right">
                    <div className="text-sm">
                      <span className="text-gray-500">Viral:</span>{' '}
                      <span className="font-medium text-orange-500">
                        {(analysis.viral_potential * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="text-sm mt-1">
                      <span className="text-gray-500">Controversy:</span>{' '}
                      <span className="font-medium text-red-500">
                        {(analysis.controversy_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center">
            <BarChart3 className="mx-auto h-12 w-12 text-gray-300" />
            <p className="mt-4 text-gray-500">No analyses yet</p>
            <p className="text-sm text-gray-400">
              Analyses will appear here when posts are processed
            </p>
          </div>
        )}
      </Card>
    </MainLayout>
  );
}
