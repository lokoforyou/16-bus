'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useState } from 'react';

import { auth, ApiError, UserRole } from '@/lib/api';

const roleOptions: { value: UserRole; label: string }[] = [
  { value: 'passenger', label: 'Passenger' },
  { value: 'driver', label: 'Driver' },
  { value: 'marshal', label: 'Marshal' },
  { value: 'org_admin', label: 'Organization Admin' },
  { value: 'super_admin', label: 'Super Admin' },
];

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<UserRole>('passenger');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await auth.register({
        full_name: fullName,
        phone,
        password,
        role,
        is_active: true,
      });
      router.replace('/login');
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Registration failed');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.18),_transparent_32%),linear-gradient(180deg,_#03111a_0%,_#082f49_42%,_#f8fafc_42%,_#f8fafc_100%)] px-6 py-12">
      <div className="mx-auto flex min-h-[80vh] max-w-4xl items-center justify-center">
        <div className="w-full overflow-hidden rounded-[2rem] border border-white/10 bg-white shadow-[0_30px_120px_rgba(15,23,42,0.2)]">
          <div className="grid md:grid-cols-[0.95fr_1.05fr]">
            <section className="bg-slate-950 p-10 text-white">
              <div className="text-xs uppercase tracking-[0.35em] text-emerald-200">Create account</div>
              <h1 className="mt-8 text-4xl font-semibold leading-tight">Register and choose a role.</h1>
              <p className="mt-4 text-sm leading-6 text-slate-300">
                Role selection is open for now so you can bootstrap the system quickly. We can harden this later with invite-based access.
              </p>
            </section>

            <section className="p-10">
              <form className="space-y-5" onSubmit={handleSubmit}>
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-slate-700">Full name</span>
                  <input
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-emerald-400 focus:bg-white"
                  />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-slate-700">Phone</span>
                  <input
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-emerald-400 focus:bg-white"
                  />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-slate-700">Password</span>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-emerald-400 focus:bg-white"
                  />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-slate-700">Role</span>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value as UserRole)}
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-emerald-400 focus:bg-white"
                  >
                    {roleOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                {error && <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded-2xl bg-emerald-600 px-4 py-3 font-semibold text-white transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:bg-slate-400"
                >
                  {loading ? 'Creating account...' : 'Register'}
                </button>
              </form>
              <div className="mt-4 text-sm text-slate-500">
                Already registered?{' '}
                <Link href="/login" className="font-medium text-slate-950 underline">
                  Sign in
                </Link>
              </div>
            </section>
          </div>
        </div>
      </div>
    </main>
  );
}
