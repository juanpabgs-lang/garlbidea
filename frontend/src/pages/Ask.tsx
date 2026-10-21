import { useMutation } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { useState } from 'react'
import { postJson, type AskAnswer } from '../api'

const STARTERS = [
  'Who is shipping more pasta into Kenya?',
  'What is the US anti-dumping margin on Garofalo?',
  'What should we do about Hormuz?',
  'Shelf price of spaghetti in Lebanon',
  'Trend of Italian pasta into Saudi Arabia',
]

export function AskPage() {
  const [sp] = useSearchParams()
  const [q, setQ] = useState(sp.get('q') || '')
  const [thread, setThread] = useState<AskAnswer[]>([])
  const mut = useMutation({
    mutationFn: (question: string) => postJson<AskAnswer>('/api/ask', { question }),
    onSuccess: (ans) => setThread((t) => [...t, ans]),
  })

  function send(question: string) {
    const t = question.trim()
    if (!t) return
    mut.mutate(t)
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h2 className="serif text-3xl">Ask the desk</h2>
      <p className="mt-2 text-sm text-muted">
        Answers are computed from the fused snapshot. No model is called unless GARLEB approves a provider.
      </p>
      <form
        className="mt-6 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault()
          send(q)
        }}
      >
        <input
          className="flex-1 border border-line bg-paper px-3 py-2"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Who is shipping pasta into Kenya?"
        />
        <button className="bg-ink px-4 py-2 text-cream" type="submit" disabled={mut.isPending}>
          Ask
        </button>
      </form>
      <div className="mt-3 flex flex-wrap gap-2 text-xs">
        {STARTERS.map((s) => (
          <button key={s} className="border border-line px-2 py-1" onClick={() => { setQ(s); send(s) }}>
            {s}
          </button>
        ))}
      </div>
      <div className="mt-8 space-y-6">
        {thread.map((a, i) => (
          <article key={i} className="card p-5">
            <p className="text-xs uppercase tracking-wide text-muted">{a.intent}</p>
            <p className="serif mt-1 text-xl">{a.question}</p>
            <p className="mt-3 leading-relaxed">{a.text}</p>
            {a.table?.length ? (
              <table className="mt-4 w-full text-left text-sm">
                <thead>
                  <tr className="text-muted">
                    {Object.keys(a.table[0]).slice(0, 6).map((k) => (
                      <th key={k} className="pb-1 font-normal">
                        {k}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {a.table.slice(0, 8).map((row, ri) => (
                    <tr key={ri} className="border-t border-line">
                      {Object.keys(a.table[0]).slice(0, 6).map((k) => (
                        <td key={k} className="py-1.5">
                          {formatCell(row[k])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : null}
            <div className="mt-3 flex flex-wrap gap-2 text-xs">
              {(a.followups || []).map((f) => (
                <button key={f} className="underline" onClick={() => send(f)}>
                  {f}
                </button>
              ))}
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}

function formatCell(v: unknown) {
  if (v == null) return '—'
  if (typeof v === 'number') return v.toLocaleString(undefined, { maximumFractionDigits: 2 })
  if (typeof v === 'object') return JSON.stringify(v).slice(0, 80)
  return String(v)
}
