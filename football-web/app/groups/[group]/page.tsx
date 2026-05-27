"use client"

import { useState, useEffect, useCallback } from "react"
import { useParams } from "next/navigation"
import { I18nProvider } from "@/lib/i18n"
import { useTranslation } from "@/lib/i18n"
import { Header } from "@/components/dashboard/header"
import { getGroupDetail } from "@/lib/api/groups"
import { cn } from "@/lib/utils"
import {
  Trophy,
  ArrowLeft,
  RefreshCw,
  Inbox,
  Clock,
  MapPin,
} from "lucide-react"
import Link from "next/link"
import { TeamFlag } from "@/lib/flags"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

// ── Types ───────────────────────────────────────────────────────────────────

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

interface GroupMatchTeam {
  id: number
  name: string
  name_zh: string
  code: string
  flag: string
  group_label: string
}

interface GroupMatch {
  id: number
  external_id: string
  home_team: GroupMatchTeam
  away_team: GroupMatchTeam
  venue: {
    id: number
    name: string
    city: string
    country: string
    timezone: string
    utc_offset: string
    capacity: number
  }
  stage: string
  group_label: string | null
  round: string
  match_day: number | null
  kickoff_utc: string
  local_time: string | null
  host_time: string | null
  status: string
  home_score: number | null
  away_score: number | null
  is_big_match: boolean
  activity_level: number
}

interface GroupDetailData {
  group_label: string
  standings: GroupStanding[]
  matches: GroupMatch[]
}

// ── Group color helper ──────────────────────────────────────────────────────

const GROUP_COLORS: Record<string, string> = {
  A: "#CCFF00", B: "#00F0FF", C: "#FF00E5", D: "#FFD700",
  E: "#CCFF00", F: "#00F0FF", G: "#FF00E5", H: "#FFD700",
  I: "#CCFF00", J: "#00F0FF", K: "#FF00E5", L: "#FFD700",
}

// ── Group Detail Content ────────────────────────────────────────────────────

