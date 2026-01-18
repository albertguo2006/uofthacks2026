'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api, VideoDetails } from '@/lib/api';
import HLSVideoPlayer from '@/components/HLSVideoPlayer';

type SearchResult = {
  start_time: number;
  end_time: number;
  confidence: number;
  transcript_snippet: string;
};

export default function VideoDetailPage() {
  const params = useParams();
  const candidateId = params.id as string;
  const videoId = params.videoId as string;

  const [video, setVideo] = useState<VideoDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentVideoTime, setCurrentVideoTime] = useState(0);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Seek video to specific time
  const seekToTime = (seconds: number) => {
    // Find video element and seek
    const videoElement = document.querySelector('video');
    if (videoElement) {
      videoElement.currentTime = seconds;
      videoElement.play().catch(() => {});
    }
  };

  useEffect(() => {
    async function fetchVideo() {
      try {
        console.log('[VideoDetail] Fetching video details for:', videoId);
        const details = await api.getVideoDetails(videoId);
        console.log('[VideoDetail] Received video details:', details);
        setVideo(details);
      } catch (err) {
        console.error('[VideoDetail] Error fetching video:', err);
        setError(err instanceof Error ? err.message : 'Failed to load video');
      } finally {
        setLoading(false);
      }
    }
    fetchVideo();
  }, [videoId]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    setSearchError(null);
    try {
      const response = await api.searchVideo(videoId, searchQuery);
      setSearchResults(response.results);
    } catch (err) {
      setSearchError(err instanceof Error ? err.message : 'Search failed');
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const formatTimestamp = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    if (mins > 0) {
      return `${mins}m ${secs}s`;
    }
    return `${secs}s`;
  };

  const getCategoryColor = (category: string): string => {
    const colors: Record<string, string> = {
      approach: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
      debugging: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
      tradeoffs: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
      questions: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
      testing: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300',
      optimization: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-300',
    };
    return colors[category] || 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300';
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error || !video) {
    return (
      <div className="space-y-4">
        <Link
          href={`/recruiter/candidates/${candidateId}`}
          className="inline-flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Candidate
        </Link>
        <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg">
          {error || 'Video not found'}
        </div>
      </div>
    );
  }

  // Check if any analysis data is available
  const hasAnalysis = video.summary ||
    video.communication_analysis ||
    (video.highlights && video.highlights.length > 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            href={`/recruiter/candidates/${candidateId}`}
            className="inline-flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Candidate
          </Link>
        </div>
        <div className="flex items-center gap-4">
          <span className={`px-2 py-1 text-xs font-medium rounded ${
            video.status === 'ready'
              ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
              : video.status === 'indexing'
              ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
              : 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300'
          }`}>
            Status: {video.status}
          </span>
          {video.duration_seconds && (
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Duration: {formatDuration(video.duration_seconds)}
            </span>
          )}
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Video Player */}
          {video.stream_url ? (
            <HLSVideoPlayer
              src={video.stream_url}
              poster={video.thumbnail_url}
              className="w-full"
            />
          ) : (
            <div className="bg-slate-900 rounded-lg aspect-video flex items-center justify-center">
              <div className="text-center text-gray-400">
                <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                <p className="text-sm">Video stream unavailable</p>
                <p className="text-xs mt-1 opacity-75">Video may still be processing</p>
              </div>
            </div>
          )}

          {/* No Analysis Available Message */}
          {!hasAnalysis && (
            <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-6">
              <div className="flex items-start gap-3">
                <svg className="w-6 h-6 text-amber-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div>
                  <h3 className="font-semibold text-amber-800 dark:text-amber-200">No AI Analysis Available</h3>
                  <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
                    This video has not been analyzed by TwelveLabs AI. This could happen if:
                  </p>
                  <ul className="text-sm text-amber-700 dark:text-amber-300 mt-2 list-disc list-inside space-y-1">
                    <li>The TwelveLabs API key is not configured on the server</li>
                    <li>The video is still being processed</li>
                    <li>There was an error during analysis</li>
                  </ul>
                  <p className="text-sm text-amber-700 dark:text-amber-300 mt-3">
                    Please check the server configuration or try uploading the video again.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* AI Summary */}
          {video.summary && (
            <div className="bg-white dark:bg-slate-800 rounded-lg p-6">
              <h2 className="font-semibold mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                AI Interview Summary
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                {video.summary}
              </p>
            </div>
          )}

          {/* Communication Analysis */}
          {video.communication_analysis && (
            <div className="bg-white dark:bg-slate-800 rounded-lg p-6">
              <h2 className="font-semibold mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                Communication Analysis
              </h2>
              <div className="space-y-4">
                {video.communication_analysis.clarity && (
                  <div className="flex items-start gap-4 p-4 bg-gray-50 dark:bg-slate-700 rounded-lg">
                    <div className="flex-shrink-0">
                      <div className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-2">Clarity</div>
                      <div className="flex items-center gap-1">
                        {[1, 2, 3, 4, 5].map((i) => (
                          <div
                            key={i}
                            className={`w-5 h-5 rounded ${
                              i <= video.communication_analysis!.clarity!.score
                                ? 'bg-blue-500'
                                : 'bg-gray-200 dark:bg-slate-600'
                            }`}
                          />
                        ))}
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 flex-1">
                      {video.communication_analysis.clarity.reason}
                    </p>
                  </div>
                )}
                {video.communication_analysis.confidence && (
                  <div className="flex items-start gap-4 p-4 bg-gray-50 dark:bg-slate-700 rounded-lg">
                    <div className="flex-shrink-0">
                      <div className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-2">Confidence</div>
                      <div className="flex items-center gap-1">
                        {[1, 2, 3, 4, 5].map((i) => (
                          <div
                            key={i}
                            className={`w-5 h-5 rounded ${
                              i <= video.communication_analysis!.confidence!.score
                                ? 'bg-green-500'
                                : 'bg-gray-200 dark:bg-slate-600'
                            }`}
                          />
                        ))}
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 flex-1">
                      {video.communication_analysis.confidence.reason}
                    </p>
                  </div>
                )}
                {video.communication_analysis.collaboration && (
                  <div className="flex items-start gap-4 p-4 bg-gray-50 dark:bg-slate-700 rounded-lg">
                    <div className="flex-shrink-0">
                      <div className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-2">Collaboration</div>
                      <div className="flex items-center gap-1">
                        {[1, 2, 3, 4, 5].map((i) => (
                          <div
                            key={i}
                            className={`w-5 h-5 rounded ${
                              i <= video.communication_analysis!.collaboration!.score
                                ? 'bg-purple-500'
                                : 'bg-gray-200 dark:bg-slate-600'
                            }`}
                          />
                        ))}
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 flex-1">
                      {video.communication_analysis.collaboration.reason}
                    </p>
                  </div>
                )}
                {video.communication_analysis.technical_depth && (
                  <div className="flex items-start gap-4 p-4 bg-gray-50 dark:bg-slate-700 rounded-lg">
                    <div className="flex-shrink-0">
                      <div className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-2">Technical Depth</div>
                      <div className="flex items-center gap-1">
                        {[1, 2, 3, 4, 5].map((i) => (
                          <div
                            key={i}
                            className={`w-5 h-5 rounded ${
                              i <= video.communication_analysis!.technical_depth!.score
                                ? 'bg-amber-500'
                                : 'bg-gray-200 dark:bg-slate-600'
                            }`}
                          />
                        ))}
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 flex-1">
                      {video.communication_analysis.technical_depth.reason}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Debug Info (only shown if no analysis) */}
          {!hasAnalysis && (
            <div className="bg-gray-100 dark:bg-slate-800 rounded-lg p-4">
              <details className="text-sm">
                <summary className="cursor-pointer text-gray-600 dark:text-gray-400 font-medium">
                  Debug: Video Data
                </summary>
                <pre className="mt-2 text-xs overflow-auto p-2 bg-gray-200 dark:bg-slate-900 rounded">
                  {JSON.stringify(video, null, 2)}
                </pre>
              </details>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Search */}
          <div className="bg-white dark:bg-slate-800 rounded-lg p-6">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Search Video
            </h3>
            <input
              type="text"
              placeholder="e.g., 'testing strategy', 'debugging'"
              className="w-full px-4 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600 text-sm"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button
              onClick={handleSearch}
              disabled={isSearching || !searchQuery.trim()}
              className="mt-2 w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
            >
              {isSearching ? 'Searching...' : 'Search'}
            </button>

            {searchError && (
              <p className="mt-2 text-sm text-red-600 dark:text-red-400">
                {searchError}
              </p>
            )}

            {searchResults.length > 0 && (
              <div className="mt-4 space-y-2">
                <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Results ({searchResults.length})
                </h4>
                {searchResults.map((result, index) => (
                  <div
                    key={index}
                    onClick={() => seekToTime(result.start_time)}
                    className="p-3 bg-gray-50 dark:bg-slate-700 rounded-lg cursor-pointer hover:bg-gray-100 dark:hover:bg-slate-600 transition-colors group"
                  >
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm font-mono text-primary-600 dark:text-primary-400 group-hover:underline">
                        {formatTimestamp(result.start_time)} - {formatTimestamp(result.end_time)}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {(result.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    {result.transcript_snippet && (
                      <p className="text-xs text-gray-600 dark:text-gray-300 line-clamp-2">
                        {result.transcript_snippet}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}

            {!isSearching && searchQuery && searchResults.length === 0 && !searchError && (
              <p className="mt-4 text-sm text-gray-500 dark:text-gray-400 text-center">
                No results found
              </p>
            )}
          </div>

          {/* Highlights */}
          {video.highlights && video.highlights.length > 0 ? (
            <div className="bg-white dark:bg-slate-800 rounded-lg p-6">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                </svg>
                Key Highlights ({video.highlights.length})
              </h3>
              <div className="space-y-3">
                {video.highlights.map((highlight, idx) => (
                  <div
                    key={idx}
                    onClick={() => seekToTime(highlight.start)}
                    className="p-3 bg-gray-50 dark:bg-slate-700 rounded-lg cursor-pointer hover:bg-gray-100 dark:hover:bg-slate-600 transition-colors group"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`px-2 py-0.5 text-xs font-medium rounded uppercase ${getCategoryColor(highlight.category)}`}>
                        {highlight.category}
                      </span>
                      <span className="text-xs font-mono text-gray-500 dark:text-gray-400 group-hover:underline">
                        {formatTimestamp(highlight.start)} - {formatTimestamp(highlight.end)}
                      </span>
                    </div>
                    {highlight.transcript && (
                      <p className="text-sm text-gray-600 dark:text-gray-300">
                        {highlight.transcript}
                      </p>
                    )}
                    <div className="mt-2 flex items-center gap-1">
                      <div className="text-xs text-gray-400">Confidence:</div>
                      <div className="flex-1 h-1.5 bg-gray-200 dark:bg-slate-600 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-amber-500 rounded-full"
                          style={{ width: `${highlight.confidence * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-400">{(highlight.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="bg-white dark:bg-slate-800 rounded-lg p-6">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                </svg>
                Key Highlights
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                No highlights available for this video.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
