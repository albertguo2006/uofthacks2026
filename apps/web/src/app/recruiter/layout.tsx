'use client';

export const dynamic = 'force-dynamic';

import { Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { SignOutButton } from '@/components/auth/SignOutButton';
import NodeGraphBackground from '@/components/ui/NodeGraphBackground';

function RecruiterNav() {
  const searchParams = useSearchParams();
  const isDevMode = searchParams.get('dev') === 'true';
  const devSuffix = isDevMode ? '?dev=true' : '';

  return (
    <nav className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center space-x-8">
            <Link href={`/recruiter${devSuffix}`} className="font-bold text-lg transition-all duration-200 hover:text-shadow-glow">
              SimplyAuthentic <span className="text-sm text-gray-500">Recruiter</span>
            </Link>
            <Link
              href={`/recruiter/candidates${devSuffix}`}
              className="text-gray-600 dark:text-gray-300 transition-all duration-200 hover:text-white hover:drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]"
            >
              Candidates
            </Link>
            <Link
              href={`/recruiter/security${devSuffix}`}
              className="text-gray-600 dark:text-gray-300 transition-all duration-200 hover:text-white hover:drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]"
            >
              Security
            </Link>
          </div>
          <div className="flex items-center">
            <SignOutButton />
          </div>
        </div>
      </div>
    </nav>
  );
}

export default function RecruiterLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-4 border-primary-600 border-t-transparent rounded-full" />
      </div>
    }>
      <ProtectedRoute role="recruiter">
        <NodeGraphBackground
          nodeCount={60}
          connectionDistance={150}
          cursorInfluenceRadius={150}
          cursorRepelStrength={0.25}
        />
        <div className="min-h-screen relative z-10">
          <Suspense fallback={<div className="h-16 bg-white/80 dark:bg-slate-800/80" />}>
            <RecruiterNav />
          </Suspense>
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>
        </div>
      </ProtectedRoute>
    </Suspense>
  );
}