function GroupDetailContent() {
  const params = useParams()
  const group = (params?.group as string) ?? ""
  const { t, locale } = useTranslation()
  const color = GROUP_COLORS[group] ?? "#CCFF00"

  const [detail, setDetail] = useState<GroupDetailData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const teamName = (team: { name: string; name_zh: string }) =>
    locale === "zh-CN" ? team.name_zh : team.name

  const fetchDetail = useCallback(async () => {
    if (!group) return
    setLoading(true)
    setError(false)
    try {
      const data = await getGroupDetail(group)
      setDetail(data)
    } catch {
      setError(true)
      setDetail(null)
    } finally {
      setLoading(false)
    }
  }, [group])

  useEffect(() => {
    fetchDetail()
  }, [fetchDetail])

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center py-20">
        <span className="text-sm text-muted-foreground animate-pulse">
          {t("common.loading")}
        </span>
      </div>
    )
  }

  if (error || !detail) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center py-20 text-center">
        <div className="w-16 h-16 rounded-2xl bg-secondary/30 border border-glass-border flex items-center justify-center mb-4">
          <RefreshCw className="h-8 w-8 text-muted-foreground/40" />
        </div>
        <p className="text-muted-foreground text-sm mb-3">
          {t("groups.errorLoading")}
        </p>
        <button
          onClick={fetchDetail}
          className="text-xs text-accent hover:underline"
        >
          {t("common.retry")}
        </button>
      </div>
    )
  }

  return (
    <div className="flex-1 p-6 max-w-5xl mx-auto w-full">
      {/* Back link */}
      <Link
        href="/groups"
        className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mb-6"
      >
        <ArrowLeft className="h-4 w-4" />
        {t("groups.backToGroups")}
      </Link>

      {/* Group title */}
      <div className="flex items-center gap-4 mb-8">
        <div
          className="w-14 h-14 rounded-xl flex items-center justify-center text-xl font-black"
          style={{
            backgroundColor: `${color}15`,
            color: color,
            border: `1px solid ${color}30`,
          }}
        >
          {detail.group_label}
        </div>
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            {t("groups.groupLabel")} {detail.group_label}
          </h1>
          <p className="text-sm text-muted-foreground">
            {detail.standings.length} {t("groups.team").toLowerCase()}s
          </p>
        </div>
      </div>

      {/* Standings table */}
      <div className="glass-card rounded-2xl overflow-hidden border border-glass-border mb-8">
        <div
          className="px-5 py-3 flex items-center gap-2"
          style={{ borderBottom: `1px solid ${color}20` }}
        >
          <Trophy className="h-4 w-4" style={{ color }} />
          <span className="text-sm font-bold text-foreground">
            {t("groups.title")}
          </span>
        </div>
        <Table>
          <TableHeader>
            <TableRow className="border-b border-glass-border hover:bg-transparent">
              <TableHead className="w-10 text-center text-[10px] uppercase tracking-wider text-muted-foreground">
                {t("groups.position")}
              </TableHead>
              <TableHead className="text-[10px] uppercase tracking-wider text-muted-foreground">
                {t("groups.team")}
              </TableHead>
              <TableHead className="w-10 text-center text-[10px] uppercase tracking-wider text-muted-foreground">
                {t("groups.played")}
              </TableHead>
              <TableHead className="w-10 text-center text-[10px] uppercase tracking-wider text-muted-foreground">
                {t("groups.won")}
              </TableHead>
              <TableHead className="w-10 text-center text-[10px] uppercase tracking-wider text-muted-foreground">
                {t("groups.drawn")}
              </TableHead>
              <TableHead className="w-10 text-center text-[10px] uppercase tracking-wider text-muted-foreground">
                {t("groups.lost")}
              </TableHead>
              <TableHead className="w-12 text-center text-[10px] uppercase tracking-wider text-muted-foreground">
                {t("groups.goalsFor")}
              </TableHead>
              <TableHead className="w-12 text-center text-[10px] uppercase tracking-wider text-muted-foreground">
                {t("groups.goalsAgainst")}
              </TableHead>
              <TableHead className="w-12 text-center text-[10px] uppercase tracking-wider text-muted-foreground">
                {t("groups.goalDiff")}
              </TableHead>
              <TableHead className="w-12 text-center text-[10px] uppercase tracking-wider text-muted-foreground font-bold">
                {t("groups.points")}
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {detail.standings.map((row, idx) => {
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
                        "inline-flex items-center justify-center w-6 h-6 rounded text-xs font-bold",
                        isQualified
                          ? "bg-primary/20 text-primary"
                          : "bg-secondary/50 text-muted-foreground",
                      )}
                    >
                      {row.position}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <TeamFlag code={row.team.code} size={24} className="rounded-sm" />
                      <div>
                        <span className="text-sm font-bold text-foreground">
                          {teamName(row.team)}
                        </span>
                        <span className="text-xs text-muted-foreground ml-2">
                          {row.team.code}
                        </span>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="text-center text-sm text-muted-foreground">{row.played}</TableCell>
                  <TableCell className="text-center text-sm text-muted-foreground">{row.won}</TableCell>
                  <TableCell className="text-center text-sm text-muted-foreground">{row.drawn}</TableCell>
                  <TableCell className="text-center text-sm text-muted-foreground">{row.lost}</TableCell>
                  <TableCell className="text-center text-sm text-muted-foreground">{row.goals_for}</TableCell>
                  <TableCell className="text-center text-sm text-muted-foreground">{row.goals_against}</TableCell>
                  <TableCell
                    className={cn(
                      "text-center text-sm font-bold",
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
                    <span className="text-sm font-black" style={{ color }}>
                      {row.points}
                    </span>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
        <div className="px-5 py-2 border-t border-glass-border/50 flex items-center gap-2">
          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
          <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">
            {t("groups.qualified")}
          </span>
          <span className="text-[10px] text-muted-foreground/50">(Top 2)</span>
        </div>
      </div>

      {/* Group matches */}
      <div className="mb-8">
        <h2 className="text-lg font-bold text-foreground mb-4 flex items-center gap-2">
          <Clock className="h-5 w-5 text-accent" />
          {t("groups.groupMatches")}
        </h2>

        {detail.matches.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="w-14 h-14 rounded-2xl bg-secondary/30 border border-glass-border flex items-center justify-center mb-3">
              <Inbox className="h-7 w-7 text-muted-foreground/40" />
            </div>
            <p className="text-muted-foreground text-sm">
              {t("common.noMatches")}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {detail.matches.map((match) => {
              const isLive = match.status === "live"
              const isFinished = match.status === "finished"

              return (
                <div
                  key={match.id}
                  className={cn(
                    "glass-card rounded-xl border p-4 transition-all",
                    isLive
                      ? "border-accent"
                      : isFinished
                        ? "border-glass-border opacity-80"
                        : "border-glass-border hover:border-primary/30",
                  )}
                >
                  {/* Match header */}
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                      {match.round}
                    </span>
                    {isLive && (
                      <span className="flex items-center gap-1 text-[10px] font-bold text-accent">
                        <span className="relative flex h-2 w-2">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75" />
                          <span className="relative inline-flex rounded-full h-2 w-2 bg-accent" />
                        </span>
                        LIVE
                      </span>
                    )}
                    {isFinished && (
                      <span className="text-[10px] font-medium text-muted-foreground">
                        {t("match.ft")}
                      </span>
                    )}
                  </div>

                  {/* Teams & Score */}
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <TeamFlag code={match.home_team.code} size={20} className="rounded-sm" />
                      <span className="text-sm font-medium text-foreground truncate">
                        {teamName(match.home_team)}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 px-2">
                      {(isLive || isFinished) && match.home_score !== null ? (
                        <span className={cn(
                          "font-score text-lg",
                          isLive && "text-accent",
                          isFinished && "text-foreground",
                        )}>
                          {match.home_score} - {match.away_score}
                        </span>
                      ) : (
                        <span className="text-sm font-bold text-muted-foreground/40">
                          {t("match.vs")}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 flex-1 min-w-0 justify-end">
                      <span className="text-sm font-medium text-foreground truncate">
                        {teamName(match.away_team)}
                      </span>
                      <TeamFlag code={match.away_team.code} size={20} className="rounded-sm" />
                    </div>
                  </div>

                  {/* Venue & Time */}
                  <div className="flex items-center justify-between mt-3 pt-3 border-t border-glass-border/50 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1.5">
                      <Clock className="h-3 w-3" />
                      <span>{match.local_time ?? match.kickoff_utc}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <MapPin className="h-3 w-3" />
                      <span className="truncate">{match.venue?.name ?? ""}</span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

// ── Page wrapper with providers ─────────────────────────────────────────────

export default function GroupDetailPage() {
  const [timezone, setTimezone] = useState<"local" | "host">("local")
  const [viewMode, setViewMode] = useState<"timeline" | "bracket">("timeline")

  return (
    <I18nProvider>
      <div className="min-h-screen flex flex-col">
        {/* Background Effects */}
        <div className="fixed inset-0 pointer-events-none overflow-hidden">
          <div
            className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full blur-[120px]"
            style={{
              background: "radial-gradient(circle, rgba(0, 240, 255, 0.15) 0%, transparent 70%)",
            }}
          />
          <div
            className="absolute top-[30%] right-[-5%] w-[500px] h-[500px] rounded-full blur-[100px]"
            style={{
              background: "radial-gradient(circle, rgba(255, 0, 229, 0.12) 0%, transparent 70%)",
            }}
          />
          <div
            className="absolute bottom-[-10%] left-[30%] w-[700px] h-[700px] rounded-full blur-[140px]"
            style={{
              background: "radial-gradient(circle, rgba(204, 255, 0, 0.08) 0%, transparent 70%)",
            }}
          />
        </div>

        <Header
          timezone={timezone}
          viewMode={viewMode}
          onTimezoneChange={setTimezone}
          onViewModeChange={setViewMode}
        />

        <main className="flex-1 flex flex-col min-w-0">
          <GroupDetailContent />
        </main>

        <footer className="h-10 border-t border-glass-border glass-card px-6 flex items-center justify-between text-xs text-muted-foreground relative z-10">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <div className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary" />
              </div>
              <span>48 Teams - 12 Groups - 104 Matches</span>
            </div>
          </div>
          <span className="text-primary font-bold tracking-wide">FIFA World Cup 2026</span>
        </footer>
      </div>
    </I18nProvider>
  )
}