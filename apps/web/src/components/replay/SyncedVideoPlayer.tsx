'use client';

import React, { useRef, useEffect, useCallback, useState } from 'react';

interface SyncedVideoPlayerProps {
  videoId: string | null;
  videoUrl: string | null;
  currentTimestamp: number | null;
  offsetSeconds: number;
  onTimeUpdate?: (seconds: number) => void;
  syncWithTimeline?: boolean;
}

export function SyncedVideoPlayer({
  videoId,
  videoUrl,
  currentTimestamp,
  offsetSeconds = 0,
  onTimeUpdate,
  syncWithTimeline = true,
}: SyncedVideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isSyncing, setIsSyncing] = useState(false);

  // Sync video to timeline timestamp
  useEffect(() => {
    if (!videoRef.current || !syncWithTimeline || isSyncing) return;
    if (currentTimestamp === null) return;

    // Calculate video time from timeline timestamp
    const videoTime = Math.max(0, currentTimestamp);

    // Only seek if difference is significant (>1 second)
    if (Math.abs(videoRef.current.currentTime - videoTime) > 1) {
      videoRef.current.currentTime = videoTime;
    }
  }, [currentTimestamp, syncWithTimeline, isSyncing]);

  // Handle video time updates
  const handleTimeUpdate = useCallback(() => {
    if (!videoRef.current) return;

    const time = videoRef.current.currentTime;
    setCurrentTime(time);

    if (!isSyncing) {
      onTimeUpdate?.(time + offsetSeconds);
    }
  }, [offsetSeconds, onTimeUpdate, isSyncing]);

  // Handle video metadata loaded
  const handleLoadedMetadata = useCallback(() => {
    if (!videoRef.current) return;
    setDuration(videoRef.current.duration);
  }, []);

  // Handle play/pause
  const togglePlay = useCallback(() => {
    if (!videoRef.current) return;

    if (videoRef.current.paused) {
      videoRef.current.play();
      setIsPlaying(true);
    } else {
      videoRef.current.pause();
      setIsPlaying(false);
    }
  }, []);

  // Handle seeking
  const handleSeek = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (!videoRef.current) return;

    const time = parseFloat(e.target.value);
    setIsSyncing(true);
    videoRef.current.currentTime = time;
    setCurrentTime(time);

    // Reset syncing after a short delay
    setTimeout(() => setIsSyncing(false), 500);
  }, []);

  // Format time for display
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Skip forward/backward
  const skip = useCallback((seconds: number) => {
    if (!videoRef.current) return;

    setIsSyncing(true);
    const newTime = Math.max(0, Math.min(duration, videoRef.current.currentTime + seconds));
    videoRef.current.currentTime = newTime;
    setCurrentTime(newTime);

    setTimeout(() => setIsSyncing(false), 500);
  }, [duration]);

  // No video available placeholder
  if (!videoId && !videoUrl) {
    return (
      <div className="bg-gray-900 rounded-lg overflow-hidden h-full flex flex-col">
        <div className="flex-1 flex items-center justify-center bg-gray-800">
          <div className="text-center">
            <svg
              className="w-16 h-16 mx-auto text-gray-600 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
              />
            </svg>
            <p className="text-gray-500 text-sm">No video linked to this session</p>
            <p className="text-gray-600 text-xs mt-1">
              Upload a video when starting the session to enable replay
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 rounded-lg overflow-hidden h-full flex flex-col">
      {/* Video element */}
      <div className="relative flex-1 bg-black">
        <video
          ref={videoRef}
          className="w-full h-full object-contain"
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
        >
          {/* TwelveLabs hosted video would be embedded differently */}
          {/* For now, use a placeholder source */}
          <source src={`/api/video/${videoId}/stream`} type="video/mp4" />
        </video>

        {/* Sync indicator */}
        {syncWithTimeline && (
          <div className="absolute top-2 right-2 flex items-center gap-1.5 px-2 py-1 bg-black/50 rounded text-xs text-gray-300">
            <div className={`w-2 h-2 rounded-full ${isSyncing ? 'bg-amber-500' : 'bg-green-500'}`} />
            {isSyncing ? 'Syncing...' : 'Synced'}
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="px-4 py-3 bg-gray-800 space-y-2">
        {/* Progress bar */}
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-400 w-12">{formatTime(currentTime)}</span>
          <input
            type="range"
            min={0}
            max={duration || 100}
            value={currentTime}
            onChange={handleSeek}
            className="flex-1 h-1 bg-gray-700 rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:rounded-full"
          />
          <span className="text-xs text-gray-400 w-12 text-right">{formatTime(duration)}</span>
        </div>

        {/* Playback controls */}
        <div className="flex items-center justify-center gap-4">
          <button
            className="p-2 text-gray-400 hover:text-white transition-colors"
            onClick={() => skip(-10)}
            title="Back 10s"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12.066 11.2a1 1 0 000 1.6l5.334 4A1 1 0 0019 16V8a1 1 0 00-1.6-.8l-5.333 4zM4.066 11.2a1 1 0 000 1.6l5.334 4A1 1 0 0011 16V8a1 1 0 00-1.6-.8l-5.334 4z"
              />
            </svg>
          </button>

          <button
            className="p-3 bg-white text-gray-900 rounded-full hover:bg-gray-200 transition-colors"
            onClick={togglePlay}
          >
            {isPlaying ? (
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
            )}
          </button>

          <button
            className="p-2 text-gray-400 hover:text-white transition-colors"
            onClick={() => skip(10)}
            title="Forward 10s"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M11.933 12.8a1 1 0 000-1.6L6.6 7.2A1 1 0 005 8v8a1 1 0 001.6.8l5.333-4zM19.933 12.8a1 1 0 000-1.6l-5.333-4A1 1 0 0013 8v8a1 1 0 001.6.8l5.333-4z"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
