'use client';

import { useState } from 'react';
import Link from 'next/link';
import { LoginForm } from '@/components/auth/LoginForm';
import { PasskeyButton } from '@/components/auth/PasskeyButton';
import NodeGraphBackground from '@/components/ui/NodeGraphBackground';

export default function LoginPage() {
  const [error, setError] = useState<string | null>(null);

  return (
    <>
      <NodeGraphBackground
        nodeCount={80}
        connectionDistance={150}
        cursorInfluenceRadius={150}
        cursorRepelStrength={0.25}
      />
      <div className="min-h-screen flex items-center justify-center p-4 relative z-10">
        {/* Frosted glass window */}
        <div className="max-w-md w-full space-y-8 bg-white/10 dark:bg-slate-800/30 backdrop-blur-xl rounded-2xl p-8 border border-white/20 dark:border-slate-700/50 shadow-2xl">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-white">Welcome Back</h1>
            <p className="mt-2 text-gray-300">
              Sign in to continue building your Skill Identity
            </p>
          </div>

          {error && (
            <div className="p-4 bg-red-500/20 border border-red-400/50 rounded-lg text-red-200 backdrop-blur-sm">
              {error}
            </div>
          )}

          <LoginForm onError={setError} />

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/20" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-transparent text-gray-400">
                Or continue with
              </span>
            </div>
          </div>

          <PasskeyButton mode="authenticate" onError={setError} />

          <p className="text-center text-sm text-gray-300">
            Don&apos;t have an account?{' '}
            <Link href="/auth/register" className="text-primary-400 hover:text-primary-300 hover:underline">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </>
  );
}
