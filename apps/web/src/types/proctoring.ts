export type ViolationType =
  | 'tab_switch'
  | 'window_blur'
  | 'mouse_idle'
  | 'right_click'
  | 'copy_paste'
  | 'browser_devtools'
  | 'multiple_monitors';

export type ProctoringStatus = 'active' | 'paused' | 'ended' | 'terminated';

export interface ProctoringViolation {
  violation_type: ViolationType;
  timestamp: string;
  details?: string;
}

export interface ProctoringAgreement {
  task_id: string;
  camera_enabled: boolean;
  terms_accepted: boolean;
  accepted_at: string;
}

export interface ProctoringSession {
  session_id: string;
  user_id: string;
  task_id: string;
  status: ProctoringStatus;
  camera_enabled: boolean;
  violations: ProctoringViolation[];
  started_at: string;
  ended_at?: string;
}

export interface StartProctoringRequest {
  task_id: string;
  camera_enabled: boolean;
}

export interface StartProctoringResponse {
  session_id: string;
  task_id: string;
  status: ProctoringStatus;
  camera_enabled: boolean;
}

export interface ProctoringSessionResponse {
  session_id: string;
  user_id: string;
  task_id: string;
  status: ProctoringStatus;
  camera_enabled: boolean;
  violation_count: number;
  started_at: string;
  ended_at?: string;
}
