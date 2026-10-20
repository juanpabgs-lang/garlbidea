export async function getJson<T>(path: string): Promise<T> {
  const r = await fetch(path)
  if (!r.ok) throw new Error(`${path} ${r.status}`)
  return r.json()
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error(`${path} ${r.status}`)
  return r.json()
}

export type Insight = {
  id: string
  title: string
  why: string
  action: string
  owner?: string
  timing?: string
  confidence?: number
  score?: number
  sources?: { title?: string; url?: string; as_of?: string }[]
  followups?: string[]
  tags?: string[]
}

export type Brief = {
  as_of: string
  headline: string
  summary: string
  insights: Insight[]
  ticker: { id: string; label: string; value?: number; unit?: string; delta?: number; delta_pct?: number; as_of?: string }[]
  ramadan: Record<string, unknown>
  calendar: { date: string; label: string }[]
}

export type AskAnswer = {
  question: string
  intent: string
  text: string
  table: Record<string, unknown>[]
  chart: Record<string, unknown>[]
  sources: { title?: string; url?: string }[]
  followups: string[]
}
