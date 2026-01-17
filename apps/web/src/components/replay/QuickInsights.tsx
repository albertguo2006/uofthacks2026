'use client';

import React from 'react';
import type { QuickInsightsResponse } from '@/types/timeline';

interface QuickInsightsProps {
  insights: QuickInsightsResponse | null;
  loading?: boolean;
  onTimelineJump?: (index: number) => void;
  onVideoSeek?: (seconds: number) => void;
}

export function QuickInsights({
  insights,
  loading = false,
  onTimelineJump,
  onVideoSeek,
}: QuickInsightsProps) {
  if (loading) {
    return (
      <div className="bg-gray-900 rounded-lg p-4 animate-pulse">
        <div className="h-4 bg-gray-800 rounded w-1/3 mb-4" />
        <div className="space-y-3">
          <div className="h-16 bg-gray-800 rounded" />
          <div className="h-16 bg-gray-800 rounded" />
          <div className="h-16 bg-gray-800 rounded" />
        </div>
      </div>
    );
  }

  if (!insights || insights.insights.length === 0) {
    return (
      <div className="bg-gray-900 rounded-lg p-4">
        <p className="text-gray-500 text-sm">No insights available yet</p>
      </div>
    );
  }

  // Get icon and color for insight category
  const getCategoryStyle = (category: string) => {
    switch (category) {
      case 'approach_change':
        return {
          icon: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15',
          color: 'text-blue-400',
          bgColor: 'bg-blue-900/20',
        };
      case 'debugging_efficiency':
        return {
          icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
          color: 'text-green-400',
          bgColor: 'bg-green-900/20',
        };
      case 'testing_habit':
        return {
          icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
          color: 'text-purple-400',
          bgColor: 'bg-purple-900/20',
        };
      case 'struggle_point':
        return {
          icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
          color: 'text-amber-400',
          bgColor: 'bg-amber-900/20',
        };
      default:
        return {
          icon: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
          color: 'text-gray-400',
          bgColor: 'bg-gray-800',
        };
    }
  };

  // Format video timestamp
  const formatVideoTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-gray-900 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <svg
            className="w-5 h-5 text-amber-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
            />
          </svg>
          <span className="font-medium">Quick Insights</span>
        </div>
      </div>

      {/* Summary */}
      <div className="px-4 py-3 border-b border-gray-800">
        <p className="text-sm text-gray-300">{insights.summary}</p>
      </div>

      {/* Insights list */}
      <div className="divide-y divide-gray-800">
        {insights.insights.map((insight, index) => {
          const style = getCategoryStyle(insight.category);

          return (
            <div key={index} className="p-4">
              <div className="flex items-start gap-3">
                <div className={`p-2 rounded-lg ${style.bgColor}`}>
                  <svg
                    className={`w-4 h-4 ${style.color}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d={style.icon}
                    />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-medium text-white">{insight.title}</h4>
                  <p className="text-xs text-gray-400 mt-1">{insight.description}</p>

                  {/* Action buttons */}
                  <div className="flex items-center gap-2 mt-2">
                    {insight.timeline_index !== null && (
                      <button
                        className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-800 hover:bg-gray-700 rounded text-gray-300 transition-colors"
                        onClick={() => onTimelineJump?.(insight.timeline_index!)}
                      >
                        <svg
                          className="w-3 h-3"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M13 7l5 5m0 0l-5 5m5-5H6"
                          />
                        </svg>
                        Jump to event
                      </button>
                    )}

                    {insight.video_timestamp !== null && (
                      <button
                        className="flex items-center gap-1 px-2 py-1 text-xs bg-purple-900/50 hover:bg-purple-800/50 rounded text-purple-300 transition-colors"
                        onClick={() => onVideoSeek?.(insight.video_timestamp!)}
                      >
                        <svg
                          className="w-3 h-3"
                          fill="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path d="M8 5v14l11-7z" />
                        </svg>
                        {formatVideoTime(insight.video_timestamp)}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
