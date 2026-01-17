export interface Archetype {
  name: string;
  label: string;
  description: string;
  confidence: number;
}

export interface Metrics {
  iteration_velocity: number;
  debug_efficiency: number;
  craftsmanship: number;
  tool_fluency: number;
  integrity: number;
}

export interface NotableMoment {
  type: string;
  description: string;
  session_id?: string;
  timestamp: string;
}

export interface InterviewHighlight {
  timestamp: string;
  description: string;
  query?: string;
  category?: string;
  confidence?: number;
}

export interface CommunicationScore {
  score: number;
  reason: string;
}

export interface CommunicationAnalysis {
  clarity?: CommunicationScore;
  confidence?: CommunicationScore;
  collaboration?: CommunicationScore;
  technical_depth?: CommunicationScore;
}

export interface Interview {
  has_video: boolean;
  video_id?: string;
  highlights: InterviewHighlight[];
  summary?: string;
  communication_analysis?: CommunicationAnalysis;
}

export interface Passport {
  user_id: string;
  display_name: string;
  archetype: Archetype;
  skill_vector: number[];
  metrics: Metrics;
  sessions_completed: number;
  tasks_passed: number;
  notable_moments?: NotableMoment[];
  interview?: Interview;
  updated_at?: string;
}
