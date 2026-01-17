'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';

interface ProtectedRouteProps {
  children: React.ReactNode;
  role?: 'candidate' | 'recruiter';
}

export function ProtectedRoute({ children, role }: ProtectedRouteProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isLoading } = useAuth();
  
  // Check for dev mode bypass
  const isDevMode = searchParams.get('dev') === 'true';

  useEffect(() => {
    if (!isLoading && !isDevMode) {
      if (!user) {
        router.push('/auth/login');
      } else if (role && user.role !== role) {
        // Redirect to correct dashboard
        router.push(user.role === 'recruiter' ? '/recruiter' : '/candidate');
      }
    }
  }, [user, isLoading, role, router, isDevMode]);

  // Allow access in dev mode without authentication
  if (isDevMode) {
    return <>{children}</>;
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-4 border-primary-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  if (role && user.role !== role) {
    return null;
  }

  return <>{children}</>;
}
