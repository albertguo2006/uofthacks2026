import type { Timeline, AskRequest, AskResponse, QuickInsightsResponse, UserSessionsResponse, RecruiterVideosResponse } from '@/types/timeline';

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
      let errorMessage = 'Request failed';
      try {
        const error = await response.json();
        // Handle various error formats
        if (typeof error.detail === 'string') {
          errorMessage = error.detail;
        } else if (typeof error.message === 'string') {
          errorMessage = error.message;
        } else if (typeof error.error === 'string') {
          errorMessage = error.error;
        } else if (error.detail && typeof error.detail === 'object') {
          // Handle validation errors from FastAPI
          errorMessage = JSON.stringify(error.detail);
        }
      } catch {
        // If JSON parsing fails, use status text
        errorMessage = `Request failed with status ${response.status}`;
      }
      throw new Error(errorMessage);
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

  async postForm<T>(endpoint: string, formData: FormData): Promise<T> {
    const token = this.getToken();
    const devMode = isDevMode();

    const headers: HeadersInit = {};

    if (devMode) {
      (headers as Record<string, string>)['X-Dev-Mode'] = 'true';
      (headers as Record<string, string>)['X-Dev-Role'] = getDevRole();
    } else if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      let errorMessage = 'Request failed';
      try {
        const error = await response.json();
        if (typeof error.detail === 'string') {
          errorMessage = error.detail;
        } else if (typeof error.message === 'string') {
          errorMessage = error.message;
        }
      } catch {
        errorMessage = `Request failed with status ${response.status}`;
      }
      throw new Error(errorMessage);
    }

    return response.json();
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

  // Replay API methods
  async getSessionTimeline(sessionId: string): Promise<Timeline> {
    if (isDevMode()) {
      return MOCK_TIMELINE as Timeline;
    }
    return this.get(`/replay/${sessionId}/timeline`);
  }

  async askAboutSession(sessionId: string, request: AskRequest): Promise<AskResponse> {
    if (isDevMode()) {
      return {
        answer: `Based on the session timeline, the candidate changed their approach at approximately 10 minutes into the session [idx: 5]. After encountering a TypeError, they received an AI hint suggesting the use of a hash map, and then rewrote their solution to use a dictionary-based approach. This resulted in all tests passing.`,
        timeline_jumps: [
          { index: 5, timestamp: MOCK_TIMELINE.entries[5].timestamp, description: 'Code edited - major refactor' },
          { index: 4, timestamp: MOCK_TIMELINE.entries[4].timestamp, description: 'AI Intervention' },
        ],
        video_segments: [
          { start_time: 580, end_time: 650, confidence: 0.92, description: 'Discussing new approach' },
        ],
        confidence: 0.85,
      };
    }
    return this.post(`/replay/${sessionId}/ask`, request);
  }

  async getSessionInsights(sessionId: string): Promise<QuickInsightsResponse> {
    if (isDevMode()) {
      return MOCK_INSIGHTS as QuickInsightsResponse;
    }
    return this.get(`/replay/${sessionId}/insights`);
  }

  async getUserSessions(userId: string): Promise<UserSessionsResponse> {
    if (isDevMode()) {
      return { sessions: MOCK_SESSIONS };
    }
    return this.get(`/replay/user/${userId}/sessions`);
  }

  async getRecruiterVideos(candidateId: string): Promise<RecruiterVideosResponse> {
    if (isDevMode()) {
      return { videos: MOCK_RECRUITER_VIDEOS };
    }
    return this.get(`/recruiter/candidates/${candidateId}/videos`);
  }

  async uploadCandidateVideo(
    candidateId: string,
    formData: FormData,
    onProgress?: (progress: number) => void
  ): Promise<{ video_id: string; status: string; candidate_id: string }> {
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

      xhr.open('POST', `${API_URL}/recruiter/candidates/${candidateId}/video`);
      if (devMode) {
        xhr.setRequestHeader('X-Dev-Mode', 'true');
        xhr.setRequestHeader('X-Dev-Role', 'recruiter');
      } else if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      }
      xhr.send(formData);
    });
  }

  async getVideoStatus(videoId: string): Promise<{
    video_id: string;
    status: string;
    duration_seconds?: number;
    ready_at?: string;
  }> {
    return this.get(`/video/${videoId}/status`);
  }

  async getVideoDetails(videoId: string): Promise<VideoDetails> {
    if (isDevMode()) {
      // Find the video in mock data
      const mockVideo = MOCK_RECRUITER_VIDEOS.find(v => v.video_id === videoId);
      if (mockVideo) {
        return {
          video_id: mockVideo.video_id,
          status: mockVideo.status,
          summary: mockVideo.summary,
          highlights: mockVideo.highlights,
          communication_analysis: mockVideo.communication_analysis,
        };
      }
      // Default mock
      return MOCK_VIDEO_DETAILS;
    }
    return this.get(`/video/${videoId}/details`);
  }

  async deleteCandidateVideo(candidateId: string, videoId: string): Promise<void> {
    if (isDevMode()) {
      // Simulate deletion in dev mode
      return;
    }
    return this.delete(`/recruiter/candidates/${candidateId}/videos/${videoId}`);
  }

  // Notification endpoints
  async getNotifications(filter: 'all' | 'unread' = 'all', limit: number = 20, skip: number = 0): Promise<{
    notifications: Array<{
      notification_id: string;
      recipient_id: string;
      sender_id: string | null;
      type: 'interview_request' | 'application_status' | 'message' | 'system';
      title: string;
      message: string;
      is_read: boolean;
      created_at: string;
      read_at: string | null;
      metadata?: any;
    }>;
  }> {
    if (isDevMode()) {
      // Return mock notifications for dev mode
      const mockNotifications = [
        {
          notification_id: 'notif-1',
          recipient_id: 'dev-user-123',
          sender_id: 'recruiter-1',
          type: 'interview_request' as const,
          title: 'Interview Request from TechCorp',
          message: 'You have been invited for a technical interview with TechCorp',
          is_read: false,
          created_at: new Date(Date.now() - 3600000).toISOString(),
          read_at: null,
          metadata: {
            company_name: 'TechCorp',
            job_title: 'Senior Software Engineer',
            interview_date: new Date(Date.now() + 86400000 * 3).toISOString(),
            interview_type: 'technical',
          }
        },
        {
          notification_id: 'notif-2',
          recipient_id: 'dev-user-123',
          sender_id: 'system',
          type: 'system' as const,
          title: 'Profile Updated',
          message: 'Your skill passport has been updated with your latest assessment results',
          is_read: true,
          created_at: new Date(Date.now() - 7200000).toISOString(),
          read_at: new Date(Date.now() - 7200000).toISOString(),
          metadata: null
        }
      ];

      const filtered = filter === 'unread'
        ? mockNotifications.filter(n => !n.is_read)
        : mockNotifications;

      return Promise.resolve({ notifications: filtered });
    }

    const params = new URLSearchParams({
      filter,
      limit: limit.toString(),
      skip: skip.toString()
    });
    return this.get(`/notifications?${params}`);
  }

  async getNotificationCount(): Promise<{ total: number; unread: number }> {
    if (isDevMode()) {
      return Promise.resolve({ total: 2, unread: 1 });
    }
    return this.get('/notifications/count');
  }

  async markNotificationAsRead(notificationId: string): Promise<void> {
    if (isDevMode()) {
      return Promise.resolve();
    }
    return this.request(`/notifications/${notificationId}`, {
      method: 'PATCH',
      body: JSON.stringify({ is_read: true })
    });
  }

  async markAllNotificationsAsRead(): Promise<void> {
    if (isDevMode()) {
      return Promise.resolve();
    }
    return this.post('/notifications/mark-all-read', {});
  }

  async sendInterviewRequest(data: {
    candidate_id: string;
    job_id?: string;
    job_title?: string;
    company_name: string;
    interview_date?: string;
    interview_type?: 'phone' | 'video' | 'onsite' | 'technical';
    message?: string;
    meeting_link?: string;
  }): Promise<any> {
    if (isDevMode()) {
      return Promise.resolve({
        notification_id: 'new-notif-' + Date.now(),
        ...data,
        type: 'interview_request',
        title: `Interview Request from ${data.company_name}`,
        created_at: new Date().toISOString()
      });
    }
    return this.post('/notifications/interview-request', data);
  }
}

