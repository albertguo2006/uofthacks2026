import { api } from './api';

interface TrackEventData {
  session_id?: string;
  task_id?: string;
  [key: string]: any;
}

let userId: string | null = null;

export function setUserId(id: string | null) {
  userId = id;
}

export async function track(eventType: string, data: TrackEventData = {}): Promise<void> {
  if (!userId) {
    console.warn('Telemetry: No user ID set, skipping event');
    return;
  }

  try {
    await api.post('/track', {
      event_type: eventType,
      user_id: userId,
      timestamp: Date.now(),
      ...data,
    });
  } catch (error) {
    // Silently fail - don't break the app for telemetry errors
    console.error('Telemetry error:', error);
  }
}

// Convenience methods for common events
export const telemetry = {
  sessionStarted: (sessionId: string, taskId: string, difficulty: string) =>
    track('session_started', { session_id: sessionId, task_id: taskId, difficulty }),

  sessionEnded: (sessionId: string, taskId: string, durationMs: number) =>
    track('session_ended', { session_id: sessionId, task_id: taskId, duration_ms: durationMs }),

  editorCommand: (sessionId: string, taskId: string, command: string, source: 'shortcut' | 'menu') =>
    track('editor_command', { session_id: sessionId, task_id: taskId, command, source }),

  codeChanged: (sessionId: string, taskId: string, linesChanged: number, charsAdded: number) =>
    track('code_changed', { session_id: sessionId, task_id: taskId, lines_changed: linesChanged, chars_added: charsAdded }),

  runAttempted: (sessionId: string, taskId: string, result: 'pass' | 'fail', runtimeMs: number) =>
    track('run_attempted', { session_id: sessionId, task_id: taskId, result, runtime_ms: runtimeMs }),

  errorEmitted: (sessionId: string, taskId: string, errorType: string, isRepeat: boolean) =>
    track('error_emitted', { session_id: sessionId, task_id: taskId, error_type: errorType, is_repeat: isRepeat }),

  fixApplied: (sessionId: string, taskId: string, fromErrorType: string, timeSinceErrorMs: number) =>
    track('fix_applied', { session_id: sessionId, task_id: taskId, from_error_type: fromErrorType, time_since_error_ms: timeSinceErrorMs }),

  taskSubmitted: (sessionId: string, taskId: string, passed: boolean, score: number) =>
    track('task_submitted', { session_id: sessionId, task_id: taskId, passed, score }),

  pasteBurstDetected: (sessionId: string, taskId: string, charsPasted: number, burstMs: number) =>
    track('paste_burst_detected', { session_id: sessionId, task_id: taskId, chars_pasted: charsPasted, burst_ms: burstMs }),

  // New semantic events for AI analysis
  semanticBlockAdded: (sessionId: string, taskId: string, blockType: string, count: number = 1) =>
    track('semantic_block_added', { session_id: sessionId, task_id: taskId, type: blockType, count }),

  libraryImport: (sessionId: string, taskId: string, count: number = 1) =>
    track('library_import', { session_id: sessionId, task_id: taskId, count }),

  testCaseAuthored: (sessionId: string, taskId: string, count: number = 1) =>
    track('test_case_authored', { session_id: sessionId, task_id: taskId, count }),

  solutionDraftStarted: (sessionId: string, taskId: string, timeSinceStartMs: number) =>
    track('solution_draft_started', { session_id: sessionId, task_id: taskId, time_since_start_ms: timeSinceStartMs }),

  refactorInitiated: (sessionId: string, taskId: string, timeSincePassMs: number) =>
    track('refactor_initiated', { session_id: sessionId, task_id: taskId, time_since_pass_ms: timeSincePassMs }),

  executionErrorStreak: (sessionId: string, taskId: string, errorType: string, streakCount: number) =>
    track('execution_error_streak', { session_id: sessionId, task_id: taskId, error_type: errorType, streak_count: streakCount }),

  docsLookup: (sessionId: string, taskId: string) =>
    track('docs_lookup', { session_id: sessionId, task_id: taskId }),

  hintDisplayed: (sessionId: string, taskId: string, hintCategory: string) =>
    track('hint_displayed', { session_id: sessionId, task_id: taskId, hint_category: hintCategory }),

  hintAcknowledged: (sessionId: string, taskId: string, hintCategory: string, helpfulRating?: number) =>
    track('hint_acknowledged', { session_id: sessionId, task_id: taskId, hint_category: hintCategory, helpful_rating: helpfulRating }),

  // Proctoring events
  proctoringSessionStarted: (taskId: string, sessionId: string, cameraEnabled: boolean) =>
    track('proctoring_session_started', { task_id: taskId, session_id: sessionId, camera_enabled: cameraEnabled }),

  proctoringSessionEnded: (taskId: string, sessionId: string, violationCount: number) =>
    track('proctoring_session_ended', { task_id: taskId, session_id: sessionId, violation_count: violationCount }),

  proctoringViolation: (taskId: string, sessionId: string, violationType: string, details?: string) =>
    track('proctoring_violation', { task_id: taskId, session_id: sessionId, violation_type: violationType, details }),

  // Tab visibility tracking
  tabSwitch: (sessionId: string, taskId: string, wasHidden: boolean, durationAwayMs?: number) =>
    track('tab_switch', { session_id: sessionId, task_id: taskId, was_hidden: wasHidden, duration_away_ms: durationAwayMs }),

  // Demo/debug events for triggering AI features
  frustrationSignal: (sessionId: string, taskId: string, intensity: 'low' | 'medium' | 'high') =>
    track('frustration_signal', { session_id: sessionId, task_id: taskId, intensity, demo_mode: true }),
};
