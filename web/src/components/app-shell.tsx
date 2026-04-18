'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { ApiError, auth, User } from '@/lib/api';

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (phone: string, password: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error('useAuth must be used within AppShell');
  }
  return value;
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const me = await auth.me();
      setUser(me);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        auth.logout();
        setUser(null);
      } else {
        console.error(error);
        setUser(null);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, []);

  useEffect(() => {
    if (loading) {
      return;
    }
    if (pathname === '/login' || pathname === '/register') {
      if (user) {
        router.replace('/');
      }
      return;
    }
    if (!user) {
      router.replace('/login');
    }
  }, [loading, pathname, router, user]);

  const login = useCallback(
    async (phone: string, password: string) => {
      await auth.login(phone, password);
      await refresh();
      router.replace('/');
    },
    [refresh, router]
  );

  const logout = useCallback(() => {
    auth.logout();
    setUser(null);
    router.replace('/login');
  }, [router]);

  const value = useMemo<AuthContextValue>(() => ({ user, loading, login, logout, refresh }), [user, loading, login, logout, refresh]);

  if (loading && pathname !== '/login') {
    return (
      <main className="min-h-screen bg-slate-950 text-white grid place-items-center">
        <div className="text-center space-y-3">
          <div className="text-sm uppercase tracking-[0.35em] text-slate-400">16 Bus</div>
          <div className="text-xl font-semibold">Loading session</div>
        </div>
      </main>
    );
  }

  if (pathname === '/login' || pathname === '/register') {
    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
  }

  if (!user) {
    return null;
  }

  return (
    <AuthContext.Provider value={value}>
      <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.18),_transparent_30%),linear-gradient(180deg,_#0f172a_0%,_#111827_35%,_#f8fafc_35%,_#f8fafc_100%)]">
        <header className="sticky top-0 z-20 border-b border-white/10 bg-slate-950/90 backdrop-blur text-white">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
            <div>
              <div className="text-xs uppercase tracking-[0.35em] text-slate-400">Transport Ops</div>
              <Link href="/" className="text-lg font-semibold hover:text-sky-300">
                16 Bus Control Panel
              </Link>
            </div>
            <nav className="flex items-center gap-4 text-sm">
              <Link href="/admin" className="text-slate-300 hover:text-white">
                Admin
              </Link>
              <Link href="/booking" className="text-slate-300 hover:text-white">
                Booking
              </Link>
              <Link href="/queue" className="text-slate-300 hover:text-white">
                Queue
              </Link>
              <Link href="/trips" className="text-slate-300 hover:text-white">
                Trips
              </Link>
              <button
                type="button"
                onClick={value.logout}
                className="rounded-full border border-white/15 px-4 py-2 text-slate-200 hover:bg-white/10"
              >
                Logout
              </button>
            </nav>
          </div>
        </header>
        {children}
      </div>
    </AuthContext.Provider>
  );
}
