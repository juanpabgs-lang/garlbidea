import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'

const LINKS = [
  ['/', 'Morning Brief'],
  ['/ask', 'Ask the Desk'],
  ['/markets', 'Markets'],
  ['/prices', 'Prices'],
  ['/freight', 'Freight'],
  ['/policy', 'Policy'],
  ['/sources', 'Sources'],
] as const

export function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-paper">
        <div className="mx-auto flex max-w-6xl items-end justify-between gap-6 px-6 py-5">
          <div>
            <p className="text-[11px] uppercase tracking-[0.22em] text-muted">Norfront · GARLEB</p>
            <h1 className="serif text-3xl leading-none">The Desk</h1>
            <p className="mt-1 text-sm text-muted">Pasta, semolina and tomato · Levant, Gulf, East Africa</p>
          </div>
          <p className="hidden max-w-xs text-right text-xs text-muted md:block">
            Public data only. No GARLEB files. Licensed feeds stay dark until they approve the provider.
          </p>
        </div>
        <nav className="mx-auto flex max-w-6xl flex-wrap gap-1 px-6 pb-3 text-sm">
          {LINKS.map(([to, label]) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `px-3 py-1.5 ${isActive ? 'bg-ink text-cream' : 'text-ink hover:bg-line/60'}`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
    </div>
  )
}

export function fmt(n?: number | null, d = 1) {
  if (n == null || Number.isNaN(n)) return '—'
  return n.toLocaleString(undefined, { maximumFractionDigits: d })
}

export function pct(n?: number | null) {
  if (n == null || Number.isNaN(n)) return '—'
  return `${(n * 100).toFixed(1)}%`
}
