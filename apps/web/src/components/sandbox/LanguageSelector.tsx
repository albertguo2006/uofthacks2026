'use client';

import { Language } from '@/types/task';

interface LanguageSelectorProps {
  languages: Language[];
  selected: Language;
  onChange: (language: Language) => void;
  disabled?: boolean;
}

const languageLabels: Record<Language, string> = {
  javascript: 'JavaScript',
  typescript: 'TypeScript',
  python: 'Python',
  cpp: 'C++',
  java: 'Java',
};

const languageIcons: Record<Language, string> = {
  javascript: 'JS',
  typescript: 'TS',
  python: 'PY',
  cpp: 'C++',
  java: 'JV',
};

export function LanguageSelector({
  languages,
  selected,
  onChange,
  disabled = false,
}: LanguageSelectorProps) {
  if (languages.length <= 1) {
    return (
      <span className="text-xs text-gray-500 dark:text-gray-400">
        {languageLabels[selected] || selected}
      </span>
    );
  }

  return (
    <div className="flex gap-1">
      {languages.map((lang) => (
        <button
          key={lang}
          onClick={() => onChange(lang)}
          disabled={disabled}
          className={`px-2 py-1 text-xs rounded transition-colors ${
            selected === lang
              ? 'bg-primary-600 text-white'
              : 'bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-600'
          } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
          title={languageLabels[lang]}
        >
          {languageIcons[lang]}
        </button>
      ))}
    </div>
  );
}
