'use client';

interface TopicTagProps {
  tag: string;
  size?: 'sm' | 'md';
}

const tagColors: Record<string, string> = {
  // Data structures
  arrays: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  strings: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200',
  'linked-list': 'bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200',
  trees: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  graphs: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200',
  'hash-table': 'bg-lime-100 text-lime-800 dark:bg-lime-900 dark:text-lime-200',
  stack: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
  queue: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  heap: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',

  // Algorithms
  'dynamic-programming': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  dp: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  recursion: 'bg-violet-100 text-violet-800 dark:bg-violet-900 dark:text-violet-200',
  sorting: 'bg-fuchsia-100 text-fuchsia-800 dark:bg-fuchsia-900 dark:text-fuchsia-200',
  searching: 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200',
  'binary-search': 'bg-rose-100 text-rose-800 dark:bg-rose-900 dark:text-rose-200',
  greedy: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200',
  backtracking: 'bg-sky-100 text-sky-800 dark:bg-sky-900 dark:text-sky-200',

  // Concepts
  pointers: 'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-200',
  'two-pointers': 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
  'sliding-window': 'bg-zinc-100 text-zinc-800 dark:bg-zinc-700 dark:text-zinc-200',
  memoization: 'bg-stone-100 text-stone-800 dark:bg-stone-700 dark:text-stone-200',
  math: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  'bit-manipulation': 'bg-neutral-100 text-neutral-800 dark:bg-neutral-700 dark:text-neutral-200',
};

const defaultColor = 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';

export function TopicTag({ tag, size = 'sm' }: TopicTagProps) {
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
  };

  const colorClass = tagColors[tag.toLowerCase()] || defaultColor;

  return (
    <span className={`inline-block rounded ${colorClass} ${sizeClasses[size]}`}>
      {tag}
    </span>
  );
}
