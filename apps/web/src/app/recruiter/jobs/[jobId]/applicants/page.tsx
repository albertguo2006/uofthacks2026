'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';

interface Applicant {
  application_id: string;
  user_id: string;
  display_name: string;
  email: string;
  applied_at: string;
  fit_score: number;
  archetype: string | null;
  archetype_label: string | null;
  sessions_completed: number;
  metrics: Record<string, number>;
  status: string;
}

interface JobInfo {
  job_id: string;
  title: string;
  company: string;
}

export default function ApplicantsPage() {
  const params = useParams();
  const jobId = params.jobId as string;

  const [applicants, setApplicants] = useState<Applicant[]>([]);
  const [jobInfo, setJobInfo] = useState<JobInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [applicantsData, jobsData] = await Promise.all([
          api.get<Applicant[]>(`/applications/job/${jobId}`),
          api.get<JobInfo[]>('/jobs/recruiter'),
        ]);

        setApplicants(applicantsData);

        const job = jobsData.find((j) => j.job_id === jobId);
        if (job) {
          setJobInfo(job);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch applicants');
      } finally {
        setIsLoading(false);
      }
    }

    fetchData();
  }, [jobId]);

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="animate-pulse bg-gray-200 dark:bg-slate-700 h-24 rounded-lg" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-center bg-white dark:bg-slate-800 rounded-lg">
        <p className="text-red-500">{error}</p>
        <Link href="/recruiter/jobs" className="text-primary-600 hover:underline mt-2 inline-block">
          Back to Jobs
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <Link href="/recruiter/jobs" className="text-primary-600 hover:underline text-sm">
          &larr; Back to Jobs
        </Link>
        <h1 className="text-3xl font-bold mt-2">
          Applicants for {jobInfo?.title || 'Job'}
        </h1>
        {jobInfo && (
          <p className="text-gray-600 dark:text-gray-300">{jobInfo.company}</p>
        )}
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          {applicants.length} applicant{applicants.length !== 1 ? 's' : ''} - sorted by fit score
        </p>
      </div>

      {applicants.length === 0 ? (
        <div className="p-8 text-center bg-white dark:bg-slate-800 rounded-lg">
          <p className="text-gray-600 dark:text-gray-300">
            No applications yet for this position.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {applicants.map((applicant, index) => (
            <div
              key={applicant.application_id}
              className="p-6 bg-white dark:bg-slate-800 rounded-lg shadow-sm"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl font-bold text-gray-300 dark:text-slate-600">
                      #{index + 1}
                    </span>
                    <div>
                      <h3 className="text-lg font-semibold">{applicant.display_name}</h3>
                      <p className="text-gray-500 dark:text-gray-400 text-sm">
                        {applicant.email}
                      </p>
                    </div>
                    {applicant.archetype_label && (
                      <span className="px-2 py-1 text-xs bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded">
                        {applicant.archetype_label}
                      </span>
                    )}
                  </div>

                  <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-gray-500 dark:text-gray-400">Tasks Completed</p>
                      <p className="font-semibold">{applicant.sessions_completed}</p>
                    </div>
                    {applicant.metrics.integrity !== undefined && (
                      <div>
                        <p className="text-gray-500 dark:text-gray-400">Integrity</p>
                        <p className="font-semibold">
                          {(applicant.metrics.integrity * 100).toFixed(0)}%
                        </p>
                      </div>
                    )}
                    {applicant.metrics.craftsmanship !== undefined && (
                      <div>
                        <p className="text-gray-500 dark:text-gray-400">Craftsmanship</p>
                        <p className="font-semibold">
                          {(applicant.metrics.craftsmanship * 100).toFixed(0)}%
                        </p>
                      </div>
                    )}
                    {applicant.metrics.debug_efficiency !== undefined && (
                      <div>
                        <p className="text-gray-500 dark:text-gray-400">Debug Efficiency</p>
                        <p className="font-semibold">
                          {(applicant.metrics.debug_efficiency * 100).toFixed(0)}%
                        </p>
                      </div>
                    )}
                  </div>

                  <p className="text-xs text-gray-400 mt-3">
                    Applied {new Date(applicant.applied_at).toLocaleDateString()}
                  </p>
                </div>

                <div className="text-right ml-4">
                  <div className="text-3xl font-bold text-primary-600">
                    {(applicant.fit_score * 100).toFixed(0)}%
                  </div>
                  <p className="text-sm text-gray-500">fit score</p>
                  <Link
                    href={`/recruiter/candidates/${applicant.user_id}`}
                    className="mt-3 inline-block px-4 py-2 bg-primary-600 text-white text-sm rounded hover:bg-primary-700"
                  >
                    View Profile
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
