'use client';

import { useState } from 'react';
import { Job } from '@/types/job';
import { api } from '@/lib/api';

interface JobCardProps {
  job: Job;
  hasApplied?: boolean;
  onApply?: (jobId: string) => void;
}

export function JobCard({ job, hasApplied = false, onApply }: JobCardProps) {
  const [isApplying, setIsApplying] = useState(false);
  const [applied, setApplied] = useState(hasApplied);
  const [error, setError] = useState<string | null>(null);

  const tierColors = {
    0: 'border-gray-200 dark:border-slate-600',
    1: 'border-blue-300 dark:border-blue-700',
    2: 'border-purple-300 dark:border-purple-700',
  };

  const isLocked = !job.unlocked;

  const handleApply = async () => {
    setIsApplying(true);
    setError(null);
    try {
      await api.post('/applications', { job_id: job.job_id });
      setApplied(true);
      onApply?.(job.job_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to apply');
    } finally {
      setIsApplying(false);
    }
  };

  return (
    <div
      className={`p-6 bg-white dark:bg-slate-800 rounded-lg border-2 ${
        tierColors[job.tier as keyof typeof tierColors] || tierColors[0]
      } ${isLocked ? 'opacity-60' : ''}`}
    >
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold">{job.title}</h3>
            {isLocked && (
              <span className="px-2 py-0.5 text-xs bg-gray-200 dark:bg-slate-600 rounded">
                Locked
              </span>
            )}
          </div>
          <p className="text-gray-600 dark:text-gray-300 text-sm mt-1">
            {job.company}
          </p>

          {job.description && (
            <p className="text-gray-500 dark:text-gray-400 text-sm mt-2">
              {job.description}
            </p>
          )}

          <div className="flex flex-wrap gap-2 mt-3">
            {job.tags?.map((tag) => (
              <span
                key={tag}
                className="px-2 py-1 text-xs bg-gray-100 dark:bg-slate-700 rounded"
              >
                {tag}
              </span>
            ))}
          </div>

          {isLocked && job.unlock_requirements && (
            <div className="mt-3 p-2 bg-gray-50 dark:bg-slate-700 rounded text-sm">
              <p className="text-gray-500">
                Required fit: {(job.unlock_requirements.min_fit * 100).toFixed(0)}%
              </p>
              {job.unlock_requirements.missing && (
                <p className="text-gray-500">
                  Missing: {job.unlock_requirements.missing.join(', ')}
                </p>
              )}
            </div>
          )}

          {error && (
            <p className="mt-2 text-sm text-red-500">{error}</p>
          )}
        </div>

        <div className="text-right ml-4">
          <div className="text-sm text-gray-500">{job.salary_range}</div>
          <div className="text-sm text-gray-500">{job.location}</div>
          {!isLocked && (
            <div className="mt-2">
              <span className="text-primary-600 font-semibold">
                {(job.fit_score * 100).toFixed(0)}% match
              </span>
            </div>
          )}
          {!isLocked && (
            applied ? (
              <span className="mt-3 inline-block px-4 py-2 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-sm rounded">
                Applied
              </span>
            ) : (
              <button
                onClick={handleApply}
                disabled={isApplying}
                className="mt-3 px-4 py-2 bg-primary-600 text-white text-sm rounded hover:bg-primary-700 disabled:opacity-50"
              >
                {isApplying ? 'Applying...' : 'Apply'}
              </button>
            )
          )}
        </div>
      </div>
    </div>
  );
}
