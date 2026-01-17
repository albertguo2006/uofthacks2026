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
      className="text-gray-600 dark:text-gray-300 transition-all duration-200 hover:text-white hover:drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]"
    >
      Sign Out
    </button>
  );
}
