'use client';

import { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import { SkillPassport } from '@/components/passport/SkillPassport';
import { HighlightsList } from '@/components/video/HighlightsList';
import { api } from '@/lib/api';

interface CandidateAnalysis {
  user_id: string;
  overall_score: number;
  summary: string;
  dimension_analysis?: Record<string, { score: number; note: string }>;
  key_strengths: string[];
  areas_of_concern: string[];
  interview_focus_areas: string[];
  hiring_recommendation: string;
}

interface PassportData {
  user_id: string;
  display_name: string;
  archetype?: {
    name: string;
    label: string;
    description: string;
    confidence: number;
  };
  skill_vector?: number[];
  metrics?: Record<string, number>;
  sessions_completed?: number;
  tasks_passed?: number;
  notable_moments?: Array<{
    type: string;
    description: string;
    timestamp: string;
  }>;
  interview?: {
    has_video: boolean;
    highlights: Array<{
      timestamp: string;
      description: string;
      query: string;
    }>;
  };
}

export default function CandidateDetailPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const candidateId = params.id as string;
  const jobId = searchParams.get('job_id');

  const [passport, setPassport] = useState<PassportData | null>(null);
  const [analysis, setAnalysis] = useState<CandidateAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        // Fetch passport data
        const passportResponse = await api.get<PassportData>(
          `/passport/${candidateId}`
        );
        setPassport(passportResponse);

        // Fetch AI analysis
        const analysisParams = new URLSearchParams();
        if (jobId) {
          analysisParams.append('job_id', jobId);
        }
        const analysisResponse = await api.get<CandidateAnalysis>(
          `/recruiter/candidates/${candidateId}/analysis?${analysisParams.toString()}`
        );
        setAnalysis(analysisResponse);
      } catch (err) {
        setError('Failed to load candidate data');
        console.error('Failed to fetch candidate:', err);
      } finally {
        setIsLoading(false);
      }
    };

    if (candidateId) {
      fetchData();
    }
  }, [candidateId, jobId]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  if (error || !passport) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500">{error || 'Candidate not found'}</p>
      </div>
    );
  }

  const recommendationColors: Record<string, string> = {
    strong_hire: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    hire: 'bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400',
    maybe: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
    no_hire: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">{passport.display_name}</h1>
        <button className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
          Invite to Interview
        </button>
      </div>

      {/* AI Analysis Panel */}
      {analysis && (
        <div className="bg-gradient-to-r from-primary-900/20 to-primary-800/10 border border-primary-700/30 rounded-lg p-6">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <svg className="w-5 h-5 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                  />
                </svg>
                AI Analysis
              </h2>
              <p className="mt-2 text-gray-300">{analysis.summary}</p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-primary-400">
                {(analysis.overall_score * 100).toFixed(0)}%
              </div>
              <span
                className={`inline-block mt-1 px-3 py-1 rounded-full text-sm font-medium ${
                  recommendationColors[analysis.hiring_recommendation] || recommendationColors.maybe
                }`}
              >
                {analysis.hiring_recommendation.replace('_', ' ').toUpperCase()}
              </span>
            </div>
          </div>

          {/* Dimension Analysis */}
          {analysis.dimension_analysis && (
            <div className="mt-6 grid grid-cols-5 gap-4">
              {Object.entries(analysis.dimension_analysis).map(([dim, data]) => (
                <div key={dim} className="text-center">
                  <div className="text-lg font-semibold text-primary-300">
                    {(data.score * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-gray-400 capitalize">{dim}</div>
                  <div className="text-xs text-gray-500 mt-1 truncate" title={data.note}>
                    {data.note}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Strengths & Concerns */}
          <div className="mt-6 grid md:grid-cols-2 gap-4">
            <div>
              <h4 className="text-sm font-medium text-green-400 mb-2">Key Strengths</h4>
              <ul className="space-y-1">
                {analysis.key_strengths.map((strength, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-gray-300">
                    <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    {strength}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-medium text-yellow-400 mb-2">Areas of Concern</h4>
              <ul className="space-y-1">
                {analysis.areas_of_concern.map((concern, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-gray-300">
                    <svg className="w-4 h-4 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                      />
                    </svg>
                    {concern}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Interview Focus Areas */}
          {analysis.interview_focus_areas.length > 0 && (
            <div className="mt-6">
              <h4 className="text-sm font-medium text-primary-400 mb-2">Suggested Interview Topics</h4>
              <div className="flex flex-wrap gap-2">
                {analysis.interview_focus_areas.map((topic, i) => (
                  <span
                    key={i}
                    className="px-3 py-1 bg-primary-900/50 text-primary-300 rounded-full text-sm"
                  >
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <SkillPassport passport={passport} />
        </div>

        <div className="space-y-6">
          <div className="bg-white dark:bg-slate-800 rounded-lg p-6">
            <h3 className="font-semibold mb-4">Interview Highlights</h3>
            {passport.interview?.has_video ? (
              <HighlightsList highlights={passport.interview.highlights} />
            ) : (
              <p className="text-gray-600 dark:text-gray-300">
                No interview video uploaded
              </p>
            )}
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-lg p-6">
            <h3 className="font-semibold mb-4">Search Video</h3>
            <input
              type="text"
              placeholder="e.g., 'testing strategy'"
              className="w-full px-4 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600"
            />
            <button className="mt-2 w-full px-4 py-2 bg-gray-100 dark:bg-slate-700 rounded-lg hover:bg-gray-200 dark:hover:bg-slate-600">
              Search
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
