'use client';

import { FrustrationStatus } from '@/hooks/useRadar';

interface FrustrationMeterProps {
  status: FrustrationStatus | null;
  onBoost?: () => void;
}

export function FrustrationMeter({ status, onBoost }: FrustrationMeterProps) {
  if (!status) {
    return null;
  }

  const percentage = Math.round(status.frustration_score * 100);
  const thresholdPercentage = Math.round(status.threshold * 100);
  const isUnlocked = status.hint_unlocked;

  // Color based on level
  const getColor = () => {
    if (percentage >= 70) return 'bg-red-500';
    if (percentage >= 50) return 'bg-yellow-500';
    if (percentage >= 30) return 'bg-orange-400';
    return 'bg-green-500';
  };

  const getGlowColor = () => {
    if (percentage >= 70) return 'shadow-red-500/50';
    if (percentage >= 50) return 'shadow-yellow-500/50';
    return '';
  };

  return (
    <div className="flex items-center gap-3">
      {/* Frustration meter */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-gray-400 whitespace-nowrap">Frustration</span>
        <div className="relative w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
          {/* Threshold marker */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-white/50 z-10"
            style={{ left: `${thresholdPercentage}%` }}
          />
          {/* Progress bar */}
          <div
            className={`h-full transition-all duration-300 ${getColor()} ${
              isUnlocked ? `shadow-lg ${getGlowColor()}` : ''
            }`}
            style={{ width: `${percentage}%` }}
          />
        </div>
        <span
          className={`text-xs font-mono min-w-[3ch] ${
            isUnlocked ? 'text-yellow-400 font-bold' : 'text-gray-400'
          }`}
        >
          {percentage}%
        </span>
      </div>

      {/* Hint unlock indicator */}
      {isUnlocked ? (
        <span className="text-xs text-yellow-400 flex items-center gap-1 animate-pulse">
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z"
              clipRule="evenodd"
            />
          </svg>
          Hint available!
        </span>
      ) : (
        <span className="text-xs text-gray-500">
          Press <kbd className="px-1 py-0.5 bg-gray-700 rounded text-gray-300 font-mono">!</kbd> to boost
        </span>
      )}

      {/* Contributing factors tooltip on hover */}
      <div className="relative group">
        <button className="text-gray-500 hover:text-gray-300 transition-colors">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </button>

        {/* Tooltip */}
        <div className="absolute right-0 top-6 w-48 p-2 bg-gray-800 border border-gray-700 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
          <div className="text-xs space-y-1">
            <div className="font-medium text-gray-300 mb-2">Contributing Factors</div>
            {status.contributing_factors.error_streak !== undefined &&
              status.contributing_factors.error_streak > 0 && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Error streak:</span>
                  <span className="text-red-400">{status.contributing_factors.error_streak}</span>
                </div>
              )}
            {status.contributing_factors.failed_runs !== undefined &&
              status.contributing_factors.failed_runs > 0 && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Failed runs:</span>
                  <span className="text-orange-400">{status.contributing_factors.failed_runs}</span>
                </div>
              )}
            {status.contributing_factors.time_stuck_minutes !== undefined &&
              status.contributing_factors.time_stuck_minutes > 0 && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Time stuck:</span>
                  <span>{status.contributing_factors.time_stuck_minutes}m</span>
                </div>
              )}
            {status.contributing_factors.demo_boosts !== undefined &&
              status.contributing_factors.demo_boosts > 0 && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Demo boosts:</span>
                  <span className="text-purple-400">
                    {status.contributing_factors.demo_boosts} (+
                    {Math.round((status.contributing_factors.demo_boost_score || 0) * 100)}%)
                  </span>
                </div>
              )}
            <div className="border-t border-gray-700 pt-1 mt-1">
              <div className="flex justify-between font-medium">
                <span className="text-gray-300">Threshold:</span>
                <span>{thresholdPercentage}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
