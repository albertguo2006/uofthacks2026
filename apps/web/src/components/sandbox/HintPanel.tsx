'use client';

import { useState, useEffect } from 'react';
import { Intervention, BehaviorAnalysis } from '@/hooks/useRadar';

interface HintContext {
  attempts?: number;
  repeated_errors?: boolean;
  code_history_length?: number;
}

interface HintPanelProps {
  intervention: Intervention | null;
  onAcknowledge: () => void;
  onDismiss?: () => void;
  context?: HintContext;
}

// Human-readable trigger reason labels
const TRIGGER_REASON_LABELS: Record<string, { label: string; description: string }> = {
  error_streak: {
    label: 'Error Streak',
    description: 'Multiple consecutive errors detected',
  },
  high_frustration_score: {
    label: 'Frustration Detected',
    description: 'Behavioral patterns suggest you might be stuck',
  },
  repeated_same_error: {
    label: 'Repeated Error',
    description: 'Same error occurring multiple times',
  },
  time_stuck: {
    label: 'Time Stuck',
    description: 'No successful progress for a while',
  },
  declining_performance: {
    label: 'Declining Performance',
    description: 'Test pass rate is going down',
  },
  stuck_not_changing_code: {
    label: 'Stuck Pattern',
    description: 'Not making code changes despite errors',
  },
  user_prefers_hints: {
    label: 'Personalized',
    description: 'Based on your hint preferences',
  },
  user_requested: {
    label: 'You Asked',
    description: 'You requested this hint',
  },
  demo_frustration_trigger: {
    label: 'Demo Mode',
    description: 'Frustration signal triggered for demonstration',
  },
};

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

export function HintPanel({ intervention, onAcknowledge, onDismiss, context }: HintPanelProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);
  const [showWhySection, setShowWhySection] = useState(false);

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

  // Get trigger reason info
  const triggerReason = intervention.trigger_reason || 'unknown';
  const triggerInfo = TRIGGER_REASON_LABELS[triggerReason] || {
    label: 'AI Analysis',
    description: 'Based on behavioral patterns',
  };

  // Format behavior metrics for display
  const formatTimeStuck = (ms?: number) => {
    if (!ms) return null;
    const seconds = Math.floor(ms / 1000);
    if (seconds < 60) return `${seconds}s`;
    return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  };

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
      <div className={`border-l-4 rounded-r-lg p-4 min-h-fit ${colorClass}`}>
        {/* Personalization Badge */}
        {intervention.personalization_badge && (
          <div className="mb-2 flex items-center gap-1.5">
            <span className="px-2 py-0.5 text-xs bg-primary-500/20 text-primary-300 rounded-full border border-primary-500/30">
              {intervention.personalization_badge}
            </span>
          </div>
        )}

        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 flex items-center justify-center bg-white/10 rounded text-xs font-mono">
              {icon}
            </span>
            <span className="text-sm font-medium text-gray-200">
              {category === 'encouragement' ? 'Keep going!' : 'Hint'}
            </span>
            {intervention.intervention_type && !intervention.personalization_badge && (
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
            <div className="text-sm text-gray-300 leading-6 break-words whitespace-normal max-w-full overflow-visible">
              {intervention.hint}
            </div>

            {/* Context info (if available) */}
            {context && (context.attempts || context.code_history_length) && (
              <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
                {context.attempts && (
                  <span>Attempt #{context.attempts}</span>
                )}
                {context.code_history_length && context.code_history_length > 0 && (
                  <span>{context.code_history_length} code changes analyzed</span>
                )}
                {context.repeated_errors && (
                  <span className="text-yellow-500">Repeated error pattern detected</span>
                )}
              </div>
            )}

            {/* Why this hint section */}
            <div className="mt-3 border-t border-white/10 pt-2">
              <button
                onClick={() => setShowWhySection(!showWhySection)}
                className="text-xs text-gray-400 hover:text-gray-200 flex items-center gap-1 transition-colors"
              >
                <svg
                  className={`w-3 h-3 transition-transform ${showWhySection ? 'rotate-90' : ''}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
                Why this hint?
              </button>

              {showWhySection && (
                <div className="mt-2 p-2 bg-black/20 rounded text-xs space-y-2">
                  {/* Trigger reason */}
                  <div className="flex items-center gap-2">
                    <span className="px-1.5 py-0.5 bg-primary-500/20 text-primary-300 rounded text-[10px] font-medium">
                      {triggerInfo.label}
                    </span>
                    <span className="text-gray-400">{triggerInfo.description}</span>
                  </div>

                  {/* Behavior metrics */}
                  {intervention.behavior_analysis && (
                    <div className="grid grid-cols-2 gap-2 text-gray-400">
                      {intervention.behavior_analysis.frustration_score !== undefined && (
                        <div className="flex items-center gap-1">
                          <span className="text-gray-500">Frustration:</span>
                          <span className={intervention.behavior_analysis.frustration_score >= 0.7 ? 'text-red-400' : intervention.behavior_analysis.frustration_score >= 0.4 ? 'text-yellow-400' : 'text-green-400'}>
                            {Math.round(intervention.behavior_analysis.frustration_score * 100)}%
                          </span>
                        </div>
                      )}
                      {intervention.behavior_analysis.error_streak !== undefined && intervention.behavior_analysis.error_streak > 0 && (
                        <div className="flex items-center gap-1">
                          <span className="text-gray-500">Error streak:</span>
                          <span className="text-red-400">{intervention.behavior_analysis.error_streak}</span>
                        </div>
                      )}
                      {intervention.behavior_analysis.time_stuck_ms !== undefined && intervention.behavior_analysis.time_stuck_ms > 0 && (
                        <div className="flex items-center gap-1">
                          <span className="text-gray-500">Time stuck:</span>
                          <span>{formatTimeStuck(intervention.behavior_analysis.time_stuck_ms)}</span>
                        </div>
                      )}
                      {intervention.behavior_analysis.tests_passed_trend && intervention.behavior_analysis.tests_passed_trend !== 'stable' && (
                        <div className="flex items-center gap-1">
                          <span className="text-gray-500">Trend:</span>
                          <span className={intervention.behavior_analysis.tests_passed_trend === 'improving' ? 'text-green-400' : 'text-red-400'}>
                            {intervention.behavior_analysis.tests_passed_trend}
                          </span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Models used */}
                  {intervention.models_used && intervention.models_used.length > 0 && (
                    <div className="text-gray-500 text-[10px]">
                      AI: {intervention.models_used.join(', ')}
                    </div>
                  )}
                </div>
              )}
            </div>

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
