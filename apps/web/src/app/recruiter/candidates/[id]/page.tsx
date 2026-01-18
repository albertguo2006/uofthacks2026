'use client';

import { useState, useEffect, useMemo } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { SkillPassport } from '@/components/passport/SkillPassport';
import { RecruiterVideoUploader } from '@/components/video/RecruiterVideoUploader';
import { InterviewRequestModal } from '@/components/recruiter/InterviewRequestModal';
import { usePassport } from '@/hooks/usePassport';
import { api } from '@/lib/api';
import type { SessionSummary, RecruiterVideo } from '@/types/timeline';

type TimelineItem =
  | { type: 'session'; data: SessionSummary; date: Date }
  | { type: 'video'; data: RecruiterVideo; date: Date };

export default function CandidateDetailPage() {
  const params = useParams();
  const candidateId = params.id as string;
  const { passport, isLoading, error } = usePassport(candidateId);

  // Sessions for replay
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(true);

  // Recruiter-uploaded videos
  const [videos, setVideos] = useState<RecruiterVideo[]>([]);
  const [loadingVideos, setLoadingVideos] = useState(true);

  // Expanded state for code display
  const [expandedCode, setExpandedCode] = useState<string | null>(null);

  // Delete confirmation state
  const [deletingVideoId, setDeletingVideoId] = useState<string | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  // Interview request modal state
  const [showInterviewModal, setShowInterviewModal] = useState(false);

  const handleDeleteVideo = async (videoId: string) => {
    setDeletingVideoId(videoId);
    try {
      await api.deleteCandidateVideo(candidateId, videoId);
      setVideos(videos.filter(v => v.video_id !== videoId));
      setDeleteConfirmId(null);
    } catch (err) {
      console.error('Failed to delete video:', err);
      alert('Failed to delete video. Please try again.');
    } finally {
      setDeletingVideoId(null);
    }
  };


  // Fetch sessions for this candidate
  useEffect(() => {
    async function fetchSessions() {
      try {
        const response = await api.getUserSessions(candidateId);
        setSessions(response.sessions);
      } catch (err) {
        console.error('Failed to load sessions:', err);
      } finally {
        setLoadingSessions(false);
      }
    }
    fetchSessions();
  }, [candidateId]);

  // Fetch recruiter-uploaded videos
  useEffect(() => {
    async function fetchVideos() {
      try {
        const response = await api.getRecruiterVideos(candidateId);
        setVideos(response.videos);
      } catch (err) {
        console.error('Failed to load videos:', err);
      } finally {
        setLoadingVideos(false);
      }
    }
    fetchVideos();
  }, [candidateId]);

  // Combine proctored sessions and videos into a unified timeline
  const timelineItems = useMemo(() => {
    const items: TimelineItem[] = [];

    // Add proctored sessions only
    sessions.filter(s => s.is_proctored).forEach(session => {
      items.push({
        type: 'session',
        data: session,
        date: new Date(session.started_at)
      });
    });

    // Add videos
    videos.forEach(video => {
      items.push({
        type: 'video',
        data: video,
        date: new Date(video.uploaded_at)
      });
    });

    // Sort by date descending (newest first)
    return items.sort((a, b) => b.date.getTime() - a.date.getTime());
  }, [sessions, videos]);

  const formatTimestamp = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const isLoaded = !loadingSessions && !loadingVideos;
  const proctoredSessionCount = sessions.filter(s => s.is_proctored).length;

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg">
        {error}
      </div>
    );
  }

  if (!passport) {
    return (
      <div className="text-center py-12 text-gray-600 dark:text-gray-400">
        Candidate not found
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">{passport.display_name}</h1>
        <button
          onClick={() => setShowInterviewModal(true)}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          Invite to Interview
        </button>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <SkillPassport passport={passport} showAnalytics />

          {/* Combined Timeline: Proctored Sessions + Recruiter Videos */}
          <div className="bg-white dark:bg-slate-800 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">Coding Sessions & Interview Videos</h3>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {proctoredSessionCount} proctored session{proctoredSessionCount !== 1 ? 's' : ''}, {videos.length} video{videos.length !== 1 ? 's' : ''}
              </span>
            </div>

            {!isLoaded ? (
              <div className="flex justify-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
              </div>
            ) : timelineItems.length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400 text-sm">
                No proctored sessions or videos recorded yet
              </p>
            ) : (
              <div className="space-y-4">
                {timelineItems.map((item, index) => {
                  if (item.type === 'session') {
                    const session = item.data;
                    const isExpanded = expandedCode === session.session_id;

                    return (
                      <div
                        key={`session-${session.session_id}`}
                        className="border border-gray-200 dark:border-slate-600 rounded-lg overflow-hidden"
                      >
                        {/* Session Header */}
                        <div className="p-4 bg-gray-50 dark:bg-slate-700">
                          <div className="flex items-start justify-between">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="px-2 py-0.5 text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 rounded">
                                  Proctored Session
                                </span>
                              </div>
                              <h4 className="font-medium text-sm mt-2 truncate">
                                {session.task_title}
                              </h4>
                              <div className="flex items-center gap-3 mt-1 text-xs text-gray-500 dark:text-gray-400">
                                <span>{session.event_count} events</span>
                                <span>{session.code_snapshots} snapshots</span>
                                <span>
                                  {new Date(session.started_at).toLocaleDateString()}
                                </span>
                              </div>
                            </div>
                            <Link
                              href={`/recruiter/candidates/${candidateId}/replay/${session.session_id}`}
                              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded-lg transition-colors flex items-center gap-1"
                            >
                              <svg
                                className="w-3 h-3"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                                />
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                                />
                              </svg>
                              View Replay
                            </Link>
                          </div>
                        </div>

                        {/* AI Insights Summary */}
                        {session.insights_summary && (
                          <div className="px-4 py-3 border-t border-gray-200 dark:border-slate-600 bg-purple-50 dark:bg-purple-900/20">
                            <div className="flex items-start gap-2">
                              <svg className="w-4 h-4 text-purple-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                              </svg>
                              <div>
                                <p className="text-xs font-medium text-purple-700 dark:text-purple-300 mb-1">AI Insights</p>
                                <p className="text-sm text-gray-700 dark:text-gray-300">
                                  {session.insights_summary}
                                </p>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Final Code (Collapsible) */}
                        {session.final_code && (
                          <div className="border-t border-gray-200 dark:border-slate-600">
                            <button
                              onClick={() => setExpandedCode(isExpanded ? null : session.session_id)}
                              className="w-full px-4 py-2 text-left text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-700 flex items-center justify-between"
                            >
                              <span className="flex items-center gap-2">
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                                </svg>
                                Final Code
                              </span>
                              <svg
                                className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                              >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                              </svg>
                            </button>
                            {isExpanded && (
                              <pre className="px-4 py-3 bg-slate-900 text-slate-100 text-xs overflow-x-auto max-h-64">
                                <code>{session.final_code}</code>
                              </pre>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  } else {
                    // Video item
                    const video = item.data;
                    const isProcessing = video.status === 'uploading' || video.status === 'indexing';
                    const isReady = video.status === 'ready';
                    const isFailed = video.status === 'failed';
                    const hasAnalysis = isReady && (video.summary || video.communication_analysis || (video.highlights && video.highlights.length > 0));

                    return (
                      <div
                        key={`video-${video.video_id}`}
                        className="border border-gray-200 dark:border-slate-600 rounded-lg overflow-hidden"
                      >
                        {/* Video Header */}
                        <div className="p-4 bg-gray-50 dark:bg-slate-700">
                          <div className="flex items-start justify-between">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className={`px-2 py-0.5 text-xs font-medium rounded ${
                                  video.is_proctored
                                    ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400'
                                    : 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
                                }`}>
                                  {video.is_proctored ? 'Proctored Video' : 'Interview Video'}
                                </span>
                                {video.is_proctored && video.task_id && (
                                  <span className="text-xs text-gray-500 dark:text-gray-400">
                                    Task: {video.task_id}
                                  </span>
                                )}
                                {isProcessing && (
                                  <span className="px-2 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400 rounded flex items-center gap-1">
                                    <div className="animate-spin rounded-full h-3 w-3 border-b border-yellow-600"></div>
                                    {video.status === 'uploading' ? 'Uploading...' : 'Processing...'}
                                  </span>
                                )}
                                {isFailed && (
                                  <span className="px-2 py-0.5 text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400 rounded">
                                    Failed
                                  </span>
                                )}
                                {isReady && hasAnalysis && (
                                  <span className="px-2 py-0.5 text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 rounded">
                                    Analysis Ready
                                  </span>
                                )}
                              </div>
                              <h4 className="font-medium text-sm mt-2 truncate">
                                {video.filename}
                              </h4>
                              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                {new Date(video.uploaded_at).toLocaleDateString()} at{' '}
                                {new Date(video.uploaded_at).toLocaleTimeString()}
                              </p>
                            </div>
                            <div className="flex items-center gap-2">
                              {isReady && hasAnalysis && (
                                <Link
                                  href={`/recruiter/candidates/${candidateId}/video/${video.video_id}`}
                                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded-lg transition-colors flex items-center gap-1"
                                >
                                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                  </svg>
                                  View Analysis
                                </Link>
                              )}
                              {/* Delete Button - only for recruiter-uploaded videos */}
                              {!video.is_proctored && deleteConfirmId === video.video_id ? (
                                <div className="flex items-center gap-1">
                                  <button
                                    onClick={() => handleDeleteVideo(video.video_id)}
                                    disabled={deletingVideoId === video.video_id}
                                    className="px-2 py-1 bg-red-600 hover:bg-red-700 text-white text-xs font-medium rounded transition-colors disabled:opacity-50"
                                  >
                                    {deletingVideoId === video.video_id ? 'Deleting...' : 'Confirm'}
                                  </button>
                                  <button
                                    onClick={() => setDeleteConfirmId(null)}
                                    className="px-2 py-1 bg-gray-300 hover:bg-gray-400 dark:bg-slate-600 dark:hover:bg-slate-500 text-gray-700 dark:text-gray-200 text-xs font-medium rounded transition-colors"
                                  >
                                    Cancel
                                  </button>
                                </div>
                              ) : !video.is_proctored ? (
                                <button
                                  onClick={() => setDeleteConfirmId(video.video_id)}
                                  className="p-1.5 text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                                  title="Delete video"
                                >
                                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                  </svg>
                                </button>
                              ) : null}
                            </div>
                          </div>
                        </div>

                        {/* Processing Status */}
                        {isProcessing && (
                          <div className="px-4 py-3 border-t border-gray-200 dark:border-slate-600 bg-yellow-50 dark:bg-yellow-900/10">
                            <div className="flex items-center gap-2 text-yellow-700 dark:text-yellow-300">
                              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              <p className="text-sm">
                                {video.status === 'uploading'
                                  ? 'Video is being uploaded...'
                                  : 'AI is analyzing the video. This may take a few minutes.'}
                              </p>
                            </div>
                          </div>
                        )}

                        {/* Failed Status */}
                        {isFailed && (
                          <div className="px-4 py-3 border-t border-gray-200 dark:border-slate-600 bg-red-50 dark:bg-red-900/10">
                            <p className="text-sm text-red-700 dark:text-red-300">
                              Video processing failed. Please try uploading again.
                            </p>
                          </div>
                        )}

                        {/* Quick Preview when ready */}
                        {isReady && hasAnalysis && (
                          <Link
                            href={`/recruiter/candidates/${candidateId}/video/${video.video_id}`}
                            className="block px-4 py-3 border-t border-gray-200 dark:border-slate-600 hover:bg-gray-50 dark:hover:bg-slate-700/50 transition-colors"
                          >
                            {video.summary && (
                              <p className="text-sm text-gray-600 dark:text-gray-300 line-clamp-2 mb-2">
                                {video.summary}
                              </p>
                            )}
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-3">
                                {video.highlights && video.highlights.length > 0 && (
                                  <span className="text-xs text-gray-500 dark:text-gray-400">
                                    {video.highlights.length} highlights
                                  </span>
                                )}
                                {video.communication_analysis && (
                                  <span className="text-xs text-gray-500 dark:text-gray-400">
                                    Communication scores available
                                  </span>
                                )}
                              </div>
                              <span className="text-xs text-primary-600 dark:text-primary-400 flex items-center gap-1">
                                View full analysis
                                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                </svg>
                              </span>
                            </div>
                          </Link>
                        )}
                      </div>
                    );
                  }
                })}
              </div>
            )}
          </div>
        </div>

        <div className="space-y-6">
          {/* Video Upload Section */}
          <RecruiterVideoUploader
            candidateId={candidateId}
            onUploadComplete={() => {
              // Refresh videos list
              api.getRecruiterVideos(candidateId).then(response => {
                setVideos(response.videos);
              });
            }}
          />
        </div>
      </div>

      {/* Interview Request Modal */}
      <InterviewRequestModal
        isOpen={showInterviewModal}
        onClose={() => setShowInterviewModal(false)}
        candidateId={candidateId}
        candidateName={passport.display_name}
      />
    </div>
  );
}
