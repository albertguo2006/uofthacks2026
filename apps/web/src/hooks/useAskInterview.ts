'use client';

import { useState, useCallback } from 'react';
import { api } from '@/lib/api';
import type { AskRequest, AskResponse } from '@/types/timeline';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timelineJumps?: AskResponse['timeline_jumps'];
  videoSegments?: AskResponse['video_segments'];
  confidence?: number;
  timestamp: Date;
}

interface UseAskInterviewResult {
  messages: ChatMessage[];
  loading: boolean;
  error: string | null;
  askQuestion: (question: string, includeVideoSearch?: boolean) => Promise<void>;
  clearMessages: () => void;
}

const SUGGESTED_QUESTIONS = [
  "When did they change their approach?",
  "Did they write tests before implementing?",
  "How did they handle errors?",
  "What was their debugging strategy?",
  "Did they optimize their solution?",
];

export function useAskInterview(sessionId: string): UseAskInterviewResult {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const askQuestion = useCallback(async (question: string, includeVideoSearch = true) => {
    if (!sessionId || !question.trim()) return;

    // Add user message
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: question,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    setError(null);

    try {
      const request: AskRequest = {
        question,
        include_video_search: includeVideoSearch,
      };

      const response = await api.askAboutSession(sessionId, request);

      // Add assistant message
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        timelineJumps: response.timeline_jumps,
        videoSegments: response.video_segments,
        confidence: response.confidence,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get response';
      setError(errorMessage);

      // Add error message
      const errorMessageObj: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `Sorry, I couldn't process your question: ${errorMessage}`,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessageObj]);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    loading,
    error,
    askQuestion,
    clearMessages,
  };
}

export { SUGGESTED_QUESTIONS };
