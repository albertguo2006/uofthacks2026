'use client';

import { useRef, useEffect } from 'react';

interface VideoPlayerProps {
  src: string;
  startTime?: number;
}

export function VideoPlayer({ src, startTime }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (videoRef.current && startTime !== undefined) {
      videoRef.current.currentTime = startTime;
    }
  }, [startTime]);

  return (
    <div className="relative aspect-video bg-black rounded-lg overflow-hidden">
      <video
        ref={videoRef}
        src={src}
        controls
        className="w-full h-full"
      >
        Your browser does not support the video tag.
      </video>
    </div>
  );
}
