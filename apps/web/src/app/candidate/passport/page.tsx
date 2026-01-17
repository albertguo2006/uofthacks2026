'use client';

import { usePassport } from '@/hooks/usePassport';
import { SkillPassport } from '@/components/passport/SkillPassport';

export default function PassportPage() {
  const { passport, isLoading, error } = usePassport();

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse bg-gray-200 dark:bg-slate-700 h-8 w-48 rounded" />
        <div className="animate-pulse bg-gray-200 dark:bg-slate-700 h-96 rounded-lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-center">
        <p className="text-red-600">Failed to load passport</p>
      </div>
    );
  }

  if (!passport) {
    return (
      <div className="p-8 text-center bg-white dark:bg-slate-800 rounded-lg">
        <h2 className="text-xl font-semibold mb-2">No Passport Yet</h2>
        <p className="text-gray-600 dark:text-gray-300">
          Complete tasks to build your Skill Identity and generate your passport.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Your Skill Passport</h1>
      <SkillPassport passport={passport} />
    </div>
  );
}
