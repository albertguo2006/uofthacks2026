import Link from 'next/link';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { SignOutButton } from '@/components/auth/SignOutButton';

export default function RecruiterLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute role="recruiter">
      <div className="min-h-screen">
        <nav className="bg-white dark:bg-slate-800 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center space-x-8">
                <Link href="/recruiter" className="font-bold text-lg">
                  Proof of Skill <span className="text-sm text-gray-500">Recruiter</span>
                </Link>
                <Link
                  href="/recruiter/candidates"
                  className="text-gray-600 hover:text-gray-900 dark:text-gray-300"
                >
                  Candidates
                </Link>
                <Link
                  href="/recruiter/security"
                  className="text-gray-600 hover:text-gray-900 dark:text-gray-300"
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
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
      </div>
    </ProtectedRoute>
  );
}
