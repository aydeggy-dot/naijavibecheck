'use client';

/**
 * Analysis Detail Page
 *
 * Shows complete vibe check results for a single post:
 * - Celebrity info and post link
 * - Headline and summary
 * - Sentiment breakdown with charts
 * - Top positive/negative comments
 * - Themes and hashtags
 * - Export and share options
 */

import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  ExternalLink,
  MessageCircle,
  ThumbsUp,
  ThumbsDown,
  Flame,
  Hash,
  Share2,
  Download,
  Copy,
  CheckCircle,
  AlertTriangle,
  TrendingUp,
  Calendar,
  User
} from 'lucide-react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardTitle } from '@/components/common/Card';
import { SentimentBadge } from '@/components/common/Badge';
import { Button } from '@/components/common/Button';
import { useAnalysis } from '@/hooks/useApi';
import { formatRelativeTime } from '@/lib/utils';
import { useState } from 'react';

export default function AnalysisDetailPage() {
  const params = useParams();
  const router = useRouter();
  const analysisId = params.id as string;

  const { data: analysis, isLoading, error } = useAnalysis(analysisId);
  const [copied, setCopied] = useState(false);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const shareReport = () => {
    const text = `
🎯 NAIJA VIBE CHECK

📊 ${analysis?.celebrity_name || 'Celebrity'} Analysis
📰 "${analysis?.headline || 'Vibe Check Complete'}"

✅ ${analysis?.sentiment_breakdown?.positive?.toFixed(0) || 0}% Positive
❌ ${analysis?.sentiment_breakdown?.negative?.toFixed(0) || 0}% Negative
💬 ${analysis?.total_comments?.toLocaleString() || 0} comments analyzed

${analysis?.vibe_summary || ''}

#NaijaVibeCheck #${analysis?.celebrity_name?.replace(/\s/g, '') || 'Naija'}
    `.trim();

    copyToClipboard(text);
  };

  if (isLoading) {
    return (
      <MainLayout title="Loading...">
        <div className="space-y-4">
          <div className="h-8 w-48 animate-pulse rounded bg-gray-200" />
          <div className="h-64 animate-pulse rounded-lg bg-gray-200" />
          <div className="h-96 animate-pulse rounded-lg bg-gray-200" />
        </div>
      </MainLayout>
    );
  }

  if (error || !analysis) {
    return (
      <MainLayout title="Analysis Not Found">
        <Card className="text-center py-12">
          <AlertTriangle className="mx-auto h-12 w-12 text-yellow-500" />
          <h2 className="mt-4 text-xl font-semibold">Analysis Not Found</h2>
          <p className="mt-2 text-gray-500">
            This analysis may have been deleted or doesn't exist.
          </p>
          <Button onClick={() => router.push('/analysis')} className="mt-4">
            Back to Analyses
          </Button>
        </Card>
      </MainLayout>
    );
  }

  return (
    <MainLayout title={analysis.headline || 'Analysis Details'}>
      {/* Back Button */}
      <button
        onClick={() => router.back()}
        className="mb-4 flex items-center gap-2 text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Analyses
      </button>

      {/* Header Card */}
      <Card className="mb-6">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div>
            {/* Celebrity & Status */}
            <div className="flex items-center gap-3 mb-3">
              <div className="h-12 w-12 rounded-full bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center">
                <User className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {analysis.celebrity_name || 'Unknown Celebrity'}
                </h1>
                <div className="flex items-center gap-2 mt-1">
                  <SentimentBadge sentiment={analysis.overall_sentiment} size="lg" />
                  <span className="text-sm text-gray-500 flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {formatRelativeTime(analysis.analyzed_at)}
                  </span>
                </div>
              </div>
            </div>

            {/* Headline */}
            {analysis.headline && (
              <h2 className="text-xl md:text-2xl font-semibold text-gray-800 mb-3">
                "{analysis.headline}"
              </h2>
            )}

            {/* Summary */}
            {analysis.vibe_summary && (
              <p className="text-gray-600 max-w-2xl">
                {analysis.vibe_summary}
              </p>
            )}

            {/* Spicy Take */}
            {analysis.spicy_take && (
              <div className="mt-3 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                <p className="text-sm text-yellow-800">
                  🌶️ <strong>Spicy Take:</strong> {analysis.spicy_take}
                </p>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-2 shrink-0">
            {analysis.post_url && (
              <a
                href={analysis.post_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-pink-500 text-white rounded-lg hover:bg-pink-600"
              >
                <ExternalLink className="h-4 w-4" />
                View Post
              </a>
            )}
            <Button variant="outline" onClick={shareReport}>
              {copied ? <CheckCircle className="h-4 w-4" /> : <Share2 className="h-4 w-4" />}
              {copied ? 'Copied!' : 'Share'}
            </Button>
          </div>
        </div>
      </Card>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-4 mb-6">
        <Card className="text-center">
          <div className="text-4xl font-bold text-green-600">
            {analysis.sentiment_breakdown?.positive?.toFixed(0) || 0}%
          </div>
          <div className="text-sm text-gray-500 mt-1">Positive</div>
        </Card>
        <Card className="text-center">
          <div className="text-4xl font-bold text-red-600">
            {analysis.sentiment_breakdown?.negative?.toFixed(0) || 0}%
          </div>
          <div className="text-sm text-gray-500 mt-1">Negative</div>
        </Card>
        <Card className="text-center">
          <div className="text-4xl font-bold text-gray-600">
            {analysis.sentiment_breakdown?.neutral?.toFixed(0) || 0}%
          </div>
          <div className="text-sm text-gray-500 mt-1">Neutral</div>
        </Card>
        <Card className="text-center">
          <div className="text-4xl font-bold text-blue-600">
            {(analysis.total_comments || 0).toLocaleString()}
          </div>
          <div className="text-sm text-gray-500 mt-1">Comments</div>
        </Card>
      </div>

      {/* Sentiment Bar */}
      <Card className="mb-6">
        <CardTitle className="mb-4">Sentiment Breakdown</CardTitle>
        <div className="h-8 rounded-full overflow-hidden bg-gray-200 flex">
          <div
            className="bg-green-500 flex items-center justify-center text-white text-sm font-medium"
            style={{ width: `${analysis.sentiment_breakdown?.positive || 0}%` }}
          >
            {(analysis.sentiment_breakdown?.positive || 0) > 10 &&
              `${analysis.sentiment_breakdown?.positive?.toFixed(0)}%`}
          </div>
          <div
            className="bg-red-500 flex items-center justify-center text-white text-sm font-medium"
            style={{ width: `${analysis.sentiment_breakdown?.negative || 0}%` }}
          >
            {(analysis.sentiment_breakdown?.negative || 0) > 10 &&
              `${analysis.sentiment_breakdown?.negative?.toFixed(0)}%`}
          </div>
          <div
            className="bg-gray-400 flex items-center justify-center text-white text-sm font-medium"
            style={{ width: `${analysis.sentiment_breakdown?.neutral || 0}%` }}
          >
            {(analysis.sentiment_breakdown?.neutral || 0) > 10 &&
              `${analysis.sentiment_breakdown?.neutral?.toFixed(0)}%`}
          </div>
        </div>
        <div className="flex justify-between mt-2 text-sm">
          <span className="text-green-600">✅ Positive</span>
          <span className="text-red-600">❌ Negative</span>
          <span className="text-gray-500">➖ Neutral</span>
        </div>

        {/* Controversy Level */}
        {analysis.controversy_level && (
          <div className="mt-4 pt-4 border-t">
            <div className="flex items-center gap-2">
              <Flame className={`h-5 w-5 ${
                analysis.controversy_level === 'wahala' ? 'text-red-500' :
                analysis.controversy_level === 'mid' ? 'text-yellow-500' :
                'text-green-500'
              }`} />
              <span className="font-medium">Controversy Level:</span>
              <span className={`px-2 py-1 rounded-full text-sm font-medium ${
                analysis.controversy_level === 'wahala' ? 'bg-red-100 text-red-700' :
                analysis.controversy_level === 'mid' ? 'bg-yellow-100 text-yellow-700' :
                'bg-green-100 text-green-700'
              }`}>
                {analysis.controversy_level.toUpperCase()}
              </span>
            </div>
          </div>
        )}
      </Card>

      {/* Top Comments */}
      <div className="grid gap-6 md:grid-cols-2 mb-6">
        {/* Top Positive */}
        <Card>
          <CardTitle className="flex items-center gap-2 mb-4">
            <ThumbsUp className="h-5 w-5 text-green-500" />
            Top Positive Comments
          </CardTitle>
          {analysis.top_positive_comments && analysis.top_positive_comments.length > 0 ? (
            <div className="space-y-3">
              {analysis.top_positive_comments.slice(0, 5).map((comment: any, i: number) => (
                <div key={i} className="p-3 bg-green-50 rounded-lg">
                  <p className="text-sm text-gray-700">{comment.text}</p>
                  <div className="mt-2 flex items-center gap-2 text-xs text-gray-500">
                    <span>@{comment.username || 'anonymous'}</span>
                    {comment.sentiment_score && (
                      <span className="text-green-600">
                        +{(comment.sentiment_score * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No positive comments highlighted</p>
          )}
        </Card>

        {/* Top Negative */}
        <Card>
          <CardTitle className="flex items-center gap-2 mb-4">
            <ThumbsDown className="h-5 w-5 text-red-500" />
            Top Negative Comments
          </CardTitle>
          {analysis.top_negative_comments && analysis.top_negative_comments.length > 0 ? (
            <div className="space-y-3">
              {analysis.top_negative_comments.slice(0, 5).map((comment: any, i: number) => (
                <div key={i} className="p-3 bg-red-50 rounded-lg">
                  <p className="text-sm text-gray-700">{comment.text}</p>
                  <div className="mt-2 flex items-center gap-2 text-xs text-gray-500">
                    <span>@{comment.username || 'anonymous'}</span>
                    {comment.toxicity_score && (
                      <span className="text-red-600">
                        Toxicity: {(comment.toxicity_score * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No negative comments highlighted</p>
          )}
        </Card>
      </div>

      {/* Notable Comments */}
      {analysis.notable_comments && analysis.notable_comments.length > 0 && (
        <Card className="mb-6">
          <CardTitle className="flex items-center gap-2 mb-4">
            <TrendingUp className="h-5 w-5 text-orange-500" />
            Notable Comments
          </CardTitle>
          <div className="space-y-3">
            {analysis.notable_comments.slice(0, 5).map((comment: any, i: number) => (
              <div key={i} className="p-3 bg-orange-50 rounded-lg border border-orange-200">
                <p className="text-sm text-gray-700">{comment.text}</p>
                <div className="mt-2 text-xs text-gray-500">
                  @{comment.username || 'anonymous'}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Themes & Hashtags */}
      <div className="grid gap-6 md:grid-cols-2 mb-6">
        {/* Themes */}
        {analysis.themes && analysis.themes.length > 0 && (
          <Card>
            <CardTitle className="mb-4">Key Themes</CardTitle>
            <div className="flex flex-wrap gap-2">
              {analysis.themes.map((theme: string, i: number) => (
                <span
                  key={i}
                  className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm"
                >
                  {theme}
                </span>
              ))}
            </div>
          </Card>
        )}

        {/* Hashtags */}
        {analysis.recommended_hashtags && analysis.recommended_hashtags.length > 0 && (
          <Card>
            <CardTitle className="flex items-center gap-2 mb-4">
              <Hash className="h-5 w-5" />
              Recommended Hashtags
            </CardTitle>
            <div className="flex flex-wrap gap-2">
              {analysis.recommended_hashtags.map((tag: string, i: number) => (
                <button
                  key={i}
                  onClick={() => copyToClipboard(`#${tag}`)}
                  className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm hover:bg-green-200 transition-colors"
                >
                  #{tag}
                </button>
              ))}
            </div>
            <p className="mt-3 text-xs text-gray-500">Click to copy</p>
          </Card>
        )}
      </div>

      {/* Key Insights */}
      {analysis.key_insights && analysis.key_insights.length > 0 && (
        <Card className="mb-6">
          <CardTitle className="mb-4">Key Insights</CardTitle>
          <ul className="space-y-2">
            {analysis.key_insights.map((insight: string, i: number) => (
              <li key={i} className="flex items-start gap-2">
                <CheckCircle className="h-5 w-5 text-green-500 shrink-0 mt-0.5" />
                <span className="text-gray-700">{insight}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {/* Analysis Metadata */}
      <Card>
        <CardTitle className="mb-4">Analysis Details</CardTitle>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 text-sm">
          <div>
            <span className="text-gray-500">Analysis ID</span>
            <p className="font-mono text-xs mt-1">{analysis.id}</p>
          </div>
          <div>
            <span className="text-gray-500">Analyzed At</span>
            <p className="mt-1">{new Date(analysis.analyzed_at).toLocaleString()}</p>
          </div>
          <div>
            <span className="text-gray-500">Method</span>
            <p className="mt-1">{analysis.analysis_method || 'cost_effective'}</p>
          </div>
          <div>
            <span className="text-gray-500">Estimated Cost</span>
            <p className="mt-1">{analysis.analysis_cost ? `$${analysis.analysis_cost.toFixed(2)}` : '~$0.05'}</p>
          </div>
        </div>
      </Card>
    </MainLayout>
  );
}
