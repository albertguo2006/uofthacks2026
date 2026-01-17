'use client';

import { useState, useCallback, useEffect } from 'react';
import { api } from '@/lib/api';
import { track } from '@/lib/telemetry';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatContext {
  code?: string;
  error?: string;
  test_results?: Record<string, unknown>;
}

interface UseTaskChatOptions {
  sessionId: string;
  taskId: string;
}

export function useTaskChat({ sessionId, taskId }: UseTaskChatOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isHistoryLoaded, setIsHistoryLoaded] = useState(false);

  // Load chat history on mount
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const response = await api.get<{
          session_id: string;
          task_id: string;
          messages: Array<{
            chat_id: string;
            role: 'user' | 'assistant';
            content: string;
            timestamp: string;
          }>;
        }>(`/chat/history/${sessionId}?task_id=${taskId}`);

        const loadedMessages: ChatMessage[] = response.messages.map((msg) => ({
          id: msg.chat_id + msg.role,
          role: msg.role,
          content: msg.content,
          timestamp: new Date(msg.timestamp),
        }));

        setMessages(loadedMessages);
        setIsHistoryLoaded(true);
      } catch (err) {
        // No history or error - that's fine
        setIsHistoryLoaded(true);
      }
    };

    if (sessionId && taskId) {
      loadHistory();
    }
  }, [sessionId, taskId]);

  const sendMessage = useCallback(
    async (message: string, context?: ChatContext) => {
      if (!message.trim() || isLoading) return null;

      setIsLoading(true);
      setError(null);

      // Add user message optimistically
      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: message,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);

      try {
        const response = await api.post<{
          response: string;
          chat_id: string;
          timestamp: string;
        }>('/chat/task-help', {
          session_id: sessionId,
          task_id: taskId,
          message,
          context: context || null,
        });

        // Add assistant message
        const assistantMessage: ChatMessage = {
          id: `assistant-${response.chat_id}`,
          role: 'assistant',
          content: response.response,
          timestamp: new Date(response.timestamp),
        };
        setMessages((prev) => [...prev, assistantMessage]);

        return response;
      } catch (err) {
        setError('Failed to send message. Please try again.');
        // Remove optimistic user message on error
        setMessages((prev) => prev.filter((m) => m.id !== userMessage.id));
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, taskId, isLoading]
  );

  const clearHistory = useCallback(async () => {
    try {
      await api.delete(`/chat/history/${sessionId}?task_id=${taskId}`);
      setMessages([]);
      
      track('chat_history_cleared', {
        session_id: sessionId,
        task_id: taskId,
      });
    } catch (err) {
      setError('Failed to clear chat history.');
    }
  }, [sessionId, taskId]);

  return {
    messages,
    isLoading,
    error,
    isHistoryLoaded,
    sendMessage,
    clearHistory,
  };
}
