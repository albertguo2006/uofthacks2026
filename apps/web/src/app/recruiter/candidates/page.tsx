'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { ArchetypeBadge } from '@/components/passport/ArchetypeBadge';
import { api } from '@/lib/api';

interface RankedCandidate {
  user_id: string;
  display_name: string;
  email?: string;
  archetype?: string;
  radar_profile?: Record<string, { score: number; confidence: number }>;
  sessions_completed: number;
  integrity_score?: number;
  ai_score: number;
  ai_strengths: string[];
  ai_gaps: string[];
  ai_recommendation: string;
}

interface Job {
  job_id: string;
  title: string;
  company: string;
  has_target_radar: boolean;
}

const archetypes = [
  { value: '', label: 'All Archetypes' },
  { value: 'careful_tester', label: 'Careful Tester' },
  { value: 'fast_iterator', label: 'Fast Iterator' },
  { value: 'refactor_first', label: 'Refactor First' },
  { value: 'debugger', label: 'Debugger' },
  { value: 'craftsman', label: 'Craftsman' },
];

export default function CandidatesPage() {
  const [candidates, setCandidates] = useState<RankedCandidate[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJob, setSelectedJob] = useState<string>('');
  const [selectedArchetype, setSelectedArchetype] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch jobs for the dropdown
  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const response = await api.get<{ jobs: Job[] }>('/recruiter/jobs');
        setJobs(response.jobs);
      } catch (err) {
        console.error('Failed to fetch jobs:', err);
      }
    };
    fetchJobs();
  }, []);

  // Fetch ranked candidates
  const fetchCandidates = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (selectedJob) {
        params.append('job_id', selectedJob);
      }
      
      const response = await api.get<{
        candidates: RankedCandidate[];
        total_candidates: number;
      }>(`/recruiter/candidates/ranked?${params.toString()}`);
      
      setCandidates(response.candidates);
    } catch (err) {
      setError('Failed to load candidates. Please try again.');
      console.error('Failed to fetch candidates:', err);
    } finally {
      setIsLoading(false);
    }
  }, [selectedJob]);

  useEffect(() => {
    fetchCandidates();
  }, [fetchCandidates]);

  // Filter by archetype (client-side)
  const filteredCandidates = selectedArchetype
    ? candidates.filter((c) => c.archetype === selectedArchetype)
    : candidates;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center flex-wrap gap-4">
        <h1 className="text-3xl font-bold">AI-Ranked Candidates</h1>
        <div className="flex gap-3">
          {/* Job Filter */}
          <select
            value={selectedJob}
            onChange={(e) => setSelectedJob(e.target.value)}
            className="px-4 py-2 border rounded-lg bg-white dark:bg-slate-800"
          >
            <option value="">All Candidates</option>
            {jobs.map((job) => (
              <option key={job.job_id} value={job.job_id}>
                {job.title} {job.has_target_radar && '⭐'}
              </option>
            ))}
          </select>

          {/* Archetype Filter */}
          <select
            value={selectedArchetype}
            onChange={(e) => setSelectedArchetype(e.target.value)}
            className="px-4 py-2 border rounded-lg bg-white dark:bg-slate-800"
          >
            {archetypes.map((a) => (
              <option key={a.value} value={a.value}>
                {a.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-500">Analyzing candidates with AI...</p>
        </div>
      ) : error ? (
        <div className="text-center py-12">
          <p className="text-red-500 mb-4">{error}</p>
          <button
            onClick={fetchCandidates}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-500"
          >
            Try Again
          </button>
        </div>
      ) : filteredCandidates.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          No candidates found matching your criteria.
        </div>
      ) : (
        <div className="grid gap-4">
          {filteredCandidates.map((candidate, index) => (
            <CandidateCard
              key={candidate.user_id}
              candidate={candidate}
              rank={index + 1}
              jobId={selectedJob}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function CandidateCard({
  candidate,
  rank,
  jobId,
}: {
  candidate: RankedCandidate;
  rank: number;
  jobId?: string;
}) {
  const scoreColor =
    candidate.ai_score >= 0.8
      ? 'text-green-500'
      : candidate.ai_score >= 0.6
      ? 'text-yellow-500'
      : 'text-red-500';

  const scoreBgColor =
    candidate.ai_score >= 0.8
      ? 'bg-green-500/10 border-green-500/30'
      : candidate.ai_score >= 0.6
      ? 'bg-yellow-500/10 border-yellow-500/30'
      : 'bg-red-500/10 border-red-500/30';

  return (
    <Link
      href={`/recruiter/candidates/${candidate.user_id}${jobId ? `?job_id=${jobId}` : ''}`}
      className="block p-6 bg-white dark:bg-slate-800 rounded-lg shadow-sm hover:shadow-md transition-shadow"
    >
      <div className="flex justify-between items-start gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-3">
            {/* Rank Badge */}
            <span className="w-8 h-8 flex items-center justify-center bg-slate-100 dark:bg-slate-700 rounded-full text-sm font-bold">
              #{rank}
            </span>
            <h3 className="text-lg font-semibold">{candidate.display_name}</h3>
            {candidate.archetype && (
              <ArchetypeBadge archetype={candidate.archetype} />
            )}
          </div>

          {/* AI Recommendation */}
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
            {candidate.ai_recommendation}
          </p>

          {/* Stats Row */}
          <div className="mt-3 flex flex-wrap gap-4 text-sm text-gray-500">
            <span>{candidate.sessions_completed} sessions completed</span>
            {candidate.integrity_score !== undefined && (
              <span>
                Integrity: {(candidate.integrity_score * 100).toFixed(0)}%
              </span>
            )}
          </div>

          {/* Strengths & Gaps */}
          <div className="mt-3 flex flex-wrap gap-2">
            {candidate.ai_strengths.slice(0, 3).map((strength, i) => (
              <span
                key={i}
                className="px-2 py-0.5 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded"
              >
                {strength}
              </span>
            ))}
            {candidate.ai_gaps.slice(0, 2).map((gap, i) => (
              <span
                key={i}
                className="px-2 py-0.5 text-xs bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded"
              >
                {gap}
              </span>
            ))}
          </div>
        </div>

        {/* AI Score */}
        <div className={`text-center p-3 rounded-lg border ${scoreBgColor}`}>
          <div className={`text-2xl font-bold ${scoreColor}`}>
            {(candidate.ai_score * 100).toFixed(0)}%
          </div>
          <div className="text-xs text-gray-500">AI Match</div>
        </div>
      </div>
    </Link>
  );
}
