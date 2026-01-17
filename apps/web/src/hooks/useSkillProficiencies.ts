'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { useAuth } from './useAuth';

export interface SkillProficiency {
  name: string;
  score: number; // 0-1
  tasks_completed: number;
}

interface SkillProficienciesResponse {
  proficiencies: SkillProficiency[];
}

export function useSkillProficiencies(userId?: string) {
  const { user } = useAuth();
  const [proficiencies, setProficiencies] = useState<SkillProficiency[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const targetUserId = userId || user?.user_id;

  const fetchProficiencies = useCallback(async () => {
    if (!targetUserId) {
      setIsLoading(false);
      return;
    }

    try {
      const response = await api.get<SkillProficienciesResponse>(
        `/passport/${targetUserId}/proficiencies`
      );
      setProficiencies(response.proficiencies || []);
      setError(null);
    } catch (err) {
      setError('Failed to fetch skill proficiencies');
      setProficiencies([]);
    } finally {
      setIsLoading(false);
    }
  }, [targetUserId]);

  useEffect(() => {
    fetchProficiencies();
  }, [fetchProficiencies]);

  return {
    proficiencies,
    isLoading,
    error,
    refetch: fetchProficiencies,
  };
}
