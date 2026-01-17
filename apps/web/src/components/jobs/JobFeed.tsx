'use client';

import { useState, useEffect } from 'react';
import { useJobFeed } from '@/hooks/useJobFeed';
import { JobCard } from './JobCard';
import { UnlockAnimation } from './UnlockAnimation';
import { api } from '@/lib/api';

interface JobFeedProps {
  limit?: number;
  showLocked?: boolean;
}

export function JobFeed({ limit, showLocked = false }: JobFeedProps) {
  const { jobs, isLoading, newlyUnlocked } = useJobFeed({ includeLocked: showLocked });
  const [appliedJobs, setAppliedJobs] = useState<Set<string>>(new Set());

  useEffect(() => {
    async function fetchApplications() {
      try {
        const jobIds = await api.get<string[]>('/applications/my');
        setAppliedJobs(new Set(jobIds));
      } catch {
        // Ignore errors fetching applications
      }
    }
    fetchApplications();
  }, []);

  const handleApply = (jobId: string) => {
    setAppliedJobs((prev) => new Set([...prev, jobId]));
  };

  const displayJobs = limit ? jobs?.slice(0, limit) : jobs;

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="animate-pulse bg-gray-200 dark:bg-slate-700 h-32 rounded-lg" />
        ))}
      </div>
    );
  }

  if (!displayJobs || displayJobs.length === 0) {
    return (
      <div className="p-8 text-center bg-white dark:bg-slate-800 rounded-lg">
        <p className="text-gray-600 dark:text-gray-300">
          No jobs available yet. Complete more tasks to unlock opportunities.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {newlyUnlocked && <UnlockAnimation jobTitle={newlyUnlocked.title} />}

      {displayJobs.map((job) => (
        <JobCard
          key={job.job_id}
          job={job}
          hasApplied={appliedJobs.has(job.job_id)}
          onApply={handleApply}
        />
      ))}
    </div>
  );
}
