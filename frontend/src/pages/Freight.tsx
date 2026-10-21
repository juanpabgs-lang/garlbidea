import { useQuery } from '@tanstack/react-query'
import { getJson } from '../api'
import { fmt, pct } from '../components/Shell'

export function FreightPage() {
  const q = useQuery({ queryKey: ['freight'], queryFn: () => getJson<any>('/api/freight') })
  if (!q.data) return <p className="text-muted">Loading freight…</p>
  const lanes = q.data.lanes || []
  const cps = q.data.chokepoints || []
  const ports = q.data.ports || []
  return (
    <div>
      <h2 className="serif text-3xl">Freight & routes</h2>
      <p className="mt-2 text-sm text-muted">
        Lane Stress is an index from PortWatch + CCFI, not a contract rate. Hormuz and Jeddah are the live story.
      </p>
      <svg viewBox="0 0 900 420" className="card mt-6 w-full">
        <rect width="900" height="420" fill="#fffdf8" />
        {lanes.map((l: any, i: number) => {
          const color = l.label === 'disrupted' ? '#8c2f1b' : l.label === 'stressed' ? '#b6894c' : '#2f6b4f'
          const y = 70 + i * 52
          return (
            <g key={l.id}>
              <text x="24" y={y} fontSize="12" fill="#6b6358">
                Napoli
              </text>
              <line x1="70" y1={y - 4} x2="620" y2={y - 4} stroke={color} strokeWidth="3" />
              <text x="630" y={y} fontSize="13" fill="#1c1916">
                {l.dest} · {l.label} · {pct(l.score)}
              </text>
            </g>
          )
        })}
      </svg>
      <div className="mt-8 grid gap-6 md:grid-cols-2">
        <div>
          <h3 className="serif text-xl">Chokepoints</h3>
          <ul className="mt-2 text-sm">
            {cps.map((c: any) => (
              <li key={c.id} className="border-t border-line py-2">
                <b>{c.name}</b> {fmt(c.recent_avg, 1)}/day vs {fmt(c.base_avg, 1)} baseline ({pct(c.drop)} down) · {c.as_of}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="serif text-xl">Ports</h3>
          <ul className="mt-2 text-sm">
            {ports.map((p: any) => (
              <li key={p.id} className="border-t border-line py-2">
                <b>{p.name}</b> box calls {fmt(p.recent_container, 1)} vs {fmt(p.base_container, 1)} ({pct(p.drop)})
              </li>
            ))}
          </ul>
        </div>
      </div>
      <h3 className="serif mt-8 text-xl">SSE CCFI lanes</h3>
      <ul className="mt-2 text-sm">
        {(q.data.freight || []).map((f: any) => (
          <li key={f.lane} className="border-t border-line py-1.5">
            {f.lane} {fmt(f.value, 1)} ({fmt(f.pct, 2)}% wow) · {f.as_of}
          </li>
        ))}
      </ul>
    </div>
  )
}
