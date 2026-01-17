'use client';

import { RunResult } from '@/types/task';

interface OutputPanelProps {
  result: RunResult | null;
}

export function OutputPanel({ result }: OutputPanelProps) {
  if (!result) {
    return (
      <div className="h-full bg-gray-900 rounded-lg p-4 text-gray-400 font-mono text-sm">
        <p>Run your code to see output...</p>
      </div>
    );
  }

  return (
    <div className="h-full bg-gray-900 rounded-lg p-4 overflow-auto">
      {/* Test Results */}
      <div className="space-y-2 mb-4">
        <h4 className="text-gray-400 text-xs uppercase tracking-wide">Test Results</h4>
        {result.results.map((test, i) => (
          <div
            key={i}
            className={`flex items-center gap-2 text-sm font-mono ${
              test.passed ? 'text-green-400' : 'text-red-400'
            }`}
          >
            <span>{test.passed ? '✓' : '✗'}</span>
            <span>Test {test.test_case}</span>
            {!test.passed && test.output && (
              <span className="text-gray-500 ml-2">Got: {JSON.stringify(test.output)}</span>
            )}
            <span className="text-gray-500 ml-auto">{test.time_ms}ms</span>
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className={`p-3 rounded ${result.all_passed ? 'bg-green-900/30' : 'bg-red-900/30'}`}>
        <p className={`font-semibold ${result.all_passed ? 'text-green-400' : 'text-red-400'}`}>
          {result.all_passed ? 'All tests passed!' : 'Some tests failed'}
        </p>
        <p className="text-gray-400 text-sm">
          Total time: {result.total_time_ms}ms
        </p>
      </div>

      {/* Stdout */}
      {result.stdout && (
        <div className="mt-4">
          <h4 className="text-gray-400 text-xs uppercase tracking-wide mb-2">Output</h4>
          <pre className="text-gray-300 font-mono text-sm whitespace-pre-wrap">
            {result.stdout}
          </pre>
        </div>
      )}

      {/* Stderr */}
      {result.stderr && (
        <div className="mt-4">
          <h4 className="text-red-400 text-xs uppercase tracking-wide mb-2">Errors</h4>
          <pre className="text-red-300 font-mono text-sm whitespace-pre-wrap">
            {result.stderr}
          </pre>
        </div>
      )}
    </div>
  );
}
