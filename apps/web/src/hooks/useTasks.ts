'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { Task } from '@/types/task';

interface TasksResponse {
  tasks: Task[];
}

export function useTasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
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
      return tasks.find((t) => t.task_id === taskId);
    },
    [tasks]
  );

  return {
    tasks,
    isLoading,
    error,
    refetch: fetchTasks,
    getTask,
  };
}
