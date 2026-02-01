/**
 * React Query hooks for API data fetching
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/services/api';
import type {
  Celebrity,
  Post,
  PostAnalysis,
  GeneratedContent,
} from '@/types';

// Query keys
export const queryKeys = {
  health: ['health'],
  celebrities: ['celebrities'],
  celebrity: (id: string) => ['celebrity', id],
  posts: ['posts'],
  post: (id: string) => ['post', id],
  postComments: (id: string) => ['post', id, 'comments'],
  viralPosts: ['posts', 'viral'],
  dashboard: ['dashboard'],
  trending: ['trending'],
  celebrityAnalytics: (id: string) => ['analytics', 'celebrity', id],
  postAnalysis: (id: string) => ['analysis', 'post', id],
  recentAnalyses: ['analyses', 'recent'],
  content: ['content'],
  contentById: (id: string) => ['content', id],
  publishingQueue: ['publishing', 'queue'],
  optimalTimes: ['publishing', 'optimal-times'],
  publishingStats: ['publishing', 'stats'],
  accountInfo: ['account'],
  settings: ['settings'],
};

// Health
export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: () => api.healthCheck(),
    refetchInterval: 30000,
  });
}

// Celebrities
export function useCelebrities(params?: {
  category?: string;
  is_active?: boolean;
  skip?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: [...queryKeys.celebrities, params],
    queryFn: () => api.getCelebrities(params),
  });
}

export function useCelebrity(id: string) {
  return useQuery({
    queryKey: queryKeys.celebrity(id),
    queryFn: () => api.getCelebrity(id),
    enabled: !!id,
  });
}

export function useCreateCelebrity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Celebrity>) => api.createCelebrity(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.celebrities });
    },
  });
}

export function useUpdateCelebrity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Celebrity> }) =>
      api.updateCelebrity(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.celebrity(id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.celebrities });
    },
  });
}

export function useDeleteCelebrity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteCelebrity(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.celebrities });
    },
  });
}

export function useScrapeCelebrity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.scrapeCelebrity(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.celebrity(id) });
    },
  });
}

// Posts
export function usePosts(params?: {
  celebrity_id?: string;
  is_viral?: boolean;
  min_viral_score?: number;
  skip?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: [...queryKeys.posts, params],
    queryFn: () => api.getPosts(params),
  });
}

export function usePost(id: string) {
  return useQuery({
    queryKey: queryKeys.post(id),
    queryFn: () => api.getPost(id),
    enabled: !!id,
  });
}

export function usePostComments(id: string, params?: { skip?: number; limit?: number }) {
  return useQuery({
    queryKey: [...queryKeys.postComments(id), params],
    queryFn: () => api.getPostComments(id, params),
    enabled: !!id,
  });
}

export function useViralPosts(params?: { min_score?: number; limit?: number }) {
  return useQuery({
    queryKey: [...queryKeys.viralPosts, params],
    queryFn: () => api.getViralPosts(params),
  });
}

// Analytics
export function useDashboardStats() {
  return useQuery({
    queryKey: queryKeys.dashboard,
    queryFn: () => api.getDashboardStats(),
    refetchInterval: 60000, // Refresh every minute
  });
}

export function useTrending(params?: {
  type?: 'celebrities' | 'topics' | 'posts';
  limit?: number;
}) {
  return useQuery({
    queryKey: [...queryKeys.trending, params],
    queryFn: () => api.getTrending(params),
  });
}

export function useCelebrityAnalytics(id: string, params?: { days?: number }) {
  return useQuery({
    queryKey: [...queryKeys.celebrityAnalytics(id), params],
    queryFn: () => api.getCelebrityAnalytics(id, params),
    enabled: !!id,
  });
}

// Analysis
export function usePostAnalysis(postId: string) {
  return useQuery({
    queryKey: queryKeys.postAnalysis(postId),
    queryFn: () => api.getPostAnalysis(postId),
    enabled: !!postId,
  });
}

export function useAnalysis(analysisId: string) {
  return useQuery({
    queryKey: ['analysis', analysisId],
    queryFn: () => api.getAnalysisById(analysisId),
    enabled: !!analysisId,
  });
}

export function useTriggerAnalysis() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (postId: string) => api.triggerAnalysis(postId),
    onSuccess: (_, postId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.postAnalysis(postId) });
    },
  });
}

export function useRecentAnalyses(params?: { limit?: number }) {
  return useQuery({
    queryKey: [...queryKeys.recentAnalyses, params],
    queryFn: () => api.getRecentAnalyses(params),
  });
}

// Content Generation
export function useGenerateContent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      postAnalysisId,
      params,
    }: {
      postAnalysisId: string;
      params?: { content_type?: string; template?: string };
    }) => api.generateContent(postAnalysisId, params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.content });
    },
  });
}

export function useGeneratedContent(params?: {
  status?: string;
  content_type?: string;
  skip?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: [...queryKeys.content, params],
    queryFn: () => api.getGeneratedContent(params),
  });
}

export function useContentById(id: string) {
  return useQuery({
    queryKey: queryKeys.contentById(id),
    queryFn: () => api.getContentById(id),
    enabled: !!id,
  });
}

// Publishing
export function useScheduleContent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      contentId,
      params,
    }: {
      contentId: string;
      params?: { scheduled_time?: string; auto_approve?: boolean };
    }) => api.scheduleContent(contentId, params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.publishingQueue });
      queryClient.invalidateQueries({ queryKey: queryKeys.content });
    },
  });
}

export function useApproveContent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ contentId, scheduleNow }: { contentId: string; scheduleNow?: boolean }) =>
      api.approveContent(contentId, scheduleNow),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.publishingQueue });
      queryClient.invalidateQueries({ queryKey: queryKeys.content });
    },
  });
}

export function useRejectContent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ contentId, reason }: { contentId: string; reason?: string }) =>
      api.rejectContent(contentId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.publishingQueue });
      queryClient.invalidateQueries({ queryKey: queryKeys.content });
    },
  });
}

export function usePublishNow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (contentId: string) => api.publishNow(contentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.publishingQueue });
      queryClient.invalidateQueries({ queryKey: queryKeys.content });
    },
  });
}

export function usePublishingQueue() {
  return useQuery({
    queryKey: queryKeys.publishingQueue,
    queryFn: () => api.getPublishingQueue(),
    refetchInterval: 30000,
  });
}

export function useOptimalTimes(count?: number) {
  return useQuery({
    queryKey: [...queryKeys.optimalTimes, count],
    queryFn: () => api.getOptimalTimes(count),
  });
}

export function usePublishingStats() {
  return useQuery({
    queryKey: queryKeys.publishingStats,
    queryFn: () => api.getPublishingStats(),
  });
}

export function useAccountInfo() {
  return useQuery({
    queryKey: queryKeys.accountInfo,
    queryFn: () => api.getAccountInfo(),
  });
}

// Settings
export function useSettings() {
  return useQuery({
    queryKey: queryKeys.settings,
    queryFn: () => api.getSettings(),
  });
}

export function useUpdateSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (settings: Record<string, unknown>) => api.updateSettings(settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.settings });
    },
  });
}
