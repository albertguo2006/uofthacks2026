'use client';

import { useRef, useCallback, useEffect } from 'react';
import Editor, { OnMount, OnChange } from '@monaco-editor/react';
import { track, telemetry } from '@/lib/telemetry';
import { debounce } from '@/lib/utils';

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  language: string;
  sessionId: string;
  taskId: string;
}

// Threshold for detecting paste bursts (characters)
const PASTE_BURST_THRESHOLD = 50;

export function CodeEditor({
  value,
  onChange,
  language,
  sessionId,
  taskId,
}: CodeEditorProps) {
  const editorRef = useRef<any>(null);
  const lastChangeTimeRef = useRef<number>(Date.now());
  const tabHiddenAtRef = useRef<number | null>(null);

  // Track tab visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        tabHiddenAtRef.current = Date.now();
      } else if (tabHiddenAtRef.current) {
        const durationAwayMs = Date.now() - tabHiddenAtRef.current;
        telemetry.tabSwitch(sessionId, taskId, true, durationAwayMs);
        tabHiddenAtRef.current = null;
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [sessionId, taskId]);

  const trackEditorCommand = useCallback(
    (command: string, source: 'shortcut' | 'menu') => {
      track('editor_command', {
        session_id: sessionId,
        task_id: taskId,
        command,
        source,
      });
    },
    [sessionId, taskId]
  );

  const trackCodeChange = useCallback(
    debounce((linesChanged: number, charsAdded: number, charsPasted: number) => {
      track('code_changed', {
        session_id: sessionId,
        task_id: taskId,
        lines_changed: linesChanged,
        chars_added: charsAdded,
        chars_pasted: charsPasted,
      });
    }, 1000),
    [sessionId, taskId]
  );

  const trackPasteBurst = useCallback(
    (charsPasted: number) => {
      const burstMs = Date.now() - lastChangeTimeRef.current;
      telemetry.pasteBurstDetected(sessionId, taskId, charsPasted, burstMs);
    },
    [sessionId, taskId]
  );

  const handleEditorMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;

    // Track formatting
    editor.addCommand(monaco.KeyMod.Shift | monaco.KeyMod.Alt | monaco.KeyCode.KeyF, () => {
      trackEditorCommand('format_document', 'shortcut');
      editor.getAction('editor.action.formatDocument')?.run();
    });

    // Track save attempts
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      trackEditorCommand('save_attempt', 'shortcut');
    });

    // Track find
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyF, () => {
      trackEditorCommand('find', 'shortcut');
      editor.getAction('actions.find')?.run();
    });

    // Track undo/redo
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyZ, () => {
      trackEditorCommand('undo', 'shortcut');
      editor.trigger('keyboard', 'undo', null);
    });
  };

  const handleChange: OnChange = (newValue) => {
    if (newValue !== undefined) {
      const oldLines = value.split('\n').length;
      const newLines = newValue.split('\n').length;
      const charDiff = newValue.length - value.length;
      const timeSinceLastChange = Date.now() - lastChangeTimeRef.current;

      // Detect paste burst: large addition in short time
      const isPasteBurst = charDiff > PASTE_BURST_THRESHOLD && timeSinceLastChange < 100;

      if (isPasteBurst) {
        trackPasteBurst(charDiff);
      }

      onChange(newValue);
      trackCodeChange(Math.abs(newLines - oldLines), charDiff, isPasteBurst ? charDiff : 0);
      lastChangeTimeRef.current = Date.now();
    }
  };

  const languageMap: Record<string, string> = {
    javascript: 'javascript',
    typescript: 'typescript',
    python: 'python',
    cpp: 'cpp',
    java: 'java',
  };

  return (
    <Editor
      height="100%"
      language={languageMap[language] || 'javascript'}
      value={value}
      onChange={handleChange}
      onMount={handleEditorMount}
      theme="vs-dark"
      options={{
        minimap: { enabled: false },
        fontSize: 14,
        lineNumbers: 'on',
        scrollBeyondLastLine: false,
        automaticLayout: true,
        tabSize: 2,
        wordWrap: 'on',
      }}
    />
  );
}
