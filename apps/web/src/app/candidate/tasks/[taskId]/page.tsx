'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams } from 'next/navigation';
import { CodeEditor } from '@/components/sandbox/CodeEditor';
import { OutputPanel } from '@/components/sandbox/OutputPanel';
import { TaskHeader } from '@/components/sandbox/TaskHeader';
import { HintPanel } from '@/components/sandbox/HintPanel';
import { RadarChartMini } from '@/components/passport/RadarChart';
import { useCodeExecution } from '@/hooks/useCodeExecution';
import { useTasks } from '@/hooks/useTasks';
import { Task } from '@/types/task';
import { useSessionIntervention, useRadar } from '@/hooks/useRadar';
import { useSemanticObserver } from '@/hooks/useSemanticObserver';
import { track } from '@/lib/telemetry';
import { saveCodeDraft, loadCodeDraft, clearCodeDraft } from '@/lib/codeStorage';
import { api } from '@/lib/api';

export default function SandboxPage() {
  const params = useParams();
  const taskId = params.taskId as string;

  const { getTask, fetchTask } = useTasks();
  const [task, setTask] = useState<Task | undefined>(getTask(taskId));

  const [code, setCode] = useState('');
  const [codeLoaded, setCodeLoaded] = useState(false);
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch full task details and saved code on mount
  useEffect(() => {
    const loadTaskAndCode = async () => {
      const fullTask = await fetchTask(taskId);
      if (fullTask) {
        setTask(fullTask);

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
          setCode(fullTask.starter_code);
        }
        setCodeLoaded(true);
      }
    };

    loadTaskAndCode();
  }, [taskId, fetchTask]);

  const [sessionId] = useState(() => crypto.randomUUID());
  const [showRadar, setShowRadar] = useState(false);

  const { run, submit, result, isRunning, isSubmitting } = useCodeExecution({
    taskId,
    sessionId,
  });

  // AI intervention hook
  const { intervention, acknowledgeHint } = useSessionIntervention(sessionId);

  // Radar profile hook (polling every 10 seconds)
  const { radarProfile } = useRadar(undefined, { pollInterval: 10000 });

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
    language: task?.language,
  });

  // Cleanup save timeout on unmount
  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, []);

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
    await submit(code);
  };

  const handleAcknowledgeHint = useCallback(() => {
    if (intervention?.hint_category) {
      trackHintAcknowledged(intervention.hint_category);
    }
    acknowledgeHint();
  }, [intervention?.hint_category, trackHintAcknowledged, acknowledgeHint]);

  if (!task) {
    return (
      <div className="h-[calc(100vh-8rem)] flex items-center justify-center">
        <div className="animate-pulse text-gray-500">Loading task...</div>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-8rem)] flex flex-col pb-8">
      <TaskHeader task={task} />

      {/* AI Hint Panel */}
      {intervention?.hint && (
        <div className="mt-2">
          <HintPanel
            intervention={intervention}
            onAcknowledge={handleAcknowledgeHint}
            onDismiss={handleAcknowledgeHint}
          />
        </div>
      )}

      <div className="flex-1 grid lg:grid-cols-2 gap-6 mt-6 min-h-[600px]">
        <div className="flex flex-col min-h-[500px]">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium">Code Editor</span>
            <div className="flex items-center gap-3">
              <span className="text-xs text-gray-500">{task.language}</span>

              {/* Mini Radar Chart Toggle */}
              <button
                onClick={() => setShowRadar(!showRadar)}
                className="text-xs text-gray-400 hover:text-gray-200 transition-colors"
                title="Toggle skill radar"
              >
                {showRadar ? 'Hide Radar' : 'Show Radar'}
              </button>
            </div>
          </div>

          {/* Radar Chart (collapsible) */}
          {showRadar && radarProfile && (
            <div className="mb-2 p-2 bg-gray-900/50 rounded-lg flex items-center gap-4">
              <RadarChartMini profile={radarProfile} size={60} />
              <div className="text-xs text-gray-400">
                <div className="font-medium text-gray-300 mb-1">Engineering DNA</div>
                <div>Your coding patterns are being analyzed</div>
              </div>
            </div>
          )}

          <div className="flex-1 border rounded-lg overflow-hidden">
            <CodeEditor
              value={code}
              onChange={handleCodeChange}
              language={task.language}
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
