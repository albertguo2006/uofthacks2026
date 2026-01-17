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
};
