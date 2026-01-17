'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useAskInterview, SUGGESTED_QUESTIONS } from '@/hooks/useAskInterview';
import type { TimelineJump, VideoSegment } from '@/types/timeline';

interface AskTheInterviewProps {
  sessionId: string;
  hasVideo: boolean;
  onTimelineJump?: (index: number) => void;
  onVideoSeek?: (seconds: number) => void;
}

export function AskTheInterview({
  sessionId,
  hasVideo,
  onTimelineJump,
  onVideoSeek,
}: AskTheInterviewProps) {
  const { messages, loading, askQuestion, clearMessages } = useAskInterview(sessionId);
  const [input, setInput] = useState('');
  const [includeVideo, setIncludeVideo] = useState(hasVideo);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const question = input.trim();
    setInput('');
    await askQuestion(question, includeVideo);
  };

  const handleSuggestedQuestion = async (question: string) => {
    if (loading) return;
    await askQuestion(question, includeVideo);
  };

  // Format video timestamp
  const formatVideoTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-gray-900 rounded-lg flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-gray-800 border-b border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <svg
            className="w-5 h-5 text-purple-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
          <span className="font-medium">Ask the Interview</span>
        </div>
        {messages.length > 0 && (
          <button
            className="text-xs text-gray-400 hover:text-gray-300"
            onClick={clearMessages}
          >
            Clear
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="space-y-4">
            <p className="text-sm text-gray-400 text-center">
              Ask questions about this coding session to get AI-powered insights
              with clickable references.
            </p>

            {/* Suggested questions */}
            <div className="space-y-2">
              <p className="text-xs text-gray-500 uppercase tracking-wide">
                Suggested questions
              </p>
              <div className="flex flex-wrap gap-2">
                {SUGGESTED_QUESTIONS.map((question, index) => (
                  <button
                    key={index}
                    className="px-3 py-1.5 text-xs bg-gray-800 hover:bg-gray-700 rounded-full text-gray-300 transition-colors"
                    onClick={() => handleSuggestedQuestion(question)}
                    disabled={loading}
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-[85%] rounded-lg px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-800 text-gray-300'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>

                  {/* Timeline jumps */}
                  {message.timelineJumps && message.timelineJumps.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-700 space-y-2">
                      <p className="text-xs text-gray-400 uppercase tracking-wide">
                        Timeline References
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {message.timelineJumps.map((jump: TimelineJump, index: number) => (
                          <button
                            key={index}
                            className="flex items-center gap-1.5 px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded text-gray-300 transition-colors"
                            onClick={() => onTimelineJump?.(jump.index)}
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
                                d="M13 7l5 5m0 0l-5 5m5-5H6"
                              />
                            </svg>
                            {jump.description}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Video segments */}
                  {message.videoSegments && message.videoSegments.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-700 space-y-2">
                      <p className="text-xs text-gray-400 uppercase tracking-wide">
                        Video Segments
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {message.videoSegments.map((segment: VideoSegment, index: number) => (
                          <button
                            key={index}
                            className="flex items-center gap-1.5 px-2 py-1 text-xs bg-purple-900/50 hover:bg-purple-800/50 rounded text-purple-300 transition-colors"
                            onClick={() => onVideoSeek?.(segment.start_time)}
                          >
                            <svg
                              className="w-3 h-3"
                              fill="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path d="M8 5v14l11-7z" />
                            </svg>
                            {formatVideoTime(segment.start_time)} -{' '}
                            {formatVideoTime(segment.end_time)}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Confidence indicator */}
                  {message.confidence !== undefined && (
                    <div className="mt-2 flex items-center gap-2">
                      <div className="flex-1 bg-gray-700 rounded-full h-1">
                        <div
                          className="h-full bg-green-500 rounded-full"
                          style={{ width: `${message.confidence * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500">
                        {Math.round(message.confidence * 100)}% confidence
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </>
        )}

        {/* Loading indicator */}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-800 rounded-lg px-4 py-3">
              <div className="flex items-center gap-2">
                <div className="animate-pulse flex space-x-1">
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:0.2s]" />
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:0.4s]" />
                </div>
                <span className="text-sm text-gray-400">Analyzing session...</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="p-4 border-t border-gray-800">
        {/* Video search toggle */}
        {hasVideo && (
          <div className="flex items-center gap-2 mb-3">
            <label className="flex items-center gap-2 text-xs text-gray-400 cursor-pointer">
              <input
                type="checkbox"
                checked={includeVideo}
                onChange={(e) => setIncludeVideo(e.target.checked)}
                className="rounded border-gray-600 bg-gray-700 text-purple-500 focus:ring-purple-500"
              />
              Search video content
            </label>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about this session..."
            className="flex-1 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
              />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}
