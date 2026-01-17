'use client';

import { useCallback, useRef, useEffect } from 'react';
import { track } from '@/lib/telemetry';

interface SemanticObserverOptions {
  sessionId: string;
  taskId: string;
  language?: string;
}

/**
 * Hook for detecting semantic code events like function definitions, imports, etc.
 * Emits semantic events to the backend for AI analysis.
 */
export function useSemanticObserver({ sessionId, taskId, language = 'python' }: SemanticObserverOptions) {
  const lastCodeRef = useRef('');
  const sessionStartTimeRef = useRef(Date.now());
  const lastRunTimeRef = useRef<number | null>(null);
  const consecutiveErrorsRef = useRef<string[]>([]);

  // Language-specific patterns for detecting semantic blocks
  const patterns = useCallback(() => {
    switch (language) {
      case 'python':
        return {
          function: /(?:def\s+\w+|class\s+\w+|async\s+def\s+\w+)/g,
          import: /(?:import\s+\w+|from\s+\w+\s+import)/g,
          test: /(?:def\s+test_\w+|assert\s+)/g,
        };
      case 'javascript':
      case 'typescript':
        return {
          function: /(?:function\s+\w+|const\s+\w+\s*=\s*(?:\([^)]*\)|async)\s*=>|class\s+\w+)/g,
          import: /(?:import\s+.*\s+from|require\s*\()/g,
          test: /(?:test\s*\(|it\s*\(|describe\s*\(|expect\s*\()/g,
        };
      default:
        return {
          function: /(?:function\s+\w+|def\s+\w+|class\s+\w+)/g,
          import: /(?:import\s+|require\s*\()/g,
          test: /(?:test|assert)/gi,
        };
    }
  }, [language]);

  /**
   * Analyze code changes and emit semantic events
   */
  const analyzeCodeChange = useCallback((newCode: string) => {
    const oldCode = lastCodeRef.current;
    const languagePatterns = patterns();

    // Detect new function/class definitions
    const newFunctions = newCode.match(languagePatterns.function) || [];
    const oldFunctions = oldCode.match(languagePatterns.function) || [];

    if (newFunctions.length > oldFunctions.length) {
      track('semantic_block_added', {
        session_id: sessionId,
        task_id: taskId,
        type: 'function',
        count: newFunctions.length - oldFunctions.length,
      });
    }

    // Detect new imports
    const newImports = newCode.match(languagePatterns.import) || [];
    const oldImports = oldCode.match(languagePatterns.import) || [];

    if (newImports.length > oldImports.length) {
      track('library_import', {
        session_id: sessionId,
        task_id: taskId,
        count: newImports.length - oldImports.length,
      });
    }

    // Detect test-related code
    const newTests = newCode.match(languagePatterns.test) || [];
    const oldTests = oldCode.match(languagePatterns.test) || [];

    if (newTests.length > oldTests.length) {
      track('test_case_authored', {
        session_id: sessionId,
        task_id: taskId,
        count: newTests.length - oldTests.length,
      });
    }

    // Track first draft start (typing begins)
    if (oldCode.trim() === '' && newCode.trim() !== '') {
      const timeSinceStart = Date.now() - sessionStartTimeRef.current;
      track('solution_draft_started', {
        session_id: sessionId,
        task_id: taskId,
        time_since_start_ms: timeSinceStart,
      });
    }

    lastCodeRef.current = newCode;
  }, [sessionId, taskId, patterns]);

  /**
   * Track when a run is attempted and detect refactoring patterns
   */
  const trackRunAttempt = useCallback((passed: boolean, testsPassed: number, testsTotal: number) => {
    const now = Date.now();

    // Detect refactoring: editing after passing tests
    if (lastRunTimeRef.current && passed) {
      const timeSinceLastRun = now - lastRunTimeRef.current;
      if (timeSinceLastRun < 60000) { // Within 1 minute
        track('refactor_initiated', {
          session_id: sessionId,
          task_id: taskId,
          time_since_pass_ms: timeSinceLastRun,
        });
      }
    }

    lastRunTimeRef.current = now;
  }, [sessionId, taskId]);

  /**
   * Track errors and detect error streaks
   */
  const trackError = useCallback((errorType: string, errorMessage: string) => {
    consecutiveErrorsRef.current.push(errorType);

    // Keep only last 5 errors
    if (consecutiveErrorsRef.current.length > 5) {
      consecutiveErrorsRef.current.shift();
    }

    // Check for error streak (3+ of same type)
    const recent = consecutiveErrorsRef.current.slice(-3);
    if (recent.length >= 3 && recent.every(e => e === errorType)) {
      track('execution_error_streak', {
        session_id: sessionId,
        task_id: taskId,
        error_type: errorType,
        streak_count: recent.length,
        error_message: errorMessage.slice(0, 200),
      });
    }
  }, [sessionId, taskId]);

  /**
   * Clear error streak on successful run
   */
  const clearErrorStreak = useCallback(() => {
    consecutiveErrorsRef.current = [];
  }, []);

  /**
   * Track when focus is lost (potentially looking at docs)
   */
  const trackFocusLost = useCallback(() => {
    track('docs_lookup', {
      session_id: sessionId,
      task_id: taskId,
      timestamp: Date.now(),
    });
  }, [sessionId, taskId]);

  /**
   * Track hint interaction
   */
  const trackHintDisplayed = useCallback((hintCategory: string) => {
    track('hint_displayed', {
      session_id: sessionId,
      task_id: taskId,
      hint_category: hintCategory,
    });
  }, [sessionId, taskId]);

  const trackHintAcknowledged = useCallback((hintCategory: string, helpfulRating?: number) => {
    track('hint_acknowledged', {
      session_id: sessionId,
      task_id: taskId,
      hint_category: hintCategory,
      helpful_rating: helpfulRating,
    });
  }, [sessionId, taskId]);

  // Reset session start time when session changes
  useEffect(() => {
    sessionStartTimeRef.current = Date.now();
    lastCodeRef.current = '';
    lastRunTimeRef.current = null;
    consecutiveErrorsRef.current = [];
  }, [sessionId]);

  return {
    analyzeCodeChange,
    trackRunAttempt,
    trackError,
    clearErrorStreak,
    trackFocusLost,
    trackHintDisplayed,
    trackHintAcknowledged,
  };
}
