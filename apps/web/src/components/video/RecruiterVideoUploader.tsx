'use client';

import { useState, useRef, useEffect } from 'react';
import { api, VideoDetails } from '@/lib/api';

interface RecruiterVideoUploaderProps {
  candidateId: string;
  onUploadComplete?: (videoId: string) => void;
}

export function RecruiterVideoUploader({ candidateId, onUploadComplete }: RecruiterVideoUploaderProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [uploadedVideoId, setUploadedVideoId] = useState<string | null>(null);
  const [videoStatus, setVideoStatus] = useState<string | null>(null);
  const [videoDetails, setVideoDetails] = useState<VideoDetails | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Poll for video status after upload
  useEffect(() => {
    if (!uploadedVideoId || videoStatus === 'ready' || videoStatus === 'failed') return;

    const pollInterval = setInterval(async () => {
      try {
        const status = await api.getVideoStatus(uploadedVideoId);
        setVideoStatus(status.status);
        if (status.status === 'ready') {
          // Fetch full video details including TwelveLabs analysis
          try {
            const details = await api.getVideoDetails(uploadedVideoId);
            setVideoDetails(details);
            console.log('TwelveLabs Analysis Results:', details);
          } catch (detailsErr) {
            console.error('Failed to fetch video details:', detailsErr);
          }
          onUploadComplete?.(uploadedVideoId);
        }
      } catch (err) {
        console.error('Failed to check video status:', err);
      }
    }, 3000);

    return () => clearInterval(pollInterval);
  }, [uploadedVideoId, videoStatus, onUploadComplete]);

  // Helper to render communication scores
  const renderCommunicationScore = (label: string, data?: { score: number; reason: string }) => {
    if (!data) return null;
    return (
      <div className="flex items-center justify-between py-1">
        <span className="text-sm text-gray-600 dark:text-gray-300">{label}</span>
        <div className="flex items-center gap-2">
          <div className="flex">
            {[1, 2, 3, 4, 5].map((i) => (
              <span
                key={i}
                className={`w-2 h-2 rounded-full mx-0.5 ${
                  i <= data.score ? 'bg-primary-500' : 'bg-gray-300 dark:bg-gray-600'
                }`}
              />
            ))}
          </div>
          <span className="text-sm font-medium">{data.score}/5</span>
        </div>
      </div>
    );
  };

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
    setVideoStatus(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.uploadCandidateVideo(candidateId, formData, (progress) => {
        setProgress(progress);
      });

      setUploadedVideoId(response.video_id);
      setVideoStatus(response.status);
    } catch (err) {
      setError('Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const getStatusDisplay = () => {
    switch (videoStatus) {
      case 'uploading':
        return { text: 'Processing upload...', color: 'text-blue-600' };
      case 'indexing':
        return { text: 'Analyzing video with AI...', color: 'text-purple-600' };
      case 'ready':
        return { text: 'Video ready for analysis', color: 'text-green-600' };
      case 'failed':
        return { text: 'Processing failed', color: 'text-red-600' };
      default:
        return { text: 'Processing...', color: 'text-gray-600' };
    }
  };

  return (
    <div className="p-6 bg-white dark:bg-slate-800 rounded-lg">
      <h3 className="font-semibold mb-4">Upload Interview Video</h3>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
        Upload an interview video to analyze with TwelveLabs AI for insights, highlights, and semantic search.
      </p>

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
      ) : uploadedVideoId && videoStatus ? (
        <div className="space-y-3">
          {videoStatus !== 'ready' && videoStatus !== 'failed' && (
            <div className="flex items-center justify-center gap-2">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600"></div>
              <span className={`text-sm ${getStatusDisplay().color}`}>
                {getStatusDisplay().text}
              </span>
            </div>
          )}
          {videoStatus === 'ready' && (
            <div className="space-y-4">
              <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                <div className="flex items-center gap-2 text-green-600">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="font-medium">Video analyzed successfully</span>
                </div>
              </div>

              {/* Summary Section */}
              {videoDetails?.summary && (
                <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                  <h4 className="font-semibold text-blue-700 dark:text-blue-300 mb-2 flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    AI Summary
                  </h4>
                  <p className="text-sm text-gray-700 dark:text-gray-200 whitespace-pre-wrap">
                    {videoDetails.summary}
                  </p>
                </div>
              )}

              {/* Communication Analysis Section */}
              {videoDetails?.communication_analysis && (
                <div className="p-4 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg">
                  <h4 className="font-semibold text-purple-700 dark:text-purple-300 mb-3 flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                    Communication Style
                  </h4>
                  <div className="space-y-2">
                    {renderCommunicationScore('Clarity', videoDetails.communication_analysis.clarity)}
                    {renderCommunicationScore('Confidence', videoDetails.communication_analysis.confidence)}
                    {renderCommunicationScore('Collaboration', videoDetails.communication_analysis.collaboration)}
                    {renderCommunicationScore('Technical Depth', videoDetails.communication_analysis.technical_depth)}
                  </div>
                </div>
              )}

              {/* Highlights Section */}
              {videoDetails?.highlights && videoDetails.highlights.length > 0 && (
                <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
                  <h4 className="font-semibold text-amber-700 dark:text-amber-300 mb-3 flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                    </svg>
                    Key Highlights ({videoDetails.highlights.length})
                  </h4>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {videoDetails.highlights.slice(0, 5).map((highlight, idx) => (
                      <div
                        key={idx}
                        className="p-2 bg-white dark:bg-slate-700 rounded border border-amber-100 dark:border-amber-800"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-800 text-amber-700 dark:text-amber-200 capitalize">
                            {highlight.category}
                          </span>
                          <span className="text-xs text-gray-500">
                            {Math.floor(highlight.start)}s - {Math.floor(highlight.end)}s
                          </span>
                        </div>
                        {highlight.transcript && (
                          <p className="text-xs text-gray-600 dark:text-gray-300 line-clamp-2">
                            {highlight.transcript}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* No analysis available message */}
              {!videoDetails?.summary && !videoDetails?.communication_analysis && !videoDetails?.highlights?.length && (
                <div className="p-4 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Video is ready. TwelveLabs analysis not available - check API configuration.
                  </p>
                </div>
              )}
            </div>
          )}
          {videoStatus === 'failed' && (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <div className="flex items-center gap-2 text-red-600">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                <span className="font-medium">Processing failed</span>
              </div>
              <button
                onClick={() => {
                  setUploadedVideoId(null);
                  setVideoStatus(null);
                }}
                className="mt-2 text-sm text-primary-600 hover:text-primary-700"
              >
                Try again
              </button>
            </div>
          )}
        </div>
      ) : (
        <button
          onClick={() => inputRef.current?.click()}
          className="w-full p-8 border-2 border-dashed border-gray-300 dark:border-slate-600 rounded-lg hover:border-primary-500 transition-colors"
        >
          <div className="text-center">
            <svg className="w-12 h-12 mx-auto text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <p className="mt-2 text-gray-600 dark:text-gray-300">
              Click to upload interview video
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
