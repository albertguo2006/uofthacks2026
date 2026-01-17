'use client';

interface SkillVectorProps {
  metrics: {
    iteration_velocity: number;
    debug_efficiency: number;
    craftsmanship: number;
    tool_fluency: number;
    integrity: number;
  };
}

export function SkillVector({ metrics }: SkillVectorProps) {
  const items = [
    { key: 'iteration_velocity', label: 'Iteration', value: metrics.iteration_velocity },
    { key: 'debug_efficiency', label: 'Debugging', value: metrics.debug_efficiency },
    { key: 'craftsmanship', label: 'Craftsmanship', value: metrics.craftsmanship },
    { key: 'tool_fluency', label: 'Tool Fluency', value: metrics.tool_fluency },
    { key: 'integrity', label: 'Integrity', value: metrics.integrity },
  ];

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.key}>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-600 dark:text-gray-300">{item.label}</span>
            <span className="font-medium">{(item.value * 100).toFixed(0)}%</span>
          </div>
          <div className="h-2 bg-gray-200 dark:bg-slate-600 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary-600 rounded-full transition-all duration-500"
              style={{ width: `${item.value * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
