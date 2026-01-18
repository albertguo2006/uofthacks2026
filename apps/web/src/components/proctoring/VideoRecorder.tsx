'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { api } from '@/lib/api';

interface VideoRecorderProps {
  sessionId: string;
  taskId: string;
  isActive: boolean;
  onRecordingComplete?: (videoBlob: Blob) => void;
}

export function VideoRecorder({ sessionId, taskId, isActive, onRecordingComplete }: VideoRecorderProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const [isRecording, setIsRecording] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(true);

  // Initialize camera and start recording
  useEffect(() => {
    if (!isActive) return;

    const initializeCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 1280 },
            height: { ideal: 720 },
            facingMode: 'user'
          },
          audio: true // Include audio for interview recording
        });

        streamRef.current = stream;

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.muted = true; // Mute local playback
        }

        // Start recording
        const mimeType = MediaRecorder.isTypeSupported('video/webm;codecs=vp9')
          ? 'video/webm;codecs=vp9'
          : 'video/webm';

        const recorder = new MediaRecorder(stream, {
          mimeType,
          videoBitsPerSecond: 2500000 // 2.5 Mbps for good quality
        });

        mediaRecorderRef.current = recorder;
        chunksRef.current = [];

        recorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            chunksRef.current.push(event.data);
          }
        };

        recorder.onstop = () => {
          const blob = new Blob(chunksRef.current, { type: mimeType });
          onRecordingComplete?.(blob);

          // Auto-upload the video
          uploadVideo(blob);
        };

        // Start recording
        recorder.start(1000); // Collect data every second
        setIsRecording(true);
        setCameraError(null);
      } catch (error) {
        console.error('Failed to access camera:', error);
        setCameraError('Failed to access camera. Please ensure camera permissions are granted.');
      }
    };

    initializeCamera();

    return () => {
      // Cleanup on unmount
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, [isActive, onRecordingComplete]);

  // Upload video to backend
  const uploadVideo = async (blob: Blob) => {
    try {
      const formData = new FormData();
      formData.append('video', blob, `proctored_${sessionId}_${Date.now()}.webm`);
      formData.append('session_id', sessionId);
      formData.append('task_id', taskId);
      formData.append('is_proctored', 'true');

      const response = await api.postForm('/proctoring/upload-video', formData);
      console.log('Video uploaded successfully:', response);
    } catch (error) {
      console.error('Failed to upload video:', error);
    }
  };

  // Stop recording when session ends
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, []);

  // Manually trigger stop (for when task is completed)
  useEffect(() => {
    if (!isActive && isRecording) {
      stopRecording();
    }
  }, [isActive, isRecording, stopRecording]);

  const togglePreview = () => {
    setShowPreview(!showPreview);
  };

  if (cameraError) {
    return (
      <div className="fixed bottom-4 right-4 z-50 p-3 bg-red-100 dark:bg-red-900/50 border border-red-300 dark:border-red-700 text-red-800 dark:text-red-200 rounded-lg">
        {cameraError}
      </div>
    );
  }

  if (!isActive) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {/* Camera Preview */}
      {showPreview && (
        <div className="relative mb-2">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-48 h-36 rounded-lg shadow-lg border-2 border-gray-700 dark:border-gray-600"
          />
          {isRecording && (
            <div className="absolute top-2 left-2 flex items-center gap-1.5">
              <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
              <span className="text-xs text-white bg-black/50 px-1.5 py-0.5 rounded">REC</span>
            </div>
          )}
        </div>
      )}

      {/* Controls */}
      <div className="flex items-center gap-2">
        <button
          onClick={togglePreview}
          className="px-3 py-1.5 text-xs bg-gray-700 text-white rounded hover:bg-gray-600 transition-colors"
        >
          {showPreview ? 'Hide Camera' : 'Show Camera'}
        </button>
        {isRecording && (
          <span className="text-xs text-gray-400">Recording session...</span>
        )}
      </div>
    </div>
  );
}