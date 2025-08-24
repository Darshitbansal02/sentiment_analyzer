"use client"

import { useEffect, useState } from "react"
import { Line, LineChart, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { fetchRolling, RollingPoint } from "@/lib/api"

interface SentimentLineChartProps {
  selectedHashtag?: string
}

export function SentimentLineChart({ selectedHashtag }: SentimentLineChartProps) {
  const [data, setData] = useState<{ time: string; sentiment: number }[]>([])

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const points: RollingPoint[] = await fetchRolling(5, selectedHashtag) // pass hashtag
        if (!mounted) return
        const rows = points.map(p => ({
          time: new Date(p.ts).toLocaleTimeString(),
          sentiment: Number.isFinite(p.value) ? p.value : 0,
        }))
        setData(rows)
      } catch {
        if (mounted) setData([])
      }
    }
    load()
    const t = setInterval(load, 2000)
    return () => { mounted = false; clearInterval(t) }
  }, [selectedHashtag]) // re-run when hashtag changes

  return (
    <ChartContainer config={{}}>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis domain={[-1, 1]} />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Line type="monotone" dataKey="sentiment" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
