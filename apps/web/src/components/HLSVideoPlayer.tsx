'use client';

import { useEffect, useRef, useState } from 'react';
import Hls from 'hls.js';

interface HLSVideoPlayerProps {
  src: string;
  poster?: string;
  className?: string;
  onTimeUpdate?: (currentTime: number) => void;
  startTime?: number;
}

export default function HLSVideoPlayer({
  src,
  poster,
  className = '',
  onTimeUpdate,
  startTime,
}: HLSVideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const hlsRef = useRef<Hls | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !src) return;

    // Check if the source is an HLS stream
    const isHLS = src.includes('.m3u8');

    if (isHLS && Hls.isSupported()) {
      // Use hls.js for HLS streams
      const hls = new Hls({
        enableWorker: true,
        lowLatencyMode: false,
      });

      hlsRef.current = hls;

      hls.loadSource(src);
      hls.attachMedia(video);

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        setIsLoading(false);
        if (startTime && startTime > 0) {
          video.currentTime = startTime;
        }
      });

      hls.on(Hls.Events.ERROR, (event, data) => {
        console.error('[HLS] Error:', data);
        if (data.fatal) {
          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              setError('Network error - trying to recover...');
              hls.startLoad();
              break;
            case Hls.ErrorTypes.MEDIA_ERROR:
              setError('Media error - trying to recover...');
              hls.recoverMediaError();
              break;
            default:
              setError('Failed to load video');
              hls.destroy();
              break;
          }
        }
      });

      return () => {
        hls.destroy();
        hlsRef.current = null;
      };
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      // Native HLS support (Safari)
      video.src = src;
      video.addEventListener('loadedmetadata', () => {
        setIsLoading(false);
        if (startTime && startTime > 0) {
          video.currentTime = startTime;
        }
      });
    } else if (!isHLS) {
      // Regular video file
      video.src = src;
      video.addEventListener('loadedmetadata', () => {
        setIsLoading(false);
        if (startTime && startTime > 0) {
          video.currentTime = startTime;
        }
      });
    } else {
      setError('HLS is not supported in this browser');
      setIsLoading(false);
    }
  }, [src, startTime]);

  // Handle time updates
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !onTimeUpdate) return;

    const handleTimeUpdate = () => {
      onTimeUpdate(video.currentTime);
    };

    video.addEventListener('timeupdate', handleTimeUpdate);
    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
    };
  }, [onTimeUpdate]);

  // Method to seek to a specific time
  const seekTo = (time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
    }
  };

  if (error) {
    return (
      <div className={`bg-slate-900 rounded-lg aspect-video flex items-center justify-center ${className}`}>
        <div className="text-center text-red-400 p-4">
          <svg className="w-12 h-12 mx-auto mb-3 opacity-75" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p className="text-sm">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative bg-slate-900 rounded-lg overflow-hidden ${className}`}>
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900">
          <div className="text-center">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-white mx-auto mb-3"></div>
            <p className="text-sm text-gray-400">Loading video...</p>
          </div>
        </div>
      )}
      <video
        ref={videoRef}
        className="w-full aspect-video"
        controls
        playsInline
        poster={poster}
        crossOrigin="anonymous"
      />
    </div>
  );
}

// Export a hook for external control
export function useVideoPlayer() {
  const seekTo = (videoElement: HTMLVideoElement | null, time: number) => {
    if (videoElement) {
      videoElement.currentTime = time;
    }
  };

  return { seekTo };
}
