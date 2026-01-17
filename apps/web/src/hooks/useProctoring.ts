'use client';

import { useEffect, useCallback, useRef, useState } from 'react';
import { api } from '@/lib/api';
import { track } from '@/lib/telemetry';
import { ViolationType, StartProctoringResponse, ProctoringStatus } from '@/types/proctoring';

interface UseProctoringOptions {
  taskId: string;
  sessionId: string | null;
  enabled: boolean;
  cameraEnabled?: boolean;
  onViolation?: (type: ViolationType, message: string) => void;
}

interface ProctoringState {
  isActive: boolean;
  sessionId: string | null;
  cameraEnabled: boolean;
  violationCount: number;
  status: ProctoringStatus | null;
}

const MOUSE_IDLE_TIMEOUT = 60000; // 60 seconds

export function useProctoring({
  taskId,
  sessionId,
  enabled,
  cameraEnabled = false,
  onViolation,
}: UseProctoringOptions) {
  const [state, setState] = useState<ProctoringState>({
    isActive: false,
    sessionId: null,
    cameraEnabled: false,
    violationCount: 0,
    status: null,
  });

  const mouseIdleTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastMouseMoveRef = useRef<number>(Date.now());
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Report violation to API and show notification
  const reportViolation = useCallback(
    async (violationType: ViolationType, details?: string) => {
      if (!state.sessionId || !enabled) return;

      const violationMessages: Record<ViolationType, string> = {
        tab_switch: 'Tab switch detected - this has been logged',
        window_blur: 'Window focus lost - this has been logged',
        mouse_idle: 'Extended inactivity detected - this has been logged',
        right_click: 'Right-click attempt detected - context menu disabled',
        copy_paste: 'Copy/paste detected - this has been logged',
        browser_devtools: 'Developer tools detected - this has been logged',
        multiple_monitors: 'Multiple monitors detected - this has been logged',
      };

      try {
        await api.post(`/proctoring/${state.sessionId}/violation`, {
          violation_type: violationType,
          details,
        });

        setState((prev) => ({
          ...prev,
          violationCount: prev.violationCount + 1,
        }));

        // Track violation in telemetry
        track('proctoring_violation', {
          task_id: taskId,
          session_id: state.sessionId,
          violation_type: violationType,
          details,
        });

        // Notify callback
        if (onViolation) {
          onViolation(violationType, violationMessages[violationType]);
        }
      } catch (error) {
        console.error('Failed to report violation:', error);
      }
    },
    [state.sessionId, enabled, taskId, onViolation]
  );

  // Start proctoring session
  const startSession = useCallback(
    async (enableCamera: boolean = false): Promise<StartProctoringResponse | null> => {
      try {
        const response = await api.post<StartProctoringResponse>('/proctoring/start', {
          task_id: taskId,
          camera_enabled: enableCamera,
        });

        setState({
          isActive: true,
          sessionId: response.session_id,
          cameraEnabled: enableCamera,
          violationCount: 0,
          status: response.status,
        });

        // Track session start
        track('proctoring_session_started', {
          task_id: taskId,
          session_id: response.session_id,
          camera_enabled: enableCamera,
        });

        return response;
      } catch (error) {
        console.error('Failed to start proctoring session:', error);
        return null;
      }
    },
    [taskId]
  );

  // End proctoring session
  const endSession = useCallback(async () => {
    if (!state.sessionId) return;

    try {
      await api.post(`/proctoring/${state.sessionId}/end`, {});

      // Track session end
      track('proctoring_session_ended', {
        task_id: taskId,
        session_id: state.sessionId,
        violation_count: state.violationCount,
      });

      // Stop camera if enabled
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }

      setState({
        isActive: false,
        sessionId: null,
        cameraEnabled: false,
        violationCount: 0,
        status: null,
      });
    } catch (error) {
      console.error('Failed to end proctoring session:', error);
    }
  }, [state.sessionId, state.violationCount, taskId]);

  // Tab visibility change handler
  useEffect(() => {
    if (!enabled || !state.isActive) return;

    const handleVisibilityChange = () => {
      if (document.hidden) {
        reportViolation('tab_switch', 'User switched to another tab');
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [enabled, state.isActive, reportViolation]);

  // Window blur handler
  useEffect(() => {
    if (!enabled || !state.isActive) return;

    const handleBlur = () => {
      reportViolation('window_blur', 'Window lost focus');
    };

    window.addEventListener('blur', handleBlur);
    return () => {
      window.removeEventListener('blur', handleBlur);
    };
  }, [enabled, state.isActive, reportViolation]);

  // Mouse idle detection
  useEffect(() => {
    if (!enabled || !state.isActive) return;

    const handleMouseMove = () => {
      lastMouseMoveRef.current = Date.now();

      // Clear and reset idle timer
      if (mouseIdleTimerRef.current) {
        clearTimeout(mouseIdleTimerRef.current);
      }

      mouseIdleTimerRef.current = setTimeout(() => {
        reportViolation('mouse_idle', `No mouse movement for ${MOUSE_IDLE_TIMEOUT / 1000} seconds`);
      }, MOUSE_IDLE_TIMEOUT);
    };

    // Start initial timer
    mouseIdleTimerRef.current = setTimeout(() => {
      reportViolation('mouse_idle', `No mouse movement for ${MOUSE_IDLE_TIMEOUT / 1000} seconds`);
    }, MOUSE_IDLE_TIMEOUT);

    document.addEventListener('mousemove', handleMouseMove);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      if (mouseIdleTimerRef.current) {
        clearTimeout(mouseIdleTimerRef.current);
      }
    };
  }, [enabled, state.isActive, reportViolation]);

  // Right-click prevention
  useEffect(() => {
    if (!enabled || !state.isActive) return;

    const handleContextMenu = (e: MouseEvent) => {
      e.preventDefault();
      reportViolation('right_click', 'Attempted to open context menu');
    };

    document.addEventListener('contextmenu', handleContextMenu);
    return () => {
      document.removeEventListener('contextmenu', handleContextMenu);
    };
  }, [enabled, state.isActive, reportViolation]);

  // Before unload warning
  useEffect(() => {
    if (!enabled || !state.isActive) return;

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = 'You are in a proctored session. Are you sure you want to leave?';
      return e.returnValue;
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [enabled, state.isActive]);

  // Camera setup (optional)
  useEffect(() => {
    if (!enabled || !state.isActive || !state.cameraEnabled) return;

    const setupCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false,
        });
        streamRef.current = stream;

        // Create hidden video element for potential recording
        if (!videoRef.current) {
          const video = document.createElement('video');
          video.style.display = 'none';
          video.srcObject = stream;
          video.play();
          videoRef.current = video;
        }
      } catch (error) {
        console.error('Failed to access camera:', error);
        setState((prev) => ({ ...prev, cameraEnabled: false }));
      }
    };

    setupCamera();

    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
    };
  }, [enabled, state.isActive, state.cameraEnabled]);

  // Initialize session if sessionId is provided
  useEffect(() => {
    if (sessionId && enabled && !state.sessionId) {
      setState((prev) => ({
        ...prev,
        sessionId,
        isActive: true,
        cameraEnabled,
      }));
    }
  }, [sessionId, enabled, cameraEnabled, state.sessionId]);

  return {
    isActive: state.isActive,
    sessionId: state.sessionId,
    cameraEnabled: state.cameraEnabled,
    violationCount: state.violationCount,
    status: state.status,
    startSession,
    endSession,
    reportViolation,
  };
}
