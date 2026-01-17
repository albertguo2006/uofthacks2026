/**
 * Local storage utilities for saving code drafts
 */

const CODE_STORAGE_PREFIX = 'task_code_draft_';

export function saveCodeDraft(taskId: string, code: string): void {
  if (typeof window === 'undefined') return;

  try {
    localStorage.setItem(`${CODE_STORAGE_PREFIX}${taskId}`, code);
  } catch (e) {
    // localStorage might be full or disabled
    console.warn('Failed to save code draft:', e);
  }
}

export function loadCodeDraft(taskId: string): string | null {
  if (typeof window === 'undefined') return null;

  try {
    return localStorage.getItem(`${CODE_STORAGE_PREFIX}${taskId}`);
  } catch (e) {
    console.warn('Failed to load code draft:', e);
    return null;
  }
}

export function clearCodeDraft(taskId: string): void {
  if (typeof window === 'undefined') return;

  try {
    localStorage.removeItem(`${CODE_STORAGE_PREFIX}${taskId}`);
  } catch (e) {
    console.warn('Failed to clear code draft:', e);
  }
}
