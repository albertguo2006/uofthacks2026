'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { SkillPassport } from '@/components/passport/SkillPassport';
import { HighlightsList } from '@/components/video/HighlightsList';
import { usePassport } from '@/hooks/usePassport';
import { api } from '@/lib/api';
import type { SessionSummary } from '@/types/timeline';

type SearchResult = {
  start_time: number;
  end_time: number;
  confidence: number;
  transcript_snippet: string;
};

export default function CandidateDetailPage() {
  const params = useParams();
  const candidateId = params.id as string;
  const { passport, isLoading, error } = usePassport(candidateId);

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Sessions for replay
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(true);

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

  const handleSearch = async () => {
    if (!searchQuery.trim() || !passport?.interview?.video_id) return;

    setIsSearching(true);
    setSearchError(null);
    try {
      const response = await api.searchVideo(passport.interview.video_id, searchQuery);
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
        <button className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
          Invite to Interview
        </button>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <SkillPassport passport={passport} showAnalytics />

          {/* Coding Sessions with Replay */}
          <div className="bg-white dark:bg-slate-800 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">Coding Sessions</h3>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {sessions.length} session{sessions.length !== 1 ? 's' : ''}
              </span>
            </div>

            {loadingSessions ? (
              <div className="flex justify-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
              </div>
            ) : sessions.length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400 text-sm">
                No coding sessions recorded yet
              </p>
            ) : (
              <div className="space-y-3">
                {sessions.map((session) => (
                  <div
                    key={session.session_id}
                    className="flex items-center justify-between p-4 bg-gray-50 dark:bg-slate-700 rounded-lg"
                  >
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-sm truncate">
                        {session.task_title}
                      </h4>
                      <div className="flex items-center gap-3 mt-1 text-xs text-gray-500 dark:text-gray-400">
                        <span>{session.event_count} events</span>
                        <span>{session.code_snapshots} snapshots</span>
                        {session.has_video && (
                          <span className="flex items-center gap-1 text-purple-500">
                            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M8 5v14l11-7z" />
                            </svg>
                            Video
                          </span>
                        )}
                        <span>
                          {new Date(session.started_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    <Link
                      href={`/recruiter/candidates/${candidateId}/replay/${session.session_id}`}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
                    >
                      <svg
                        className="w-4 h-4"
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
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white dark:bg-slate-800 rounded-lg p-6">
            <h3 className="font-semibold mb-4">Interview Highlights</h3>
            {passport.interview?.has_video ? (
              <HighlightsList highlights={passport.interview.highlights || []} />
            ) : (
              <p className="text-gray-600 dark:text-gray-300">
                No interview video uploaded
              </p>
            )}
          </div>

          {passport.interview?.has_video && passport.interview.video_id && (
            <div className="bg-white dark:bg-slate-800 rounded-lg p-6">
              <h3 className="font-semibold mb-4">Search Video</h3>
              <input
                type="text"
                placeholder="e.g., 'testing strategy'"
                className="w-full px-4 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={handleKeyDown}
              />
              <button
                onClick={handleSearch}
                disabled={isSearching || !searchQuery.trim()}
                className="mt-2 w-full px-4 py-2 bg-gray-100 dark:bg-slate-700 rounded-lg hover:bg-gray-200 dark:hover:bg-slate-600 disabled:opacity-50"
              >
                {isSearching ? 'Searching...' : 'Search'}
              </button>

              {searchError && (
                <p className="mt-2 text-sm text-red-600 dark:text-red-400">
                  {searchError}
                </p>
              )}

              {searchResults.length > 0 && (
                <div className="mt-4 space-y-3">
                  <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Results ({searchResults.length})
                  </h4>
                  {searchResults.map((result, index) => (
                    <div
                      key={index}
                      className="p-3 bg-gray-50 dark:bg-slate-700 rounded-lg"
                    >
                      <div className="flex justify-between items-start">
                        <span className="text-sm font-mono text-primary-600">
                          {formatTimestamp(result.start_time)} - {formatTimestamp(result.end_time)}
                        </span>
                        <span className="text-xs text-gray-500">
                          {(result.confidence * 100).toFixed(0)}% match
                        </span>
                      </div>
                      {result.transcript_snippet && (
                        <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
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
          )}
        </div>
      </div>
    </div>
  );
}
