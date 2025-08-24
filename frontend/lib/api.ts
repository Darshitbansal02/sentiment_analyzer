export type CountItem = { label: string; count: number }
export type RollingPoint = { ts: string; value: number }
export type PostItem = {
  id: string
  ts: string
  source: string
  author: string | null
  label: string | null
  confidence: number | null
  text: string
}

const API_BASE = (() => {
  const env = (typeof process !== "undefined" ? (process.env as any)?.NEXT_PUBLIC_API_BASE : undefined) as string | undefined
  if (env) return env.replace(/\/$/, "")
  if (typeof window !== "undefined") {
    try {
      const h = window.location.hostname
      if (h === "localhost" || h === "127.0.0.1") return "http://127.0.0.1:8000"
    } catch {}
  }
  return ""
})()

async function safeFetch<T>(path: string): Promise<T> {
  const url = API_BASE ? `${API_BASE}${path}` : path
  const res = await fetch(url, { cache: "no-store" })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return (await res.json()) as T
}

// ✅ Updated functions to accept optional hashtag
export async function fetchCounts(minutes = 5, hashtag?: string): Promise<CountItem[]> {
  try {
    let path = `/api/stats/counts?minutes=${minutes}`
    if (hashtag) path += `&hashtag=${encodeURIComponent(hashtag)}`
    const data = await safeFetch<{ positive: number; neutral: number; negative: number }>(path)
    return [
      { label: "positive", count: data.positive || 0 },
      { label: "neutral", count: data.neutral || 0 },
      { label: "negative", count: data.negative || 0 },
    ]
  } catch (err) {
    console.warn("[api] fetchCounts failed, returning simulated counts", err)
    const pos = Math.floor(Math.random() * 40)
    const neg = Math.floor(Math.random() * 40)
    const neu = Math.floor(Math.random() * 40)
    return [
      { label: "positive", count: pos },
      { label: "neutral", count: neu },
      { label: "negative", count: neg },
    ]
  }
}

export async function fetchRolling(minutes = 5, hashtag?: string): Promise<RollingPoint[]> {
  try {
    let path = `/api/stats/rolling?minutes=${minutes}`
    if (hashtag) path += `&hashtag=${encodeURIComponent(hashtag)}`
    const data = await safeFetch<{ points: { ts: string; value: number }[] }>(path)
    return data.points.map((p) => ({ ts: p.ts, value: p.value }))
  } catch (err) {
    console.warn("[api] fetchRolling failed, returning simulated rolling points", err)
    const now = Date.now()
    const n = Math.max(12, minutes * 4)
    const pts: RollingPoint[] = []
    for (let i = 0; i < n; i++) {
      const ts = new Date(now - (n - i) * (minutes * 60_000 / n)).toISOString()
      pts.push({ ts, value: Math.round((Math.random() * 2 - 1) * 100) / 100 })
    }
    return pts
  }
}

export async function fetchPosts(limit = 50, _minutes = 5, hashtag?: string): Promise<PostItem[]> {
  try {
    let path = `/api/posts?limit=${limit}`
    if (hashtag) path += `&hashtag=${encodeURIComponent(hashtag)}`
    const data = await safeFetch<PostItem[]>(path)
    return data
  } catch (err) {
    console.warn("[api] fetchPosts failed, returning simulated posts", err)
    const examples = [
      "I love how this is coming together!",
      "Not sure — needs more work",
      "Absolutely fantastic result",
      "This is disappointing",
      "Meh. Could be better",
      "Wow — exceeded expectations",
    ]
    const out: PostItem[] = []
    for (let i = 0; i < Math.min(limit, 100); i++) {
      out.push({
        id: `sim-${Date.now()}-${i}`,
        ts: new Date(Date.now() - Math.floor(Math.random() * _minutes * 60_000)).toISOString(),
        source: "simulate",
        author: `user${Math.floor(Math.random() * 10000)}`,
        label: Math.random() > 0.65 ? "positive" : Math.random() > 0.5 ? "neutral" : "negative",
        confidence: Math.round((0.4 + Math.random() * 0.6) * 100) / 100,
        text: examples[Math.floor(Math.random() * examples.length)],
      })
    }
    return out
  }
}
