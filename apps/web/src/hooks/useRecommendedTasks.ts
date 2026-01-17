'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { TaskSummary } from '@/types/task';

export type ReasonType = 'weak_area' | 'archetype_match' | 'confidence_builder' | 'error_pattern';

export interface RecommendedTask {
  task: TaskSummary;
  reason: string;
  reason_type: ReasonType;
  relevance_score: number;
}

export interface RecommendedTasksResponse {
  recommendations: RecommendedTask[];
  personalization_summary: string;
}

export function useRecommendedTasks(limit: number = 5) {
  const [recommendations, setRecommendations] = useState<RecommendedTask[]>([]);
  const [personalizationSummary, setPersonalizationSummary] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRecommendations = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await api.get<RecommendedTasksResponse>(`/tasks/recommended?limit=${limit}`);
      setRecommendations(response.recommendations);
      setPersonalizationSummary(response.personalization_summary);
      setError(null);
    } catch (err) {
      setError('Failed to fetch recommendations');
      console.error('Failed to fetch recommendations:', err);
    } finally {
      setIsLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    fetchRecommendations();
  }, [fetchRecommendations]);

  return {
    recommendations,
    personalizationSummary,
    isLoading,
    error,
    refetch: fetchRecommendations,
  };
}
