'use client';

import { Passport } from '@/types/passport';
import { ArchetypeBadge } from './ArchetypeBadge';
import { RadarPentagon } from './RadarPentagon';
import { SkillBars } from './SkillBars';
import { EvidenceList } from './EvidenceList';
import { useRadar } from '@/hooks/useRadar';
import { usePassportAnalytics } from '@/hooks/usePassportAnalytics';
import { useSkillProficiencies } from '@/hooks/useSkillProficiencies';

interface SkillPassportProps {
  passport: Passport;
  compact?: boolean;
  showAnalytics?: boolean;
}

interface IntegrityMetrics {
  violations: number;
  integrity_score: number;
  violation_types?: string[];
}

function getIntegrityRating(score: number): { label: string; color: string; bgColor: string; borderColor: string } {
  if (score >= 0.95) {
    return { label: 'Excellent', color: 'text-green-600', bgColor: 'bg-green-50 dark:bg-green-900/20', borderColor: 'border-green-200 dark:border-green-800' };
  } else if (score >= 0.85) {
    return { label: 'Good', color: 'text-blue-600', bgColor: 'bg-blue-50 dark:bg-blue-900/20', borderColor: 'border-blue-200 dark:border-blue-800' };
  } else if (score >= 0.7) {
    return { label: 'Acceptable', color: 'text-amber-600', bgColor: 'bg-amber-50 dark:bg-amber-900/20', borderColor: 'border-amber-200 dark:border-amber-800' };
  } else {
    return { label: 'Needs Review', color: 'text-red-600', bgColor: 'bg-red-50 dark:bg-red-900/20', borderColor: 'border-red-200 dark:border-red-800' };
  }
}

function getViolationSummary(violations: number): string {
  if (violations === 0) {
    return 'No session anomalies detected.';
  } else if (violations <= 2) {
    return 'Minimal session anomalies detected. This may include minor events like accidental tab switches.';
  } else if (violations <= 5) {
    return 'Some session anomalies detected. Review recommended to distinguish between unintentional events and actual concerns.';
  } else {
    return 'Multiple session anomalies detected. Manual review suggested to assess the nature of these events.';
  }
}

const METRIC_INFO: Record<string, { label: string; description: string }> = {
  debug_efficiency: {
    label: 'Debug Efficiency',
    description: 'Skill in identifying and resolving code errors quickly',
  },
  iteration_velocity: {
    label: 'Iteration Velocity',
    description: 'Speed of making incremental improvements and testing changes',
  },
  craftsmanship: {
    label: 'Craftsmanship',
    description: 'Attention to code quality, readability, and best practices',
  },
  tool_fluency: {
    label: 'Tool Fluency',
    description: 'Proficiency with development tools and IDE features',
  },
  integrity: {
    label: 'Integrity',
    description: 'Consistency and honesty in coding behavior',
  },
};

function getMetricInfo(key: string): { label: string; description: string } {
  if (METRIC_INFO[key]) {
    return METRIC_INFO[key];
  }
  // Fallback: capitalize first letter of each word
  const label = key
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
  return { label, description: '' };
}

