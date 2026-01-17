'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { Task } from '@/types/task';

interface TasksResponse {
  tasks: Task[];
}

export function useTasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
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
      // Return full task if available, otherwise return from list
      return fullTasks[taskId] || tasks.find((t) => t.task_id === taskId);
    },
    [tasks, fullTasks]
  );

  const fetchTask = useCallback(async (taskId: string): Promise<Task | null> => {
    // Return cached full task if available
    if (fullTasks[taskId]) {
      return fullTasks[taskId];
    }

    try {
      const task = await api.get<Task>(`/tasks/${taskId}`);
      setFullTasks((prev) => ({ ...prev, [taskId]: task }));
      return task;
    } catch (err) {
      setError('Failed to fetch task');
      return null;
    }
  }, [fullTasks]);

  return {
    tasks,
    isLoading,
    error,
    refetch: fetchTasks,
    getTask,
    fetchTask,
  };
}
