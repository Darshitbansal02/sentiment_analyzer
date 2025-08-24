"use client"

import { useEffect, useMemo, useState } from "react"
import { Activity, TrendingUp, TrendingDown, Minus } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { fetchCounts, fetchPosts, CountItem, PostItem } from "@/lib/api"

interface DashboardStatsProps {
  selectedHashtag?: string
}

export function DashboardStats({ selectedHashtag }: DashboardStatsProps) {
  const [counts, setCounts] = useState<CountItem[]>([])
  const [posts, setPosts] = useState<PostItem[]>([])

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const [c, p] = await Promise.all([
          fetchCounts(5, selectedHashtag),  // pass hashtag to fetchCounts
          fetchPosts(200, 5, selectedHashtag) // pass hashtag to fetchPosts
        ])
        if (!mounted) return
        setCounts(c)
        setPosts(p)
      } catch {
        if (mounted) { setCounts([]); setPosts([]) }
      }
    }
    load()
    const t = setInterval(load, 4000)
    return () => { mounted = false; clearInterval(t) }
  }, [selectedHashtag])  // re-run when selectedHashtag changes

  const totals = useMemo(() => {
    const total = counts.reduce((a, b) => a + b.count, 0)
    const pos = counts.find(c => c.label === "positive")?.count ?? 0
    const neu = counts.find(c => c.label === "neutral")?.count ?? 0
    const neg = counts.find(c => c.label === "negative")?.count ?? 0
    const sentiment = total ? (pos - neg) / total : 0
    return { total, pos, neu, neg, sentiment }
  }, [counts])

  const tiles = [
    { title: "Total Posts (5m)", value: String(totals.total), icon: Activity, trend: "flat" },
    { title: "Positive", value: String(totals.pos), icon: TrendingUp, trend: "up" },
    { title: "Neutral", value: String(totals.neu), icon: Minus, trend: "flat" },
    { title: "Negative", value: String(totals.neg), icon: TrendingDown, trend: "down" },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {tiles.map((t, i) => {
        const Icon = t.icon as any
        return (
          <Card key={i}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">{t.title}</CardTitle>
            </CardHeader>
            <CardContent className="flex items-center justify-between">
              <div className="text-2xl font-bold">{t.value}</div>
              <Icon className="h-5 w-5 text-muted-foreground" />
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
