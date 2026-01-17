'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { api } from '@/lib/api';

interface CreateJobFormProps {
  onSuccess: () => void;
  onCancel: () => void;
}

export function CreateJobForm({ onSuccess, onCancel }: CreateJobFormProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    company: '',
    salary_range: '',
    location: '',
    tags: '',
    tier: 0,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      await api.post('/jobs', {
        title: formData.title,
        description: formData.description,
        company: formData.company,
        salary_range: formData.salary_range,
        location: formData.location,
        tags: formData.tags.split(',').map((t) => t.trim()).filter(Boolean),
        tier: formData.tier,
      });
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create job');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="p-3 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-lg text-sm">
          {error}
        </div>
      )}

      <div>
        <label htmlFor="title" className="block text-sm font-medium mb-1">
          Job Title
        </label>
        <Input
          id="title"
          type="text"
          value={formData.title}
          onChange={(e) => setFormData({ ...formData, title: e.target.value })}
          placeholder="Senior Backend Engineer"
          required
        />
      </div>

      <div>
        <label htmlFor="company" className="block text-sm font-medium mb-1">
          Company Name
        </label>
        <Input
          id="company"
          type="text"
          value={formData.company}
          onChange={(e) => setFormData({ ...formData, company: e.target.value })}
          placeholder="Acme Corp"
          required
        />
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium mb-1">
          Description
        </label>
        <textarea
          id="description"
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          placeholder="Describe the role and responsibilities..."
          required
          rows={4}
          className="w-full px-4 py-2 border rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-slate-800 dark:border-slate-600 border-gray-300"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="salary_range" className="block text-sm font-medium mb-1">
            Salary Range
          </label>
          <Input
            id="salary_range"
            type="text"
            value={formData.salary_range}
            onChange={(e) => setFormData({ ...formData, salary_range: e.target.value })}
            placeholder="$100-150k"
            required
          />
        </div>

        <div>
          <label htmlFor="location" className="block text-sm font-medium mb-1">
            Location
          </label>
          <Input
            id="location"
            type="text"
            value={formData.location}
            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
            placeholder="Remote"
            required
          />
        </div>
      </div>

      <div>
        <label htmlFor="tier" className="block text-sm font-medium mb-1">
          Experience Level
        </label>
        <select
          id="tier"
          value={formData.tier}
          onChange={(e) => setFormData({ ...formData, tier: parseInt(e.target.value) })}
          className="w-full px-4 py-2 border rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-slate-800 dark:border-slate-600 border-gray-300"
        >
          <option value={0}>Entry Level</option>
          <option value={1}>Mid Level</option>
          <option value={2}>Senior Level</option>
        </select>
      </div>

      <div>
        <label htmlFor="tags" className="block text-sm font-medium mb-1">
          Tags (comma-separated)
        </label>
        <Input
          id="tags"
          type="text"
          value={formData.tags}
          onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
          placeholder="backend, python, aws"
        />
      </div>

      <div className="flex gap-3 pt-2">
        <Button type="submit" isLoading={isLoading} className="flex-1">
          Create Job
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
