'use client';

import Link from 'next/link';
import { useRecommendedTasks, ReasonType } from '@/hooks/useRecommendedTasks';
import { ProctoredBadge } from '@/components/ui/ProctoredBadge';
import { TopicTag } from '@/components/ui/TopicTag';

const REASON_TYPE_COLORS: Record<ReasonType, string> = {
  weak_area: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300 border-orange-300 dark:border-orange-700',
  archetype_match: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300 border-purple-300 dark:border-purple-700',
  confidence_builder: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300 border-green-300 dark:border-green-700',
  error_pattern: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 border-blue-300 dark:border-blue-700',
};

const REASON_TYPE_ICONS: Record<ReasonType, string> = {
  weak_area: '!',
  archetype_match: '*',
  confidence_builder: '+',
  error_pattern: '~',
};

const difficultyColors = {
  easy: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  hard: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
};

export function RecommendedTasksSection() {
  const { recommendations, personalizationSummary, isLoading, error } = useRecommendedTasks(3);

  if (error) {
    return null; // Silently fail - recommendations are optional
  }

  if (isLoading) {
    return (
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-lg font-semibold">Recommended for You</span>
          <span className="text-xs text-gray-500 dark:text-gray-400">Loading...</span>
        </div>
        <div className="grid gap-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse bg-gray-200 dark:bg-slate-700 h-24 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (recommendations.length === 0) {
    return null; // No recommendations available
  }

  return (
    <div className="mb-8">
      {/* Section Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-lg font-semibold">Recommended for You</span>
          <span className="px-2 py-0.5 text-xs bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-full">
            Personalized
          </span>
        </div>
        {personalizationSummary && (
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {personalizationSummary}
          </span>
        )}
      </div>

      {/* Recommended Tasks Grid */}
      <div className="grid gap-3">
        {recommendations.map((rec) => (
          <Link
            key={rec.task.task_id}
            href={`/candidate/tasks/${rec.task.task_id}`}
            className="block p-4 bg-gradient-to-r from-white to-gray-50 dark:from-slate-800 dark:to-slate-800/80 rounded-lg border border-gray-200 dark:border-slate-700 hover:shadow-md hover:border-primary-300 dark:hover:border-primary-600 transition-all"
          >
            <div className="flex justify-between items-start">
              <div className="flex-1">
                {/* Task Title with Proctored Badge */}
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">{rec.task.title}</h3>
                  {rec.task.proctored && <ProctoredBadge />}
                </div>

                {/* Recommendation Reason Badge */}
                <div className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full border mb-2 ${REASON_TYPE_COLORS[rec.reason_type]}`}>
                  <span className="font-mono">{REASON_TYPE_ICONS[rec.reason_type]}</span>
                  <span>{rec.reason}</span>
                </div>

                {/* Task Tags */}
                {rec.task.tags && rec.task.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {rec.task.tags.slice(0, 3).map((tag) => (
                      <TopicTag key={tag} tag={tag} />
                    ))}
                  </div>
                )}

                {/* Task Metadata */}
                <div className="flex flex-wrap gap-2">
                  <span className={`px-2 py-0.5 text-xs rounded ${difficultyColors[rec.task.difficulty]}`}>
                    {rec.task.difficulty}
                  </span>
                  <span className="px-2 py-0.5 text-xs bg-gray-100 dark:bg-slate-700 text-gray-800 dark:text-gray-200 rounded">
                    {rec.task.category}
                  </span>
                  {rec.task.languages && rec.task.languages.length > 0 && (
                    <span className="px-2 py-0.5 text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded">
                      {rec.task.languages.length === 1
                        ? rec.task.languages[0]
                        : `${rec.task.languages.length} languages`}
                    </span>
                  )}
                </div>
              </div>

              {/* Relevance Score Indicator */}
              <div className="flex flex-col items-end ml-4">
                <div className="w-12 h-12 relative">
                  <svg className="w-12 h-12 transform -rotate-90" viewBox="0 0 36 36">
                    <path
                      d="M18 2.0845
                        a 15.9155 15.9155 0 0 1 0 31.831
                        a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      className="text-gray-200 dark:text-slate-700"
                    />
                    <path
                      d="M18 2.0845
                        a 15.9155 15.9155 0 0 1 0 31.831
                        a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeDasharray={`${rec.relevance_score * 100}, 100`}
                      className="text-primary-500"
                    />
                  </svg>
                  <span className="absolute inset-0 flex items-center justify-center text-xs font-medium text-gray-700 dark:text-gray-300">
                    {Math.round(rec.relevance_score * 100)}%
                  </span>
                </div>
                <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">match</span>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Divider */}
      <div className="mt-6 mb-2 border-b border-gray-200 dark:border-slate-700" />
      <div className="text-sm text-gray-500 dark:text-gray-400 mb-4">All Tasks</div>
    </div>
  );
}
