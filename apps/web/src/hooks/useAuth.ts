'use client';

import { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { User } from '@/types/user';
import * as authLib from '@/lib/auth';
import { setUserId } from '@/lib/telemetry';

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
