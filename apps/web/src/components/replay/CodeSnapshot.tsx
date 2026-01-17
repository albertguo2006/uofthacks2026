'use client';

import React, { useState, useMemo } from 'react';

interface CodeSnapshotProps {
  code: string | null;
  diff: string | null;
  language?: string;
}

export function CodeSnapshot({ code, diff, language = 'python' }: CodeSnapshotProps) {
  const [showDiff, setShowDiff] = useState(false);

  // Parse diff to highlight additions and deletions
  const parsedDiff = useMemo(() => {
    if (!diff) return null;

    const lines = diff.split('\n');
    return lines.map((line, index) => {
      let type: 'added' | 'removed' | 'context' | 'header' = 'context';

      if (line.startsWith('+++') || line.startsWith('---') || line.startsWith('@@')) {
        type = 'header';
      } else if (line.startsWith('+')) {
        type = 'added';
      } else if (line.startsWith('-')) {
        type = 'removed';
      }

      return { line, type, index };
    });
  }, [diff]);

  // Get background color for diff lines
  const getDiffLineStyle = (type: string) => {
    switch (type) {
      case 'added':
        return 'bg-green-900/30 border-l-2 border-green-500';
      case 'removed':
        return 'bg-red-900/30 border-l-2 border-red-500';
      case 'header':
        return 'bg-blue-900/20 text-blue-400';
      default:
        return '';
    }
  };

  if (!code && !diff) {
    return (
      <div className="bg-gray-900 rounded-lg p-4 h-full flex items-center justify-center">
        <p className="text-gray-500 text-sm">No code snapshot available for this event</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 rounded-lg overflow-hidden h-full flex flex-col">
      {/* Header with toggle */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
        <span className="text-sm text-gray-400">
          {showDiff && diff ? 'Code Diff' : 'Code Snapshot'}
        </span>

        {diff && (
          <button
            className={`px-3 py-1 text-xs rounded-full transition-colors ${
              showDiff
                ? 'bg-blue-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
            onClick={() => setShowDiff(!showDiff)}
          >
            {showDiff ? 'View Code' : 'View Diff'}
          </button>
        )}
      </div>

      {/* Code/Diff content */}
      <div className="flex-1 overflow-auto">
        {showDiff && parsedDiff ? (
          <pre className="text-sm font-mono">
            {parsedDiff.map(({ line, type, index }) => (
              <div
                key={index}
                className={`px-4 py-0.5 ${getDiffLineStyle(type)}`}
              >
                <code className="text-gray-300">{line}</code>
              </div>
            ))}
          </pre>
        ) : code ? (
          <pre className="p-4 text-sm font-mono">
            {code.split('\n').map((line, index) => (
              <div key={index} className="flex">
                <span className="text-gray-600 select-none w-8 text-right pr-4">
                  {index + 1}
                </span>
                <code className="text-gray-300">{line}</code>
              </div>
            ))}
          </pre>
        ) : (
          <div className="p-4 text-gray-500 text-sm">
            No code content available
          </div>
        )}
      </div>

      {/* Language badge */}
      <div className="px-4 py-2 bg-gray-800 border-t border-gray-700">
        <span className="text-xs text-gray-500 bg-gray-700 px-2 py-1 rounded">
          {language}
        </span>
      </div>
    </div>
  );
}
