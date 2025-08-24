"use client"

import { useEffect, useState } from "react"
import { fetchPosts, PostItem } from "@/lib/api"

interface PostsDataTableProps {
  selectedHashtag?: string
}

export function PostsDataTable({ selectedHashtag }: PostsDataTableProps) {
  const [rows, setRows] = useState<PostItem[]>([])

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const data = await fetchPosts(50, 5, selectedHashtag) // pass hashtag
        if (mounted) setRows(data)
      } catch {
        if (mounted) setRows([])
      }
    }
    load()
    const t = setInterval(load, 2000)
    return () => { mounted = false; clearInterval(t) }
  }, [selectedHashtag]) // refetch when hashtag changes

  const getRowBg = (label?: string | null) => {
    switch (label) {
      case "positive": return "bg-green-50 dark:bg-green-950"
      case "neutral":  return "bg-gray-50 dark:bg-gray-950"
      case "negative": return "bg-red-50 dark:bg-red-950"
      default:         return ""
    }
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left">
            <th className="p-2">Time</th>
            <th className="p-2">Source</th>
            <th className="p-2">Author</th>
            <th className="p-2">Label</th>
            <th className="p-2">Conf</th>
            <th className="p-2">Text</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(r => (
            <tr key={r.id} className={`${getRowBg(r.label)} border-b border-border`}>
              <td className="p-2">{new Date(r.ts).toLocaleString()}</td>
              <td className="p-2">{r.source}</td>
              <td className="p-2">{r.author || "-"}</td>
              <td className="p-2 capitalize">{r.label || "-"}</td>
              <td className="p-2">{r.confidence != null ? r.confidence.toFixed(2) : "-"}</td>
              <td className="p-2">{r.text}</td>
            </tr>
          ))}
          {rows.length === 0 && (
            <tr><td className="p-4 text-muted-foreground" colSpan={6}>Waiting for data…</td></tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
