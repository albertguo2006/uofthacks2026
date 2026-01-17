'use client';

import { useState } from 'react';
import Link from 'next/link';
import { RegisterForm } from '@/components/auth/RegisterForm';
import NodeGraphBackground from '@/components/ui/NodeGraphBackground';

export default function RegisterPage() {
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
            <h1 className="text-3xl font-bold text-white">Create Account</h1>
            <p className="mt-2 text-gray-300">
              Start building your verified Skill Identity
            </p>
          </div>

          {error && (
            <div className="p-4 bg-red-500/20 border border-red-400/50 rounded-lg text-red-200 backdrop-blur-sm">
              {error}
            </div>
          )}

          <RegisterForm onError={setError} />

          <p className="text-center text-sm text-gray-300">
            Already have an account?{' '}
            <Link href="/auth/login" className="text-primary-400 hover:text-primary-300 hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </>
  );
}
