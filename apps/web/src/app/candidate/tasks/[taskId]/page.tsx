'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { CodeEditor } from '@/components/sandbox/CodeEditor';
import { OutputPanel } from '@/components/sandbox/OutputPanel';
import { TaskHeader } from '@/components/sandbox/TaskHeader';
import { useCodeExecution } from '@/hooks/useCodeExecution';
import { useTasks } from '@/hooks/useTasks';
import { track } from '@/lib/telemetry';

export default function SandboxPage() {
  const params = useParams();
  const taskId = params.taskId as string;

  const { getTask } = useTasks();
  const task = getTask(taskId);

  const [code, setCode] = useState('');
  const [sessionId] = useState(() => crypto.randomUUID());

  const { run, submit, result, isRunning, isSubmitting } = useCodeExecution({
    taskId,
    sessionId,
  });

  useEffect(() => {
    if (task?.starter_code) {
      setCode(task.starter_code);
    }
  }, [task]);

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

  const handleCodeChange = (newCode: string) => {
    setCode(newCode);
    // Debounced tracking handled in CodeEditor
  };

  const handleRun = async () => {
    await run(code);
  };

  const handleSubmit = async () => {
    await submit(code);
  };

  if (!task) {
    return <div>Loading task...</div>;
  }

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      <TaskHeader task={task} />

      <div className="flex-1 grid lg:grid-cols-2 gap-4 mt-4">
        <div className="flex flex-col">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium">Code Editor</span>
            <span className="text-xs text-gray-500">{task.language}</span>
          </div>
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

        <div className="flex flex-col">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium">Output</span>
            <div className="flex gap-2">
              <button
                onClick={handleRun}
                disabled={isRunning}
                className="px-4 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
              >
                {isRunning ? 'Running...' : 'Run'}
              </button>
              <button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="px-4 py-1 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50"
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
