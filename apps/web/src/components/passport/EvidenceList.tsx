'use client';

interface NotableMoment {
  type: string;
  description: string;
  session_id?: string;
  timestamp: string;
}

interface EvidenceListProps {
  moments: NotableMoment[];
}

export function EvidenceList({ moments }: EvidenceListProps) {
  const typeIcons: Record<string, string> = {
    achievement: '🏆',
    improvement: '📈',
    consistency: '🎯',
    speed: '⚡',
  };

  return (
    <ul className="space-y-2">
      {moments.map((moment, i) => (
        <li
          key={i}
          className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-slate-700 rounded-lg"
        >
          <span className="text-xl">{typeIcons[moment.type] || '📌'}</span>
          <div className="flex-1">
            <p className="text-sm">{moment.description}</p>
            <p className="text-xs text-gray-500 mt-1">
              {new Date(moment.timestamp).toLocaleDateString()}
            </p>
          </div>
        </li>
      ))}
    </ul>
  );
}
