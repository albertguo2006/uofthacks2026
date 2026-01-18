'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams } from 'next/navigation';
import { CodeEditor } from '@/components/sandbox/CodeEditor';
import { OutputPanel } from '@/components/sandbox/OutputPanel';
import { TaskHeader } from '@/components/sandbox/TaskHeader';
import { HintPanel } from '@/components/sandbox/HintPanel';
import { FrustrationMeter } from '@/components/sandbox/FrustrationMeter';
import { TaskHelpChat } from '@/components/sandbox/TaskHelpChat';
import { LanguageSelector } from '@/components/sandbox/LanguageSelector';
import { ProctoringModal } from '@/components/proctoring/ProctoringModal';
import { ProctoringIndicator } from '@/components/proctoring/ProctoringIndicator';
import { VideoRecorder } from '@/components/proctoring/VideoRecorder';
import { useCodeExecution } from '@/hooks/useCodeExecution';
import { useTasks } from '@/hooks/useTasks';
import { useProctoring } from '@/hooks/useProctoring';
import { Task, Language } from '@/types/task';
import { ViolationType } from '@/types/proctoring';
import { useSessionIntervention, useFrustrationTracking } from '@/hooks/useRadar';
import { useSemanticObserver } from '@/hooks/useSemanticObserver';
import { track } from '@/lib/telemetry';
import { saveCodeDraft, loadCodeDraft, clearCodeDraft } from '@/lib/codeStorage';
import { api } from '@/lib/api';

