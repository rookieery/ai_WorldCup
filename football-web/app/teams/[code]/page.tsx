"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import {
  ArrowLeft,
  Trophy,
  Calendar,
  MapPin,
  Globe,
  Award,
} from "lucide-react"
import { Header } from "@/components/dashboard/header"
import { useTranslation } from "@/lib/i18n"
import { getTeamStats, type TeamStatsData } from "@/lib/api/teams"

type TimezoneOption = "local" | "host"
type ViewMode = "timeline" | "bracket"

export default function TeamDetailPage() {
  const params = useParams<{ code: string }>()
  const code = params.code.toUpperCase()
  const { t } = useTranslation()

  const [timezone, setTimezone] = useState<TimezoneOption>("local")
  const [viewMode, setViewMode] = useState<ViewMode>("timeline")
  const [teamData, setTeamData] = useState<TeamStatsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function fetchTeam() {
      try {
        setLoading(true)
        setError(null)
        const data = await getTeamStats(code)
        if (!cancelled) {
          setTeamData(data)
        }
      } catch {
        if (!cancelled) {
          setError(t("teamDetail.errorLoading"))
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    fetchTeam()
    return () => {
      cancelled = true
    }
  }, [code, t])

  const formatDate = (isoString: string) => {
    const date = new Date(isoString)
    return date.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    })
  }

  const formatTime = (isoString: string) => {
    const date = new Date(isoString)
    return date.toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  const stageLabel = (stage: string) => {
    const key = `timeline.stage${stage.charAt(0).toUpperCase() + stage.slice(1)}`
    const label = t(key)
    return label === key ? stage.toUpperCase() : label
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Background Effects */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div
          className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full blur-[120px]"
          style={{
            background:
              "radial-gradient(circle, rgba(0, 240, 255, 0.15) 0%, transparent 70%)",
          }}
        />
        <div
          className="absolute top-[30%] right-[-5%] w-[500px] h-[500px] rounded-full blur-[100px]"
          style={{
            background:
              "radial-gradient(circle, rgba(255, 0, 229, 0.12) 0%, transparent 70%)",
          }}
        />
        <div
          className="absolute bottom-[-10%] left-[30%] w-[700px] h-[700px] rounded-full blur-[140px]"
          style={{
            background:
              "radial-gradient(circle, rgba(204, 255, 0, 0.08) 0%, transparent 70%)",
          }}
        />
      </div>

      <Header
        timezone={timezone}
        viewMode={viewMode}
        onTimezoneChange={setTimezone}
        onViewModeChange={setViewMode}
      />

      <main className="flex-1 flex flex-col min-w-0 p-6 relative z-10">
        {/* Back navigation */}
        <Link
          href="/groups"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-primary transition-colors mb-4 w-fit"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>{t("teamDetail.backToTeams")}</span>
        </Link>

        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="text-muted-foreground">
              {t("common.loading")}
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-center justify-center py-20">
            <div className="glass-card rounded-xl border border-glass-border p-8 text-center">
              <p className="text-destructive mb-4">{error}</p>
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 rounded-lg bg-primary text-primary-foreground font-medium text-sm hover:opacity-90 transition-opacity"
              >
                {t("common.retry")}
              </button>
            </div>
          </div>
        )}

        {!loading && !error && teamData && (
          <div className="space-y-6">
            <TeamHeader team={teamData} t={t} />
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-1">
                <GroupStandingCard team={teamData} t={t} />
              </div>
              <div className="lg:col-span-2 space-y-6">
                <FinishedMatchesCard
                  matches={teamData.finished_matches}
                  teamCode={teamData.code}
                  t={t}
                  formatDate={formatDate}
                  formatTime={formatTime}
                  stageLabel={stageLabel}
                />
                <UpcomingMatchesCard
                  matches={teamData.upcoming_matches}
                  t={t}
                  formatDate={formatDate}
                  formatTime={formatTime}
                  stageLabel={stageLabel}
                />
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
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
        <span className="text-primary font-bold tracking-wide">
          FIFA World Cup 2026
        </span>
      </footer>
    </div>
  )
}

// ── Sub-components ────────────────────────────────────────────────────────────

interface TeamHeaderProps {
  team: TeamStatsData
  t: (key: string) => string
}

