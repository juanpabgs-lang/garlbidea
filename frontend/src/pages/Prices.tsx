import { useQuery } from '@tanstack/react-query'
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { getJson } from '../api'
import { fmt } from '../components/Shell'

export function PricesPage() {
  const q = useQuery({ queryKey: ['prices'], queryFn: () => getJson<any>('/api/prices') })
  if (!q.data) return <p className="text-muted">Loading prices…</p>
  const d = q.data.durum || {}
  const shelf = q.data.shelf || []
  return (
    <div>
      <h2 className="serif text-3xl">Prices</h2>
      <p className="mt-2 text-sm text-muted">
        Durum from the EU agri-food weekly. Shelf prices from WFP (CC BY-IGO). Wheat from IMF via FRED.
      </p>
      <div className="mt-6 grid gap-6 md:grid-cols-2">
        <div className="card p-4">
          <p className="text-xs uppercase tracking-wide text-muted">Durum · {d.market}</p>
          <p className="serif text-3xl">€{fmt(d.price_eur_t, 1)}/t</p>
          <p className="text-sm text-muted">{d.as_of}</p>
          <div className="mt-4 h-48">
            <ResponsiveContainer>
              <LineChart data={d.series || []}>
                <XAxis dataKey="date" hide />
                <YAxis domain={['auto', 'auto']} width={40} />
                <Tooltip />
                <Line type="monotone" dataKey="price" stroke="#8c2f1b" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="card p-4">
          <p className="text-xs uppercase tracking-wide text-muted">FX</p>
          <p className="serif text-2xl">EUR/USD {fmt(q.data.fx?.EURUSD, 4)}</p>
          <p className="serif text-2xl">USD/TRY {fmt(q.data.fx?.USDTRY, 2)}</p>
          <p className="mt-2 text-sm text-muted">ECB + open.er-api spot.</p>
        </div>
      </div>
      <h3 className="serif mt-10 text-2xl">WFP retail pasta</h3>
      <div className="mt-3 grid gap-3 md:grid-cols-3">
        {shelf.map((s: any) => (
          <div key={s.market} className="card p-4">
            <p className="text-xs text-muted">{s.as_of}</p>
            <h4 className="serif text-xl">{s.name}</h4>
            <p className="text-2xl">${fmt(s.usd_per_kg, 2)}/kg</p>
          </div>
        ))}
      </div>
    </div>
  )
}