export default function SandboxPage() {
  const params = useParams();
  const taskId = params.taskId as string;

  const { getTask, getTaskSummary, fetchTask, clearTaskCache } = useTasks();
  const [task, setTask] = useState<Task | undefined>(getTask(taskId));
  const taskSummary = getTaskSummary(taskId);

  const [code, setCode] = useState('');
  const [codeLoaded, setCodeLoaded] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState<Language>('javascript');
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Proctoring state
  const [showProctoringModal, setShowProctoringModal] = useState(false);
  const [proctoringSessionId, setProctoringSessionId] = useState<string | null>(null);
  const [violationToast, setViolationToast] = useState<string | null>(null);

  // Check if task is proctored (from summary or full task)
  const isProctored = taskSummary?.proctored || task?.proctored || false;

  // Proctoring hook
  const proctoring = useProctoring({
    taskId,
    sessionId: proctoringSessionId,
    enabled: isProctored && !!proctoringSessionId,
    onViolation: (type: ViolationType, message: string) => {
      setViolationToast(message);
      setTimeout(() => setViolationToast(null), 5000);
    },
  });

  // Handle proctoring modal acceptance
  const handleProctoringAccept = async (cameraEnabled: boolean) => {
    const session = await proctoring.startSession(cameraEnabled);
    if (session) {
      setProctoringSessionId(session.session_id);
      setShowProctoringModal(false);
      // Clear cache and refetch with proctoring session
      clearTaskCache(taskId);
    }
  };

  // Fetch full task details and saved code on mount
  useEffect(() => {
    const loadTaskAndCode = async () => {
      // For proctored tasks, show modal first if no session
      if (isProctored && !proctoringSessionId) {
        setShowProctoringModal(true);
        return;
      }

      const fullTask = await fetchTask(taskId, proctoringSessionId || undefined);
      if (fullTask) {
        setTask(fullTask);

        // Set initial language
        if (fullTask.languages && fullTask.languages.length > 0) {
          setSelectedLanguage(fullTask.languages[0] as Language);
        }

        // Priority: 1. Saved code from API, 2. localStorage draft, 3. starter code
        try {
          const savedResponse = await api.get<{ code: string | null }>(`/tasks/${taskId}/saved-code`);
          if (savedResponse.code) {
            setCode(savedResponse.code);
            setCodeLoaded(true);
            return;
          }
        } catch (e) {
          // No saved code or not logged in, continue to localStorage
        }

        const draft = loadCodeDraft(taskId);
        if (draft) {
          setCode(draft);
        } else {
          // Get starter code for selected language
          const lang = fullTask.languages?.[0] || 'javascript';
          const starterCode = fullTask.starter_codes?.[lang as Language] || '';
          setCode(starterCode);
        }
        setCodeLoaded(true);
      }
    };

    loadTaskAndCode();
  }, [taskId, fetchTask, isProctored, proctoringSessionId, clearTaskCache]);

  // Handle language change
  const handleLanguageChange = useCallback(
    (language: Language) => {
      setSelectedLanguage(language);
      // Update code to language-specific starter code if no custom code
      if (task?.starter_codes?.[language]) {
        const draft = loadCodeDraft(`${taskId}-${language}`);
        if (draft) {
          setCode(draft);
        } else {
          setCode(task.starter_codes[language]);
        }
      }
    },
    [task, taskId]
  );

  const [sessionId] = useState(() => crypto.randomUUID());

  const { run, submit, result, isRunning, isSubmitting } = useCodeExecution({
    taskId,
    sessionId,
  });

  // AI intervention hook with contextual hints
  const { intervention, acknowledgeHint, requestContextualHint } = useSessionIntervention(sessionId);
  const [hintContext, setHintContext] = useState<{ attempts?: number; repeated_errors?: boolean; code_history_length?: number } | undefined>();
  const [isRequestingHint, setIsRequestingHint] = useState(false);

  // Frustration tracking for hint unlocking
  const { frustrationStatus, boostFrustration } = useFrustrationTracking(sessionId);
  const hintUnlocked = frustrationStatus?.hint_unlocked ?? false;

  // Helper to extract stderr from result
  const currentStderr = result?.type === 'run' ? result.data.stderr : undefined;

  // Semantic observer for tracking code patterns
  const {
    analyzeCodeChange,
    trackRunAttempt,
    trackError,
    clearErrorStreak,
    trackHintDisplayed,
    trackHintAcknowledged,
  } = useSemanticObserver({
    sessionId,
    taskId,
    language: selectedLanguage,
  });

  // Store proctoring in ref to access in cleanup without causing re-renders
  const proctoringRef = useRef(proctoring);
  useEffect(() => {
    proctoringRef.current = proctoring;
  }, [proctoring]);

  // Cleanup on unmount - save code and end proctoring session
  useEffect(() => {
    return () => {
      // Clear save timeout
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }

      // End proctoring session if active when leaving page
      if (proctoringRef.current.isActive) {
        proctoringRef.current.endSession();
      }
    };
  }, []); // Empty dependency array - only run on unmount

  useEffect(() => {
    // Track session start
    track('session_started', {
      session_id: sessionId,
      task_id: taskId,
      difficulty: task?.difficulty,
    });

    return () => {
      // Track session end
      track('session_ended', {
        session_id: sessionId,
        task_id: taskId,
      });
    };
  }, [sessionId, taskId, task?.difficulty]);

  // Track when hint is displayed
  useEffect(() => {
    if (intervention?.hint) {
      trackHintDisplayed(intervention.hint_category || 'approach');
    }
  }, [intervention?.hint, intervention?.hint_category, trackHintDisplayed]);

  const handleCodeChange = useCallback((newCode: string) => {
    setCode(newCode);
    // Analyze code for semantic events
    analyzeCodeChange(newCode);

    // Debounced save to localStorage (500ms delay)
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }
    saveTimeoutRef.current = setTimeout(() => {
      saveCodeDraft(taskId, newCode);
    }, 500);
  }, [analyzeCodeChange, taskId]);

  const handleRun = async () => {
    const runResult = await run(code);

    // Track run attempt for semantic analysis
    if (runResult) {
      const testsPassed = runResult.results?.filter((r: any) => r.passed).length || 0;
      const testsTotal = runResult.results?.length || 0;
      trackRunAttempt(runResult.all_passed, testsPassed, testsTotal);

      if (runResult.all_passed) {
        clearErrorStreak();
      } else if (runResult.stderr) {
        // Extract error type from stderr
        const errorType = extractErrorType(runResult.stderr);
        trackError(errorType, runResult.stderr);
      }
    }
  };

  const handleSubmit = async () => {
    const result = await submit(code);

    // End proctoring session after successful submission
    if (result && proctoring.isActive) {
      await proctoring.endSession();
    }

    return result;
  };

  const handleAcknowledgeHint = useCallback(() => {
    if (intervention?.hint_category) {
      trackHintAcknowledged(intervention.hint_category);
    }
    acknowledgeHint();
    setHintContext(undefined);
  }, [intervention?.hint_category, trackHintAcknowledged, acknowledgeHint]);

  const handleRequestHint = useCallback(async () => {
    if (!taskId || isRequestingHint || !hintUnlocked) return;

    setIsRequestingHint(true);
    try {
      const response = await requestContextualHint(
        taskId,
        code,
        currentStderr || null,
      );
      if (response) {
        setHintContext(response.context);
        trackHintDisplayed('contextual');
      }
    } finally {
      setIsRequestingHint(false);
    }
  }, [taskId, code, currentStderr, requestContextualHint, trackHintDisplayed, isRequestingHint, hintUnlocked]);

  // Keyboard listener for "!" to boost frustration (demo mode)
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Check if "!" is pressed (Shift + 1)
      if (e.key === '!' && !e.ctrlKey && !e.metaKey && !e.altKey) {
        // Don't trigger if user is typing in an input field (except Monaco editor)
        const target = e.target as HTMLElement;
        if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
          return;
        }
        // Boost frustration
        boostFrustration();
      }
    };

    window.addEventListener('keypress', handleKeyPress);
    return () => {
      window.removeEventListener('keypress', handleKeyPress);
    };
  }, [boostFrustration]);

  // Show proctoring modal for proctored tasks
  if (isProctored && !proctoringSessionId) {
    return (
      <>
        <div className="h-[calc(100vh-8rem)] flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-xl font-semibold mb-2">Proctored Task</h2>
            <p className="text-gray-500 mb-4">
              Please accept the proctoring terms to view this task.
            </p>
            <button
              onClick={() => setShowProctoringModal(true)}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              View Proctoring Terms
            </button>
          </div>
        </div>
        <ProctoringModal
          isOpen={showProctoringModal}
          onClose={() => window.history.back()}
          onAccept={handleProctoringAccept}
          taskTitle={taskSummary?.title}
        />
      </>
    );
  }

  if (!task) {
    return (
      <div className="h-[calc(100vh-8rem)] flex items-center justify-center">
        <div className="animate-pulse text-gray-500">Loading task...</div>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-8rem)] flex flex-col pb-8">
      {/* Proctoring Indicator */}
      {proctoring.isActive && (
        <div className="mb-4">
          <ProctoringIndicator
            isActive={proctoring.isActive}
            cameraEnabled={proctoring.cameraEnabled}
            violationCount={proctoring.violationCount}
          />
        </div>
      )}

      {/* Violation Toast */}
      {violationToast && (
        <div className="fixed top-4 right-4 z-50 px-4 py-3 bg-red-100 dark:bg-red-900/50 border border-red-300 dark:border-red-700 text-red-800 dark:text-red-200 rounded-lg shadow-lg animate-pulse">
          {violationToast}
        </div>
      )}

      {/* Video Recorder for Proctored Sessions */}
      {proctoring.isActive && proctoring.cameraEnabled && proctoringSessionId && (
        <VideoRecorder
          sessionId={proctoringSessionId}
          taskId={taskId}
          isActive={proctoring.isActive}
        />
      )}

      <TaskHeader task={task} />

      {/* Frustration Meter & AI Hint Panel */}
      <div className="mt-2 space-y-2">
        {/* Frustration meter - always visible */}
        <div className="flex items-center justify-between">
          <FrustrationMeter status={frustrationStatus} onBoost={boostFrustration} />

          {/* Hint button - locked until frustration threshold reached */}
          {!intervention?.hint && (
            <button
              onClick={handleRequestHint}
              disabled={isRequestingHint || !hintUnlocked}
              className={`px-3 py-1.5 text-sm rounded-lg transition-all flex items-center gap-2 ${
                hintUnlocked
                  ? 'bg-yellow-600/20 text-yellow-400 border border-yellow-600/30 hover:bg-yellow-600/30'
                  : 'bg-gray-700/50 text-gray-500 border border-gray-600/30 cursor-not-allowed'
              } disabled:opacity-50`}
              title={
                hintUnlocked
                  ? 'Request an AI-powered hint based on your code history'
                  : 'Keep coding - hints unlock when you need them most!'
              }
            >
              {hintUnlocked ? (
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                  />
                </svg>
              ) : (
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                  />
                </svg>
              )}
              {isRequestingHint ? 'Getting Hint...' : hintUnlocked ? 'Need a Hint?' : 'Hint Locked'}
            </button>
          )}
        </div>

        {/* Hint panel - shown when there's an active hint */}
        {intervention?.hint && (
          <HintPanel
            intervention={intervention}
            onAcknowledge={handleAcknowledgeHint}
            onDismiss={handleAcknowledgeHint}
            context={hintContext}
          />
        )}
      </div>

      <div className="flex-1 grid lg:grid-cols-2 gap-6 mt-6 min-h-[600px]">
        <div className="flex flex-col min-h-[500px]">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium">Code Editor</span>
            <div className="flex items-center gap-3">
              {/* Language Selector */}
              {task.languages && task.languages.length > 0 && (
                <LanguageSelector
                  languages={task.languages}
                  selected={selectedLanguage}
                  onChange={handleLanguageChange}
                />
              )}
            </div>
          </div>

          <div className="flex-1 border rounded-lg overflow-hidden">
            <CodeEditor
              value={code}
              onChange={handleCodeChange}
              language={selectedLanguage}
              sessionId={sessionId}
              taskId={taskId}
            />
          </div>
        </div>

        <div className="flex flex-col min-h-[500px]">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium">Output</span>
            <div className="flex gap-2">
              <button
                onClick={handleRun}
                disabled={isRunning}
                className="px-4 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 transition-colors"
              >
                {isRunning ? 'Running...' : 'Run'}
              </button>
              <button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="px-4 py-1 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 transition-colors"
              >
                {isSubmitting ? 'Submitting...' : 'Submit'}
              </button>
            </div>
          </div>
          <div className="flex-1">
            <OutputPanel result={result} />
          </div>
        </div>
      </div>

      {/* Task Help Chat (Feature 3) */}
      <TaskHelpChat
        sessionId={sessionId}
        taskId={taskId}
        currentCode={code}
        currentError={currentStderr}
      />
    </div>
  );
}

/**
 * Extract error type from stderr for categorization
 */
function extractErrorType(stderr: string): string {
  // Python errors
  if (stderr.includes('SyntaxError')) return 'SyntaxError';
  if (stderr.includes('TypeError')) return 'TypeError';
  if (stderr.includes('NameError')) return 'NameError';
  if (stderr.includes('ValueError')) return 'ValueError';
  if (stderr.includes('IndexError')) return 'IndexError';
  if (stderr.includes('KeyError')) return 'KeyError';
  if (stderr.includes('AttributeError')) return 'AttributeError';
  if (stderr.includes('ZeroDivisionError')) return 'ZeroDivisionError';

  // JavaScript errors
  if (stderr.includes('ReferenceError')) return 'ReferenceError';
  if (stderr.includes('TypeError')) return 'TypeError';
  if (stderr.includes('SyntaxError')) return 'SyntaxError';

  return 'RuntimeError';
}
