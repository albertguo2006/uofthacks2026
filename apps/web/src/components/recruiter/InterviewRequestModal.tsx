'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

interface InterviewRequestModalProps {
  isOpen: boolean;
  onClose: () => void;
  candidateId: string;
  candidateName: string;
}

export function InterviewRequestModal({
  isOpen,
  onClose,
  candidateId,
  candidateName,
}: InterviewRequestModalProps) {
  const [formData, setFormData] = useState({
    company_name: '',
    job_title: '',
    interview_date: '',
    interview_time: '',
    interview_type: 'video' as 'phone' | 'video' | 'onsite' | 'technical',
    meeting_link: '',
    message: '',
  });
  const [sending, setSending] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [success, setSuccess] = useState(false);

  // Clear error when modal opens/closes
  useEffect(() => {
    if (!isOpen) {
      // Reset everything when modal closes
      setErrorMessage('');
      setSuccess(false);
      setSending(false);
      setFormData({
        company_name: '',
        job_title: '',
        interview_date: '',
        interview_time: '',
        interview_type: 'video',
        meeting_link: '',
        message: '',
      });
    }
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSending(true);
    setErrorMessage('');

    try {
      // Combine date and time if both provided
      let interviewDateTime: string | undefined;
      if (formData.interview_date && formData.interview_time) {
        interviewDateTime = new Date(
          `${formData.interview_date}T${formData.interview_time}`
        ).toISOString();
      }

      await api.sendInterviewRequest({
        candidate_id: candidateId,
        company_name: formData.company_name,
        job_title: formData.job_title || undefined,
        interview_date: interviewDateTime,
        interview_type: formData.interview_type,
        meeting_link: formData.meeting_link || undefined,
        message: formData.message || `Dear ${candidateName},\n\nWe are pleased to invite you for an interview with ${formData.company_name}.`,
      });

      setSuccess(true);
      setTimeout(() => {
        onClose();
      }, 2000);
    } catch (err) {
      console.error('Interview request error:', err);

      // Ensure we always set a string error message
      let msg = 'Failed to send interview request. Please try again.';

      if (err instanceof Error) {
        msg = err.message;
      } else if (typeof err === 'string') {
        msg = err;
      } else if (err && typeof err === 'object') {
        // Handle object errors by trying to extract a meaningful message
        if ('message' in err && typeof err.message === 'string') {
          msg = err.message;
        } else if ('detail' in err && typeof err.detail === 'string') {
          msg = err.detail;
        } else {
          // Last resort: stringify the object (but avoid [object Object])
          try {
            msg = JSON.stringify(err);
          } catch {
            msg = 'An unexpected error occurred. Please try again.';
          }
        }
      }

      setErrorMessage(msg);
    } finally {
      setSending(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-slate-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Send Interview Request</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Inviting: <span className="font-medium">{candidateName}</span>
        </p>

        {success ? (
          <div className="py-8 text-center">
            <div className="mb-4">
              <svg className="w-16 h-16 text-green-500 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-lg font-medium text-green-600 dark:text-green-400">
              Interview request sent successfully!
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
              The candidate will receive a notification in their inbox.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">
                  Company Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.company_name}
                  onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-slate-700"
                  placeholder="e.g., TechCorp"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Position/Job Title
                </label>
                <input
                  type="text"
                  value={formData.job_title}
                  onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-slate-700"
                  placeholder="e.g., Senior Software Engineer"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">
                  Interview Date
                </label>
                <input
                  type="date"
                  value={formData.interview_date}
                  onChange={(e) => setFormData({ ...formData, interview_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-slate-700"
                  min={new Date().toISOString().split('T')[0]}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Interview Time
                </label>
                <input
                  type="time"
                  value={formData.interview_time}
                  onChange={(e) => setFormData({ ...formData, interview_time: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-slate-700"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Interview Type <span className="text-red-500">*</span>
              </label>
              <select
                required
                value={formData.interview_type}
                onChange={(e) => setFormData({ ...formData, interview_type: e.target.value as any })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-slate-700"
              >
                <option value="phone">Phone Interview</option>
                <option value="video">Video Interview</option>
                <option value="onsite">Onsite Interview</option>
                <option value="technical">Technical Interview</option>
              </select>
            </div>

            {(formData.interview_type === 'video' || formData.interview_type === 'phone') && (
              <div>
                <label className="block text-sm font-medium mb-1">
                  Meeting Link / Phone Number
                </label>
                <input
                  type="text"
                  value={formData.meeting_link}
                  onChange={(e) => setFormData({ ...formData, meeting_link: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-slate-700"
                  placeholder={formData.interview_type === 'video' ? 'https://zoom.us/...' : '+1-234-567-8900'}
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium mb-1">
                Custom Message (Optional)
              </label>
              <textarea
                value={formData.message}
                onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-slate-700"
                placeholder={`Dear ${candidateName},\n\nWe are pleased to invite you for an interview...`}
              />
            </div>

            {errorMessage && (
              <div className="p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-md text-sm">
                {errorMessage}
              </div>
            )}

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-md transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={sending}
                className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {sending ? 'Sending...' : 'Send Interview Request'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}