'use client';

/**
 * Analysis Dashboard - View all vibe check results
 *
 * Features:
 * - Search by celebrity name
 * - Filter by date range
 * - Filter by sentiment (positive/negative/mixed)
 * - Sort by date, positivity, controversy
 * - View detailed analysis for each post
 */

import { useState, useMemo } from 'react';
import Link from 'next/link';
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  MessageCircle,
  Sparkles,
  Search,
  Calendar,
  Filter,
  ChevronDown,
  ExternalLink,
  Flame,
  Hash
} from 'lucide-react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardTitle } from '@/components/common/Card';
import { SentimentBadge } from '@/components/common/Badge';
import { Button } from '@/components/common/Button';
import { useRecentAnalyses } from '@/hooks/useApi';
import { formatRelativeTime, truncate, formatPercent } from '@/lib/utils';

type SortOption = 'date' | 'positivity' | 'negativity' | 'controversy' | 'comments';
type SentimentFilter = 'all' | 'positive' | 'negative' | 'mixed' | 'neutral';

export default function AnalysisPage() {
  const { data: analyses, isLoading, error } = useRecentAnalyses({ limit: 100 });

  // Search and filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [sentimentFilter, setSentimentFilter] = useState<SentimentFilter>('all');
  const [sortBy, setSortBy] = useState<SortOption>('date');
  const [dateRange, setDateRange] = useState<'all' | '7d' | '30d' | '90d'>('all');
  const [showFilters, setShowFilters] = useState(false);

  // Filter and sort analyses
  const filteredAnalyses = useMemo(() => {
    if (!analyses) return [];

    let filtered = [...analyses];

    // Search by celebrity name or headline
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(a =>
        a.celebrity_name?.toLowerCase().includes(query) ||
        a.headline?.toLowerCase().includes(query) ||
        a.summary?.toLowerCase().includes(query)
      );
    }

    // Filter by sentiment
    if (sentimentFilter !== 'all') {
      filtered = filtered.filter(a => a.overall_sentiment === sentimentFilter);
    }

    // Filter by date range
    if (dateRange !== 'all') {
      const now = new Date();
      const days = dateRange === '7d' ? 7 : dateRange === '30d' ? 30 : 90;
      const cutoff = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
      filtered = filtered.filter(a => new Date(a.analyzed_at) >= cutoff);
    }

    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'date':
          return new Date(b.analyzed_at).getTime() - new Date(a.analyzed_at).getTime();
        case 'positivity':
          return (b.sentiment_breakdown?.positive || 0) - (a.sentiment_breakdown?.positive || 0);
        case 'negativity':
          return (b.sentiment_breakdown?.negative || 0) - (a.sentiment_breakdown?.negative || 0);
        case 'controversy':
          return (b.controversy_score || 0) - (a.controversy_score || 0);
        case 'comments':
          return (b.total_comments || 0) - (a.total_comments || 0);
        default:
          return 0;
      }
    });

    return filtered;
  }, [analyses, searchQuery, sentimentFilter, sortBy, dateRange]);

  // Calculate stats
  const stats = useMemo(() => {
    if (!filteredAnalyses.length) return { total: 0, positive: 0, negative: 0, mixed: 0 };
    return {
      total: filteredAnalyses.length,
      positive: filteredAnalyses.filter(a => a.overall_sentiment === 'positive').length,
      negative: filteredAnalyses.filter(a => a.overall_sentiment === 'negative').length,
      mixed: filteredAnalyses.filter(a => a.overall_sentiment === 'mixed').length,
    };
  }, [filteredAnalyses]);

  return (
    <MainLayout title="Analysis Dashboard">
      {/* Search Bar */}
      <div className="mb-6">
        <div className="flex gap-4 flex-col sm:flex-row">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search by celebrity name, headline..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-lg border border-gray-300 py-3 pl-10 pr-4 focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
            />
          </div>

          {/* Filter Toggle */}
          <Button
            variant={showFilters ? 'primary' : 'outline'}
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2"
          >
            <Filter className="h-4 w-4" />
            Filters
            <ChevronDown className={`h-4 w-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
          </Button>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <Card className="mt-4">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {/* Sentiment Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Sentiment
                </label>
                <select
                  value={sentimentFilter}
                  onChange={(e) => setSentimentFilter(e.target.value as SentimentFilter)}
                  className="w-full rounded-lg border border-gray-300 py-2 px-3 focus:border-green-500 focus:outline-none"
                >
                  <option value="all">All Sentiments</option>
                  <option value="positive">Positive Only</option>
                  <option value="negative">Negative Only</option>
                  <option value="mixed">Mixed</option>
                  <option value="neutral">Neutral</option>
                </select>
              </div>

              {/* Date Range */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Calendar className="inline h-4 w-4 mr-1" />
                  Date Range
                </label>
                <select
                  value={dateRange}
                  onChange={(e) => setDateRange(e.target.value as typeof dateRange)}
                  className="w-full rounded-lg border border-gray-300 py-2 px-3 focus:border-green-500 focus:outline-none"
                >
                  <option value="all">All Time</option>
                  <option value="7d">Last 7 Days</option>
                  <option value="30d">Last 30 Days</option>
                  <option value="90d">Last 90 Days</option>
                </select>
              </div>

              {/* Sort By */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Sort By
                </label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as SortOption)}
                  className="w-full rounded-lg border border-gray-300 py-2 px-3 focus:border-green-500 focus:outline-none"
                >
                  <option value="date">Most Recent</option>
                  <option value="positivity">Most Positive</option>
                  <option value="negativity">Most Negative</option>
                  <option value="controversy">Most Controversial</option>
                  <option value="comments">Most Comments</option>
                </select>
              </div>

              {/* Clear Filters */}
              <div className="flex items-end">
                <Button
                  variant="ghost"
                  onClick={() => {
                    setSearchQuery('');
                    setSentimentFilter('all');
                    setDateRange('all');
                    setSortBy('date');
                  }}
                  className="w-full"
                >
                  Clear Filters
                </Button>
              </div>
            </div>
          </Card>
        )}
      </div>

      {/* Stats Cards */}
      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="flex items-center gap-4 cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => setSentimentFilter('all')}>
          <div className="rounded-lg bg-blue-100 p-3">
            <BarChart3 className="h-6 w-6 text-blue-600" />
          </div>
          <div>
            <p className="text-2xl font-bold">{stats.total}</p>
            <p className="text-sm text-gray-500">Total Analyses</p>
          </div>
        </Card>

        <Card className="flex items-center gap-4 cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => setSentimentFilter('positive')}>
          <div className="rounded-lg bg-green-100 p-3">
            <TrendingUp className="h-6 w-6 text-green-600" />
          </div>
          <div>
            <p className="text-2xl font-bold text-green-600">{stats.positive}</p>
            <p className="text-sm text-gray-500">Positive Vibes</p>
          </div>
        </Card>

        <Card className="flex items-center gap-4 cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => setSentimentFilter('negative')}>
          <div className="rounded-lg bg-red-100 p-3">
            <TrendingDown className="h-6 w-6 text-red-600" />
          </div>
          <div>
            <p className="text-2xl font-bold text-red-600">{stats.negative}</p>
            <p className="text-sm text-gray-500">Negative Vibes</p>
          </div>
        </Card>

        <Card className="flex items-center gap-4 cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => setSentimentFilter('mixed')}>
          <div className="rounded-lg bg-yellow-100 p-3">
            <Sparkles className="h-6 w-6 text-yellow-600" />
          </div>
          <div>
            <p className="text-2xl font-bold text-yellow-600">{stats.mixed}</p>
            <p className="text-sm text-gray-500">Mixed Vibes</p>
          </div>
        </Card>
      </div>

      {/* Results Count */}
      {searchQuery || sentimentFilter !== 'all' || dateRange !== 'all' ? (
        <p className="mb-4 text-sm text-gray-500">
          Showing {filteredAnalyses.length} results
          {searchQuery && ` for "${searchQuery}"`}
        </p>
      ) : null}

      {/* Analysis List */}
      <Card padding="none">
        <div className="border-b p-4">
          <div className="flex items-center justify-between">
            <CardTitle>Vibe Check Results</CardTitle>
          </div>
        </div>

        {isLoading ? (
          <div className="p-4 space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-32 animate-pulse rounded-lg bg-gray-100" />
            ))}
          </div>
        ) : error ? (
          <div className="p-8 text-center">
            <p className="text-red-500">Failed to load analyses</p>
            <p className="text-sm text-gray-400 mt-2">Make sure the backend is running</p>
          </div>
        ) : filteredAnalyses.length > 0 ? (
          <div className="divide-y">
            {filteredAnalyses.map((analysis) => (
              <Link
                key={analysis.id}
                href={`/analysis/${analysis.id}`}
                className="block p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start gap-4">
                  {/* Main Content */}
                  <div className="flex-1 min-w-0">
                    {/* Header */}
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      <span className="font-semibold text-gray-900">
                        {analysis.celebrity_name || 'Unknown Celebrity'}
                      </span>
                      <SentimentBadge sentiment={analysis.overall_sentiment} />
                      <span className="text-xs text-gray-500">
                        {formatRelativeTime(analysis.analyzed_at)}
                      </span>
                    </div>

                    {/* Headline */}
                    {analysis.headline && (
                      <h3 className="text-lg font-medium text-gray-800 mb-2">
                        "{analysis.headline}"
                      </h3>
                    )}

                    {/* Summary */}
                    <p className="text-sm text-gray-600 line-clamp-2 mb-3">
                      {truncate(analysis.vibe_summary || analysis.summary || 'No summary available', 200)}
                    </p>

                    {/* Sentiment Bar */}
                    <div className="mb-3">
                      <div className="flex h-2 rounded-full overflow-hidden bg-gray-200">
                        <div
                          className="bg-green-500"
                          style={{ width: `${analysis.sentiment_breakdown?.positive || 0}%` }}
                        />
                        <div
                          className="bg-red-500"
                          style={{ width: `${analysis.sentiment_breakdown?.negative || 0}%` }}
                        />
                        <div
                          className="bg-gray-400"
                          style={{ width: `${analysis.sentiment_breakdown?.neutral || 0}%` }}
                        />
                      </div>
                      <div className="flex justify-between mt-1 text-xs text-gray-500">
                        <span className="text-green-600">
                          {analysis.sentiment_breakdown?.positive?.toFixed(0) || 0}% positive
                        </span>
                        <span className="text-red-600">
                          {analysis.sentiment_breakdown?.negative?.toFixed(0) || 0}% negative
                        </span>
                      </div>
                    </div>

                    {/* Stats Row */}
                    <div className="flex items-center gap-4 text-xs text-gray-500 flex-wrap">
                      <span className="flex items-center gap-1">
                        <MessageCircle className="h-3 w-3" />
                        {(analysis.total_comments || 0).toLocaleString()} comments
                      </span>

                      {analysis.controversy_level && (
                        <span className={`flex items-center gap-1 ${
                          analysis.controversy_level === 'wahala' ? 'text-red-500' :
                          analysis.controversy_level === 'mid' ? 'text-yellow-500' :
                          'text-green-500'
                        }`}>
                          <Flame className="h-3 w-3" />
                          {analysis.controversy_level}
                        </span>
                      )}

                      {analysis.post_url && (
                        <span className="flex items-center gap-1 text-blue-500">
                          <ExternalLink className="h-3 w-3" />
                          View Post
                        </span>
                      )}
                    </div>

                    {/* Themes/Hashtags */}
                    {analysis.themes && analysis.themes.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-1">
                        {analysis.themes.slice(0, 5).map((theme: string, i: number) => (
                          <span
                            key={i}
                            className="inline-flex items-center rounded-full bg-green-50 px-2 py-0.5 text-xs text-green-700"
                          >
                            <Hash className="h-3 w-3 mr-0.5" />
                            {theme}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Right Side Stats */}
                  <div className="text-right shrink-0">
                    <div className="text-3xl font-bold text-green-600">
                      {analysis.sentiment_breakdown?.positive?.toFixed(0) || 0}%
                    </div>
                    <div className="text-xs text-gray-500">positive</div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center">
            <BarChart3 className="mx-auto h-12 w-12 text-gray-300" />
            <p className="mt-4 text-gray-500">
              {searchQuery || sentimentFilter !== 'all'
                ? 'No analyses match your filters'
                : 'No analyses yet'}
            </p>
            <p className="text-sm text-gray-400 mt-2">
              {searchQuery || sentimentFilter !== 'all'
                ? 'Try adjusting your search or filters'
                : 'Run a vibe check to see results here'}
            </p>
          </div>
        )}
      </Card>
    </MainLayout>
  );
}
