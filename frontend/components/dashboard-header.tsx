"use client"

import { useEffect, useState } from "react"
import { Activity, Bell, Settings, ChevronDown } from "lucide-react"
import { ThemeToggle } from "./theme-toggle"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

interface DashboardHeaderProps {
  onHashtagClick?: (hashtag: string) => void
  selectedHashtag?: string
}

export function DashboardHeader({ onHashtagClick, selectedHashtag }: DashboardHeaderProps) {
  const [hashtags, setHashtags] = useState<string[]>([])
  const [openDropdown, setOpenDropdown] = useState(false)

  // Fetch dynamic hashtags every few seconds
  useEffect(() => {
    const fetchHashtags = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/api/hashtags`)
        if (res.ok) {
          const data: string[] = await res.json()
          setHashtags(data.map(tag => tag))
        }
      } catch (err) {
        console.error("Failed to fetch hashtags:", err)
      }
    }

    fetchHashtags()
    const interval = setInterval(fetchHashtags, 5000)
    return () => clearInterval(interval)
  }, [])

  const handleSelect = (tag: string) => {
    onHashtagClick?.(tag)
    setOpenDropdown(false)
  }

  return (
    <header className="sticky top-0 z-50 border-b bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/95">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        {/* Left: Title */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Activity className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">Sentiment Analyzer</h1>
              <p className="text-xs text-muted-foreground hidden sm:block">
                Real-time social media insights
              </p>
            </div>
          </div>

          {/* Hashtag dropdown */}
          <div className="ml-6 relative">
            <Button
              variant="outline"
              onClick={() => setOpenDropdown(!openDropdown)}
              className="flex items-center gap-2"
            >
              {selectedHashtag ? `#${selectedHashtag}` : "Select hashtag"}
              <ChevronDown className="h-4 w-4" />
            </Button>

            {openDropdown && (
              <div className="absolute mt-1 bg-card border rounded shadow-md w-40 z-50">
                {hashtags.map(tag => (
                  <div
                    key={tag}
                    className="px-3 py-2 cursor-pointer hover:bg-primary/10"
                    onClick={() => handleSelect(tag)}
                  >
                    #{tag}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right: Notifications + Theme */}
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="relative">
            <Bell className="h-4 w-4" />
            <div className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full flex items-center justify-center">
              <span className="text-[10px] text-white font-medium">3</span>
            </div>
            <span className="sr-only">Notifications</span>
          </Button>
          <Button variant="ghost" size="icon">
            <Settings className="h-4 w-4" />
            <span className="sr-only">Settings</span>
          </Button>
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
