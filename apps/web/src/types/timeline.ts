/**
 * Timeline types for session replay feature.
 *
 * These types mirror the backend models for timeline data,
 * enabling type-safe handling of replay functionality.
 */

export interface TimelineEntry {
  id: string;
  timestamp: string; // ISO date string
  type: string; // "code_snapshot", "run_attempted", "error_emitted", "ai_intervention", etc.
  code_snapshot: string | null;
  code_diff: string | null;
  event_data: Record<string, unknown> | null;
  video_timestamp_seconds: number | null;
  intervention: {
    hint: string;
    type: string;
    personalization_badge?: string;
  } | null;
  label: string;
  severity: "info" | "warning" | "error" | "success" | null;
}

export interface Timeline {
  session_id: string;
  user_id: string;
  task_id: string;
  task_title: string;
  start_time: string; // ISO date string
  end_time: string | null;
  duration_seconds: number;
  entries: TimelineEntry[];
  has_video: boolean;
  video_id: string | null;
  video_url: string | null;
  video_start_offset_seconds: number;
  total_runs: number;
  total_submissions: number;
  errors_encountered: number;
  interventions_received: number;
  final_result: "passed" | "failed" | null;
}

export interface TimelineJump {
  index: number;
  timestamp: string;
  description: string;
}

export interface VideoSegment {
  start_time: number;
  end_time: number;
  confidence: number;
  description?: string;
}

export interface AskRequest {
  question: string;
  include_video_search?: boolean;
}

export interface AskResponse {
  answer: string;
  timeline_jumps: TimelineJump[];
  video_segments: VideoSegment[];
  confidence: number;
}

export interface QuickInsight {
  category: "approach_change" | "debugging_efficiency" | "testing_habit" | "struggle_point";
  title: string;
  description: string;
  timeline_index: number | null;
  video_timestamp: number | null;
}

export interface QuickInsightsResponse {
  session_id: string;
  insights: QuickInsight[];
  summary: string;
}

export interface SessionSummary {
  session_id: string;
  task_id: string;
  task_title: string;
  started_at: string;
  ended_at: string | null;
  event_count: number;
  code_snapshots: number;
  has_video: boolean;
  video_id: string | null;
}

export interface UserSessionsResponse {
  sessions: SessionSummary[];
}

// Helper type for timeline event filtering
export type TimelineEventType =
  | "code_snapshot"
  | "code_changed"
  | "run_attempted"
  | "test_passed"
  | "test_failed"
  | "error_emitted"
  | "submission_attempted"
  | "submission_passed"
  | "submission_failed"
  | "hint_shown"
  | "contextual_hint_shown"
  | "ai_intervention"
  | "format_command"
  | "find_command"
  | "paste_burst"
  | "session_started"
  | "session_ended";

// Severity colors for styling
export const SEVERITY_COLORS: Record<string, string> = {
  info: "#6B7280",      // gray-500
  warning: "#F59E0B",   // amber-500
  error: "#EF4444",     // red-500
  success: "#10B981",   // green-500
};

// Event type icons (using emoji as simple icons)
export const EVENT_TYPE_ICONS: Record<string, string> = {
  code_changed: "code",
  run_attempted: "play",
  test_passed: "check",
  test_failed: "x",
  error_emitted: "alert-triangle",
  submission_passed: "check-circle",
  submission_failed: "x-circle",
  hint_shown: "lightbulb",
  contextual_hint_shown: "lightbulb",
  ai_intervention: "bot",
  format_command: "align-left",
  paste_burst: "clipboard",
  session_started: "play-circle",
  session_ended: "stop-circle",
};
