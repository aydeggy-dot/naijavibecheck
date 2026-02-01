'use client';

/**
 * Celebrity Discovery Page
 *
 * Features:
 * - View trending celebrities from Twitter/Google
 * - View celebrities mentioned in blogs
 * - Submit new celebrity suggestions
 * - Admin approval for pending suggestions
 */

import { useState } from 'react';
import {
  TrendingUp,
  Newspaper,
  UserPlus,
  CheckCircle,
  XCircle,
  ThumbsUp,
  Search,
  Loader2,
  ExternalLink,
  RefreshCw,
  Sparkles,
  Clock
} from 'lucide-react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardTitle } from '@/components/common/Card';
import { Button } from '@/components/common/Button';

// Types
interface DiscoveredCelebrity {
  name: string;
  trend?: string;
  source?: string;
  confidence?: number;
  mention_count?: number;
  articles?: Array<{ title: string; link: string; source: string }>;
}

interface Suggestion {
  id: string;
  instagram_username: string;
  full_name?: string;
  category?: string;
  reason?: string;
  vote_count: number;
  submitted_at: string;
  status: string;
}

type Tab = 'trending' | 'blogs' | 'suggest' | 'pending';

export default function DiscoverPage() {
  const [activeTab, setActiveTab] = useState<Tab>('trending');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Discovery results
  const [trendingCelebs, setTrendingCelebs] = useState<DiscoveredCelebrity[]>([]);
  const [blogCelebs, setBlogCelebs] = useState<DiscoveredCelebrity[]>([]);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);

  // Suggestion form
  const [formData, setFormData] = useState({
    instagram_username: '',
    full_name: '',
    category: 'musician',
    reason: '',
    example_post_url: ''
  });
  const [submitSuccess, setSubmitSuccess] = useState(false);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

  // Run trending discovery
  const runTrendingDiscovery = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/discovery/trending/run`, { method: 'POST' });
      const data = await res.json();
      setTrendingCelebs(data.celebrities || []);
    } catch (err) {
      setError('Failed to fetch trending celebrities');
    } finally {
      setLoading(false);
    }
  };

  // Run blog scraping
  const runBlogScraping = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/discovery/blogs/scrape`, { method: 'POST' });
      const data = await res.json();
      setBlogCelebs(data.celebrities || []);
    } catch (err) {
      setError('Failed to scrape blogs');
    } finally {
      setLoading(false);
    }
  };

  // Fetch pending suggestions
  const fetchSuggestions = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/discovery/suggestions?status=pending`);
      const data = await res.json();
      setSuggestions(data.suggestions || []);
    } catch (err) {
      setError('Failed to fetch suggestions');
    } finally {
      setLoading(false);
    }
  };

  // Submit suggestion
  const submitSuggestion = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/discovery/suggestions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const data = await res.json();

      if (data.status === 'submitted' || data.status === 'already_submitted') {
        setSubmitSuccess(true);
        setFormData({
          instagram_username: '',
          full_name: '',
          category: 'musician',
          reason: '',
          example_post_url: ''
        });
        setTimeout(() => setSubmitSuccess(false), 3000);
      } else {
        setError(data.message || 'Submission failed');
      }
    } catch (err) {
      setError('Failed to submit suggestion');
    } finally {
      setLoading(false);
    }
  };

  // Approve suggestion
  const approveSuggestion = async (id: string) => {
    try {
      await fetch(`${API_BASE}/discovery/suggestions/${id}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scrape_priority: 5 })
      });
      fetchSuggestions();
    } catch (err) {
      setError('Failed to approve');
    }
  };

  // Reject suggestion
  const rejectSuggestion = async (id: string) => {
    try {
      await fetch(`${API_BASE}/discovery/suggestions/${id}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      fetchSuggestions();
    } catch (err) {
      setError('Failed to reject');
    }
  };

  // Upvote suggestion
  const upvoteSuggestion = async (id: string) => {
    try {
      await fetch(`${API_BASE}/discovery/suggestions/${id}/upvote`, { method: 'POST' });
      fetchSuggestions();
    } catch (err) {
      setError('Failed to upvote');
    }
  };

  // Render tabs
  const tabs = [
    { id: 'trending' as Tab, label: 'Trending', icon: TrendingUp },
    { id: 'blogs' as Tab, label: 'Blog Mentions', icon: Newspaper },
    { id: 'suggest' as Tab, label: 'Suggest Celebrity', icon: UserPlus },
    { id: 'pending' as Tab, label: 'Pending Approval', icon: Clock },
  ];

  return (
    <MainLayout title="Celebrity Discovery">
      {/* Tab Navigation */}
      <div className="mb-6 flex flex-wrap gap-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => {
              setActiveTab(tab.id);
              if (tab.id === 'pending') fetchSuggestions();
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              activeTab === tab.id
                ? 'bg-green-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Trending Tab */}
      {activeTab === 'trending' && (
        <Card>
          <div className="flex items-center justify-between mb-4">
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-500" />
              Trending Celebrities
            </CardTitle>
            <Button onClick={runTrendingDiscovery} disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
              {loading ? 'Scanning...' : 'Scan Trends'}
            </Button>
          </div>

          <p className="text-sm text-gray-500 mb-4">
            Scans Twitter/X trends and Google Trends Nigeria to find celebrities people are talking about.
          </p>

          {trendingCelebs.length > 0 ? (
            <div className="space-y-3">
              {trendingCelebs.map((celeb, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <span className="font-medium">{celeb.name}</span>
                    {celeb.trend && (
                      <span className="ml-2 text-sm text-gray-500">
                        from "{celeb.trend}"
                      </span>
                    )}
                    <div className="text-xs text-gray-400 mt-1">
                      Source: {celeb.source} • Confidence: {((celeb.confidence || 0) * 100).toFixed(0)}%
                    </div>
                  </div>
                  <Button size="sm" variant="outline">
                    <UserPlus className="h-4 w-4" />
                    Track
                  </Button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <TrendingUp className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>Click "Scan Trends" to discover trending celebrities</p>
            </div>
          )}
        </Card>
      )}

      {/* Blogs Tab */}
      {activeTab === 'blogs' && (
        <Card>
          <div className="flex items-center justify-between mb-4">
            <CardTitle className="flex items-center gap-2">
              <Newspaper className="h-5 w-5 text-blue-500" />
              Blog Mentions
            </CardTitle>
            <Button onClick={runBlogScraping} disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
              {loading ? 'Scraping...' : 'Scrape Blogs'}
            </Button>
          </div>

          <p className="text-sm text-gray-500 mb-4">
            Scrapes Linda Ikeji, Bella Naija, Pulse Nigeria to find celebrities in the news.
          </p>

          {blogCelebs.length > 0 ? (
            <div className="space-y-3">
              {blogCelebs.map((celeb, i) => (
                <div key={i} className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="font-medium">{celeb.name}</span>
                      <span className="ml-2 text-sm text-green-600">
                        {celeb.mention_count} mentions
                      </span>
                    </div>
                    <Button size="sm" variant="outline">
                      <UserPlus className="h-4 w-4" />
                      Track
                    </Button>
                  </div>
                  {celeb.articles && celeb.articles.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {celeb.articles.slice(0, 2).map((article, j) => (
                        <a
                          key={j}
                          href={article.link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-xs text-blue-600 hover:underline"
                        >
                          <ExternalLink className="h-3 w-3" />
                          {article.title?.slice(0, 60)}...
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Newspaper className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>Click "Scrape Blogs" to find celebrities in the news</p>
            </div>
          )}
        </Card>
      )}

      {/* Suggest Tab */}
      {activeTab === 'suggest' && (
        <Card>
          <CardTitle className="flex items-center gap-2 mb-4">
            <UserPlus className="h-5 w-5 text-purple-500" />
            Suggest a Celebrity
          </CardTitle>

          {submitSuccess && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700 flex items-center gap-2">
              <CheckCircle className="h-5 w-5" />
              Thanks! Your suggestion has been submitted for review.
            </div>
          )}

          <form onSubmit={submitSuggestion} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Instagram Username *
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">@</span>
                <input
                  type="text"
                  value={formData.instagram_username}
                  onChange={(e) => setFormData({ ...formData, instagram_username: e.target.value })}
                  placeholder="davido"
                  required
                  className="w-full pl-8 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Full Name
              </label>
              <input
                type="text"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                placeholder="David Adeleke"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category
              </label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              >
                <option value="musician">Musician</option>
                <option value="actor">Actor/Actress</option>
                <option value="comedian">Comedian</option>
                <option value="influencer">Influencer</option>
                <option value="athlete">Athlete</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Why should we track this celebrity?
              </label>
              <textarea
                value={formData.reason}
                onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                placeholder="They're trending because..."
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Example Post URL (optional)
              </label>
              <input
                type="url"
                value={formData.example_post_url}
                onChange={(e) => setFormData({ ...formData, example_post_url: e.target.value })}
                placeholder="https://www.instagram.com/p/..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
            </div>

            <Button type="submit" disabled={loading || !formData.instagram_username}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              Submit Suggestion
            </Button>
          </form>
        </Card>
      )}

      {/* Pending Approval Tab */}
      {activeTab === 'pending' && (
        <Card>
          <div className="flex items-center justify-between mb-4">
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-yellow-500" />
              Pending Approval
            </CardTitle>
            <Button onClick={fetchSuggestions} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
          </div>

          {suggestions.length > 0 ? (
            <div className="space-y-3">
              {suggestions.map((suggestion) => (
                <div key={suggestion.id} className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold">@{suggestion.instagram_username}</span>
                        {suggestion.full_name && (
                          <span className="text-gray-500">({suggestion.full_name})</span>
                        )}
                        <span className="px-2 py-0.5 bg-gray-200 rounded text-xs">
                          {suggestion.category}
                        </span>
                      </div>
                      {suggestion.reason && (
                        <p className="text-sm text-gray-600 mt-1">{suggestion.reason}</p>
                      )}
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <ThumbsUp className="h-3 w-3" />
                          {suggestion.vote_count} votes
                        </span>
                        <span>
                          Submitted {new Date(suggestion.submitted_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => upvoteSuggestion(suggestion.id)}
                      >
                        <ThumbsUp className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => approveSuggestion(suggestion.id)}
                      >
                        <CheckCircle className="h-4 w-4" />
                        Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-red-600 hover:bg-red-50"
                        onClick={() => rejectSuggestion(suggestion.id)}
                      >
                        <XCircle className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Clock className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No pending suggestions</p>
              <p className="text-sm mt-1">Suggestions will appear here for review</p>
            </div>
          )}
        </Card>
      )}
    </MainLayout>
  );
}
