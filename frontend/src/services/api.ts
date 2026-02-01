/**
 * API Service for NaijaVibeCheck Backend
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  Celebrity,
  Post,
  PostAnalysis,
  GeneratedContent,
  DashboardStats,
  TrendingItem,
  PublishingQueue,
  OptimalTime,
  AccountStats,
  PaginatedResponse,
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

class APIService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  // Health check
  async healthCheck(): Promise<{ status: string; database: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }

  // Celebrities
  async getCelebrities(params?: {
    category?: string;
    is_active?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<PaginatedResponse<Celebrity>> {
    const response = await this.client.get('/celebrities', { params });
    return response.data;
  }

  async getCelebrity(id: string): Promise<Celebrity> {
    const response = await this.client.get(`/celebrities/${id}`);
    return response.data;
  }

  async createCelebrity(data: Partial<Celebrity>): Promise<Celebrity> {
    const response = await this.client.post('/celebrities', data);
    return response.data;
  }

  async updateCelebrity(id: string, data: Partial<Celebrity>): Promise<Celebrity> {
    const response = await this.client.patch(`/celebrities/${id}`, data);
    return response.data;
  }

  async deleteCelebrity(id: string): Promise<void> {
    await this.client.delete(`/celebrities/${id}`);
  }

  async scrapeCelebrity(id: string): Promise<{ status: string; task_id: string }> {
    const response = await this.client.post(`/celebrities/${id}/scrape`);
    return response.data;
  }

  // Posts
  async getPosts(params?: {
    celebrity_id?: string;
    is_viral?: boolean;
    min_viral_score?: number;
    skip?: number;
    limit?: number;
  }): Promise<PaginatedResponse<Post>> {
    const response = await this.client.get('/posts', { params });
    return response.data;
  }

  async getPost(id: string): Promise<Post> {
    const response = await this.client.get(`/posts/${id}`);
    return response.data;
  }

  async getPostComments(id: string, params?: {
    skip?: number;
    limit?: number;
  }): Promise<PaginatedResponse<Comment>> {
    const response = await this.client.get(`/posts/${id}/comments`, { params });
    return response.data;
  }

  async getViralPosts(params?: {
    min_score?: number;
    limit?: number;
  }): Promise<Post[]> {
    const response = await this.client.get('/posts/viral', {
      params: { page_size: params?.limit || 20 }
    });
    // Backend returns { items: [...], total: ..., ... }
    return response.data.items || [];
  }

  // Analytics
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await this.client.get('/analytics/dashboard');
    const data = response.data;
    // Transform backend response to expected format
    return {
      total_celebrities: data.celebrities?.total_active || 0,
      total_posts: data.posts?.total || 0,
      total_comments: data.comments?.total || 0,
      posts_today: 0,
      viral_posts: data.posts?.viral || 0,
      pending_content: data.content?.pending_review || 0,
      published_today: data.content?.published || 0,
      avg_engagement_rate: 0,
    };
  }

  async getTrending(params?: {
    type?: 'celebrities' | 'topics' | 'posts';
    limit?: number;
  }): Promise<TrendingItem[]> {
    const response = await this.client.get('/analytics/trending', { params });
    return response.data;
  }

  async getCelebrityAnalytics(id: string, params?: {
    days?: number;
  }): Promise<{
    celebrity: Celebrity;
    post_count: number;
    avg_engagement: number;
    viral_posts: number;
    sentiment_trend: { date: string; sentiment: number }[];
  }> {
    const response = await this.client.get(`/analytics/celebrity/${id}`, { params });
    return response.data;
  }

  // Analysis
  async getPostAnalysis(postId: string): Promise<PostAnalysis> {
    const response = await this.client.get(`/analysis/post/${postId}`);
    return response.data;
  }

  async triggerAnalysis(postId: string): Promise<{ status: string; task_id: string }> {
    const response = await this.client.post(`/analysis/post/${postId}/analyze`);
    return response.data;
  }

  async getRecentAnalyses(params?: {
    limit?: number;
  }): Promise<PostAnalysis[]> {
    const response = await this.client.get('/analysis/recent', { params });
    return response.data;
  }

  // Content Generation
  async generateContent(postAnalysisId: string, params?: {
    content_type?: string;
    template?: string;
  }): Promise<{ status: string; task_id: string }> {
    const response = await this.client.post(`/generate/${postAnalysisId}`, params);
    return response.data;
  }

  async getGeneratedContent(params?: {
    status?: string;
    content_type?: string;
    skip?: number;
    limit?: number;
  }): Promise<PaginatedResponse<GeneratedContent>> {
    const response = await this.client.get('/content', { params });
    return response.data;
  }

  async getContentById(id: string): Promise<GeneratedContent> {
    const response = await this.client.get(`/content/${id}`);
    return response.data;
  }

  // Publishing
  async scheduleContent(contentId: string, params?: {
    scheduled_time?: string;
    auto_approve?: boolean;
  }): Promise<{ status: string; scheduled_for: string }> {
    const response = await this.client.post(`/publish/content/${contentId}/schedule`, params);
    return response.data;
  }

  async rescheduleContent(contentId: string, newTime: string): Promise<{ status: string }> {
    const response = await this.client.post(`/publish/content/${contentId}/reschedule`, {
      new_time: newTime,
    });
    return response.data;
  }

  async approveContent(contentId: string, scheduleNow?: boolean): Promise<{ status: string }> {
    const response = await this.client.post(`/publish/content/${contentId}/approve`, {
      schedule_now: scheduleNow ?? true,
    });
    return response.data;
  }

  async rejectContent(contentId: string, reason?: string): Promise<{ status: string }> {
    const response = await this.client.post(`/publish/content/${contentId}/reject`, { reason });
    return response.data;
  }

  async publishNow(contentId: string): Promise<{ status: string }> {
    const response = await this.client.post(`/publish/content/${contentId}/publish`);
    return response.data;
  }

  async getPublishingQueue(): Promise<PublishingQueue> {
    const response = await this.client.get('/publish/queue');
    return response.data;
  }

  async getOptimalTimes(count?: number): Promise<{ suggestions: OptimalTime[] }> {
    const response = await this.client.get('/publish/optimal-times', {
      params: { count },
    });
    // Transform backend response to expected format
    const suggestions = response.data.suggestions?.map((s: { datetime_lagos: string; day: string; time: string; confidence: number; is_peak: boolean }) => ({
      datetime: s.datetime_lagos,
      hour: parseInt(s.time?.split(':')[0] || '0'),
      day_name: s.day,
      confidence: s.confidence,
      reason: s.is_peak ? 'Peak engagement time' : 'Good engagement time',
    })) || [];
    return { suggestions };
  }

  async getPublishingStats(): Promise<{
    total_published: number;
    published_this_week: number;
    avg_engagement: number;
    best_performing: GeneratedContent | null;
  }> {
    const response = await this.client.get('/publish/stats');
    // Transform backend response to expected format
    const data = response.data;
    return {
      total_published: data.by_status?.published || 0,
      published_this_week: data.published_today || 0,
      avg_engagement: 0,
      best_performing: null,
    };
  }

  async getAccountInfo(): Promise<AccountStats> {
    const response = await this.client.get('/publish/account');
    return response.data;
  }

  // Settings
  async getSettings(): Promise<Record<string, unknown>> {
    const response = await this.client.get('/settings');
    return response.data;
  }

  async updateSettings(settings: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await this.client.patch('/settings', settings);
    return response.data;
  }
}

export const api = new APIService();
export default api;
