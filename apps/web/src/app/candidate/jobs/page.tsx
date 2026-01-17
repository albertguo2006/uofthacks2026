'use client';

export const dynamic = 'force-dynamic';

import { JobFeed } from '@/components/jobs/JobFeed';

export default function JobsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Job Feed</h1>
        <p className="text-gray-600 dark:text-gray-300 mt-2">
          Jobs unlock as your Skill Identity evolves. Complete more tasks to access premium opportunities.
        </p>
      </div>

      <JobFeed showLocked />
    </div>
  );
}
