'use client';

interface ArchetypeBadgeProps {
  archetype: string;
  showDescription?: boolean;
}

const archetypeConfig: Record<string, { label: string; color: string; description: string }> = {
  careful_tester: {
    label: 'Careful Tester',
    color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    description: 'Prioritizes test coverage and validation before shipping',
  },
  fast_iterator: {
    label: 'Fast Iterator',
    color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    description: 'Rapidly tests hypotheses with quick feedback loops',
  },
  refactor_first: {
    label: 'Refactor First',
    color: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
    description: 'Improves code structure before adding features',
  },
  debugger: {
    label: 'Debugger',
    color: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
    description: 'Excels at systematic problem diagnosis',
  },
};

export function ArchetypeBadge({ archetype, showDescription = false }: ArchetypeBadgeProps) {
  const config = archetypeConfig[archetype] || {
    label: archetype,
    color: 'bg-gray-100 text-gray-800',
    description: '',
  };

  return (
    <div>
      <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${config.color}`}>
        {config.label}
      </span>
      {showDescription && config.description && (
        <p className="text-sm text-gray-500 mt-1">{config.description}</p>
      )}
    </div>
  );
}
