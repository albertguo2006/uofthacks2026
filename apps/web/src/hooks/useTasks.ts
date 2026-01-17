'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { Task, TaskSummary } from '@/types/task';

interface TasksResponse {
  tasks: TaskSummary[];
}

export function useTasks() {
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [fullTasks, setFullTasks] = useState<Record<string, Task>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = useCallback(async () => {
    try {
      const response = await api.get<TasksResponse>('/tasks');
      setTasks(response.tasks);
      setError(null);
    } catch (err) {
      setError('Failed to fetch tasks');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const getTask = useCallback(
    (taskId: string): Task | undefined => {
      // Return full task if available
      return fullTasks[taskId];
    },
    [fullTasks]
  );

  const getTaskSummary = useCallback(
    (taskId: string): TaskSummary | undefined => {
      return tasks.find((t) => t.task_id === taskId);
    },
    [tasks]
  );

  const fetchTask = useCallback(
    async (taskId: string, proctoringSessionId?: string): Promise<Task | null> => {
      // Return cached full task if available
      if (fullTasks[taskId]) {
        return fullTasks[taskId];
      }

      try {
        const url = proctoringSessionId
          ? `/tasks/${taskId}?proctoring_session_id=${proctoringSessionId}`
          : `/tasks/${taskId}`;
        const task = await api.get<Task>(url);
        setFullTasks((prev) => ({ ...prev, [taskId]: task }));
        return task;
      } catch (err) {
        setError('Failed to fetch task');
        return null;
      }
    },
    [fullTasks]
  );

  // Clear cached task (useful when proctoring session starts)
  const clearTaskCache = useCallback((taskId: string) => {
    setFullTasks((prev) => {
      const updated = { ...prev };
      delete updated[taskId];
      return updated;
    });
  }, []);

  return {
    tasks,
    isLoading,
    error,
    refetch: fetchTasks,
    getTask,
    getTaskSummary,
    fetchTask,
    clearTaskCache,
  };
}
