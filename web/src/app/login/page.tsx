'use client';

import { FormEvent, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

import { ApiError } from '@/lib/api';
import { useAuth } from '@/components/app-shell';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(phone, password);
      router.replace('/');
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Login failed');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(14,165,233,0.22),_transparent_32%),linear-gradient(180deg,_#020617_0%,_#0f172a_45%,_#f8fafc_45%,_#f8fafc_100%)] px-6 py-12">
      <div className="mx-auto flex min-h-[80vh] max-w-6xl items-center justify-center">
        <div className="grid w-full max-w-5xl overflow-hidden rounded-[2rem] border border-white/10 bg-white shadow-[0_30px_120px_rgba(15,23,42,0.2)] md:grid-cols-[1.1fr_0.9fr]">
          <section className="bg-slate-950 p-10 text-white">
            <div className="inline-flex rounded-full border border-sky-400/20 bg-sky-400/10 px-4 py-1 text-xs uppercase tracking-[0.3em] text-sky-200">
              16 Bus Ops
            </div>
            <h1 className="mt-8 text-4xl font-semibold leading-tight">
              Sign in to manage bookings, trips, and rank operations.
            </h1>
            <p className="mt-4 max-w-md text-sm leading-6 text-slate-300">
              Use your operational account. Once authenticated, the control panel will unlock the real backend and Supabase-backed data surfaces.
            </p>
            <div className="mt-12 grid gap-4 text-sm text-slate-300">
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">Protected auth flow</div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">CRUD surfaces for core entities</div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">FastAPI + Supabase-ready data layer</div>
            </div>
          </section>

          <section className="p-10">
            <h2 className="text-2xl font-semibold text-slate-950">Welcome back</h2>
            <p className="mt-2 text-sm text-slate-500">Enter your phone number and password to continue.</p>
            <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">Phone</span>
                <input
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-sky-400 focus:bg-white"
                  placeholder="+27..."
                  autoComplete="username"
                />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">Password</span>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-sky-400 focus:bg-white"
                  autoComplete="current-password"
                />
              </label>
              {error && (
                <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                  {error}
                </div>
              )}
              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-2xl bg-slate-950 px-4 py-3 font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                {loading ? 'Signing in...' : 'Sign in'}
              </button>
            </form>
            <div className="mt-4 text-sm text-slate-500">
              Need an account?{' '}
              <Link href="/register" className="font-medium text-slate-950 underline">
                Register
              </Link>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
