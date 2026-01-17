'use client';

import { useState, useRef } from 'react';
import { api } from '@/lib/api';

interface InterviewUploaderProps {
  onUploadComplete?: (videoId: string) => void;
}

export function InterviewUploader({ onUploadComplete }: InterviewUploaderProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('video/')) {
      setError('Please select a video file');
      return;
    }

    // Validate file size (max 500MB)
    if (file.size > 500 * 1024 * 1024) {
      setError('File size must be less than 500MB');
      return;
    }

    setIsUploading(true);
    setError(null);
    setProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.uploadVideo(formData, (progress) => {
        setProgress(progress);
      });

      onUploadComplete?.(response.video_id);
    } catch (err) {
      setError('Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="p-6 bg-white dark:bg-slate-800 rounded-lg">
      <h3 className="font-semibold mb-4">Upload Interview Video</h3>

      <input
        ref={inputRef}
        type="file"
        accept="video/*"
        onChange={handleFileSelect}
        className="hidden"
      />

      {isUploading ? (
        <div className="space-y-3">
          <div className="h-2 bg-gray-200 dark:bg-slate-600 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary-600 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-sm text-gray-500 text-center">
            Uploading... {progress}%
          </p>
        </div>
      ) : (
        <button
          onClick={() => inputRef.current?.click()}
          className="w-full p-8 border-2 border-dashed border-gray-300 dark:border-slate-600 rounded-lg hover:border-primary-500 transition-colors"
        >
          <div className="text-center">
            <span className="text-4xl">📹</span>
            <p className="mt-2 text-gray-600 dark:text-gray-300">
              Click to upload or drag and drop
            </p>
            <p className="text-sm text-gray-500">MP4, WebM up to 500MB</p>
          </div>
        </button>
      )}

      {error && (
        <p className="mt-3 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}
