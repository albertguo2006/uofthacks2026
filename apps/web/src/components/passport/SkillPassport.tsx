'use client';

import { Passport } from '@/types/passport';
import { ArchetypeBadge } from './ArchetypeBadge';
import { SkillVector } from './SkillVector';
import { EvidenceList } from './EvidenceList';

interface SkillPassportProps {
  passport: Passport;
  compact?: boolean;
}

export function SkillPassport({ passport, compact = false }: SkillPassportProps) {
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

      {/* Skill Vector Visualization */}
      {passport.metrics && (
        <div>
          <h3 className="font-semibold mb-3">Skill Profile</h3>
          <SkillVector metrics={passport.metrics} />
        </div>
      )}

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
