import Link from 'next/link';

const panels = [
  {
    title: 'Passenger Booking',
    description: 'Book a seat, pay, and get a QR token.',
    href: '/booking',
    color: 'from-sky-500 to-cyan-400',
  },
  {
    title: 'Rank Queue',
    description: 'Issue queue tickets and manage boarding at the rank.',
    href: '/queue',
    color: 'from-emerald-500 to-lime-400',
  },
  {
    title: 'Trip Console',
    description: 'Start trips, scan passengers, and manage departures.',
    href: '/trips',
    color: 'from-amber-500 to-orange-400',
  },
  {
    title: 'Admin CRUD',
    description: 'Manage organizations and stops through backend or Supabase.',
    href: '/admin',
    color: 'from-slate-950 to-slate-700',
  },
];

export default function DashboardPage() {
  return (
    <main className="flex-1 px-6 py-10 text-slate-900">
      <div className="mx-auto max-w-7xl">
        <section className="overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-sm">
          <div className="grid gap-8 bg-[radial-gradient(circle_at_top_right,_rgba(14,165,233,0.14),_transparent_35%),linear-gradient(180deg,_#0f172a_0%,_#111827_100%)] px-8 py-10 text-white md:grid-cols-[1.2fr_0.8fr]">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-sky-200">16 Bus Control Panel</p>
              <h1 className="mt-4 max-w-2xl text-4xl font-semibold leading-tight md:text-5xl">
                Operational control for bookings, rank queueing, and trip lifecycle work.
              </h1>
              <p className="mt-4 max-w-xl text-sm leading-6 text-slate-300">
                The web app now uses authenticated sessions, registration, and CRUD-backed admin screens.
                Supabase is used when configured, with FastAPI fallback for the same data flows.
              </p>
              <div className="mt-6 flex gap-3">
                <Link href="/login" className="rounded-full bg-white px-5 py-2 text-sm font-semibold text-slate-950">
                  Sign in
                </Link>
                <Link href="/register" className="rounded-full border border-white/20 px-5 py-2 text-sm font-semibold text-white">
                  Register
                </Link>
              </div>
            </div>

            <div className="grid gap-3 rounded-[1.5rem] border border-white/10 bg-white/5 p-5 text-sm text-slate-200">
              <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">Auth: backend login + registration</div>
              <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">Data: backend API or Supabase REST</div>
              <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">Operations: bookings, queue, trips</div>
              <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">Admin: organizations, stops CRUD</div>
            </div>
          </div>
        </section>

        <section className="mt-8 grid gap-6 md:grid-cols-2 xl:grid-cols-4">
          {panels.map((panel) => (
            <Link
              key={panel.href}
              href={panel.href}
              className="group overflow-hidden rounded-[1.5rem] border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-lg"
            >
              <div className={`mb-5 h-14 w-14 rounded-2xl bg-gradient-to-br ${panel.color}`} />
              <h2 className="text-xl font-semibold text-slate-950 group-hover:text-sky-700">{panel.title}</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">{panel.description}</p>
            </Link>
          ))}
        </section>
      </div>
    </main>
  );
}
