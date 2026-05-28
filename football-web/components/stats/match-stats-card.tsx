"use client"

import { useState, useEffect, useCallback } from "react"
import { BarChart3, RefreshCw } from "lucide-react"
import { cn } from "@/lib/utils"
import { useTranslation } from "@/lib/i18n"
import { getMatches } from "@/lib/api/matches"

interface MatchStatGroup {
  label: string
  count: number
  color: string
}

export function MatchStatsCard() {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)
  const [totalMatches, setTotalMatches] = useState(0)
  const [statGroups, setStatGroups] = useState<MatchStatGroup[]>([])

  const fetchStats = useCallback(async () => {
    setLoading(true)
    setError(false)
    try {
      const [upcoming, live, finished] = await Promise.all([
        getMatches({ status: "upcoming", pageSize: 1 }),
        getMatches({ status: "live", pageSize: 1 }),
        getMatches({ status: "finished", pageSize: 1 }),
      ])

      const total = upcoming.total + live.total + finished.total
      setTotalMatches(total)
      setStatGroups([
        { label: t("match.upcoming"), count: upcoming.total, color: "bg-[#CCFF00]" },
        { label: t("match.live"), count: live.total, color: "bg-[#00F0FF]" },
        { label: t("match.finished"), count: finished.total, color: "bg-muted-foreground/50" },
      ])
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }, [t])

  useEffect(() => {
    fetchStats()
  }, [fetchStats])

  return (
    <div className="glass-card rounded-2xl border border-glass-border overflow-hidden">
      <div className="px-6 py-4 border-b border-glass-border flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#00F0FF]/20 to-[#FF00E5]/20 border border-[#00F0FF]/30 flex items-center justify-center">
          <BarChart3 className="h-4 w-4 text-[#00F0FF]" />
        </div>
        <div>
          <h3 className="text-base font-bold text-foreground">{t("stats.matchStats")}</h3>
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider">
            {totalMatches} {t("match.title")}
          </p>
        </div>
      </div>

      <div className="p-6">
        {loading && (
          <div className="flex items-center justify-center py-8">
            <span className="text-sm text-muted-foreground animate-pulse">{t("common.loading")}</span>
          </div>
        )}

        {error && !loading && (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <RefreshCw className="h-6 w-6 text-muted-foreground/40 mb-3" />
            <p className="text-muted-foreground text-sm mb-2">{t("stats.errorLoading")}</p>
            <button onClick={fetchStats} className="text-xs text-[#00F0FF] hover:underline">
              {t("common.retry")}
            </button>
          </div>
        )}

        {!loading && !error && statGroups.length > 0 && (
          <div className="space-y-4">
            {statGroups.map((group) => {
              const percentage = totalMatches > 0 ? (group.count / totalMatches) * 100 : 0
              return (
                <div key={group.label}>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-sm text-foreground font-medium">{group.label}</span>
                    <span className="text-sm font-score font-bold text-foreground">{group.count}</span>
                  </div>
                  <div className="h-2 bg-secondary/50 rounded-full overflow-hidden">
                    <div
                      className={cn("h-full rounded-full transition-all duration-500", group.color)}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              )
            })}

            {/* Total bar */}
            <div className="pt-3 border-t border-glass-border">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground font-medium">{t("stats.total")}</span>
                <span className="text-lg font-score font-bold text-[#FFD700]">{totalMatches}</span>
              </div>
            </div>
          </div>
        )}

        {!loading && !error && statGroups.length === 0 && (
          <div className="flex items-center justify-center py-8">
            <p className="text-muted-foreground text-sm">{t("stats.noData")}</p>
          </div>
        )}
      </div>
    </div>
  )
}

