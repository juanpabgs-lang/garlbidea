import { useMutation, useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { getJson } from '../api'

export function PolicyPage() {
  const policy = useQuery({ queryKey: ['policy'], queryFn: () => getJson<any>('/api/policy') })
  const quality = useQuery({ queryKey: ['quality'], queryFn: () => getJson<any[]>('/api/quality') })
  const [q, setQ] = useState('')
  const screen = useMutation({
    mutationFn: (name: string) => getJson<any[]>(`/api/screen?q=${encodeURIComponent(name)}`),
  })
  const p = policy.data || {}
  return (
    <div>
      <h2 className="serif text-3xl">Policy, tenders & quality</h2>
      <section className="mt-6">
        <h3 className="serif text-xl">US pasta AD/CVD</h3>
        <ul className="mt-2 text-sm">
          {(p.pasta_ad || []).map((n: any) => (
            <li key={n.document_number} className="card mb-2 p-3">
              <a className="underline" href={n.url} target="_blank" rel="noreferrer">
                {n.title}
              </a>
              <p className="text-muted">
                {n.date}
                {n.garofalo_margin != null ? ` · Garofalo ${n.garofalo_margin}%` : ''}
                {n.molisana_margin != null ? ` · La Molisana ${n.molisana_margin}%` : ''}
              </p>
            </li>
          ))}
        </ul>
      </section>
      <section className="mt-8">
        <h3 className="serif text-xl">Screen a counterparty</h3>
        <p className="text-xs text-muted">Fuzzy match against OFAC SDN, UN and UK OFSI. Not a legal opinion.</p>
        <form
          className="mt-2 flex gap-2"
          onSubmit={(e) => {
            e.preventDefault()
            if (q.length >= 3) screen.mutate(q)
          }}
        >
          <input className="flex-1 border border-line bg-paper px-3 py-2" value={q} onChange={(e) => setQ(e.target.value)} />
          <button className="bg-ink px-3 py-2 text-cream">Screen</button>
        </form>
        <ul className="mt-2 text-sm">
          {(screen.data || []).map((h, i) => (
            <li key={i}>
              {h.name} · {h.list} · score {h.score}
            </li>
          ))}
        </ul>
      </section>
      <section className="mt-8 grid gap-6 md:grid-cols-2">
        <div>
          <h3 className="serif text-xl">Lebanon PPA</h3>
          <ul className="mt-2 text-sm">
            {(p.tenders || []).map((t: any) => (
              <li key={t.id} className="border-t border-line py-2">
                <a className="underline" href={t.url} target="_blank" rel="noreferrer">
                  {t.title}
                </a>
                <p className="text-muted">
                  {t.buyer} · open {t.opening}
                </p>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="serif text-xl">Resmî Gazete hits</h3>
          <ul className="mt-2 text-sm">
            {(p.gazette || []).slice(0, 8).map((g: any) => (
              <li key={g.date} className="border-t border-line py-2">
                <a className="underline" href={g.url} target="_blank" rel="noreferrer">
                  {g.date}
                </a>
                <p className="text-muted">{String(g.headlines || '').slice(0, 180)}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>
      <section className="mt-8">
        <h3 className="serif text-xl">RASFF / FDA</h3>
        <ul className="mt-2 text-sm">
          {(quality.data || []).slice(0, 12).map((r: any, i: number) => (
            <li key={i} className="border-t border-line py-2">
              <b>{r.system}</b> {r.date} · {r.origin} · {String(r.subject || '').slice(0, 160)}
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
