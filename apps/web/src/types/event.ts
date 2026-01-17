export interface TrackEvent {
  event_type: string;
  user_id: string;
  session_id?: string;
  task_id?: string;
  timestamp: number;
  properties?: Record<string, any>;
}

export type EventType =
  | 'session_started'
  | 'session_ended'
  | 'editor_command'
  | 'code_changed'
  | 'run_attempted'
  | 'error_emitted'
  | 'fix_applied'
  | 'refactor_applied'
  | 'test_added'
  | 'paste_burst_detected'
  | 'task_submitted';

export interface EditorCommandEvent {
  command: string;
  source: 'shortcut' | 'menu';
}

export interface RunAttemptedEvent {
  result: 'pass' | 'fail';
  runtime_ms: number;
  tests_passed: number;
  tests_total: number;
}

export interface ErrorEmittedEvent {
  error_type: string;
  stack_depth?: number;
  is_repeat: boolean;
}

export interface PasteBurstEvent {
  chars_pasted: number;
  burst_ms: number;
}
