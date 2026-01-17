'use client';

import { useState } from 'react';
import { Modal } from '@/components/ui/Modal';

interface ProctoringModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAccept: (cameraEnabled: boolean) => void;
  taskTitle?: string;
}

export function ProctoringModal({
  isOpen,
  onClose,
  onAccept,
  taskTitle,
}: ProctoringModalProps) {
  const [cameraEnabled, setCameraEnabled] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(false);

  const handleAccept = () => {
    if (termsAccepted) {
      onAccept(cameraEnabled);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Proctored Session" size="lg">
      <div className="space-y-4">
        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <svg
              className="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <div>
              <h3 className="font-semibold text-amber-800 dark:text-amber-200">
                This is a proctored task
              </h3>
              {taskTitle && (
                <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
                  {taskTitle}
                </p>
              )}
            </div>
          </div>
        </div>

        <div className="text-sm text-gray-600 dark:text-gray-300 space-y-3">
          <p className="font-medium">By starting this proctored session, you agree to the following:</p>
          <ul className="list-disc pl-5 space-y-2">
            <li>
              <strong>Tab switching detection:</strong> Switching to other browser tabs will be logged
            </li>
            <li>
              <strong>Window focus tracking:</strong> Leaving this window will be logged
            </li>
            <li>
              <strong>Mouse activity monitoring:</strong> Extended periods of inactivity will be noted
            </li>
            <li>
              <strong>Right-click prevention:</strong> Context menu access is disabled
            </li>
            <li>
              <strong>Navigation warning:</strong> Leaving the page will prompt for confirmation
            </li>
          </ul>
        </div>

        <div className="border-t dark:border-slate-700 pt-4 space-y-3">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={cameraEnabled}
              onChange={(e) => setCameraEnabled(e.target.checked)}
              className="w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm">
              Enable camera monitoring (optional)
            </span>
          </label>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={termsAccepted}
              onChange={(e) => setTermsAccepted(e.target.checked)}
              className="w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm">
              I understand and agree to be monitored during this session
            </span>
          </label>
        </div>

        <div className="flex gap-3 pt-2">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-slate-700 rounded-lg hover:bg-gray-200 dark:hover:bg-slate-600 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleAccept}
            disabled={!termsAccepted}
            className="flex-1 px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Start Proctored Session
          </button>
        </div>
      </div>
    </Modal>
  );
}
