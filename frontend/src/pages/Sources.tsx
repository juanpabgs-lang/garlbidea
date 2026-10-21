import { useQuery } from '@tanstack/react-query'
import { getJson } from '../api'

export function SourcesPage() {
  const q = useQuery({ queryKey: ['sources'], queryFn: () => getJson<any>('/api/sources') })
  if (!q.data) return <p className="text-muted">Loading sources…</p>
  const sources = Object.values(q.data.manifest?.sources || {}) as any[]
  const slots = q.data.slots || []
  return (
    <div>
      <h2 className="serif text-3xl">Sources & trust</h2>
      <p className="mt-2 max-w-2xl text-sm text-muted">
        NDA: GARLEB must approve providers before we call them. This build uses only public government and agency feeds.
        Snapshot built {q.data.manifest?.built_at || 'not yet'}.
      </p>
      <h3 className="serif mt-8 text-xl">Live and attempted</h3>
      <table className="mt-3 w-full text-left text-sm">
        <thead>
          <tr className="text-muted">
            <th className="font-normal">Source</th>
            <th>Status</th>
            <th>Rows</th>
            <th>As of</th>
            <th>License</th>
          </tr>
        </thead>
        <tbody>
          {sources.map((s) => (
            <tr key={s.name} className="border-t border-line align-top">
              <td className="py-1.5">
                <div>{s.name}</div>
                <div className="text-xs text-muted">{s.notes}</div>
                {s.error ? <div className="text-xs text-rust">{s.error}</div> : null}
              </td>
              <td>{s.status}</td>
              <td>{s.rows}</td>
              <td>{s.as_of || '—'}</td>
              <td className="text-xs">{s.license}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h3 className="serif mt-10 text-xl">Slots</h3>
      <ul className="mt-2 text-sm">
        {slots.map((s: any) => (
          <li key={s.name} className="border-t border-line py-2">
            <b>{s.name}</b> · {s.kind} · {s.reason}
          </li>
        ))}
      </ul>
      <h3 className="serif mt-10 text-xl">Shipments</h3>
      <pre className="card mt-2 overflow-auto p-3 text-xs">{JSON.stringify(q.data.shipments, null, 2)}</pre>
    </div>
  )
}
