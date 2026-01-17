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
            {Object.entries(passport.metrics).map(([key, value]) => (
              <div key={key} className="text-center p-3 bg-gray-50 dark:bg-slate-700 rounded-lg">
                <div className="text-2xl font-bold text-primary-600">
                  {((value || 0) * 100).toFixed(0)}%
                </div>
                <div className="text-xs text-gray-500 capitalize">
                  {key.replace('_', ' ')}
                </div>
              </div>
            ))}
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
          
          {/* Integrity Warning */}
          {analytics.integrity_metrics.violations > 0 && (
            <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <div className="flex items-center gap-2 text-red-600">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span className="font-medium">
                  {analytics.integrity_metrics.violations} proctoring violation{analytics.integrity_metrics.violations !== 1 ? 's' : ''} detected
                </span>
              </div>
            </div>
          )}
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
