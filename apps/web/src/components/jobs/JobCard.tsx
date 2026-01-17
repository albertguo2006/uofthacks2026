'use client';

import { Job } from '@/types/job';

interface JobCardProps {
  job: Job;
}

export function JobCard({ job }: JobCardProps) {
  const tierColors = {
    0: 'border-gray-200 dark:border-slate-600',
    1: 'border-blue-300 dark:border-blue-700',
    2: 'border-purple-300 dark:border-purple-700',
  };

  const isLocked = !job.unlocked;

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
                🔒 Locked
              </span>
            )}
          </div>
          <p className="text-gray-600 dark:text-gray-300 text-sm mt-1">
            {job.company}
          </p>

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
        </div>

        <div className="text-right ml-4">
          <div className="text-sm text-gray-500">{job.salary_range}</div>
          {!isLocked && (
            <div className="mt-2">
              <span className="text-primary-600 font-semibold">
                {(job.fit_score * 100).toFixed(0)}% match
              </span>
            </div>
          )}
          {!isLocked && (
            <button className="mt-3 px-4 py-2 bg-primary-600 text-white text-sm rounded hover:bg-primary-700">
              Apply
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
