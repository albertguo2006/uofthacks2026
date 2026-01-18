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
  const hasInitializedRef = useRef(false);

  // Store props in refs to avoid closure issues
  const sessionIdRef = useRef(sessionId);
  const taskIdRef = useRef(taskId);

  // Update refs when props change
  useEffect(() => {
    sessionIdRef.current = sessionId;
    taskIdRef.current = taskId;
  }, [sessionId, taskId]);

  const [isRecording, setIsRecording] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(true);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'uploaded' | 'error'>('idle');

  // Initialize camera and start recording - only run once when becoming active
  useEffect(() => {
    // Only initialize if isActive is true and we haven't already initialized
    if (!isActive || hasInitializedRef.current) return;

    const initializeCamera = async () => {
      try {
        console.log('Initializing camera for proctoring...');
        hasInitializedRef.current = true;

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

        recorder.onstop = async () => {
          console.log('Recording stopped, uploading video...');
          const blob = new Blob(chunksRef.current, { type: mimeType });

          // Upload the video
          try {
            setUploadStatus('uploading');
            const formData = new FormData();
            formData.append('video', blob, `proctored_${sessionIdRef.current}_${Date.now()}.webm`);
            formData.append('session_id', sessionIdRef.current);
            formData.append('task_id', taskIdRef.current);
            formData.append('is_proctored', 'true');

            const response = await api.postForm('/proctoring/upload-video', formData);
            console.log('Video uploaded successfully:', response);
            setUploadStatus('uploaded');

            onRecordingComplete?.(blob);
          } catch (error) {
            console.error('Failed to upload video:', error);
            setUploadStatus('error');
          }
        };

        // Start recording
        recorder.start(1000); // Collect data every second
        setIsRecording(true);
        setCameraError(null);
        console.log('Recording started successfully');
      } catch (error) {
        console.error('Failed to access camera:', error);
        setCameraError('Failed to access camera. Please ensure camera permissions are granted.');
        hasInitializedRef.current = false; // Reset on error so it can retry
      }
    };

    initializeCamera();
  }, [isActive]); // Only depend on isActive

  // Separate cleanup effect - only runs on unmount or when isActive becomes false
  useEffect(() => {
    return () => {
      // Only cleanup if we're actually unmounting or if isActive changed to false
      if (!isActive && hasInitializedRef.current) {
        console.log('Cleaning up video recording...');
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
          mediaRecorderRef.current.stop();
        }
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
        }
        hasInitializedRef.current = false;
        setIsRecording(false);
      }
    };
  }, [isActive]);

  // Final cleanup on component unmount
  useEffect(() => {
    return () => {
      // This runs only when the component is completely unmounting
      if (hasInitializedRef.current) {
        console.log('Component unmounting, stopping recording...');
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
          mediaRecorderRef.current.stop();
        }
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
        }
      }
    };
  }, []); // Empty dependency array - only runs on unmount

  // Handle tab visibility changes - continue recording but don't hide preview
  // (hiding preview might cause issues with some browsers)
  useEffect(() => {
    if (!isActive) return;

    const handleVisibilityChange = () => {
      if (document.hidden) {
        console.log('Tab switched - recording continues in background');
        // Keep preview visible to avoid any browser issues with hidden video elements
      } else {
        console.log('Tab returned - recording continues');
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [isActive]);

  // Stop recording manually
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, []);

  const togglePreview = () => {
    setShowPreview(!showPreview);
  };

  if (cameraError) {
    return (
      <div className="fixed bottom-4 left-4 z-50 p-3 bg-red-100 dark:bg-red-900/50 border border-red-300 dark:border-red-700 text-red-800 dark:text-red-200 rounded-lg">
        {cameraError}
      </div>
    );
  }

  if (!isActive) return null;

  return (
    <div className="fixed bottom-4 left-4 z-50">
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
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2">
          <button
            onClick={togglePreview}
            className="px-3 py-1.5 text-xs bg-gray-700 text-white rounded hover:bg-gray-600 transition-colors"
          >
            {showPreview ? 'Hide Camera' : 'Show Camera'}
          </button>
          {isRecording && (
            <button
              onClick={stopRecording}
              className="px-3 py-1.5 text-xs bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
            >
              Stop Recording
            </button>
          )}
        </div>

        {/* Status Messages */}
        {isRecording && (
          <span className="text-xs text-gray-400">Recording session...</span>
        )}
        {uploadStatus === 'uploading' && (
          <span className="text-xs text-yellow-400">Uploading video...</span>
        )}
        {uploadStatus === 'uploaded' && (
          <span className="text-xs text-green-400">Video uploaded successfully</span>
        )}
        {uploadStatus === 'error' && (
          <span className="text-xs text-red-400">Failed to upload video</span>
        )}
      </div>
    </div>
  );
}