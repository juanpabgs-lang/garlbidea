import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { getJson, type Brief, type Insight } from '../api'
import { fmt, pct } from '../components/Shell'

export function BriefPage() {
  const q = useQuery({ queryKey: ['brief'], queryFn: () => getJson<Brief>('/api/brief') })
  const nav = useNavigate()
  if (q.isLoading) return <p className="text-muted">Composing the brief…</p>
  if (q.error || !q.data) return <p>Desk could not load. Is the API on :8011?</p>
  const b = q.data

  async function copyWhatsapp() {
    const t = await fetch('/api/whatsapp').then((r) => r.text())
    await navigator.clipboard.writeText(t)
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-widest text-muted">{b.as_of}</p>
          <h2 className="serif mt-1 max-w-3xl text-3xl leading-tight">{b.headline}</h2>
          <p className="mt-3 max-w-3xl text-[15px] leading-relaxed text-ink/80">{b.summary}</p>
        </div>
        <div className="no-print flex gap-2">
          <button className="border border-line px-3 py-1.5 text-sm" onClick={copyWhatsapp}>
            Copy for WhatsApp
          </button>
          <button className="border border-line px-3 py-1.5 text-sm" onClick={() => window.print()}>
            Print
          </button>
        </div>
      </div>

      <div className="mb-8 grid grid-cols-2 gap-2 md:grid-cols-4">
        {b.ticker.map((t) => (
          <div key={t.id} className="card px-3 py-2">
            <p className="text-[11px] uppercase tracking-wide text-muted">{t.label}</p>
            <p className="serif text-xl">
              {fmt(t.value, t.id.includes('usd') || t.id === 'eurusd' ? 4 : 1)}
              {t.unit ? <span className="ml-1 text-xs text-muted">{t.unit}</span> : null}
            </p>
            <p className="text-[11px] text-muted">
              {t.delta != null ? `${t.delta > 0 ? '+' : ''}${fmt(t.delta)}` : ''}
              {t.delta_pct != null ? ` ${pct(t.delta_pct)} vs baseline` : ''}
              {t.as_of ? ` · ${t.as_of}` : ''}
            </p>
          </div>
        ))}
      </div>

      <div className="grid gap-4">
        {b.insights.map((ins, i) => (
          <InsightCard key={ins.id} ins={ins} index={i + 1} onAsk={(q) => nav(`/ask?q=${encodeURIComponent(q)}`)} />
        ))}
      </div>

      {b.calendar?.length ? (
        <section className="mt-10">
          <h3 className="serif text-xl">Deadlines</h3>
          <ul className="mt-2 text-sm">
            {b.calendar.map((c) => (
              <li key={c.date + c.label} className="border-t border-line py-2">
                <span className="mr-3 font-medium">{c.date}</span>
                {c.label}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  )
}

function InsightCard({
  ins,
  index,
  onAsk,
}: {
  ins: Insight
  index: number
  onAsk: (q: string) => void
}) {
  return (
    <article className="card p-5">
      <div className="flex items-start justify-between gap-4">
        <p className="text-xs text-muted">
          {String(index).padStart(2, '0')} · {(ins.tags || []).join(' · ')} · confidence {pct(ins.confidence)}
        </p>
        <p className="text-xs text-muted">
          {ins.owner} · {ins.timing}
        </p>
      </div>
      <h3 className="serif mt-2 text-2xl leading-snug">{ins.title}</h3>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <div>
          <p className="text-[11px] uppercase tracking-wide text-rust">Why it matters</p>
          <p className="mt-1 text-[15px] leading-relaxed">{ins.why}</p>
        </div>
        <div>
          <p className="text-[11px] uppercase tracking-wide text-sea">What to do</p>
          <p className="mt-1 text-[15px] leading-relaxed">{ins.action}</p>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-3 text-xs text-muted">
        {(ins.sources || []).map((s, i) =>
          s.url ? (
            <a key={i} href={s.url} className="underline" target="_blank" rel="noreferrer">
              {s.title || s.url}
            </a>
          ) : (
            <span key={i}>{s.title}</span>
          ),
        )}
        <Link className="ml-auto text-ink underline" to="/ask">
          Ask follow-up
        </Link>
        {(ins.followups || []).slice(0, 1).map((f) => (
          <button key={f} className="underline" onClick={() => onAsk(f)}>
            {f}
          </button>
        ))}
      </div>
    </article>
  )
}
