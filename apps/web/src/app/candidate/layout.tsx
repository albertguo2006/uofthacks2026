'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { SignOutButton } from '@/components/auth/SignOutButton';
import NodeGraphBackground from '@/components/ui/NodeGraphBackground';

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
      <NodeGraphBackground
        nodeCount={60}
        connectionDistance={150}
        cursorInfluenceRadius={150}
        cursorRepelStrength={0.25}
      />
      <div className="min-h-screen relative z-10">
        <nav className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center space-x-8">
                <Link href={`/candidate${devSuffix}`} className="font-bold text-lg transition-all duration-200 hover:text-shadow-glow">
                  Simply Authentic
                </Link>
                <Link
                  href={`/candidate/tasks${devSuffix}`}
                  className="text-gray-600 dark:text-gray-300 transition-all duration-200 hover:text-white hover:drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]"
                >
                  Tasks
                </Link>
                <Link
                  href={`/candidate/jobs${devSuffix}`}
                  className="text-gray-600 dark:text-gray-300 transition-all duration-200 hover:text-white hover:drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]"
                >
                  Jobs
                </Link>
                <Link
                  href={`/candidate/passport${devSuffix}`}
                  className="text-gray-600 dark:text-gray-300 transition-all duration-200 hover:text-white hover:drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]"
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
