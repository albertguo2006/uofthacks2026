'use client';

import { Task } from '@/types/task';
import ReactMarkdown from 'react-markdown';

interface TaskHeaderProps {
  task: Task;
}

export function TaskHeader({ task }: TaskHeaderProps) {
  const difficultyColors = {
    easy: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    hard: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg p-4">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold">{task.title}</h1>
          <div className="flex gap-2 mt-2">
            <span className={`px-2 py-1 text-xs rounded ${difficultyColors[task.difficulty]}`}>
              {task.difficulty}
            </span>
            <span className="px-2 py-1 text-xs bg-gray-100 dark:bg-slate-700 rounded">
              {task.category}
            </span>
            <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded">
              {task.language}
            </span>
          </div>
        </div>
        <div className="text-sm text-gray-500">
          Time limit: {task.time_limit_seconds}s per test
        </div>
      </div>

      <div className="mt-4 text-sm text-gray-600 dark:text-gray-300">
        <details open>
          <summary className="cursor-pointer font-medium">Problem Description</summary>
          <div className="mt-2 prose dark:prose-invert prose-sm max-w-none">
            <ReactMarkdown>{task.description}</ReactMarkdown>
          </div>
        </details>
      </div>
    </div>
  );
}
