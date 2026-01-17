'use client';

export const dynamic = 'force-dynamic';

import Link from 'next/link';
import { usePassport } from '@/hooks/usePassport';
import { SkillPassport } from '@/components/passport/SkillPassport';
import { JobFeed } from '@/components/jobs/JobFeed';

export default function CandidateDashboard() {
  const { passport, isLoading } = usePassport();

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <Link
          href="/candidate/tasks"
          className="px-4 py-2 bg-primary-600 text-white rounded-lg transition-all duration-200 hover:shadow-[0_0_15px_rgba(255,255,255,0.5)] hover:ring-2 hover:ring-white/50"
        >
          Start a Task
        </Link>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        <div>
          <h2 className="text-xl font-semibold mb-4">Your Skill Passport</h2>
          {isLoading ? (
            <div className="animate-pulse bg-gray-200 dark:bg-slate-700 h-64 rounded-lg" />
          ) : passport ? (
            <SkillPassport passport={passport} compact />
          ) : (
            <div className="p-8 text-center bg-white dark:bg-slate-800 rounded-lg">
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Complete tasks to build your Skill Identity
              </p>
              <Link
                href="/candidate/tasks"
                className="text-primary-600 hover:underline"
              >
                Browse available tasks
              </Link>
            </div>
          )}
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-4">Available Jobs</h2>
          <JobFeed limit={5} />
        </div>
      </div>
    </div>
  );
}
