'use client';

export interface SkillProficiency {
  name: string;
  score: number; // 0-1
}

interface SkillBarsProps {
  skills: SkillProficiency[];
  className?: string;
}

// Default skills for when no data is provided
const DEFAULT_SKILLS: SkillProficiency[] = [
  { name: 'Dynamic Programming', score: 0.75 },
  { name: 'Arrays & Strings', score: 0.90 },
  { name: 'Pointers & References', score: 0.65 },
  { name: 'Trees & Graphs', score: 0.80 },
  { name: 'Recursion', score: 0.85 },
  { name: 'Hash Tables', score: 0.70 },
];

export function SkillBars({ skills, className = '' }: SkillBarsProps) {
  const activeSkills = skills.length > 0 ? skills : DEFAULT_SKILLS;

  return (
    <div className={`space-y-3 ${className}`}>
      {activeSkills.map((skill) => (
        <div key={skill.name} className="space-y-1">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {skill.name}
            </span>
            <span className="text-sm font-bold text-primary-600 dark:text-primary-400">
              {Math.round(skill.score * 100)}%
            </span>
          </div>
          <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500"
              style={{ width: `${skill.score * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Compact version showing fewer skills
 */
export function SkillBarsCompact({
  skills,
  maxItems = 3,
  className = '',
}: {
  skills: SkillProficiency[];
  maxItems?: number;
  className?: string;
}) {
  const activeSkills = skills.length > 0 ? skills : DEFAULT_SKILLS;
  const displaySkills = activeSkills.slice(0, maxItems);

  return (
    <div className={`space-y-2 ${className}`}>
      {displaySkills.map((skill) => (
        <div key={skill.name} className="flex items-center gap-2">
          <span className="text-xs text-gray-500 w-24 truncate">{skill.name}</span>
          <div className="flex-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-blue-500 to-purple-500"
              style={{ width: `${skill.score * 100}%` }}
            />
          </div>
          <span className="text-xs font-medium text-gray-600 dark:text-gray-400 w-8">
            {Math.round(skill.score * 100)}%
          </span>
        </div>
      ))}
    </div>
  );
}
