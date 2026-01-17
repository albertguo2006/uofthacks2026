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
}

export const api = new ApiClient();
