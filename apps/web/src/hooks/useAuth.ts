'use client';

import { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { User } from '@/types/user';
import * as authLib from '@/lib/auth';
import { setUserId } from '@/lib/telemetry';

// Dev mode mock users
const DEV_USER: User = {
  user_id: 'dev-candidate-123',
  email: 'jane.candidate@example.com',
  role: 'candidate',
  display_name: 'Jane Candidate',
};

const DEV_RECRUITER: User = {
  user_id: 'dev-recruiter-123',
  email: 'john.recruiter@example.com',
  role: 'recruiter',
  display_name: 'John Recruiter',
};

// Helper to check if we're in dev mode
function isDevMode(): boolean {
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

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (data: authLib.RegisterRequest) => Promise<User>;
  logout: () => Promise<void>;
  setUser: (user: User | null) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);

  // If no context, create a standalone hook for use outside provider
  const [user, setUserState] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!context) {
      // Check for dev mode first
      if (isDevMode()) {
        const devRole = getDevRole();
        const devUser = devRole === 'recruiter' ? DEV_RECRUITER : DEV_USER;
        setUserState(devUser);
        setUserId(devUser.user_id);
        setIsLoading(false);
        return;
      }
      
      authLib.getCurrentUser().then((user) => {
        setUserState(user);
        setUserId(user?.user_id || null);
        setIsLoading(false);
      });
    }
  }, [context]);

  const login = useCallback(async (email: string, password: string) => {
    const response = await authLib.login(email, password);
    setUserState(response.user);
    setUserId(response.user.user_id);
    return response.user;
  }, []);

  const register = useCallback(async (data: authLib.RegisterRequest) => {
    const response = await authLib.register(data);
    setUserState(response.user);
    setUserId(response.user.user_id);
    return response.user;
  }, []);

  const logout = useCallback(async () => {
    await authLib.logout();
    setUserState(null);
    setUserId(null);
  }, []);

  const setUser = useCallback((user: User | null) => {
    setUserState(user);
    setUserId(user?.user_id || null);
  }, []);

  if (context) return context;

  return {
    user,
    isLoading,
    login,
    register,
    logout,
    setUser,
  };
}

export { AuthContext };
