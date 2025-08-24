"use client"

import { useState, useEffect } from "react"
import { DashboardHeader } from "@/components/dashboard-header"
import { DashboardStats } from "@/components/dashboard-stats"
import { SentimentLineChart } from "@/components/sentiment-line-chart"
import { SentimentBarChart } from "@/components/sentiment-bar-chart"
import { PostsDataTable } from "@/components/posts-data-table"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue, SelectGroup, SelectLabel } from "@/components/ui/select"

export default function DashboardPage() {
  const [dynamicHashtags, setDynamicHashtags] = useState<string[]>([])
  const [allHashtags, setAllHashtags] = useState<string[]>([])
  const [selectedHashtag, setSelectedHashtag] = useState<string | null>(null)

  // Fetch dynamic hashtags
  useEffect(() => {
    const fetchDynamic = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/api/hashtags`)
        if (res.ok) {
          const data: string[] = await res.json()
          setDynamicHashtags(data)
          if (!selectedHashtag && data.length > 0) setSelectedHashtag(data[0])
        }
      } catch (err) {
        console.error("Failed to fetch dynamic hashtags:", err)
      }
    }
    fetchDynamic()
    const interval = setInterval(fetchDynamic, 5000)
    return () => clearInterval(interval)
  }, [selectedHashtag])

  // Fetch historical/all hashtags (from model or backend endpoint)
  useEffect(() => {
    const fetchAll = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/api/hashtags-all`)
        if (res.ok) {
          const data: string[] = await res.json()
          setAllHashtags(data)
        }
      } catch (err) {
        console.error("Failed to fetch all hashtags:", err)
      }
    }
    fetchAll()
  }, [])

  if (!selectedHashtag) return <div>Loading hashtags...</div>

  return (
    <div className="min-h-screen bg-background">
      <DashboardHeader
        selectedHashtag={selectedHashtag}
        onHashtagClick={(tag) => setSelectedHashtag(tag)}
      />

      <main className="container mx-auto px-4 py-6 space-y-6">

        {/* Stats */}
        <DashboardStats selectedHashtag={selectedHashtag} />

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-card rounded-lg border shadow-sm transition-all hover:shadow-md">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Sentiment Over Time</h2>
                <div className="text-sm text-muted-foreground">Rolling 2-hour average</div>
              </div>
              <SentimentLineChart selectedHashtag={selectedHashtag} />
            </div>
          </div>
          <div className="bg-card rounded-lg border shadow-sm transition-all hover:shadow-md">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Sentiment Distribution</h2>
                <div className="text-sm text-muted-foreground">Last 24 hours</div>
              </div>
              <SentimentBarChart selectedHashtag={selectedHashtag} />
            </div>
          </div>
        </div>

        {/* Table Section */}
        <div className="bg-card rounded-lg border shadow-sm transition-all hover:shadow-md">
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold">Recent Posts</h2>
              <div className="text-sm text-muted-foreground">Real-time social media mentions</div>
            </div>
            <PostsDataTable selectedHashtag={selectedHashtag} />
          </div>
        </div>
      </main>
    </div>
  )
}
