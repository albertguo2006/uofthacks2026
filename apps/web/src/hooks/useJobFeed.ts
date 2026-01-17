'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { api } from '@/lib/api';
import { Job } from '@/types/job';
import { POLLING_INTERVAL } from '@/lib/constants';

interface UseJobFeedOptions {
  includeLocked?: boolean;
}

interface JobsResponse {
  jobs: Job[];
  user_skill_vector: number[];
  last_updated: string;
}

export function useJobFeed(options: UseJobFeedOptions = {}) {
  const { includeLocked = false } = options;
  const [jobs, setJobs] = useState<Job[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newlyUnlocked, setNewlyUnlocked] = useState<Job | null>(null);

  const previousJobIds = useRef<Set<string>>(new Set());

  const fetchJobs = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (includeLocked) {
        params.set('include_locked', 'true');
      }

      const response = await api.get<JobsResponse>(`/jobs?${params}`);

      // Check for newly unlocked jobs
      const currentUnlockedIds = new Set(
        response.jobs.filter((j) => j.unlocked).map((j) => j.job_id)
      );

      for (const job of response.jobs) {
        if (job.unlocked && !previousJobIds.current.has(job.job_id)) {
          // New job unlocked!
          setNewlyUnlocked(job);
          setTimeout(() => setNewlyUnlocked(null), 5000);
          break;
        }
      }

      previousJobIds.current = currentUnlockedIds;
      setJobs(response.jobs);
      setError(null);
    } catch (err) {
      setError('Failed to fetch jobs');
    } finally {
      setIsLoading(false);
    }
  }, [includeLocked]);

  // Initial fetch
  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  // Polling
  useEffect(() => {
    const interval = setInterval(fetchJobs, POLLING_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchJobs]);

  return {
    jobs,
    isLoading,
    error,
    newlyUnlocked,
    refetch: fetchJobs,
  };
}
