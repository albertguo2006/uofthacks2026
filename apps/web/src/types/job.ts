export interface Job {
  job_id: string;
  title: string;
  description?: string;
  company: string;
  tier: number;
  fit_score: number;
  unlocked: boolean;
  salary_range?: string;
  location?: string;
  tags?: string[];
  unlock_requirements?: {
    min_fit: number;
    missing?: string[];
  };
}
