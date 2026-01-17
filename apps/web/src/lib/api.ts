const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Helper to check if we're in dev mode (from URL query param)
export function isDevMode(): boolean {
  if (typeof window === 'undefined') return false;
  const params = new URLSearchParams(window.location.search);
  return params.get('dev') === 'true';
}

// Helper to get dev role from URL path or query param
function getDevRole(): string {
  if (typeof window === 'undefined') return 'candidate';
  
  // First check query param for explicit override
  const params = new URLSearchParams(window.location.search);
  const roleParam = params.get('role');
  if (roleParam) return roleParam;
  
  // Auto-detect from path
  const path = window.location.pathname;
  if (path.startsWith('/recruiter')) return 'recruiter';
  return 'candidate';
}

// Mock candidates data for dev mode
const MOCK_CANDIDATES = [
  {
    user_id: 'dev-candidate-123',
    display_name: 'Jane Candidate',
    email: 'jane@example.com',
    archetype: 'craftsman',
    archetype_label: 'Code Craftsman',
    metrics: {
      iteration_velocity: 0.72,
      debug_efficiency: 0.85,
      craftsmanship: 0.91,
      tool_fluency: 0.78,
      integrity: 1.0,
    },
    sessions_completed: 12,
    has_video: true,
  },
  {
    user_id: 'dev-candidate-456',
    display_name: 'Bob Developer',
    email: 'bob@example.com',
    archetype: 'fast_iterator',
    archetype_label: 'Fast Iterator',
    metrics: {
      iteration_velocity: 0.95,
      debug_efficiency: 0.68,
      craftsmanship: 0.72,
      tool_fluency: 0.88,
      integrity: 1.0,
    },
    sessions_completed: 8,
    has_video: false,
  },
  {
    user_id: 'dev-candidate-789',
    display_name: 'Alice Engineer',
    email: 'alice@example.com',
    archetype: 'debugger',
    archetype_label: 'Debugger',
    metrics: {
      iteration_velocity: 0.65,
      debug_efficiency: 0.95,
      craftsmanship: 0.80,
      tool_fluency: 0.75,
      integrity: 1.0,
    },
    sessions_completed: 15,
    has_video: true,
  },
];

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }

  getToken(): string | null {
    if (this.token) return this.token;
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('token');
    }
    return this.token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken();
    const devMode = isDevMode();

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (devMode) {
      // Add dev mode headers for backend bypass
      (headers as Record<string, string>)['X-Dev-Mode'] = 'true';
      (headers as Record<string, string>)['X-Dev-Role'] = getDevRole();
    } else if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || 'Request failed');
    }

    return response.json();
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async put<T>(endpoint: string, data: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  async uploadVideo(
    formData: FormData,
    onProgress?: (progress: number) => void
  ): Promise<{ video_id: string }> {
    const token = this.getToken();
    const devMode = isDevMode();

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable && onProgress) {
          const progress = Math.round((e.loaded / e.total) * 100);
          onProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          reject(new Error('Upload failed'));
        }
      });

      xhr.addEventListener('error', () => reject(new Error('Upload failed')));

      xhr.open('POST', `${API_URL}/video/upload`);
      if (devMode) {
        xhr.setRequestHeader('X-Dev-Mode', 'true');
        xhr.setRequestHeader('X-Dev-Role', getDevRole());
      } else if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      }
      xhr.send(formData);
    });
  }

  async getCandidates(archetype?: string): Promise<{
    candidates: Array<{
      user_id: string;
      display_name: string;
      email: string;
      archetype: string | null;
      archetype_label: string | null;
      metrics: Record<string, number>;
      sessions_completed: number;
      has_video: boolean;
    }>;
    total: number;
  }> {
    // Return mock data in dev mode
    if (isDevMode()) {
      let candidates = MOCK_CANDIDATES;
      if (archetype) {
        candidates = candidates.filter(c => c.archetype === archetype);
      }
      return Promise.resolve({
        candidates,
        total: candidates.length,
      });
    }
    const params = archetype ? `?archetype=${encodeURIComponent(archetype)}` : '';
    return this.get(`/recruiter/candidates${params}`);
  }

  async searchVideo(
    videoId: string,
    query: string
  ): Promise<{
    results: Array<{
      start_time: number;
      end_time: number;
      confidence: number;
      transcript_snippet: string;
    }>;
  }> {
    return this.get(`/video/${videoId}/search?q=${encodeURIComponent(query)}`);
  }

  // Analytics endpoints
  async getPassportAnalytics(userId?: string): Promise<PassportAnalytics> {
    if (isDevMode()) {
      return MOCK_PASSPORT_ANALYTICS;
    }
    const endpoint = userId ? `/analytics/passport/${userId}` : '/analytics/passport';
    return this.get(endpoint);
  }

  async getEventCounts(): Promise<Record<string, number>> {
    if (isDevMode()) {
      return MOCK_EVENT_COUNTS;
    }
    return this.get('/analytics/events/counts');
  }
}

// Analytics types
export interface PassportAnalytics {
  user_id: string;
  event_summary: Record<string, number>;
  session_stats: {
    total_sessions: number;
    passed_sessions: number;
    pass_rate: number;
    average_score: number;
  };
  activity_metrics: {
    total_test_runs: number;
    total_submissions: number;
    runs_per_submission: number;
    code_changes: number;
  };
  ai_assistance_metrics: {
    hints_requested: number;
    hints_acknowledged: number;
    chat_messages_sent: number;
    chat_help_requests: number;
    ai_reliance_score: number;  // 0 = independent, 1 = heavily reliant
  };
  learning_metrics: {
    errors_encountered: number;
    fixes_applied: number;
    fix_efficiency: number;  // How quickly they fix errors (0-1)
  };
  integrity_metrics: {
    violations: number;
    integrity_score: number;
  };
}

// Mock analytics for dev mode
const MOCK_PASSPORT_ANALYTICS: PassportAnalytics = {
  user_id: 'dev-candidate-123',
  event_summary: {
    test_cases_ran: 47,
    task_submitted: 12,
    code_changed: 156,
    run_attempted: 45,
    error_emitted: 23,
    fix_applied: 21,
    contextual_hint_shown: 5,
    chat_help_requested: 3,
  },
  session_stats: {
    total_sessions: 12,
    passed_sessions: 10,
    pass_rate: 0.83,
    average_score: 87.5,
  },
  activity_metrics: {
    total_test_runs: 47,
    total_submissions: 12,
    runs_per_submission: 3.9,
    code_changes: 156,
  },
  ai_assistance_metrics: {
    hints_requested: 5,
    hints_acknowledged: 4,
    chat_messages_sent: 8,
    chat_help_requests: 3,
    ai_reliance_score: 0.05,  // Very independent
  },
  learning_metrics: {
    errors_encountered: 23,
    fixes_applied: 21,
    fix_efficiency: 0.91,
  },
  integrity_metrics: {
    violations: 0,
    integrity_score: 1.0,
  },
};

const MOCK_EVENT_COUNTS: Record<string, number> = {
  test_cases_ran: 47,
  task_submitted: 12,
  code_changed: 156,
  run_attempted: 45,
  error_emitted: 23,
  fix_applied: 21,
};

export const api = new ApiClient();