function TeamHeader({ team, t }: TeamHeaderProps) {
  return (
    <div className="glass-card rounded-xl border border-glass-border p-6">
      <div className="flex items-center gap-6 flex-wrap">
        <div className="text-5xl">{team.flag}</div>
        <div className="flex-1 min-w-0">
          <h1 className="text-3xl font-bold text-foreground mb-1">
            {team.name}
          </h1>
          <div className="flex items-center gap-4 flex-wrap text-sm text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <Trophy className="h-3.5 w-3.5 text-primary" />
              {t("teamDetail.fifaRanking")} #{team.fifa_ranking}
            </span>
            <span className="flex items-center gap-1.5">
              <Globe className="h-3.5 w-3.5 text-accent" />
              {team.confederation}
            </span>
            <span className="flex items-center gap-1.5">
              <Award className="h-3.5 w-3.5 text-[var(--gold)]" />
              {t("teamDetail.group")} {team.group_label}
            </span>
          </div>
        </div>
        <div className="glass-card rounded-lg border border-glass-border px-4 py-3 text-center">
          <div className="text-2xl font-bold text-primary">
            {team.world_cup_appearances}
          </div>
          <div className="text-xs text-muted-foreground">
            {t("teamDetail.worldCupAppearances")}
          </div>
        </div>
      </div>
    </div>
  )
}

interface GroupStandingCardProps {
  team: TeamStatsData
  t: (key: string) => string
}

function GroupStandingCard({ team, t }: GroupStandingCardProps) {
  const standing = team.standing

  return (
    <div className="glass-card rounded-xl border border-glass-border p-5 h-fit">
      <h2 className="text-lg font-semibold text-foreground mb-4">
        {t("teamDetail.groupStageRecord")}
      </h2>

      {standing ? (
        <div className="space-y-3">
          <div className="glass-card rounded-lg border border-glass-border p-4 text-center">
            <div className="text-3xl font-bold text-primary">
              {standing.points}
            </div>
            <div className="text-xs text-muted-foreground">
              {t("teamDetail.points")}
            </div>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              {t("teamDetail.position")}
            </span>
            <span className="font-semibold text-foreground">
              #{standing.position}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-sm">
            <StatItem label={t("teamDetail.played")} value={standing.played} />
            <StatItem
              label={t("teamDetail.won")}
              value={standing.won}
              color="text-primary"
            />
            <StatItem label={t("teamDetail.drawn")} value={standing.drawn} />
            <StatItem
              label={t("teamDetail.lost")}
              value={standing.lost}
              color="text-destructive"
            />
            <StatItem
              label={t("teamDetail.goalsFor")}
              value={standing.goals_for}
            />
            <StatItem
              label={t("teamDetail.goalsAgainst")}
              value={standing.goals_against}
            />
          </div>

          <div className="flex items-center justify-between text-sm border-t border-glass-border pt-3">
            <span className="text-muted-foreground">
              {t("teamDetail.goalDiff")}
            </span>
            <span
              className={`font-bold ${
                standing.goal_difference >= 0
                  ? "text-primary"
                  : "text-destructive"
              }`}
            >
              {standing.goal_difference >= 0 ? "+" : ""}
              {standing.goal_difference}
            </span>
          </div>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">
          {t("teamDetail.noFinishedMatches")}
        </p>
      )}
    </div>
  )
}

function StatItem({
  label,
  value,
  color,
}: {
  label: string
  value: number
  color?: string
}) {
  return (
    <div className="glass-card rounded-lg border border-glass-border px-3 py-2">
      <div
        className={`text-lg font-semibold ${color ?? "text-foreground"}`}
      >
        {value}
      </div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  )
}

interface FinishedMatchesProps {
  matches: TeamStatsData["finished_matches"]
  teamCode: string
  t: (key: string) => string
  formatDate: (iso: string) => string
  formatTime: (iso: string) => string
  stageLabel: (stage: string) => string
}

function FinishedMatchesCard({
  matches,
  teamCode,
  t,
  formatDate,
  formatTime,
  stageLabel,
}: FinishedMatchesProps) {
  return (
    <div className="glass-card rounded-xl border border-glass-border p-5">
      <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
        <Trophy className="h-4 w-4 text-primary" />
        {t("teamDetail.finishedMatches")}
        <span className="text-sm text-muted-foreground font-normal">
          ({matches.length})
        </span>
      </h2>

      {matches.length === 0 ? (
        <p className="text-sm text-muted-foreground py-4">
          {t("teamDetail.noFinishedMatches")}
        </p>
      ) : (
        <div className="space-y-2">
          {matches.map((match) => (
            <MatchRow
              key={match.id}
              match={match}
              teamCode={teamCode}
              t={t}
              formatDate={formatDate}
              formatTime={formatTime}
              stageLabel={stageLabel}
            />
          ))}
        </div>
      )}
    </div>
  )
}

