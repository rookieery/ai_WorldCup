"use client"

import { useState, useEffect, useCallback } from "react"
import Link from "next/link"
import { Trophy, RefreshCw, Inbox, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"
import { useTranslation } from "@/lib/i18n"
import { getGroups } from "@/lib/api/groups"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { TeamFlag } from "@/lib/flags"

// ── Types (local, matching API response) ────────────────────────────────────

interface GroupTeam {
  id: number
  name: string
  name_zh: string
  code: string
  flag: string
  group_label: string
}

interface GroupStanding {
  id: number
  team: GroupTeam
  group_label: string
  played: number
  won: number
  drawn: number
  lost: number
  goals_for: number
  goals_against: number
  goal_difference: number
  points: number
  position: number
}

interface GroupOverview {
  group_label: string
  standings: GroupStanding[]
}

// ── Group color mapping (A-L) ──────────────────────────────────────────────

const GROUP_COLORS: Record<string, string> = {
  A: "#CCFF00", B: "#00F0FF", C: "#FF00E5", D: "#FFD700",
  E: "#CCFF00", F: "#00F0FF", G: "#FF00E5", H: "#FFD700",
  I: "#CCFF00", J: "#00F0FF", K: "#FF00E5", L: "#FFD700",
}

// ── Single Group Card ──────────────────────────────────────────────────────

function GroupCard({ group }: { group: GroupOverview }) {
  const { t, locale } = useTranslation()
  const color = GROUP_COLORS[group.group_label] ?? "#CCFF00"
  const teamName = (team: GroupTeam) =>
    locale === "zh-CN" ? team.name_zh : team.name

  return (
    <div className="glass-card rounded-2xl overflow-hidden border border-glass-border hover:border-primary/30 transition-all duration-300">
      {/* Group header */}
      <div
        className="px-4 py-3 flex items-center justify-between"
        style={{
          background: `linear-gradient(135deg, ${color}10 0%, transparent 100%)`,
          borderBottom: `1px solid ${color}20`,
        }}
      >
        <div className="flex items-center gap-2">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-black"
            style={{
              backgroundColor: `${color}15`,
              color: color,
              border: `1px solid ${color}30`,
            }}
          >
            {group.group_label}
          </div>
          <span className="text-sm font-bold text-foreground">
            {t("groups.groupLabel")} {group.group_label}
          </span>
        </div>
        <Link
          href={`/groups/${group.group_label}`}
          className="flex items-center gap-1 text-xs font-medium transition-colors hover:underline"
          style={{ color: color }}
        >
          {t("groups.viewDetail")}
          <ChevronRight className="h-3 w-3" />
        </Link>
      </div>

      {/* Standings table */}
      <Table>
        <TableHeader>
          <TableRow className="border-b border-glass-border hover:bg-transparent">
            <TableHead className="w-8 text-center text-[10px] uppercase tracking-wider text-muted-foreground">
              {t("groups.position")}
            </TableHead>
            <TableHead className="text-[10px] uppercase tracking-wider text-muted-foreground">
              {t("groups.team")}
            </TableHead>
            <TableHead className="w-8 text-center text-[10px] uppercase tracking-wider text-muted-foreground">
              {t("groups.played")}
            </TableHead>
            <TableHead className="w-8 text-center text-[10px] uppercase tracking-wider text-muted-foreground">
              {t("groups.won")}
            </TableHead>
            <TableHead className="w-8 text-center text-[10px] uppercase tracking-wider text-muted-foreground">
              {t("groups.drawn")}
            </TableHead>
            <TableHead className="w-8 text-center text-[10px] uppercase tracking-wider text-muted-foreground">
              {t("groups.lost")}
            </TableHead>
            <TableHead className="w-8 text-center text-[10px] uppercase tracking-wider text-muted-foreground">
              {t("groups.goalDiff")}
            </TableHead>
            <TableHead className="w-10 text-center text-[10px] uppercase tracking-wider text-muted-foreground font-bold">
              {t("groups.points")}
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {group.standings.map((row, idx) => {
            const isQualified = idx < 2
            return (
              <TableRow
                key={row.id}
                className={cn(
                  "border-b border-glass-border/50 transition-colors",
                  isQualified && "bg-primary/5",
                )}
              >
                <TableCell className="text-center text-sm font-medium">
                  <span
                    className={cn(
                      "inline-flex items-center justify-center w-5 h-5 rounded text-[10px] font-bold",
                      isQualified
                        ? "bg-primary/20 text-primary"
                        : "bg-secondary/50 text-muted-foreground",
                    )}
                  >
                    {row.position}
                  </span>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <TeamFlag code={row.team.code} size={18} className="rounded-sm" />
                    <span className="text-sm font-medium text-foreground truncate max-w-[80px]">
                      {teamName(row.team)}
                    </span>
                  </div>
                </TableCell>
                <TableCell className="text-center text-sm text-muted-foreground">
                  {row.played}
                </TableCell>
                <TableCell className="text-center text-sm text-muted-foreground">
                  {row.won}
                </TableCell>
                <TableCell className="text-center text-sm text-muted-foreground">
                  {row.drawn}
                </TableCell>
                <TableCell className="text-center text-sm text-muted-foreground">
                  {row.lost}
                </TableCell>
                <TableCell
                  className={cn(
                    "text-center text-sm font-medium",
                    row.goal_difference > 0
                      ? "text-primary"
                      : row.goal_difference < 0
                        ? "text-destructive"
                        : "text-muted-foreground",
                  )}
                >
                  {row.goal_difference > 0 ? `+${row.goal_difference}` : row.goal_difference}
                </TableCell>
                <TableCell className="text-center">
                  <span className="text-sm font-black" style={{ color: color }}>
                    {row.points}
                  </span>
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>

      {/* Qualified indicator */}
      <div className="px-4 py-2 border-t border-glass-border/50 flex items-center gap-2">
        <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color }} />
        <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">
          {t("groups.qualified")}
        </span>
        <span className="text-[10px] text-muted-foreground/50">(Top 2)</span>
      </div>
    </div>
  )
}

// ── Main GroupStandings Component ──────────────────────────────────────────

export function GroupStandings() {
  const { t } = useTranslation()
  const [groups, setGroups] = useState<GroupOverview[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const fetchGroups = useCallback(async () => {
    setLoading(true)
    setError(false)
    try {
      const data = await getGroups()
      setGroups(data)
    } catch {
      setError(true)
      setGroups([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchGroups()
  }, [fetchGroups])

  return (
    <div className="flex-1 p-6">
      {/* Title */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
            <Trophy className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-foreground">
              {t("groups.title")}
            </h2>
            <p className="text-sm text-muted-foreground">
              {t("groups.subtitle")}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-primary" />
            <span>{t("groups.qualified")} (Top 2)</span>
          </div>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <span className="text-sm text-muted-foreground animate-pulse">
            {t("common.loading")}
          </span>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-16 h-16 rounded-2xl bg-secondary/30 border border-glass-border flex items-center justify-center mb-4">
            <RefreshCw className="h-8 w-8 text-muted-foreground/40" />
          </div>
          <p className="text-muted-foreground text-sm mb-3">
            {t("groups.errorLoading")}
          </p>
          <button
            onClick={fetchGroups}
            className="text-xs text-accent hover:underline"
          >
            {t("common.retry")}
          </button>
        </div>
      )}

      {/* Empty */}
      {!loading && !error && groups.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-16 h-16 rounded-2xl bg-secondary/30 border border-glass-border flex items-center justify-center mb-4">
            <Inbox className="h-8 w-8 text-muted-foreground/40" />
          </div>
          <p className="text-muted-foreground text-sm">
            {t("groups.noGroups")}
          </p>
        </div>
      )}

      {/* Groups grid */}
      {!loading && !error && groups.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-5">
          {groups.map((group) => (
            <GroupCard key={group.group_label} group={group} />
          ))}
        </div>
      )}
    </div>
  )
}