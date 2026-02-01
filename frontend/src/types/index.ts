/**
 * NaijaVibeCheck TypeScript Types
 */

export interface Celebrity {
  id: string;
  username: string;
  platform: string;
  display_name: string | null;
  profile_pic_url: string | null;
  bio: string | null;
  follower_count: number;
  following_count: number;
  post_count: number;
  category: string | null;
  is_active: boolean;
  priority: number;
  last_scraped_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Post {
  id: string;
  celebrity_id: string;
  platform_post_id: string;
  post_type: string;
  caption: string | null;
  media_urls: string[];
  thumbnail_url: string | null;
  like_count: number;
  comment_count: number;
  share_count: number;
  view_count: number | null;
  posted_at: string;
  scraped_at: string;
  is_viral: boolean;
  viral_score: number | null;
  engagement_rate: number | null;
  celebrity?: Celebrity;
}

export interface Comment {
  id: string;
  post_id: string;
  platform_comment_id: string;
  username: string;
  text: string;
  like_count: number;
  reply_count: number;
  commented_at: string;
  scraped_at: string;
  is_celebrity_reply: boolean;
}

export interface CommentAnalysis {
  id: string;
  comment_id: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  sentiment_score: number;
  emotion: string | null;
  is_nigerian_slang: boolean;
  slang_terms: string[];
  engagement_potential: number;
  summary: string | null;
  themes: string[];
  analyzed_at: string;
  comment?: Comment;
}

export interface PostAnalysis {
  id: string;
  post_id: string;
  overall_sentiment: 'positive' | 'negative' | 'neutral' | 'mixed';
  sentiment_breakdown: {
    positive: number;
    negative: number;
    neutral: number;
  };
  top_positive_comments: string[];
  top_negative_comments: string[];
  controversy_score: number;
  viral_potential: number;
  key_themes: string[];
  trending_topics: string[];
  nigerian_context: Record<string, unknown>;
  summary: string | null;
  analyzed_at: string;
  post?: Post;
}

export interface GeneratedContent {
  id: string;
  post_analysis_id: string;
  content_type: 'image' | 'carousel' | 'video' | 'reel';
  title: string;
  caption: string | null;
  hashtags: string[];
  media_paths: string[];
  thumbnail_url: string | null;
  template_used: string | null;
  generation_params: Record<string, unknown>;
  status: 'draft' | 'pending_review' | 'approved' | 'rejected' | 'published';
  scheduled_for: string | null;
  published_at: string | null;
  instagram_post_id: string | null;
  created_at: string;
  updated_at: string;
  post_analysis?: PostAnalysis;
}

export interface OurEngagement {
  id: string;
  generated_content_id: string;
  like_count: number | null;
  comment_count: number | null;
  share_count: number | null;
  save_count: number | null;
  reach: number | null;
  impressions: number | null;
  recorded_at: string;
}

export interface DashboardStats {
  total_celebrities: number;
  total_posts: number;
  total_comments: number;
  posts_today: number;
  viral_posts: number;
  pending_content: number;
  published_today: number;
  avg_engagement_rate: number;
}

export interface TrendingItem {
  id: string;
  name: string;
  type: 'celebrity' | 'topic' | 'post';
  score: number;
  change: number;
  metadata?: Record<string, unknown>;
}

export interface PublishingQueue {
  pending_review: GeneratedContent[];
  approved: GeneratedContent[];
  recently_published: GeneratedContent[];
  counts: {
    pending: number;
    approved: number;
    published: number;
  };
}

export interface OptimalTime {
  datetime: string;
  hour: number;
  day_name: string;
  confidence: number;
  reason: string;
}

export interface AccountStats {
  follower_count: number;
  following_count: number;
  media_count: number;
  engagement_rate: number;
  updated_at: string;
}

export interface APIResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}
