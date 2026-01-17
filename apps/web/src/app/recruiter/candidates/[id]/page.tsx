'use client';

import { useParams } from 'next/navigation';
import { SkillPassport } from '@/components/passport/SkillPassport';
import { HighlightsList } from '@/components/video/HighlightsList';

// TODO: Replace with actual API call
const mockPassport = {
  user_id: '1',
  display_name: 'Jane Developer',
  archetype: {
    name: 'careful_tester',
    label: 'Careful Tester',
    description: 'Prioritizes test coverage and validation before shipping',
    confidence: 0.85,
  },
  skill_vector: [0.7, 0.8, 0.1],
  metrics: {
    iteration_velocity: 0.65,
    debug_efficiency: 0.82,
    craftsmanship: 0.71,
    tool_fluency: 0.58,
    integrity: 0.95,
  },
  sessions_completed: 12,
  tasks_passed: 10,
  notable_moments: [
    {
      type: 'achievement',
      description: 'Fixed 5 consecutive errors without re-running',
      timestamp: '2024-01-15T10:30:00Z',
    },
  ],
  interview: {
    has_video: true,
    highlights: [
      {
        timestamp: '02:34',
        description: 'Explained testing philosophy',
        query: 'testing approach',
      },
      {
        timestamp: '05:12',
        description: 'Discussed debugging strategy',
        query: 'debugging',
      },
    ],
  },
};

export default function CandidateDetailPage() {
  const params = useParams();
  const candidateId = params.id as string;

  // TODO: Fetch actual passport data
  const passport = mockPassport;

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">{passport.display_name}</h1>
        <button className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
          Invite to Interview
        </button>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <SkillPassport passport={passport} />
        </div>

        <div className="space-y-6">
          <div className="bg-white dark:bg-slate-800 rounded-lg p-6">
            <h3 className="font-semibold mb-4">Interview Highlights</h3>
            {passport.interview.has_video ? (
              <HighlightsList highlights={passport.interview.highlights} />
            ) : (
              <p className="text-gray-600 dark:text-gray-300">
                No interview video uploaded
              </p>
            )}
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-lg p-6">
            <h3 className="font-semibold mb-4">Search Video</h3>
            <input
              type="text"
              placeholder="e.g., 'testing strategy'"
              className="w-full px-4 py-2 border rounded-lg"
            />
            <button className="mt-2 w-full px-4 py-2 bg-gray-100 dark:bg-slate-700 rounded-lg hover:bg-gray-200">
              Search
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
