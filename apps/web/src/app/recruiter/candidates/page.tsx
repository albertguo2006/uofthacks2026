'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { ArchetypeBadge } from '@/components/passport/ArchetypeBadge';
import { api } from '@/lib/api';

type Candidate = {
  user_id: string;
  display_name: string;
  email: string;
  archetype: string | null;
  archetype_label: string | null;
  metrics: Record<string, number>;
  sessions_completed: number;
  has_video: boolean;
};

const archetypes = [
  { value: '', label: 'All Archetypes' },
  { value: 'careful_tester', label: 'Careful Tester' },
  { value: 'fast_iterator', label: 'Fast Iterator' },
  { value: 'refactor_first', label: 'Refactor First' },
  { value: 'debugger', label: 'Debugger' },
  { value: 'craftsman', label: 'Craftsman' },
];

export default function CandidatesPage() {
  const [selectedArchetype, setSelectedArchetype] = useState('');
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchCandidates() {
      setIsLoading(true);
      setError(null);
      try {
        const response = await api.getCandidates(selectedArchetype || undefined);
        setCandidates(response.candidates);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch candidates');
        setCandidates([]);
      } finally {
        setIsLoading(false);
      }
    }
    fetchCandidates();
  }, [selectedArchetype]);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center flex-wrap gap-4">
        <h1 className="text-3xl font-bold">Candidates</h1>
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

      {isLoading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg">
          {error}
        </div>
      )}

      {!isLoading && !error && candidates.length === 0 && (
        <div className="text-center py-12 text-gray-600 dark:text-gray-400">
          No candidates found
        </div>
      )}

      {!isLoading && !error && candidates.length > 0 && (
        <div className="grid gap-4">
          {candidates.map((candidate) => (
            <Link
              key={candidate.user_id}
              href={`/recruiter/candidates/${candidate.user_id}`}
              className="block p-6 bg-white dark:bg-slate-800 rounded-lg shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-semibold">{candidate.display_name}</h3>
                    {candidate.has_video && (
                      <span className="px-2 py-0.5 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full">
                        Has Video
                      </span>
                    )}
                  </div>
                  {candidate.archetype && (
                    <div className="mt-2">
                      <ArchetypeBadge archetype={candidate.archetype} />
                    </div>
                  )}
                  <div className="mt-3 text-sm text-gray-600 dark:text-gray-300">
                    {candidate.metrics.debug_efficiency !== undefined && (
                      <>
                        <span>Debug Efficiency: {(candidate.metrics.debug_efficiency * 100).toFixed(0)}%</span>
                        <span className="mx-2">•</span>
                      </>
                    )}
                    {candidate.metrics.craftsmanship !== undefined && (
                      <>
                        <span>Craftsmanship: {(candidate.metrics.craftsmanship * 100).toFixed(0)}%</span>
                        <span className="mx-2">•</span>
                      </>
                    )}
                    <span>{candidate.sessions_completed} sessions</span>
                  </div>
                </div>
                <span className="text-primary-600">View Passport →</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
