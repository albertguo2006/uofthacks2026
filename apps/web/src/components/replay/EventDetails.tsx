'use client';

import React from 'react';
import type { TimelineEntry } from '@/types/timeline';
import { SEVERITY_COLORS } from '@/types/timeline';

interface EventDetailsProps {
  entry: TimelineEntry | null;
  onVideoSeek?: (seconds: number) => void;
}

export function EventDetails({ entry, onVideoSeek }: EventDetailsProps) {
  if (!entry) {
    return (
      <div className="bg-gray-900 rounded-lg p-4 h-full">
        <p className="text-gray-500 text-sm">Select an event to view details</p>
      </div>
    );
  }

  // Format timestamp for display
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  // Format video timestamp
  const formatVideoTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Get icon for event type
  const getEventIcon = (type: string) => {
    const icons: Record<string, string> = {
      code_changed: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4',
      run_attempted: 'M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
      test_passed: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
      test_failed: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z',
      error_emitted: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
      ai_intervention: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
      submission_passed: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
      submission_failed: 'M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636',
      default: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    };
    return icons[type] || icons.default;
  };

  const severityColor = entry.severity ? SEVERITY_COLORS[entry.severity] : SEVERITY_COLORS.info;

  return (
    <div className="bg-gray-900 rounded-lg overflow-hidden h-full flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center gap-3">
          <div
            className="p-2 rounded-lg"
            style={{ backgroundColor: `${severityColor}20` }}
          >
            <svg
              className="w-5 h-5"
              style={{ color: severityColor }}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d={getEventIcon(entry.type)}
              />
            </svg>
          </div>
          <div>
            <h3 className="font-medium text-white">{entry.label}</h3>
            <p className="text-xs text-gray-400">{formatTimestamp(entry.timestamp)}</p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {/* Video timestamp */}
        {entry.video_timestamp_seconds !== null && (
          <div className="flex items-center justify-between bg-gray-800 rounded-lg p-3">
            <span className="text-sm text-gray-400">Video timestamp</span>
            <button
              className="flex items-center gap-2 text-blue-400 hover:text-blue-300 text-sm"
              onClick={() => onVideoSeek?.(entry.video_timestamp_seconds!)}
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
              {formatVideoTime(entry.video_timestamp_seconds)}
            </button>
          </div>
        )}

        {/* Event data */}
        {entry.event_data && Object.keys(entry.event_data).length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-400">Event Data</h4>
            <div className="bg-gray-800 rounded-lg p-3 space-y-2">
              {Object.entries(entry.event_data).map(([key, value]) => (
                <div key={key} className="flex justify-between text-sm">
                  <span className="text-gray-500">{key.replace(/_/g, ' ')}</span>
                  <span className="text-gray-300">{String(value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* AI Intervention */}
        {entry.intervention && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-amber-400 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                />
              </svg>
              AI Intervention
            </h4>
            <div className="bg-amber-900/20 border border-amber-700/30 rounded-lg p-3">
              <p className="text-sm text-gray-300">{entry.intervention.hint}</p>
              {entry.intervention.personalization_badge && (
                <p className="text-xs text-amber-500 mt-2">
                  {entry.intervention.personalization_badge}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Severity indicator */}
        {entry.severity && (
          <div className="pt-2 border-t border-gray-800">
            <div
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium"
              style={{
                backgroundColor: `${severityColor}20`,
                color: severityColor,
              }}
            >
              <span
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: severityColor }}
              />
              {entry.severity.charAt(0).toUpperCase() + entry.severity.slice(1)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
