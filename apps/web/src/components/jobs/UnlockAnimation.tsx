'use client';

import { useEffect, useState } from 'react';

interface UnlockAnimationProps {
  jobTitle: string;
}

export function UnlockAnimation({ jobTitle }: UnlockAnimationProps) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setVisible(false), 5000);
    return () => clearTimeout(timer);
  }, []);

  if (!visible) return null;

  return (
    <div className="fixed top-4 right-4 z-50 animate-bounce">
      <div className="bg-green-600 text-white px-6 py-4 rounded-lg shadow-lg">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🎉</span>
          <div>
            <p className="font-semibold">New Job Unlocked!</p>
            <p className="text-sm opacity-90">{jobTitle}</p>
          </div>
          <button
            onClick={() => setVisible(false)}
            className="ml-4 text-white/80 hover:text-white"
          >
            ✕
          </button>
        </div>
      </div>
    </div>
  );
}
