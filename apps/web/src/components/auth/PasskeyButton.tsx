'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  startRegistration,
  startAuthentication,
} from '@simplewebauthn/browser';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';

interface PasskeyButtonProps {
  mode: 'register' | 'authenticate';
  onError: (error: string) => void;
}

export function PasskeyButton({ mode, onError }: PasskeyButtonProps) {
  const router = useRouter();
  const { setUser } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [email, setEmail] = useState('');

  const handlePasskeyRegister = async () => {
    setIsLoading(true);

    try {
      // Get registration options from server
      const options = await api.post('/auth/passkey/register/begin', {});

      // Start WebAuthn registration
      const credential = await startRegistration(options.options);

      // Complete registration on server
      await api.post('/auth/passkey/register/complete', { credential });

      alert('Passkey registered successfully!');
    } catch (err: any) {
      if (err.name === 'NotAllowedError') {
        onError('Passkey registration was cancelled');
      } else {
        onError('Failed to register passkey');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handlePasskeyAuthenticate = async () => {
    if (!email) {
      onError('Please enter your email first');
      return;
    }

    setIsLoading(true);

    try {
      // Get authentication options from server
      const options = await api.post('/auth/passkey/authenticate/begin', { email });

      // Start WebAuthn authentication
      const credential = await startAuthentication(options.options);

      // Complete authentication on server
      const response = await api.post('/auth/passkey/authenticate/complete', {
        email,
        credential,
      });

      setUser(response.user);

      // Redirect based on role
      if (response.user.role === 'recruiter') {
        router.push('/recruiter');
      } else {
        router.push('/candidate');
      }
    } catch (err: any) {
      if (err.name === 'NotAllowedError') {
        onError('Passkey authentication was cancelled');
      } else {
        onError('Failed to authenticate with passkey');
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (mode === 'register') {
    return (
      <button
        onClick={handlePasskeyRegister}
        disabled={isLoading}
        className="w-full flex items-center justify-center gap-2 px-4 py-3 border border-gray-300 dark:border-slate-600 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors disabled:opacity-50"
      >
        <span>🔐</span>
        <span>{isLoading ? 'Registering...' : 'Register Passkey'}</span>
      </button>
    );
  }

  return (
    <div className="space-y-3">
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Enter your email for passkey"
        className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-lg"
      />
      <button
        onClick={handlePasskeyAuthenticate}
        disabled={isLoading}
        className="w-full flex items-center justify-center gap-2 px-4 py-3 border border-gray-300 dark:border-slate-600 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors disabled:opacity-50"
      >
        <span>🔐</span>
        <span>{isLoading ? 'Authenticating...' : 'Sign in with Passkey'}</span>
      </button>
    </div>
  );
}
