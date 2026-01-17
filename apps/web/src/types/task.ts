export type Language = 'javascript' | 'typescript' | 'python' | 'cpp' | 'java';

export interface Task {
  task_id: string;
  title: string;
  description: string;
  difficulty: 'easy' | 'medium' | 'hard';
  category: 'bugfix' | 'refactor' | 'feature' | 'optimization';
  languages: Language[];
  starter_codes: Record<Language, string>;
  test_cases: TestCase[];
  time_limit_seconds: number;
  proctored: boolean;
  tags: string[];
}

export interface TaskSummary {
  task_id: string;
  title: string;
  description: string;
  difficulty: 'easy' | 'medium' | 'hard';
  category: 'bugfix' | 'refactor' | 'feature' | 'optimization';
  languages: Language[];
  estimated_minutes: number;
  proctored: boolean;
  tags: string[];
}

export interface TestCase {
  input: any;
  expected_output: any;
  hidden?: boolean;
}

export interface TestResult {
  test_case: number;
  passed: boolean;
  output?: any;
  expected?: any;
  hidden?: boolean;
  time_ms: number;
  error?: string;
}

export interface RunResult {
  success: boolean;
  results: TestResult[];
  all_passed: boolean;
  total_time_ms: number;
  stdout: string;
  stderr: string;
}

export interface SubmitResult {
  submitted: boolean;
  passed: boolean;
  score: number;
  passport_updated: boolean;
  new_archetype?: string;
  jobs_unlocked: number;
}
