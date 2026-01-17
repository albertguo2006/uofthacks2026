'use client';

import { useState, useCallback } from 'react';
import { api } from '@/lib/api';
import { RunResult } from '@/types/task';
import { track } from '@/lib/telemetry';

interface UseCodeExecutionOptions {
  taskId: string;
  sessionId: string;
}

interface SubmitResponse extends RunResult {
  passport_updated: boolean;
  new_archetype?: string;
  jobs_unlocked: number;
}

export function useCodeExecution({ taskId, sessionId }: UseCodeExecutionOptions) {
  const [result, setResult] = useState<RunResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const run = useCallback(
    async (code: string): Promise<RunResult> => {
      setIsRunning(true);

      try {
        const response = await api.post<RunResult>(`/tasks/${taskId}/run`, {
          session_id: sessionId,
          code,
        });

        setResult(response);

        // Track the run attempt
        track('run_attempted', {
          session_id: sessionId,
          task_id: taskId,
          result: response.all_passed ? 'pass' : 'fail',
          runtime_ms: response.total_time_ms,
          tests_passed: response.results.filter((r) => r.passed).length,
          tests_total: response.results.length,
        });

        // Track errors if any
        if (response.stderr) {
          track('error_emitted', {
            session_id: sessionId,
            task_id: taskId,
            error_type: 'runtime',
            is_repeat: false,
          });
        }

        return response;
      } finally {
        setIsRunning(false);
      }
    },
    [taskId, sessionId]
  );

  const submit = useCallback(
    async (code: string): Promise<SubmitResponse> => {
      setIsSubmitting(true);

      try {
        const response = await api.post<SubmitResponse>(`/tasks/${taskId}/submit`, {
          session_id: sessionId,
          code,
        });

        setResult(response);

        // Track submission
        track('task_submitted', {
          session_id: sessionId,
          task_id: taskId,
          passed: response.all_passed,
          score: response.all_passed ? 100 : 0,
        });

        return response;
      } finally {
        setIsSubmitting(false);
      }
    },
    [taskId, sessionId]
  );

  const reset = useCallback(() => {
    setResult(null);
  }, []);

  return {
    result,
    isRunning,
    isSubmitting,
    run,
    submit,
    reset,
  };
}
