'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ArchetypeBadge } from '@/components/passport/ArchetypeBadge';

// TODO: Replace with actual API call
const mockCandidates = [
  {
    user_id: '1',
    display_name: 'Jane Developer',
    archetype: 'careful_tester',
    metrics: { debug_efficiency: 0.82, craftsmanship: 0.71 },
    sessions_completed: 12,
  },
  {
    user_id: '2',
    display_name: 'John Coder',
    archetype: 'fast_iterator',
    metrics: { debug_efficiency: 0.65, craftsmanship: 0.58 },
    sessions_completed: 8,
  },
];

const archetypes = [
  { value: '', label: 'All Archetypes' },
  { value: 'careful_tester', label: 'Careful Tester' },
  { value: 'fast_iterator', label: 'Fast Iterator' },
  { value: 'refactor_first', label: 'Refactor First' },
  { value: 'debugger', label: 'Debugger' },
];

export default function CandidatesPage() {
  const [selectedArchetype, setSelectedArchetype] = useState('');

  const filteredCandidates = selectedArchetype
    ? mockCandidates.filter((c) => c.archetype === selectedArchetype)
    : mockCandidates;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
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

      <div className="grid gap-4">
        {filteredCandidates.map((candidate) => (
          <Link
            key={candidate.user_id}
            href={`/recruiter/candidates/${candidate.user_id}`}
            className="block p-6 bg-white dark:bg-slate-800 rounded-lg shadow-sm hover:shadow-md transition-shadow"
          >
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-lg font-semibold">{candidate.display_name}</h3>
                <div className="mt-2">
                  <ArchetypeBadge archetype={candidate.archetype} />
                </div>
                <div className="mt-3 text-sm text-gray-600 dark:text-gray-300">
                  <span>Debug Efficiency: {(candidate.metrics.debug_efficiency * 100).toFixed(0)}%</span>
                  <span className="mx-2">•</span>
                  <span>Craftsmanship: {(candidate.metrics.craftsmanship * 100).toFixed(0)}%</span>
                  <span className="mx-2">•</span>
                  <span>{candidate.sessions_completed} sessions</span>
                </div>
              </div>
              <span className="text-primary-600">View Passport →</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
