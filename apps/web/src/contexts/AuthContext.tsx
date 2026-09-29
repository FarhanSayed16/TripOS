'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { useRefreshMutation, useLogoutMutation } from '@/lib/api/authApi';
import { setAccessToken } from '@/lib/apiSlice';

export interface AuthUser {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  active_organization_id?: string;
  org_role?: string | null;
  is_platform_admin?: boolean;
}

interface AuthContextType {
  user: AuthUser | null;
  login: (token: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
  isPlatformAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

async function fetchMe(token: string): Promise<AuthUser | null> {
  const userRes = await fetch('/api/v1/auth/me', {
    headers: { Authorization: `Bearer ${token}` },
    credentials: 'include',
  });
  if (!userRes.ok) return null;
  return userRes.json();
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const [refreshApi] = useRefreshMutation();
  const [logoutApi] = useLogoutMutation();

  useEffect(() => {
    let mounted = true;

    const initAuth = async () => {
      try {
        const res = await refreshApi().unwrap();
        if (!mounted) return;
        setAccessToken(res.access_token);
        const me = await fetchMe(res.access_token);
        if (mounted && me) setUser(me);
      } catch {
        // Silent failure — no valid refresh cookie
      } finally {
        if (mounted) setIsLoading(false);
      }
    };

    initAuth();
    return () => {
      mounted = false;
    };
  }, [refreshApi]);

  const login = async (newToken: string) => {
    setAccessToken(newToken);
    try {
      const data = await fetchMe(newToken);
      if (!data) return;
      setUser(data);
      if (data.is_platform_admin) {
        router.push('/admin');
      } else {
        router.push('/app');
      }
    } catch (e) {
      console.error(e);
    }
  };

  const logout = async () => {
    try {
      await logoutApi().unwrap();
    } catch {
      // ignore
    }
    setAccessToken(null);
    setUser(null);
    router.push('/login');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        logout,
        isAuthenticated: !!user,
        isLoading,
        isPlatformAdmin: !!user?.is_platform_admin,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
