'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import type { Timeline, QuickInsightsResponse } from '@/types/timeline';

interface UseTimelineResult {
  timeline: Timeline | null;
  insights: QuickInsightsResponse | null;
  loading: boolean;
  error: string | null;
  currentIndex: number;
  setCurrentIndex: (index: number) => void;
  jumpToIndex: (index: number) => void;
  jumpToVideoTimestamp: (seconds: number) => void;
  currentEntry: Timeline['entries'][number] | null;
  refetch: () => Promise<void>;
}

export function useTimeline(sessionId: string): UseTimelineResult {
  const [timeline, setTimeline] = useState<Timeline | null>(null);
  const [insights, setInsights] = useState<QuickInsightsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);

  const fetchTimeline = useCallback(async () => {
    if (!sessionId) return;

    setLoading(true);
    setError(null);

    try {
      const [timelineData, insightsData] = await Promise.all([
        api.getSessionTimeline(sessionId),
        api.getSessionInsights(sessionId),
      ]);

      setTimeline(timelineData);
      setInsights(insightsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load timeline');
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchTimeline();
  }, [fetchTimeline]);

  const jumpToIndex = useCallback((index: number) => {
    if (timeline && index >= 0 && index < timeline.entries.length) {
      setCurrentIndex(index);
    }
  }, [timeline]);

  const jumpToVideoTimestamp = useCallback((seconds: number) => {
    if (!timeline) return;

    // Find the closest timeline entry to this video timestamp
    let closestIndex = 0;
    let closestDiff = Infinity;

    timeline.entries.forEach((entry, index) => {
      if (entry.video_timestamp_seconds !== null) {
        const diff = Math.abs(entry.video_timestamp_seconds - seconds);
        if (diff < closestDiff) {
          closestDiff = diff;
          closestIndex = index;
        }
      }
    });

    setCurrentIndex(closestIndex);
  }, [timeline]);

  const currentEntry = timeline?.entries[currentIndex] ?? null;

  return {
    timeline,
    insights,
    loading,
    error,
    currentIndex,
    setCurrentIndex,
    jumpToIndex,
    jumpToVideoTimestamp,
    currentEntry,
    refetch: fetchTimeline,
  };
}
