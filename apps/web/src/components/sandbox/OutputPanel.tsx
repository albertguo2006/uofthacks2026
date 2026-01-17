'use client';

import { RunResult, SubmitResult } from '@/types/task';

type ExecutionResult =
  | { type: 'run'; data: RunResult }
  | { type: 'submit'; data: SubmitResult };

interface OutputPanelProps {
  result: ExecutionResult | null;
}

export function OutputPanel({ result }: OutputPanelProps) {
  if (!result) {
    return (
      <div className="h-full bg-gray-900 rounded-lg p-4 text-gray-400 font-mono text-sm">
        <p>Run your code to see output...</p>
      </div>
    );
  }

  // Handle submit result
  if (result.type === 'submit') {
    const submitData = result.data;
    return (
      <div className="h-full bg-gray-900 rounded-lg p-4 overflow-auto">
        <div className={`p-4 rounded ${submitData.passed ? 'bg-green-900/30' : 'bg-red-900/30'}`}>
          <p className={`text-xl font-bold ${submitData.passed ? 'text-green-400' : 'text-red-400'}`}>
            {submitData.passed ? 'Submission Passed!' : 'Submission Failed'}
          </p>
          <p className="text-2xl font-bold text-white mt-2">
            Score: {submitData.score}%
          </p>
          {submitData.passport_updated && (
            <p className="text-gray-400 text-sm mt-2">
              Your passport has been updated
            </p>
          )}
          {submitData.new_archetype && (
            <p className="text-primary-400 text-sm mt-1">
              New archetype: {submitData.new_archetype}
            </p>
          )}
          {submitData.jobs_unlocked > 0 && (
            <p className="text-blue-400 text-sm mt-1">
              {submitData.jobs_unlocked} new job{submitData.jobs_unlocked > 1 ? 's' : ''} unlocked!
            </p>
          )}
        </div>
      </div>
    );
  }

  // Handle run result
  const runData = result.data;
  return (
    <div className="h-full bg-gray-900 rounded-lg p-4 overflow-auto">
      {/* Test Results */}
      <div className="space-y-3 mb-4">
        <h4 className="text-gray-400 text-xs uppercase tracking-wide">Test Results</h4>
        {runData.results.map((test, i) => (
          <div
            key={i}
            className={`p-2 rounded ${
              test.passed ? 'bg-green-900/20' : 'bg-red-900/20'
            }`}
          >
            <div className={`flex items-center gap-2 text-sm font-mono ${
              test.passed ? 'text-green-400' : 'text-red-400'
            }`}>
              <span>{test.passed ? '✓' : '✗'}</span>
              <span>Test {test.test_case}</span>
              <span className="text-gray-500 ml-auto">{test.time_ms}ms</span>
            </div>
            {!test.passed && (
              <div className="mt-2 text-xs font-mono space-y-1">
                {test.error && (
                  <div className="text-red-400">
                    <span className="text-gray-500">Error: </span>
                    {test.error}
                  </div>
                )}
                <div className="text-gray-400">
                  <span className="text-gray-500">Expected: </span>
                  {test.hidden ? (
                    <span className="text-gray-500 italic">[hidden]</span>
                  ) : (
                    <span className="text-green-400">{JSON.stringify(test.expected)}</span>
                  )}
                </div>
                {test.output !== undefined && (
                  <div className="text-gray-400">
                    <span className="text-gray-500">Got: </span>
                    <span className="text-red-400">{JSON.stringify(test.output)}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className={`p-3 rounded ${runData.all_passed ? 'bg-green-900/30' : 'bg-red-900/30'}`}>
        <p className={`font-semibold ${runData.all_passed ? 'text-green-400' : 'text-red-400'}`}>
          {runData.all_passed ? 'All tests passed!' : 'Some tests failed'}
        </p>
        <p className="text-gray-400 text-sm">
          Total time: {runData.total_time_ms}ms
        </p>
      </div>

      {/* Stdout */}
      {runData.stdout && (
        <div className="mt-4">
          <h4 className="text-gray-400 text-xs uppercase tracking-wide mb-2">Output</h4>
          <pre className="text-gray-300 font-mono text-sm whitespace-pre-wrap">
            {runData.stdout}
          </pre>
        </div>
      )}

      {/* Stderr */}
      {runData.stderr && (
        <div className="mt-4">
          <h4 className="text-red-400 text-xs uppercase tracking-wide mb-2">Errors</h4>
          <pre className="text-red-300 font-mono text-sm whitespace-pre-wrap">
            {runData.stderr}
          </pre>
        </div>
      )}
    </div>
  );
}
