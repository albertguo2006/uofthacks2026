import { api } from './api';
import { User } from '@/types/user';

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
  display_name: string;
  role: 'candidate' | 'recruiter';
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const response = await api.post<LoginResponse>('/auth/login', { email, password });
  api.setToken(response.access_token);
  return response;
}

export async function register(data: RegisterRequest): Promise<LoginResponse> {
  const response = await api.post<LoginResponse>('/auth/register', data);
  api.setToken(response.access_token);
  return response;
}

export async function logout(): Promise<void> {
  api.setToken(null);
}

export async function getCurrentUser(): Promise<User | null> {
  const token = api.getToken();
  if (!token) return null;

  try {
    return await api.get<User>('/auth/me');
  } catch {
    api.setToken(null);
    return null;
  }
}
