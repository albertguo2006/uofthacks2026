export interface Task {
  task_id: string;
  title: string;
  description: string;
  difficulty: 'easy' | 'medium' | 'hard';
  category: 'bugfix' | 'refactor' | 'feature' | 'optimization';
  language: 'javascript' | 'typescript' | 'python' | 'cpp' | 'java';
  starter_code: string;
  test_cases: TestCase[];
  time_limit_seconds: number;
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
