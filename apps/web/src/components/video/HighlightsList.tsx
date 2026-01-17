'use client';

interface Highlight {
  timestamp: string;
  description: string;
  query?: string;
}

interface HighlightsListProps {
  highlights: Highlight[];
  onHighlightClick?: (timestamp: string) => void;
}

export function HighlightsList({ highlights, onHighlightClick }: HighlightsListProps) {
  if (highlights.length === 0) {
    return (
      <p className="text-gray-500 text-sm">No highlights found</p>
    );
  }

  return (
    <ul className="space-y-2">
      {highlights.map((highlight, i) => (
        <li key={i}>
          <button
            onClick={() => onHighlightClick?.(highlight.timestamp)}
            className="w-full text-left p-3 bg-gray-50 dark:bg-slate-700 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-600 transition-colors"
          >
            <div className="flex items-center gap-3">
              <span className="text-primary-600 font-mono text-sm">
                {highlight.timestamp}
              </span>
              <span className="text-sm">{highlight.description}</span>
            </div>
            {highlight.query && (
              <span className="text-xs text-gray-500 mt-1 block">
                Matched: &quot;{highlight.query}&quot;
              </span>
            )}
          </button>
        </li>
      ))}
    </ul>
  );
}
