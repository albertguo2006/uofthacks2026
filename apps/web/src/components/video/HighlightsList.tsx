'use client';

interface Highlight {
  timestamp: string;
  description: string;
  query?: string;
  category?: string;
  confidence?: number;
}

interface HighlightsListProps {
  highlights: Highlight[];
  onHighlightClick?: (timestamp: string) => void;
}

const CATEGORY_COLORS: Record<string, string> = {
  approach: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  debugging: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
  tradeoffs: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
  questions: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
  testing: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
  optimization: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300',
};

const CATEGORY_LABELS: Record<string, string> = {
  approach: 'Problem Solving',
  debugging: 'Debugging',
  tradeoffs: 'Trade-offs',
  questions: 'Questions',
  testing: 'Testing',
  optimization: 'Optimization',
};

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
            <div className="flex items-center gap-2 mb-1">
              <span className="text-primary-600 font-mono text-sm">
                {highlight.timestamp}
              </span>
              {highlight.category && (
                <span className={`text-xs px-2 py-0.5 rounded-full ${CATEGORY_COLORS[highlight.category] || 'bg-gray-100 text-gray-700'}`}>
                  {CATEGORY_LABELS[highlight.category] || highlight.category}
                </span>
              )}
              {highlight.confidence !== undefined && (
                <span className="text-xs text-gray-400">
                  {(highlight.confidence * 100).toFixed(0)}% match
                </span>
              )}
            </div>
            <p className="text-sm text-gray-700 dark:text-gray-300">
              {highlight.description}
            </p>
            {highlight.query && !highlight.category && (
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
