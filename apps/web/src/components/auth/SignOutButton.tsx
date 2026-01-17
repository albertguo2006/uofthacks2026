'use client';

import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';

export function SignOutButton() {
  const { logout } = useAuth();
  const router = useRouter();

  const handleSignOut = async () => {
    await logout();
    router.push('/');
  };

  return (
    <button
      onClick={handleSignOut}
      className="text-gray-600 hover:text-gray-900 dark:text-gray-300"
    >
      Sign Out
    </button>
  );
}
