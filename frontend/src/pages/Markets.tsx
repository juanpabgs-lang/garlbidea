import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getJson } from '../api'
import { fmt, pct } from '../components/Shell'

type Market = {
  market: string
  name: string
  period?: string
  origins: { origin: string; origin_name: string; share?: number; tonnes?: number; unit?: number; src?: string }[]
  italy_share?: number
  turkey_share?: number
}

export function MarketsPage() {
  const { code } = useParams()
  const nav = useNavigate()
  const list = useQuery({ queryKey: ['markets'], queryFn: () => getJson<Market[]>('/api/markets') })
  const detail = useQuery({
    queryKey: ['market', code],
    queryFn: () => getJson<any>(`/api/markets/${code}`),
    enabled: !!code,
  })
  const markets = list.data || []

  return (
    <div>
      <h2 className="serif text-3xl">Markets & competitors</h2>
      <p className="mt-2 max-w-2xl text-sm text-muted">
        Share nowcast reconciles Comext, Comtrade (including mirrors), GASTAT monthly and the TİM cereals-sector proxy.
        Confidence is on every row.
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        {markets.map((m) => (
          <button
            key={m.market}
            onClick={() => nav(`/markets/${m.market}`)}
            className={`border px-2 py-1 text-sm ${code === m.market ? 'border-ink bg-ink text-cream' : 'border-line'}`}
          >
            {m.name}
          </button>
        ))}
      </div>

      {!code ? (
        <div className="mt-6 grid gap-3 md:grid-cols-2">
          {markets.map((m) => (
            <Link key={m.market} to={`/markets/${m.market}`} className="card p-4">
              <p className="text-xs text-muted">{m.period || 'no print'}</p>
              <h3 className="serif text-2xl">{m.name}</h3>
              <p className="mt-2 text-sm">
                Italy {pct(m.italy_share)} · Turkey {pct(m.turkey_share)}
              </p>
              <p className="mt-1 text-sm text-muted">
                {(m.origins || [])
                  .slice(0, 3)
                  .map((o) => `${o.origin_name} ${pct(o.share)}`)
                  .join(' · ')}
              </p>
            </Link>
          ))}
        </div>
      ) : detail.data ? (
        <MarketDetail data={detail.data} />
      ) : (
        <p className="mt-6 text-muted">Loading {code}…</p>
      )}
    </div>
  )
}

function MarketDetail({ data }: { data: any }) {
  const b = data.brief || {}
  const italy = data.italy || []
  const landed = data.landed || {}
  return (
    <div className="mt-6">
      <h3 className="serif text-3xl">{b.name}</h3>
      <p className="text-sm text-muted">Nowcast period {b.period}</p>
      <table className="mt-4 w-full text-left text-sm">
        <thead>
          <tr className="text-muted">
            <th className="font-normal">Origin</th>
            <th>Share</th>
            <th>Tonnes</th>
            <th>Unit</th>
            <th>Source</th>
          </tr>
        </thead>
        <tbody>
          {(b.origins || []).map((o: any) => (
            <tr key={o.origin} className="border-t border-line">
              <td className="py-1.5">{o.origin_name}</td>
              <td>{pct(o.share)}</td>
              <td>{fmt(o.tonnes, 0)}</td>
              <td>{fmt(o.unit, 0)}</td>
              <td className="text-muted">{o.src}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {italy.length ? (
        <div className="mt-6">
          <h4 className="serif text-xl">Italy monthly (Comext)</h4>
          <p className="mt-2 text-sm text-muted">
            {italy
              .slice(-8)
              .map((r: any) => `${r.period} ${fmt(r.tonnes, 0)}t`)
              .join(' · ')}
          </p>
        </div>
      ) : null}
      {landed.ladder?.length ? (
        <div className="mt-6">
          <h4 className="serif text-xl">Landed-cost ladder (proxy)</h4>
          <p className="text-xs text-muted">{landed.note}</p>
          <ul className="mt-2 text-sm">
            {landed.ladder.map((r: any) => (
              <li key={r.origin}>
                {r.origin} FOB {fmt(r.fob_usd_t, 0)} + freight {fmt(r.freight_proxy, 0)} → landed $
                {fmt(r.landed_usd_t, 0)}/t
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  )
}
