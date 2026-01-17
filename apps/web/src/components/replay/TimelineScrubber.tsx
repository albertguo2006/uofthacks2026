'use client';

import React, { useRef, useCallback, useMemo } from 'react';
import type { Timeline, TimelineEntry } from '@/types/timeline';
import { SEVERITY_COLORS } from '@/types/timeline';

interface TimelineScrubberProps {
  timeline: Timeline;
  currentIndex: number;
  onIndexChange: (index: number) => void;
  onEntryClick?: (entry: TimelineEntry, index: number) => void;
}

export function TimelineScrubber({
  timeline,
  currentIndex,
  onIndexChange,
  onEntryClick,
}: TimelineScrubberProps) {
  const scrubberRef = useRef<HTMLDivElement>(null);

  // Calculate position for each entry (0-100%)
  const entryPositions = useMemo(() => {
    if (!timeline.entries.length) return [];

    const startTime = new Date(timeline.start_time).getTime();
    const endTime = timeline.end_time
      ? new Date(timeline.end_time).getTime()
      : startTime + timeline.duration_seconds * 1000;
    const totalDuration = endTime - startTime;

    return timeline.entries.map((entry) => {
      const entryTime = new Date(entry.timestamp).getTime();
      return ((entryTime - startTime) / totalDuration) * 100;
    });
  }, [timeline]);

  // Handle click on scrubber bar
  const handleScrubberClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!scrubberRef.current || !timeline.entries.length) return;

      const rect = scrubberRef.current.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const percentage = (clickX / rect.width) * 100;

      // Find closest entry to click position
      let closestIndex = 0;
      let closestDiff = Infinity;

      entryPositions.forEach((pos, index) => {
        const diff = Math.abs(pos - percentage);
        if (diff < closestDiff) {
          closestDiff = diff;
          closestIndex = index;
        }
      });

      onIndexChange(closestIndex);
    },
    [timeline.entries, entryPositions, onIndexChange]
  );

  // Get marker color based on severity
  const getMarkerColor = (entry: TimelineEntry) => {
    if (entry.severity) {
      return SEVERITY_COLORS[entry.severity] || SEVERITY_COLORS.info;
    }
    return SEVERITY_COLORS.info;
  };

  // Get marker size based on event importance
  const getMarkerSize = (entry: TimelineEntry) => {
    const importantTypes = [
      'submission_passed',
      'submission_failed',
      'ai_intervention',
      'error_emitted',
    ];
    return importantTypes.includes(entry.type) ? 'w-3 h-3' : 'w-2 h-2';
  };

  // Format time for display
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Calculate current position percentage
  const currentPosition = entryPositions[currentIndex] ?? 0;

  return (
    <div className="w-full">
      {/* Time labels */}
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>0:00</span>
        <span>{formatTime(timeline.duration_seconds)}</span>
      </div>

      {/* Scrubber track */}
      <div
        ref={scrubberRef}
        className="relative h-8 bg-gray-800 rounded-lg cursor-pointer group"
        onClick={handleScrubberClick}
      >
        {/* Progress fill */}
        <div
          className="absolute top-0 left-0 h-full bg-blue-900/50 rounded-l-lg transition-all duration-150"
          style={{ width: `${currentPosition}%` }}
        />

        {/* Event markers */}
        {timeline.entries.map((entry, index) => (
          <button
            key={entry.id}
            className={`absolute top-1/2 -translate-y-1/2 rounded-full transition-all duration-150 hover:scale-150 ${getMarkerSize(
              entry
            )} ${index === currentIndex ? 'ring-2 ring-white scale-125' : ''}`}
            style={{
              left: `${entryPositions[index]}%`,
              backgroundColor: getMarkerColor(entry),
              transform: `translateX(-50%) translateY(-50%)`,
            }}
            onClick={(e) => {
              e.stopPropagation();
              onIndexChange(index);
              onEntryClick?.(entry, index);
            }}
            title={entry.label}
          />
        ))}

        {/* Current position indicator */}
        <div
          className="absolute top-0 h-full w-0.5 bg-white transition-all duration-150"
          style={{ left: `${currentPosition}%` }}
        />
      </div>

      {/* Current event label */}
      <div className="mt-2 text-sm text-center">
        {timeline.entries[currentIndex] && (
          <span
            className="px-2 py-1 rounded-full text-xs font-medium"
            style={{
              backgroundColor: `${getMarkerColor(timeline.entries[currentIndex])}20`,
              color: getMarkerColor(timeline.entries[currentIndex]),
            }}
          >
            {timeline.entries[currentIndex].label}
          </span>
        )}
      </div>

      {/* Navigation controls */}
      <div className="flex items-center justify-center gap-4 mt-3">
        <button
          className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={() => onIndexChange(Math.max(0, currentIndex - 1))}
          disabled={currentIndex === 0}
        >
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
              d="M15 19l-7-7 7-7"
            />
          </svg>
        </button>

        <span className="text-sm text-gray-400">
          {currentIndex + 1} / {timeline.entries.length}
        </span>

        <button
          className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={() =>
            onIndexChange(Math.min(timeline.entries.length - 1, currentIndex + 1))
          }
          disabled={currentIndex === timeline.entries.length - 1}
        >
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
              d="M9 5l7 7-7 7"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}
