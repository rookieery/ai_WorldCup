"use client"

import { useState, useEffect, useCallback } from "react"
import { Trophy, ArrowUpDown, RefreshCw } from "lucide-react"
import { cn } from "@/lib/utils"
import { useTranslation } from "@/lib/i18n"
import { getScorers, type ScorerItem } from "@/lib/api/stats"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

type SortField = "goals" | "assists"
type SortOrder = "asc" | "desc"

export function ScorersTable() {
  const { t } = useTranslation()
  const [scorers, setScorers] = useState<ScorerItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)
  const [sortField, setSortField] = useState<SortField>("goals")
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc")

  const fetchScorers = useCallback(async () => {
    setLoading(true)
    setError(false)
    try {
      const data = await getScorers({ limit: 50 })
      setScorers(data)
    } catch {
      setError(true)
      setScorers([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchScorers()
  }, [fetchScorers])

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder((prev) => (prev === "desc" ? "asc" : "desc"))
    } else {
      setSortField(field)
      setSortOrder("desc")
    }
  }

  const sortedScorers = [...scorers].sort((a, b) => {
    const multiplier = sortOrder === "desc" ? -1 : 1
    const valA = sortField === "goals" ? a.goals : a.assists
    const valB = sortField === "goals" ? b.goals : b.assists
    return (valA - valB) * multiplier
  })

  const rankedScorers = sortedScorers.map((s, idx) => ({
    ...s,
    rank: idx + 1,
  }))

  return (
    <div className="glass-card rounded-2xl border border-glass-border overflow-hidden">
      <div className="px-6 py-4 border-b border-glass-border flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#FFD700]/20 to-[#CCFF00]/20 border border-[#FFD700]/30 flex items-center justify-center">
            <Trophy className="h-4 w-4 text-[#FFD700]" />
          </div>
          <div>
            <h3 className="text-base font-bold text-foreground">{t("stats.scorersTitle")}</h3>
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">
              {t("stats.goldenBoot")}
            </p>
          </div>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-16">
          <span className="text-sm text-muted-foreground animate-pulse">{t("common.loading")}</span>
        </div>
      )}

      {error && !loading && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-14 h-14 rounded-2xl bg-secondary/30 border border-glass-border flex items-center justify-center mb-4">
            <RefreshCw className="h-7 w-7 text-muted-foreground/40" />
          </div>
          <p className="text-muted-foreground text-sm mb-3">{t("stats.errorLoading")}</p>
          <button
            onClick={fetchScorers}
            className="text-xs text-[#00F0FF] hover:underline"
          >
            {t("common.retry")}
          </button>
        </div>
      )}

      {!loading && !error && scorers.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-14 h-14 rounded-2xl bg-secondary/30 border border-glass-border flex items-center justify-center mb-4">
            <Trophy className="h-7 w-7 text-muted-foreground/40" />
          </div>
          <p className="text-muted-foreground text-sm">{t("stats.noData")}</p>
        </div>
      )}

      {!loading && !error && rankedScorers.length > 0 && (
        <Table>
          <TableHeader>
            <TableRow className="border-b border-glass-border hover:bg-transparent">
              <TableHead className="w-16 text-center text-muted-foreground text-xs uppercase tracking-wider">
                {t("stats.rank")}
              </TableHead>
              <TableHead className="text-muted-foreground text-xs uppercase tracking-wider">
                {t("stats.player")}
              </TableHead>
              <TableHead className="text-muted-foreground text-xs uppercase tracking-wider">
                {t("stats.team")}
              </TableHead>
              <TableHead
                className="text-right cursor-pointer select-none text-muted-foreground text-xs uppercase tracking-wider"
                onClick={() => handleSort("goals")}
              >
                <span className="inline-flex items-center gap-1.5">
                  {t("stats.goals")}
                  <ArrowUpDown className={cn("h-3 w-3 transition-colors", sortField === "goals" ? "text-[#CCFF00]" : "text-muted-foreground/50")} />
                </span>
              </TableHead>
              <TableHead
                className="text-right cursor-pointer select-none text-muted-foreground text-xs uppercase tracking-wider"
                onClick={() => handleSort("assists")}
              >
                <span className="inline-flex items-center gap-1.5">
                  {t("stats.assists")}
                  <ArrowUpDown className={cn("h-3 w-3 transition-colors", sortField === "assists" ? "text-[#00F0FF]" : "text-muted-foreground/50")} />
                </span>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rankedScorers.map((scorer) => (
              <ScorerRow key={scorer.player_name + "-" + scorer.team_code} scorer={scorer} />
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  )
}

function ScorerRow({ scorer }: { scorer: ScorerItem }) {
  const isTopThree = scorer.rank <= 3

  return (
    <TableRow
      className={cn(
        "border-b border-glass-border transition-colors",
        isTopThree ? "bg-[#FFD700]/5 hover:bg-[#FFD700]/10" : "hover:bg-secondary/30"
      )}
    >
      <TableCell className="text-center">
        <span
          className={cn(
            "inline-flex items-center justify-center w-8 h-8 rounded-lg text-sm font-bold",
            scorer.rank === 1 && "bg-[#FFD700]/20 text-[#FFD700] border border-[#FFD700]/30",
            scorer.rank === 2 && "bg-muted/50 text-foreground border border-glass-border",
            scorer.rank === 3 && "bg-[#CCFF00]/10 text-[#CCFF00] border border-[#CCFF00]/20",
            scorer.rank > 3 && "text-muted-foreground"
          )}
        >
          {scorer.rank}
        </span>
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-3">
          <span className="font-semibold text-foreground text-sm">{scorer.player_name}</span>
        </div>
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          <span className="text-lg">{scorer.team_flag}</span>
          <span className="text-sm text-muted-foreground">{scorer.team_code}</span>
        </div>
      </TableCell>
      <TableCell className="text-right">
        <span className={cn("font-score text-base font-bold", scorer.goals > 0 ? "text-[#CCFF00]" : "text-muted-foreground/50")}>
          {scorer.goals}
        </span>
      </TableCell>
      <TableCell className="text-right">
        <span className={cn("font-score text-base font-bold", scorer.assists > 0 ? "text-[#00F0FF]" : "text-muted-foreground/50")}>
          {scorer.assists}
        </span>
      </TableCell>
    </TableRow>
  )
}
