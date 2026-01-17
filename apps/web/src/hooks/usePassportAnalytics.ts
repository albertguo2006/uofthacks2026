'use client';

import { useState, useEffect, useCallback } from 'react';
import { api, PassportAnalytics } from '@/lib/api';
import { useAuth } from './useAuth';

export function usePassportAnalytics(userId?: string) {
  const { user } = useAuth();
  const [analytics, setAnalytics] = useState<PassportAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const targetUserId = userId || user?.user_id;

  const fetchAnalytics = useCallback(async () => {
    if (!targetUserId) {
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      const response = await api.getPassportAnalytics(targetUserId);
      setAnalytics(response);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch analytics');
      setAnalytics(null);
    } finally {
      setIsLoading(false);
    }
  }, [targetUserId]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  return {
    analytics,
    isLoading,
    error,
    refetch: fetchAnalytics,
  };
}

// Re-export the type for convenience
export type { PassportAnalytics };