function IntegrityScoreDisplay({ metrics }: { metrics: IntegrityMetrics }) {
  const rating = getIntegrityRating(metrics.integrity_score);
  const summary = getViolationSummary(metrics.violations);

  return (
    <div className={`mt-4 p-4 ${rating.bgColor} border ${rating.borderColor} rounded-lg`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <svg className={`w-5 h-5 ${rating.color}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          <span className={`font-medium ${rating.color}`}>
            Session Integrity: {rating.label}
          </span>
        </div>
        <span className={`text-sm font-semibold ${rating.color}`}>
          {(metrics.integrity_score * 100).toFixed(0)}%
        </span>
      </div>
      <p className="text-sm text-gray-600 dark:text-gray-300">{summary}</p>
      {metrics.violations > 0 && (
        <p className="mt-2 text-xs text-gray-500 dark:text-gray-400 italic">
          Note: Anomalies may include unintentional events such as accidental tab switches or brief focus loss. We recommend reviewing session context before drawing conclusions.
        </p>
      )}
    </div>
  );
}

export function SkillPassport({ passport, compact = false, showAnalytics = false }: SkillPassportProps) {
  // Fetch Engineering DNA radar profile
  const { radarProfile, radarSummary } = useRadar(passport.user_id, { enablePolling: false });
  
  // Fetch skill proficiencies
  const { proficiencies } = useSkillProficiencies(passport.user_id);
  
  // Fetch analytics if requested
  const { analytics } = usePassportAnalytics(showAnalytics ? passport.user_id : undefined);

  if (compact) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          {passport.archetype ? (
            <ArchetypeBadge archetype={passport.archetype.name} />
          ) : (
            <span className="text-sm text-gray-500">No archetype yet</span>
          )}
          <span className="text-sm text-gray-500">
            {passport.sessions_completed || 0} sessions
          </span>
        </div>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Debug Efficiency</span>
            <div className="font-semibold">
              {((passport.metrics?.debug_efficiency || 0) * 100).toFixed(0)}%
            </div>
          </div>
          <div>
            <span className="text-gray-500">Integrity</span>
            <div className="font-semibold">
              {((passport.metrics?.integrity || 0) * 100).toFixed(0)}%
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold">{passport.display_name}</h2>
          <div className="mt-2">
            {passport.archetype ? (
              <ArchetypeBadge archetype={passport.archetype.name} showDescription />
            ) : (
              <span className="text-sm text-gray-500">Complete tasks to discover your archetype</span>
            )}
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-primary-600">
            {passport.tasks_passed || 0}/{passport.sessions_completed || 0}
          </div>
          <div className="text-sm text-gray-500">Tasks Passed</div>
        </div>
      </div>

      {/* Skill Profile - Pentagon visualization with radar data */}
      <div>
        <h3 className="font-semibold mb-3">Skill Profile</h3>
        <div className="flex flex-col items-center">
          <RadarPentagon profile={radarProfile} size={280} />
        </div>
        {radarSummary && (
          <div className="mt-4 p-4 bg-gray-50 dark:bg-slate-700 rounded-lg">
            <h4 className="text-sm font-medium text-gray-500 mb-2">AI Summary</h4>
            <p className="text-sm text-gray-700 dark:text-gray-300">{radarSummary}</p>
          </div>
        )}
      </div>

      {/* Engineering DNA - Bar charts showing skill proficiency */}
      <div>
        <h3 className="font-semibold mb-3">Engineering DNA</h3>
        <SkillBars skills={proficiencies} />
      </div>

      {/* Metrics Grid */}
      {passport.metrics && (
        <div>
          <h3 className="font-semibold mb-3">Detailed Metrics</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {Object.entries(passport.metrics).map(([key, value]) => {
              const info = getMetricInfo(key);
              return (
                <div
                  key={key}
                  className="relative text-center p-3 bg-gray-50 dark:bg-slate-700 rounded-lg cursor-help group"
                >
                  <div className="text-2xl font-bold text-primary-600">
                    {((value || 0) * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-gray-500">
                    {info.label}
                  </div>
                  {/* Tooltip */}
                  {info.description && (
                    <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:block z-50 w-48">
                      <div className="bg-gray-900 dark:bg-gray-700 text-white text-xs rounded-lg py-2 px-3 shadow-lg">
                        {info.description}
                        <div className="absolute left-1/2 -translate-x-1/2 top-full border-t-gray-900 dark:border-t-gray-700 border-t-8 border-x-8 border-x-transparent"></div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Notable Moments */}
      {passport.notable_moments && passport.notable_moments.length > 0 && (
        <div>
          <h3 className="font-semibold mb-3">Notable Moments</h3>
          <EvidenceList moments={passport.notable_moments} />
        </div>
      )}

      {/* Analytics Section */}
      {showAnalytics && analytics && (
        <div>
          <h3 className="font-semibold mb-3">Activity Analytics</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {analytics.activity_metrics.total_test_runs}
              </div>
              <div className="text-xs text-gray-500">Test Runs</div>
            </div>
            <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {(analytics.session_stats.pass_rate * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-gray-500">Pass Rate</div>
            </div>
            <div className="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {analytics.session_stats.average_score.toFixed(1)}
              </div>
              <div className="text-xs text-gray-500">Avg Score</div>
            </div>
            <div className="text-center p-4 bg-amber-50 dark:bg-amber-900/20 rounded-lg">
              <div className="text-2xl font-bold text-amber-600">
                {analytics.activity_metrics.runs_per_submission.toFixed(1)}
              </div>
              <div className="text-xs text-gray-500">Runs/Submit</div>
            </div>
          </div>
          
          {/* Integrity Score */}
          <IntegrityScoreDisplay metrics={analytics.integrity_metrics} />
        </div>
      )}

      {/* Confidence & Timestamp */}
      <div className="pt-4 border-t border-gray-200 dark:border-slate-600 text-sm text-gray-500">
        <div className="flex justify-between">
          <span>
            {passport.archetype
              ? `Archetype confidence: ${(passport.archetype.confidence * 100).toFixed(0)}%`
              : 'No archetype determined yet'}
          </span>
          <span>Updated: {new Date(passport.updated_at || Date.now()).toLocaleDateString()}</span>
        </div>
      </div>
    </div>
  );
}
