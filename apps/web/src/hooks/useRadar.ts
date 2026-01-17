'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '@/lib/api';
import { useAuth } from './useAuth';

export interface RadarDimension {
  score: number;
  confidence: number;
}

export interface RadarProfile {
  verification?: RadarDimension;
  velocity?: RadarDimension;
  optimization?: RadarDimension;
  decomposition?: RadarDimension;
  debugging?: RadarDimension;
}

export interface Intervention {
  hint: string | null;
  hint_category?: string;
  intervention_type?: string;
  session_id: string;
  triggered_at?: string;
}

export interface RadarResponse {
  user_id: string;
  radar_profile: RadarProfile | null;
  intervention: Intervention | null;
  radar_summary?: string;
}

interface UseRadarOptions {
  /** Polling interval in milliseconds (default: 5000) */
  pollInterval?: number;
  /** Whether to enable polling (default: true) */
  enablePolling?: boolean;
}

export function useRadar(userId?: string, options: UseRadarOptions = {}) {
  const { pollInterval = 5000, enablePolling = true } = options;
  const { user } = useAuth();
  const [radarData, setRadarData] = useState<RadarResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const targetUserId = userId || user?.user_id;

  const fetchRadar = useCallback(async () => {
    if (!targetUserId) {
      setIsLoading(false);
      return;
    }

    try {
      const response = await api.get<RadarResponse>(`/radar/${targetUserId}`);
      setRadarData(response);
      setError(null);
    } catch (err) {
      setError('Failed to fetch radar profile');
    } finally {
      setIsLoading(false);
    }
  }, [targetUserId]);

  // Initial fetch
  useEffect(() => {
    fetchRadar();
  }, [fetchRadar]);

  // Polling
  useEffect(() => {
    if (enablePolling && targetUserId) {
      intervalRef.current = setInterval(fetchRadar, pollInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchRadar, pollInterval, enablePolling, targetUserId]);

  const acknowledgeHint = useCallback(async (sessionId: string) => {
    try {
      await api.post('/radar/intervention/acknowledge', { session_id: sessionId });
      // Refetch to update state
      await fetchRadar();
    } catch (err) {
      console.error('Failed to acknowledge hint:', err);
    }
  }, [fetchRadar]);

  const reportEffectiveness = useCallback(async (
    sessionId: string,
    codeChanged: boolean,
    issueResolved: boolean
  ) => {
    try {
      await api.post('/radar/intervention/effectiveness', {
        session_id: sessionId,
        code_changed: codeChanged,
        issue_resolved: issueResolved,
      });
    } catch (err) {
      console.error('Failed to report effectiveness:', err);
    }
  }, []);

  return {
    radarProfile: radarData?.radar_profile || null,
    intervention: radarData?.intervention || null,
    radarSummary: radarData?.radar_summary || null,
    isLoading,
    error,
    refetch: fetchRadar,
    acknowledgeHint,
    reportEffectiveness,
  };
}

/**
 * Hook specifically for getting intervention status during a coding session
 */
export function useSessionIntervention(sessionId: string | null) {
  const [intervention, setIntervention] = useState<Intervention | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchIntervention = useCallback(async () => {
    if (!sessionId) return;

    try {
      const response = await api.get<{ intervention: Intervention | null }>(
        `/radar/session/${sessionId}/intervention`
      );
      setIntervention(response.intervention);
    } catch (err) {
      // Silently fail - intervention check is non-critical
      console.debug('Failed to check intervention:', err);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  // Initial fetch
  useEffect(() => {
    if (sessionId) {
      setIsLoading(true);
      fetchIntervention();
    }
  }, [sessionId, fetchIntervention]);

  // Poll for interventions during active session
  useEffect(() => {
    if (sessionId) {
      intervalRef.current = setInterval(fetchIntervention, 3000);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [sessionId, fetchIntervention]);

  const acknowledgeHint = useCallback(async () => {
    if (!sessionId) return;

    try {
      await api.post('/radar/intervention/acknowledge', { session_id: sessionId });
      setIntervention(null);
    } catch (err) {
      console.error('Failed to acknowledge hint:', err);
    }
  }, [sessionId]);

  const requestContextualHint = useCallback(async (
    taskId: string,
    currentCode: string,
    currentError?: string | null,
  ) => {
    if (!sessionId) return null;

    try {
      const response = await api.post<{
        hint: string;
        context: {
          attempts: number;
          repeated_errors: boolean;
          code_history_length: number;
        };
        hint_id: string;
      }>('/radar/session/hints', {
        session_id: sessionId,
        task_id: taskId,
        current_code: currentCode,
        current_error: currentError || null,
      });
      
      // Update local intervention state with the new hint
      setIntervention({
        hint: response.hint,
        hint_category: 'contextual',
        intervention_type: 'user_requested',
        session_id: sessionId,
      });
      
      return response;
    } catch (err) {
      console.error('Failed to request contextual hint:', err);
      return null;
    }
  }, [sessionId]);

  return {
    intervention,
    isLoading,
    acknowledgeHint,
    refetch: fetchIntervention,
    requestContextualHint,
  };
}
