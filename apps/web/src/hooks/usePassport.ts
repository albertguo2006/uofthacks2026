'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { Passport } from '@/types/passport';
import { useAuth } from './useAuth';

export function usePassport(userId?: string) {
  const { user } = useAuth();
  const [passport, setPassport] = useState<Passport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const targetUserId = userId || user?.user_id;

  const fetchPassport = useCallback(async () => {
    if (!targetUserId) {
      setIsLoading(false);
      return;
    }

    try {
      const response = await api.get<Passport>(`/passport/${targetUserId}`);
      setPassport(response);
      setError(null);
    } catch (err) {
      setError('Failed to fetch passport');
      setPassport(null);
    } finally {
      setIsLoading(false);
    }
  }, [targetUserId]);

  useEffect(() => {
    fetchPassport();
  }, [fetchPassport]);

  return {
    passport,
    isLoading,
    error,
    refetch: fetchPassport,
  };
}
