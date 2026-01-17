'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { SignOutButton } from '@/components/auth/SignOutButton';

export default function CandidateLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const searchParams = useSearchParams();
  const isDevMode = searchParams.get('dev') === 'true';
  const devSuffix = isDevMode ? '?dev=true' : '';

  return (
    <ProtectedRoute role="candidate">
      <div className="min-h-screen">
        <nav className="bg-white dark:bg-slate-800 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center space-x-8">
                <Link href={`/candidate${devSuffix}`} className="font-bold text-lg">
                  Proof of Skill
                </Link>
                <Link
                  href={`/candidate/tasks${devSuffix}`}
                  className="text-gray-600 hover:text-gray-900 dark:text-gray-300"
                >
                  Tasks
                </Link>
                <Link
                  href={`/candidate/jobs${devSuffix}`}
                  className="text-gray-600 hover:text-gray-900 dark:text-gray-300"
                >
                  Jobs
                </Link>
                <Link
                  href={`/candidate/passport${devSuffix}`}
                  className="text-gray-600 hover:text-gray-900 dark:text-gray-300"
                >
                  My Passport
                </Link>
              </div>
              <div className="flex items-center">
                <SignOutButton />
              </div>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
      </div>
    </ProtectedRoute>
  );
}
