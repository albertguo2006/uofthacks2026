'use client';

export default function SecurityPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Security & Privacy</h1>
        <p className="text-gray-600 dark:text-gray-300 mt-2">
          Transparency about how we collect, process, and protect data
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-slate-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span className="text-green-600">✓</span>
            What We Collect
          </h2>
          <ul className="space-y-3 text-gray-600 dark:text-gray-300">
            <li className="flex items-start gap-2">
              <span className="text-green-600 mt-1">•</span>
              <span><strong>Behavioral signals</strong>: Command types (format, refactor), timing patterns, iteration speed</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-600 mt-1">•</span>
              <span><strong>Outcomes</strong>: Test pass/fail, error types, fix patterns</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-600 mt-1">•</span>
              <span><strong>Video summaries</strong>: AI-generated highlights from interviews (opt-in)</span>
            </li>
          </ul>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span className="text-red-600">✗</span>
            What We Don&apos;t Collect
          </h2>
          <ul className="space-y-3 text-gray-600 dark:text-gray-300">
            <li className="flex items-start gap-2">
              <span className="text-red-600 mt-1">•</span>
              <span><strong>Raw keystrokes</strong>: We track signal types, not individual characters</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-red-600 mt-1">•</span>
              <span><strong>Screen recordings</strong>: Code is processed server-side, not recorded</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-red-600 mt-1">•</span>
              <span><strong>Personal browsing</strong>: Only in-sandbox activity is tracked</span>
            </li>
          </ul>
        </div>

        <div className="md:col-span-2 bg-white dark:bg-slate-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Data Retention & Deletion</h2>
          <div className="grid md:grid-cols-3 gap-4 text-gray-600 dark:text-gray-300">
            <div>
              <h3 className="font-medium">Behavioral Events</h3>
              <p className="text-sm">Retained for 90 days, then aggregated</p>
            </div>
            <div>
              <h3 className="font-medium">Video Content</h3>
              <p className="text-sm">Retained until candidate requests deletion</p>
            </div>
            <div>
              <h3 className="font-medium">Skill Passports</h3>
              <p className="text-sm">Retained while account is active</p>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t">
            <button className="text-red-600 hover:underline">
              Request Data Deletion
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
