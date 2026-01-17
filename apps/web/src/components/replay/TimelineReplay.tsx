'use client';

import React, { useCallback, useState } from 'react';
import { useTimeline } from '@/hooks/useTimeline';
import { TimelineScrubber } from './TimelineScrubber';
import { CodeSnapshot } from './CodeSnapshot';
import { EventDetails } from './EventDetails';
import { AskTheInterview } from './AskTheInterview';
import { SyncedVideoPlayer } from './SyncedVideoPlayer';
import { QuickInsights } from './QuickInsights';

interface TimelineReplayProps {
  sessionId: string;
  onBack?: () => void;
}

type ActivePanel = 'details' | 'ask' | 'insights';

export function TimelineReplay({ sessionId, onBack }: TimelineReplayProps) {
  const {
    timeline,
    insights,
    loading,
    error,
    currentIndex,
    setCurrentIndex,
    jumpToIndex,
    jumpToVideoTimestamp,
    currentEntry,
  } = useTimeline(sessionId);

  const [activePanel, setActivePanel] = useState<ActivePanel>('details');
  const [videoRef, setVideoRef] = useState<{ seekTo: (seconds: number) => void } | null>(null);

  // Handle video seek from timeline
  const handleVideoSeek = useCallback((seconds: number) => {
    videoRef?.seekTo(seconds);
  }, [videoRef]);

  // Handle video time update - sync timeline
  const handleVideoTimeUpdate = useCallback((seconds: number) => {
    jumpToVideoTimestamp(seconds);
  }, [jumpToVideoTimestamp]);

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 text-white p-6">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-gray-800 rounded w-1/3" />
            <div className="h-64 bg-gray-800 rounded" />
            <div className="grid grid-cols-2 gap-6">
              <div className="h-96 bg-gray-800 rounded" />
              <div className="h-96 bg-gray-800 rounded" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-950 text-white p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-900/20 border border-red-700 rounded-lg p-6 text-center">
            <svg
              className="w-12 h-12 mx-auto text-red-500 mb-4"
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
            <h2 className="text-xl font-semibold text-red-400 mb-2">Failed to load session</h2>
            <p className="text-gray-400">{error}</p>
            {onBack && (
              <button
                className="mt-4 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg"
                onClick={onBack}
              >
                Go Back
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // No timeline data
  if (!timeline) {
    return (
      <div className="min-h-screen bg-gray-950 text-white p-6">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-gray-400">No session data found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <div className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            {onBack && (
              <button
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                onClick={onBack}
              >
                <svg
                  className="w-5 h-5"
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
            )}
            <div>
              <h1 className="text-xl font-semibold">{timeline.task_title}</h1>
              <p className="text-sm text-gray-400">
                Session Replay - {Math.floor(timeline.duration_seconds / 60)} minutes
              </p>
            </div>
          </div>

          {/* Session stats */}
          <div className="flex items-center gap-6 text-sm">
            <div className="text-center">
              <p className="text-gray-400">Runs</p>
              <p className="font-medium">{timeline.total_runs}</p>
            </div>
            <div className="text-center">
              <p className="text-gray-400">Errors</p>
              <p className="font-medium text-red-400">{timeline.errors_encountered}</p>
            </div>
            <div className="text-center">
              <p className="text-gray-400">AI Hints</p>
              <p className="font-medium text-amber-400">{timeline.interventions_received}</p>
            </div>
            <div className="text-center">
              <p className="text-gray-400">Result</p>
              <p
                className={`font-medium ${
                  timeline.final_result === 'passed'
                    ? 'text-green-400'
                    : timeline.final_result === 'failed'
                    ? 'text-red-400'
                    : 'text-gray-400'
                }`}
              >
                {timeline.final_result || 'Incomplete'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Timeline scrubber */}
      <div className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-7xl mx-auto">
          <TimelineScrubber
            timeline={timeline}
            currentIndex={currentIndex}
            onIndexChange={setCurrentIndex}
          />
        </div>
      </div>

      {/* Main content */}
      <div className="p-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left column: Code snapshot */}
            <div className="space-y-4">
              <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wide">
                Code at this point
              </h2>
              <div className="h-[500px]">
                <CodeSnapshot
                  code={currentEntry?.code_snapshot ?? null}
                  diff={currentEntry?.code_diff ?? null}
                />
              </div>
            </div>

            {/* Right column: Panel switcher */}
            <div className="space-y-4">
              {/* Panel tabs */}
              <div className="flex items-center gap-2">
                <button
                  className={`px-4 py-2 text-sm rounded-lg transition-colors ${
                    activePanel === 'details'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                  }`}
                  onClick={() => setActivePanel('details')}
                >
                  Event Details
                </button>
                <button
                  className={`px-4 py-2 text-sm rounded-lg transition-colors ${
                    activePanel === 'ask'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                  }`}
                  onClick={() => setActivePanel('ask')}
                >
                  Ask the Interview
                </button>
                <button
                  className={`px-4 py-2 text-sm rounded-lg transition-colors ${
                    activePanel === 'insights'
                      ? 'bg-amber-600 text-white'
                      : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                  }`}
                  onClick={() => setActivePanel('insights')}
                >
                  Quick Insights
                </button>
              </div>

              {/* Active panel content */}
              <div className="h-[460px]">
                {activePanel === 'details' && (
                  <EventDetails
                    entry={currentEntry}
                    onVideoSeek={handleVideoSeek}
                  />
                )}
                {activePanel === 'ask' && (
                  <AskTheInterview
                    sessionId={sessionId}
                    hasVideo={timeline.has_video}
                    onTimelineJump={jumpToIndex}
                    onVideoSeek={handleVideoSeek}
                  />
                )}
                {activePanel === 'insights' && (
                  <QuickInsights
                    insights={insights}
                    onTimelineJump={jumpToIndex}
                    onVideoSeek={handleVideoSeek}
                  />
                )}
              </div>
            </div>
          </div>

          {/* Video player (if available) */}
          {timeline.has_video && (
            <div className="mt-6">
              <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wide mb-4">
                Interview Recording
              </h2>
              <div className="h-[400px]">
                <SyncedVideoPlayer
                  videoId={timeline.video_id}
                  videoUrl={timeline.video_url}
                  currentTimestamp={currentEntry?.video_timestamp_seconds ?? null}
                  offsetSeconds={timeline.video_start_offset_seconds}
                  onTimeUpdate={handleVideoTimeUpdate}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
