export interface User {
  user_id: string;
  email: string;
  display_name: string;
  role: 'candidate' | 'recruiter';
  created_at?: string;
  skill_vector?: number[];
  archetype?: string;
  integrity_score?: number;
}

export interface UserCreate {
  email: string;
  password: string;
  display_name: string;
  role: 'candidate' | 'recruiter';
}
