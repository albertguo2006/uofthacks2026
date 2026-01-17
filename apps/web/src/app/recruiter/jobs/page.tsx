'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { CreateJobForm } from '@/components/jobs/CreateJobForm';

interface RecruiterJob {
  job_id: string;
  title: string;
  description: string;
  company: string;
  tier: number;
  salary_range: string;
  location: string;
  tags: string[];
  created_at: string;
}

export default function RecruiterJobsPage() {
  const [jobs, setJobs] = useState<RecruiterJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchJobs = useCallback(async () => {
    try {
      const data = await api.get<RecruiterJob[]>('/jobs/recruiter');
      setJobs(data);
    } catch (err) {
      console.error('Failed to fetch jobs:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  const handleDelete = async (jobId: string) => {
    if (!confirm('Are you sure you want to delete this job posting?')) return;

    setDeletingId(jobId);
    try {
      await api.delete(`/jobs/${jobId}`);
      setJobs(jobs.filter((j) => j.job_id !== jobId));
    } catch (err) {
      console.error('Failed to delete job:', err);
    } finally {
      setDeletingId(null);
    }
  };

  const handleCreateSuccess = () => {
    setShowCreateForm(false);
    fetchJobs();
  };

  const tierLabels = ['Entry Level', 'Mid Level', 'Senior Level'];

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="animate-pulse bg-gray-200 dark:bg-slate-700 h-32 rounded-lg" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">My Job Postings</h1>
          <p className="text-gray-600 dark:text-gray-300 mt-1">
            Create and manage your job listings
          </p>
        </div>
        <Button onClick={() => setShowCreateForm(true)}>Create New Job</Button>
      </div>

      {showCreateForm && (
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-4">Create New Job Posting</h2>
          <CreateJobForm
            onSuccess={handleCreateSuccess}
            onCancel={() => setShowCreateForm(false)}
          />
        </div>
      )}

      {jobs.length === 0 && !showCreateForm ? (
        <div className="p-8 text-center bg-white dark:bg-slate-800 rounded-lg">
          <p className="text-gray-600 dark:text-gray-300 mb-4">
            You haven&apos;t created any job postings yet.
          </p>
          <Button onClick={() => setShowCreateForm(true)}>Create Your First Job</Button>
        </div>
      ) : (
        <div className="space-y-4">
          {jobs.map((job) => (
            <div
              key={job.job_id}
              className="bg-white dark:bg-slate-800 rounded-lg shadow-sm p-6"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-semibold">{job.title}</h3>
                    <span className="px-2 py-0.5 text-xs bg-gray-100 dark:bg-slate-700 rounded">
                      {tierLabels[job.tier]}
                    </span>
                  </div>
                  <p className="text-gray-600 dark:text-gray-400">{job.company}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                    {job.description}
                  </p>
                  <div className="flex items-center gap-4 mt-3 text-sm text-gray-500 dark:text-gray-400">
                    <span>{job.salary_range}</span>
                    <span>{job.location}</span>
                  </div>
                  {job.tags.length > 0 && (
                    <div className="flex gap-2 mt-3">
                      {job.tags.map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-1 text-xs bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDelete(job.job_id)}
                  disabled={deletingId === job.job_id}
                  className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
                >
                  {deletingId === job.job_id ? 'Deleting...' : 'Delete'}
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
