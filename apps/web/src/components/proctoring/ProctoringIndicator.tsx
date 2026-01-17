'use client';

interface ProctoringIndicatorProps {
  isActive: boolean;
  cameraEnabled?: boolean;
  violationCount?: number;
}

export function ProctoringIndicator({
  isActive,
  cameraEnabled = false,
  violationCount = 0,
}: ProctoringIndicatorProps) {
  if (!isActive) return null;

  return (
    <div className="flex items-center gap-3 px-3 py-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
      {/* Recording indicator */}
      <div className="flex items-center gap-2">
        <span className="relative flex h-3 w-3">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500" />
        </span>
        <span className="text-sm font-medium text-red-800 dark:text-red-200">
          Proctoring Active
        </span>
      </div>

      {/* Camera indicator */}
      {cameraEnabled && (
        <div className="flex items-center gap-1 text-red-700 dark:text-red-300">
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
            />
          </svg>
          <span className="text-xs">Camera On</span>
        </div>
      )}

      {/* Violation count */}
      {violationCount > 0 && (
        <div className="flex items-center gap-1 text-red-700 dark:text-red-300">
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <span className="text-xs">{violationCount} violation{violationCount !== 1 ? 's' : ''}</span>
        </div>
      )}
    </div>
  );
}