// Video types
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

export interface InterviewHighlight {
  category: string;
  query: string;
  start: number;
  end: number;
  confidence: number;
  transcript?: string;
}

export interface VideoDetails {
  video_id: string;
  status: string;
  duration_seconds?: number;
  ready_at?: string;
  summary?: string;
  highlights?: InterviewHighlight[];
  communication_analysis?: CommunicationAnalysis;
  stream_url?: string;  // HLS streaming URL
  thumbnail_url?: string;  // Video thumbnail
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

// Mock session data for dev mode replay
const MOCK_SESSIONS = [
  {
    session_id: 'dev-session-001',
    task_id: 'task-001',
    task_title: 'Two Sum',
    started_at: new Date(Date.now() - 3600000).toISOString(),
    ended_at: new Date(Date.now() - 1800000).toISOString(),
    event_count: 45,
    code_snapshots: 12,
    has_video: false,
    video_id: null,
    is_proctored: true,
    final_code: `def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []`,
    insights_summary: 'The candidate demonstrated strong problem-solving skills, efficiently pivoting from a brute force approach to an optimized hash map solution after receiving a hint.',
  },
  {
    session_id: 'dev-session-002',
    task_id: 'task-002',
    task_title: 'Binary Search',
    started_at: new Date(Date.now() - 7200000).toISOString(),
    ended_at: new Date(Date.now() - 5400000).toISOString(),
    event_count: 32,
    code_snapshots: 8,
    has_video: false,
    video_id: null,
    is_proctored: true,
    final_code: `def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1`,
    insights_summary: 'Session showed methodical approach with good debugging practices. Completed binary search implementation successfully.',
  },
];

// Mock recruiter videos for dev mode
const MOCK_RECRUITER_VIDEOS = [
  {
    video_id: 'video-001',
    status: 'ready' as const,
    filename: 'interview-2024-01-15.mp4',
    uploaded_at: new Date(Date.now() - 86400000).toISOString(),
    uploaded_by: 'recruiter-001',
    summary: 'The candidate demonstrated excellent communication skills and technical depth during this system design discussion. They showed clear thinking about trade-offs and asked relevant clarifying questions.',
    highlights: [
      {
        category: 'approach',
        query: 'problem-solving approach',
        start: 120,
        end: 180,
        confidence: 0.92,
        transcript: 'I would start by understanding the requirements...',
      },
      {
        category: 'tradeoffs',
        query: 'discussing tradeoffs',
        start: 450,
        end: 520,
        confidence: 0.88,
        transcript: 'The main tradeoff here is between latency and consistency...',
      },
    ],
    communication_analysis: {
      clarity: { score: 4, reason: 'Explains concepts clearly with good examples' },
      confidence: { score: 5, reason: 'Speaks confidently and handles uncertainty well' },
      collaboration: { score: 4, reason: 'Asks good clarifying questions' },
      technical_depth: { score: 4, reason: 'Uses appropriate technical terminology' },
    },
  },
  {
    video_id: 'video-002',
    status: 'indexing' as const,
    filename: 'behavioral-interview.mp4',
    uploaded_at: new Date(Date.now() - 3600000).toISOString(),
    uploaded_by: 'recruiter-001',
  },
];

const MOCK_VIDEO_DETAILS: VideoDetails = {
  video_id: 'video-001',
  status: 'ready',
  duration_seconds: 1800,
  stream_url: 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8',  // Demo HLS stream for dev mode
  thumbnail_url: 'https://picsum.photos/seed/interview/640/360',
  summary: 'The candidate demonstrated excellent communication skills and technical depth during this system design discussion. They showed clear thinking about trade-offs and asked relevant clarifying questions. Their approach to breaking down the problem was methodical, and they handled edge cases well.',
  highlights: [
    {
      category: 'approach',
      query: 'problem-solving approach',
      start: 120,
      end: 180,
      confidence: 0.92,
      transcript: 'I would start by understanding the requirements and breaking down the problem into smaller components...',
    },
    {
      category: 'tradeoffs',
      query: 'discussing tradeoffs',
      start: 450,
      end: 520,
      confidence: 0.88,
      transcript: 'The main tradeoff here is between latency and consistency. If we prioritize consistency...',
    },
    {
      category: 'debugging',
      query: 'debugging and fixing errors',
      start: 780,
      end: 850,
      confidence: 0.85,
      transcript: 'Let me trace through this logic again. I think the issue might be in how we handle the edge case...',
    },
  ],
  communication_analysis: {
    clarity: { score: 4, reason: 'Explains concepts clearly with good examples and analogies' },
    confidence: { score: 5, reason: 'Speaks confidently and handles uncertainty well' },
    collaboration: { score: 4, reason: 'Asks good clarifying questions and thinks out loud' },
    technical_depth: { score: 4, reason: 'Uses appropriate technical terminology accurately' },
  },
};

const MOCK_TIMELINE = {
  session_id: 'dev-session-001',
  user_id: 'dev-candidate-123',
  task_id: 'task-001',
  task_title: 'Two Sum',
  start_time: new Date(Date.now() - 3600000).toISOString(),
  end_time: new Date(Date.now() - 1800000).toISOString(),
  duration_seconds: 1800,
  entries: [
    {
      id: '1',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      type: 'session_started',
      code_snapshot: null,
      code_diff: null,
      event_data: null,
      video_timestamp_seconds: 0,
      intervention: null,
      label: 'Session started',
      severity: 'info',
    },
    {
      id: '2',
      timestamp: new Date(Date.now() - 3500000).toISOString(),
      type: 'code_changed',
      code_snapshot: 'def two_sum(nums, target):\n    pass',
      code_diff: null,
      event_data: { lines_changed: 2 },
      video_timestamp_seconds: 100,
      intervention: null,
      label: 'Code edited',
      severity: 'info',
    },
    {
      id: '3',
      timestamp: new Date(Date.now() - 3400000).toISOString(),
      type: 'run_attempted',
      code_snapshot: 'def two_sum(nums, target):\n    for i in range(len(nums)):\n        pass',
      code_diff: '@@ -1,2 +1,3 @@\n def two_sum(nums, target):\n-    pass\n+    for i in range(len(nums)):\n+        pass',
      event_data: { result: 'error' },
      video_timestamp_seconds: 200,
      intervention: null,
      label: 'Run attempted',
      severity: 'warning',
    },
    {
      id: '4',
      timestamp: new Date(Date.now() - 3300000).toISOString(),
      type: 'error_emitted',
      code_snapshot: null,
      code_diff: null,
      event_data: { error_type: 'TypeError' },
      video_timestamp_seconds: 300,
      intervention: null,
      label: 'Error: TypeError',
      severity: 'error',
    },
    {
      id: '5',
      timestamp: new Date(Date.now() - 3200000).toISOString(),
      type: 'ai_intervention',
      code_snapshot: null,
      code_diff: null,
      event_data: null,
      video_timestamp_seconds: 400,
      intervention: {
        hint: 'Consider using a hash map to store previously seen numbers and their indices.',
        type: 'technical_hint',
        personalization_badge: 'Based on your coding patterns',
      },
      label: 'AI Intervention',
      severity: 'warning',
    },
    {
      id: '6',
      timestamp: new Date(Date.now() - 3000000).toISOString(),
      type: 'code_changed',
      code_snapshot: 'def two_sum(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in seen:\n            return [seen[complement], i]\n        seen[num] = i',
      code_diff: '@@ -1,3 +1,7 @@\n def two_sum(nums, target):\n-    for i in range(len(nums)):\n-        pass\n+    seen = {}\n+    for i, num in enumerate(nums):\n+        complement = target - num\n+        if complement in seen:\n+            return [seen[complement], i]\n+        seen[num] = i',
      event_data: { lines_changed: 7 },
      video_timestamp_seconds: 600,
      intervention: null,
      label: 'Code edited',
      severity: 'info',
    },
    {
      id: '7',
      timestamp: new Date(Date.now() - 2800000).toISOString(),
      type: 'test_passed',
      code_snapshot: null,
      code_diff: null,
      event_data: { tests_passed: 3, tests_total: 3 },
      video_timestamp_seconds: 800,
      intervention: null,
      label: 'Test passed',
      severity: 'success',
    },
    {
      id: '8',
      timestamp: new Date(Date.now() - 2700000).toISOString(),
      type: 'submission_passed',
      code_snapshot: null,
      code_diff: null,
      event_data: { tests_passed: 10, tests_total: 10 },
      video_timestamp_seconds: 900,
      intervention: null,
      label: 'All tests passed',
      severity: 'success',
    },
  ],
  has_video: true,
  video_id: 'video-001',
  video_url: null,
  video_start_offset_seconds: 0,
  total_runs: 4,
  total_submissions: 1,
  errors_encountered: 1,
  interventions_received: 1,
  final_result: 'passed',
};

const MOCK_INSIGHTS = {
  session_id: 'dev-session-001',
  insights: [
    {
      category: 'approach_change',
      title: 'Approach Change Detected',
      description: 'After encountering an error, the candidate switched from brute force to hash map approach (~7 lines changed)',
      timeline_index: 5,
      video_timestamp: 600,
    },
    {
      category: 'debugging_efficiency',
      title: 'Debugging Efficiency: High',
      description: 'Average time to recover from errors: ~300s',
      timeline_index: null,
      video_timestamp: null,
    },
    {
      category: 'testing_habit',
      title: 'Testing Style: Iterative',
      description: 'Ran code 4 times (1.3 runs/minute)',
      timeline_index: null,
      video_timestamp: null,
    },
  ],
  summary: 'The candidate demonstrated strong problem-solving skills, efficiently pivoting from a brute force approach to an optimized hash map solution after receiving a hint. They showed good debugging practices and completed the task successfully.',
};

export const api = new ApiClient();
