'use client';

import { useState, useEffect } from 'react';
import { Intervention } from '@/hooks/useRadar';

interface HintPanelProps {
  intervention: Intervention | null;
  onAcknowledge: () => void;
  onDismiss?: () => void;
}

const HINT_CATEGORY_ICONS: Record<string, string> = {
  syntax: '{ }',
  logic: '?',
  approach: '!',
  encouragement: '*',
};

const HINT_CATEGORY_COLORS: Record<string, string> = {
  syntax: 'border-blue-500 bg-blue-500/10',
  logic: 'border-purple-500 bg-purple-500/10',
  approach: 'border-yellow-500 bg-yellow-500/10',
  encouragement: 'border-green-500 bg-green-500/10',
};

export function HintPanel({ intervention, onAcknowledge, onDismiss }: HintPanelProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);

  useEffect(() => {
    if (intervention?.hint) {
      // Slight delay for animation
      setTimeout(() => setIsVisible(true), 100);
    } else {
      setIsVisible(false);
    }
  }, [intervention?.hint]);

  if (!intervention?.hint) {
    return null;
  }

  const category = intervention.hint_category || 'approach';
  const icon = HINT_CATEGORY_ICONS[category] || '!';
  const colorClass = HINT_CATEGORY_COLORS[category] || HINT_CATEGORY_COLORS.approach;

  const handleAcknowledge = () => {
    setIsVisible(false);
    setTimeout(onAcknowledge, 200);
  };

  const handleDismiss = () => {
    setIsVisible(false);
    setTimeout(() => onDismiss?.(), 200);
  };

  return (
    <div
      className={`
        transition-all duration-300 ease-out
        ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-2'}
      `}
    >
      <div className={`border-l-4 rounded-r-lg p-4 ${colorClass}`}>
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 flex items-center justify-center bg-white/10 rounded text-xs font-mono">
              {icon}
            </span>
            <span className="text-sm font-medium text-gray-200">
              {category === 'encouragement' ? 'Keep going!' : 'Hint'}
            </span>
            {intervention.intervention_type && (
              <span className="text-xs text-gray-500 ml-2">
                ({intervention.intervention_type.replace('_', ' ')})
              </span>
            )}
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-gray-400 hover:text-gray-200 p-1 rounded transition-colors"
              title={isExpanded ? 'Minimize' : 'Expand'}
            >
              {isExpanded ? (
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                </svg>
              ) : (
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              )}
            </button>
            <button
              onClick={handleDismiss}
              className="text-gray-400 hover:text-gray-200 p-1 rounded transition-colors"
              title="Dismiss"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        {isExpanded && (
          <>
            <p className="text-sm text-gray-300 leading-relaxed">
              {intervention.hint}
            </p>

            {/* Actions */}
            <div className="mt-3 flex items-center gap-3">
              <button
                onClick={handleAcknowledge}
                className="text-xs text-gray-400 hover:text-white underline underline-offset-2 transition-colors"
              >
                Got it, thanks!
              </button>
              <span className="text-gray-600 text-xs">|</span>
              <button
                onClick={handleDismiss}
                className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
              >
                Not helpful
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/**
 * Minimal hint indicator that shows when there's a hint available but panel is minimized
 */
export function HintIndicator({
  hasHint,
  onClick,
}: {
  hasHint: boolean;
  onClick: () => void;
}) {
  if (!hasHint) return null;

  return (
    <button
      onClick={onClick}
      className="
        fixed bottom-4 right-4 z-50
        w-10 h-10 rounded-full
        bg-yellow-500 hover:bg-yellow-400
        flex items-center justify-center
        shadow-lg shadow-yellow-500/20
        transition-all duration-200
        animate-pulse
      "
      title="AI hint available"
    >
      <svg className="w-5 h-5 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
        />
      </svg>
    </button>
  );
}
