'use client';

import Link from 'next/link';
import { useTasks } from '@/hooks/useTasks';
import { ProctoredBadge } from '@/components/ui/ProctoredBadge';
import { TopicTag } from '@/components/ui/TopicTag';

export default function TasksPage() {
  const { tasks, isLoading } = useTasks();

  const difficultyColors = {
    easy: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    hard: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
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
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-semibold">{task.title}</h3>
                    {task.proctored && <ProctoredBadge />}
                  </div>
                  <p className="text-gray-600 dark:text-gray-300 mt-1">
                    {task.description.substring(0, 100)}
                    {task.description.length > 100 ? '...' : ''}
                  </p>

                  {/* Tags section */}
                  {task.tags && task.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {task.tags.map((tag) => (
                        <TopicTag key={tag} tag={tag} />
                      ))}
                    </div>
                  )}

                  <div className="flex flex-wrap gap-2 mt-3">
                    <span className={`px-2 py-1 text-xs rounded ${difficultyColors[task.difficulty]}`}>
                      {task.difficulty}
                    </span>
                    <span className="px-2 py-1 text-xs bg-gray-100 dark:bg-slate-700 text-gray-800 dark:text-gray-200 rounded">
                      {task.category}
                    </span>
                    {/* Languages */}
                    {task.languages && task.languages.length > 0 && (
                      <span className="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded">
                        {task.languages.length === 1
                          ? task.languages[0]
                          : `${task.languages.length} languages`}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 ml-4">
                  {task.passed && (
                    <span className="text-green-600 dark:text-green-400 text-lg" title="Completed">
                      ✓
                    </span>
                  )}
                  <span className="text-primary-600">Start →</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
