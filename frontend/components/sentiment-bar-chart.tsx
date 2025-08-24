"use client"

import { useEffect, useState } from "react"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Cell } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { fetchCounts } from "@/lib/api"

interface SentimentBarChartProps {
  selectedHashtag?: string
}

export function SentimentBarChart({ selectedHashtag }: SentimentBarChartProps) {
  const [data, setData] = useState<{ label: string; count: number }[]>([])

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const counts = await fetchCounts(5, selectedHashtag)
        if (!mounted) return
        const ordered = ["positive", "neutral", "negative"].map((lbl) => ({
          label: lbl,
          count: counts.find((c) => c.label === lbl)?.count ?? 0,
        }))
        setData(ordered)
      } catch {
        if (mounted) setData([])
      }
    }
    load()
    const interval = setInterval(load, 2000)
    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [selectedHashtag])

  // Assign visually intuitive colors per sentiment
  const getColor = (label: string) => {
    switch (label) {
      case "positive":
        return "#22c55e" // green = positive
      case "neutral":
        return "#facc15" // yellow = neutral
      case "negative":
        return "#ef4444" // red = negative
      default:
        return "#8884d8"
    }
  }

  return (
    <ChartContainer config={{}}>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="label" />
          <YAxis allowDecimals={false} />
          <ChartTooltip content={<ChartTooltipContent />} />

          <Bar dataKey="count" radius={[8, 8, 0, 0]}>
            {data.map((entry) => (
              <Cell key={entry.label} fill={getColor(entry.label)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
