'use client';

import Link from 'next/link';
import { useTasks } from '@/hooks/useTasks';

export default function TasksPage() {
  const { tasks, isLoading } = useTasks();

  const difficultyColors = {
    easy: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    hard: 'bg-red-100 text-red-800',
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Tasks</h1>
        <p className="text-gray-600 dark:text-gray-300 mt-2">
          Complete tasks to build your Skill Identity and unlock jobs
        </p>
      </div>

      {isLoading ? (
        <div className="grid gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse bg-gray-200 dark:bg-slate-700 h-32 rounded-lg" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4">
          {tasks?.map((task) => (
            <Link
              key={task.task_id}
              href={`/candidate/tasks/${task.task_id}`}
              className="block p-6 bg-white dark:bg-slate-800 rounded-lg shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-semibold">{task.title}</h3>
                  <p className="text-gray-600 dark:text-gray-300 mt-1">
                    {task.description.substring(0, 100)}...
                  </p>
                  <div className="flex gap-2 mt-3">
                    <span className={`px-2 py-1 text-xs rounded ${difficultyColors[task.difficulty]}`}>
                      {task.difficulty}
                    </span>
                    <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded">
                      {task.category}
                    </span>
                    <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                      {task.language}
                    </span>
                  </div>
                </div>
                <span className="text-primary-600">Start →</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
