'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { Passport } from '@/types/passport';
import { useAuth } from './useAuth';

// Helper to check if we're in dev mode
function isDevMode(): boolean {
  if (typeof window === 'undefined') return false;
  const params = new URLSearchParams(window.location.search);
  return params.get('dev') === 'true';
}

// Mock passport data for Jane Candidate in dev mode
const MOCK_JANE_PASSPORT: Passport = {
  user_id: 'dev-candidate-123',
  display_name: 'Jane Candidate',
  archetype: {
    name: 'craftsman',
    label: 'Code Craftsman',
    description: 'Focuses on clean, maintainable code with attention to detail',
    confidence: 0.87,
  },
  skill_vector: [0.85, 0.78, 0.72, 0.68, 0.65, 0.82, 0.75, 0.80],
  metrics: {
    iteration_velocity: 0.72,
    debug_efficiency: 0.85,
    craftsmanship: 0.91,
    tool_fluency: 0.78,
    integrity: 1.0,
  },
  sessions_completed: 12,
  tasks_passed: 10,
  notable_moments: [
    {
      type: 'achievement',
      description: 'Solved complex async race condition in under 5 minutes',
      session_id: 'session-001',
      timestamp: '2026-01-10T14:30:00Z',
    },
    {
      type: 'insight',
      description: "Identified edge case that wasn't in the test suite",
      session_id: 'session-003',
      timestamp: '2026-01-12T10:15:00Z',
    },
    {
      type: 'achievement',
      description: 'Refactored legacy code with zero regressions',
      session_id: 'session-007',
      timestamp: '2026-01-14T16:45:00Z',
    },
  ],
  interview: {
    has_video: true,
    video_id: 'mock-video-123',
    highlights: [
      {
        timestamp: '02:34',
        description: 'Explained approach to debugging systematically',
        query: 'debugging methodology',
      },
      {
        timestamp: '08:15',
        description: 'Discussed trade-offs in architecture decisions',
        query: 'system design',
      },
    ],
  },
  updated_at: '2026-01-15T10:30:00Z',
};

// Mock passport data for Bob Developer
const MOCK_BOB_PASSPORT: Passport = {
  user_id: 'dev-candidate-456',
  display_name: 'Bob Developer',
  archetype: {
    name: 'fast_iterator',
    label: 'Fast Iterator',
    description: 'Rapidly prototypes and iterates on solutions',
    confidence: 0.82,
  },
  skill_vector: [0.95, 0.68, 0.72, 0.88, 0.70, 0.75, 0.80, 0.65],
  metrics: {
    iteration_velocity: 0.95,
    debug_efficiency: 0.68,
    craftsmanship: 0.72,
    tool_fluency: 0.88,
    integrity: 1.0,
  },
  sessions_completed: 8,
  tasks_passed: 7,
  notable_moments: [
    {
      type: 'achievement',
      description: 'Completed 3 tasks in a single session',
      session_id: 'session-002',
      timestamp: '2026-01-11T09:00:00Z',
    },
  ],
  interview: {
    has_video: false,
    highlights: [],
  },
  updated_at: '2026-01-14T15:00:00Z',
};

// Mock passport data for Alice Engineer
const MOCK_ALICE_PASSPORT: Passport = {
  user_id: 'dev-candidate-789',
  display_name: 'Alice Engineer',
  archetype: {
    name: 'debugger',
    label: 'Debugger',
    description: 'Excels at finding and fixing complex bugs',
    confidence: 0.91,
  },
  skill_vector: [0.65, 0.95, 0.80, 0.75, 0.85, 0.70, 0.88, 0.72],
  metrics: {
    iteration_velocity: 0.65,
    debug_efficiency: 0.95,
    craftsmanship: 0.80,
    tool_fluency: 0.75,
    integrity: 1.0,
  },
  sessions_completed: 15,
  tasks_passed: 14,
  notable_moments: [
    {
      type: 'achievement',
      description: 'Found and fixed a memory leak in 2 minutes',
      session_id: 'session-005',
      timestamp: '2026-01-13T11:30:00Z',
    },
    {
      type: 'insight',
      description: 'Identified root cause of intermittent test failure',
      session_id: 'session-008',
      timestamp: '2026-01-15T14:00:00Z',
    },
  ],
  interview: {
    has_video: true,
    video_id: 'mock-video-789',
    highlights: [
      {
        timestamp: '05:22',
        description: 'Demonstrated systematic debugging approach',
        query: 'debugging',
      },
    ],
  },
  updated_at: '2026-01-16T09:00:00Z',
};

// Map of user IDs to mock passports
const MOCK_PASSPORTS: Record<string, Passport> = {
  'dev-candidate-123': MOCK_JANE_PASSPORT,
  'dev-candidate-456': MOCK_BOB_PASSPORT,
  'dev-candidate-789': MOCK_ALICE_PASSPORT,
};

export function usePassport(userId?: string) {
  const { user } = useAuth();
  const [passport, setPassport] = useState<Passport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const targetUserId = userId || user?.user_id;

  const fetchPassport = useCallback(async () => {
    // In dev mode, return mock data immediately
    if (isDevMode()) {
      // If a specific userId is provided, look it up in mock data
      if (targetUserId && MOCK_PASSPORTS[targetUserId]) {
        setPassport(MOCK_PASSPORTS[targetUserId]);
      } else {
        // Default to Jane's passport
        setPassport(MOCK_JANE_PASSPORT);
      }
      setIsLoading(false);
      setError(null);
      return;
    }

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