interface UpcomingMatchesProps {
  matches: TeamStatsData["upcoming_matches"]
  t: (key: string) => string
  formatDate: (iso: string) => string
  formatTime: (iso: string) => string
  stageLabel: (stage: string) => string
}

function UpcomingMatchesCard({
  matches,
  t,
  formatDate,
  formatTime,
  stageLabel,
}: UpcomingMatchesProps) {
  return (
    <div className="glass-card rounded-xl border border-glass-border p-5">
      <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
        <Calendar className="h-4 w-4 text-accent" />
        {t("teamDetail.upcomingMatches")}
        <span className="text-sm text-muted-foreground font-normal">
          ({matches.length})
        </span>
      </h2>

      {matches.length === 0 ? (
        <p className="text-sm text-muted-foreground py-4">
          {t("teamDetail.noUpcomingMatches")}
        </p>
      ) : (
        <div className="space-y-2">
          {matches.map((match) => (
            <UpcomingMatchRow
              key={match.id}
              match={match}
              t={t}
              formatDate={formatDate}
              formatTime={formatTime}
              stageLabel={stageLabel}
            />
          ))}
        </div>
      )}
    </div>
  )
}

interface MatchRowProps {
  match: TeamStatsData["finished_matches"][number]
  teamCode: string
  t: (key: string) => string
  formatDate: (iso: string) => string
  formatTime: (iso: string) => string
  stageLabel: (stage: string) => string
}

function MatchRow({
  match,
  teamCode,
  t,
  formatDate,
  formatTime,
  stageLabel,
}: MatchRowProps) {
  const isWin = (match.score_for ?? 0) > (match.score_against ?? 0)
  const isLoss = (match.score_for ?? 0) < (match.score_against ?? 0)

  return (
    <div className="glass-card rounded-lg border border-glass-border p-3 flex items-center gap-3 hover:border-primary/20 transition-colors">
      <div
        className={`w-1 h-10 rounded-full ${
          isWin
            ? "bg-primary"
            : isLoss
              ? "bg-destructive"
              : "bg-muted-foreground"
        }`}
      />

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 text-sm">
          <span className="text-xs text-muted-foreground uppercase">
            {stageLabel(match.stage)}
          </span>
          <span className="text-xs text-muted-foreground">
            {formatDate(match.kickoff_utc)}
          </span>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-muted-foreground">
            {match.home_away === "home"
              ? t("teamDetail.home")
              : t("teamDetail.away")}
          </span>
          <span className="text-sm font-medium text-foreground">
            {match.opponent_flag} {match.opponent}
          </span>
        </div>
      </div>

      <div className="text-right">
        <div className="flex items-center gap-1">
          <span
            className={`text-lg font-bold ${
              isWin
                ? "text-primary"
                : isLoss
                  ? "text-destructive"
                  : "text-foreground"
            }`}
          >
            {match.score_for ?? 0}
          </span>
          <span className="text-xs text-muted-foreground">-</span>
          <span className="text-lg font-bold text-foreground">
            {match.score_against ?? 0}
          </span>
        </div>
        <span className="text-[10px] text-muted-foreground">
          {t("teamDetail.ft")}
        </span>
      </div>
    </div>
  )
}

interface UpcomingMatchRowProps {
  match: TeamStatsData["upcoming_matches"][number]
  t: (key: string) => string
  formatDate: (iso: string) => string
  formatTime: (iso: string) => string
  stageLabel: (stage: string) => string
}

function UpcomingMatchRow({
  match,
  t,
  formatDate,
  formatTime,
  stageLabel,
}: UpcomingMatchRowProps) {
  return (
    <div className="glass-card rounded-lg border border-glass-border p-3 flex items-center gap-3 hover:border-accent/20 transition-colors">
      <div className="w-1 h-10 rounded-full bg-accent" />

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 text-sm">
          <span className="text-xs text-muted-foreground uppercase">
            {stageLabel(match.stage)}
          </span>
          <span className="text-xs text-muted-foreground">
            {formatDate(match.kickoff_utc)}
          </span>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-muted-foreground">
            {match.home_away === "home"
              ? t("teamDetail.home")
              : t("teamDetail.away")}
          </span>
          <span className="text-sm font-medium text-foreground">
            {match.opponent_flag} {match.opponent}
          </span>
        </div>
      </div>

      <div className="text-right">
        <div className="text-sm font-semibold text-accent">
          {match.host_time ?? formatTime(match.kickoff_utc)}
        </div>
        <div className="flex items-center gap-1 text-[10px] text-muted-foreground justify-end">
          <MapPin className="h-2.5 w-2.5" />
          <span>{match.venue_city}</span>
        </div>
      </div>
    </div>
  )
}