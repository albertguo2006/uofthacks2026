export const APP_NAME = 'Simply Authentic';

export const POLLING_INTERVAL = 5000; // 5 seconds

export const ARCHETYPES = {
  careful_tester: {
    label: 'Careful Tester',
    description: 'Prioritizes test coverage and validation before shipping',
  },
  fast_iterator: {
    label: 'Fast Iterator',
    description: 'Rapidly tests hypotheses with quick feedback loops',
  },
  refactor_first: {
    label: 'Refactor First',
    description: 'Improves code structure before adding features',
  },
  debugger: {
    label: 'Debugger',
    description: 'Excels at systematic problem diagnosis',
  },
} as const;

export const DIFFICULTY_COLORS = {
  easy: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  hard: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
} as const;

export const LANGUAGES = {
  javascript: { label: 'JavaScript', extension: 'js' },
  typescript: { label: 'TypeScript', extension: 'ts' },
  python: { label: 'Python', extension: 'py' },
} as const;
