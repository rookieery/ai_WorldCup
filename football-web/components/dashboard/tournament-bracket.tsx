"use client"

import { useState, useEffect, useCallback } from "react"
import { cn } from "@/lib/utils"
import { Trophy, Zap, Loader2, AlertCircle, Medal } from "lucide-react"
import { getBracket } from "@/lib/api/bracket"
import { useTranslation } from "@/lib/i18n"
import { MatchDetailDialog } from "@/components/dashboard/match-detail-dialog"
import { dispatchMatchAnalysis } from "@/components/dashboard/match-detail-helpers"
import type { MatchDetailData } from "@/components/dashboard/match-detail-helpers"
import type {
  BracketMatch,
  BracketTeam,
  BracketRoundName,
  BracketTree,
} from "@/lib/types"
import { TeamFlag } from "@/lib/flags"

// ── Round config ──────────────────────────────────────────────────────────────

const ROUND_COLORS: Record<BracketRoundName, { text: string; bg: string }> = {
  R32: { text: "text-primary", bg: "bg-primary/20" },
  R16: { text: "text-accent", bg: "bg-accent/20" },
  QF: { text: "text-accent", bg: "bg-accent/20" },
  SF: { text: "text-magenta", bg: "bg-magenta/20" },
  "3rd": { text: "text-muted-foreground", bg: "bg-muted" },
  F: { text: "text-gold", bg: "bg-gold/20" },
}

function getRoundLabel(round: BracketRoundName, t: (key: string) => string): string {
  const map: Record<BracketRoundName, string> = {
    R32: t("bracket.roundOf32"),
    R16: t("bracket.roundOf16"),
    QF: t("bracket.quarterFinals"),
    SF: t("bracket.semiFinals"),
    "3rd": t("bracket.thirdPlace"),
    F: t("bracket.final"),
  }
  return map[round]
}

// ── Sub-components ────────────────────────────────────────────────────────────

function TeamRow({ team, isCompleted }: { team: BracketTeam; isCompleted: boolean }) {
  const { t } = useTranslation()

  const isTbd = team.code === "---" || team.code === "TBD"
  const displayName = isTbd
    ? team.fromGroup
      ? t("bracket.fromGroup")
          .replace("{position}", team.fromGroup.replace(/[^1st2nd3rd4th]/g, ""))
          .replace("{group}", team.fromGroup.replace(/[0-9stndrdth]/g, ""))
      : t("bracket.tbd")
    : team.code

  return (
    <div
      className={cn(
        "flex items-center gap-2 py-1.5 px-2 rounded-lg transition-all",
        team.isWinner && isCompleted && "bg-primary/10"
      )}
    >
      <TeamFlag code={team.code} size={18} className="rounded-sm" />
      <span
        className={cn(
          "flex-1 font-medium text-xs truncate",
          team.isWinner && isCompleted ? "text-foreground" : "text-muted-foreground"
        )}
      >
        {displayName}
      </span>
      {team.score !== undefined && (
        <span
          className={cn(
            "font-score text-base w-6 text-center",
            team.isWinner && isCompleted ? "text-gold" : "text-muted-foreground"
          )}
        >
          {team.score}
        </span>
      )}
    </div>
  )
}

function BracketCard({ match, onClick }: { match: BracketMatch; onClick: () => void }) {
  const { t } = useTranslation()
  const isLive = match.status === "live"
  const isCompleted = match.status === "completed"
  const isFinal = match.round === "F"
  const isThirdPlace = match.round === "3rd"
  const colors = ROUND_COLORS[match.round]

  return (
    <div
      className={cn(
        "relative glass-card rounded-xl overflow-hidden transition-all duration-300 w-[170px] cursor-pointer hover:border-primary/30",
        isLive && "border-accent glow-pulse-cyan",
        isFinal && "border-gold/50 glow-pulse-gold",
        isThirdPlace && "border-border"
      )}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") onClick() }}
    >
      {isLive && (
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-accent via-primary to-accent animate-pulse" />
      )}
      {(isFinal || isThirdPlace) && (
        <div className="absolute top-2 right-2">
          {isFinal ? (
            <Trophy className="h-4 w-4 text-gold" />
          ) : (
            <Medal className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      )}

      <div className="p-2.5 space-y-1.5">
        <div className="flex items-center justify-between">
          <span className={cn("text-[9px] font-bold tracking-wider px-1.5 py-0.5 rounded-full", colors.bg, colors.text)}>
            {getRoundLabel(match.round, t)}
          </span>
          {isLive && (
            <span className="flex items-center gap-1 text-[9px] text-accent">
              <Zap className="h-3 w-3" />
              LIVE
            </span>
          )}
        </div>

        <TeamRow team={match.team1} isCompleted={isCompleted} />

        <div className="flex items-center gap-1.5">
          <div className="flex-1 h-px bg-glass-border" />
          <span className="text-[9px] text-muted-foreground font-medium">{t("bracket.vs")}</span>
          <div className="flex-1 h-px bg-glass-border" />
        </div>

        <TeamRow team={match.team2} isCompleted={isCompleted} />

        {match.venue && (
          <div className="pt-1.5 border-t border-glass-border">
            <p className="text-[9px] text-muted-foreground truncate">{match.venue}</p>
            <p className="text-[9px] text-muted-foreground/70">{match.time}</p>
          </div>
        )}
      </div>
    </div>
  )
}

// ── SVG Connector between rounds ─────────────────────────────────────────────

function RoundConnector({
  matchCount,
  isActive,
  connId,
}: {
  matchCount: number
  isActive: boolean
  connId: string
}) {
  const cardHeight = 120
  const gap = 16
  const totalHeight = matchCount * 2 * (cardHeight + gap)
  const halfCard = cardHeight / 2

  return (
    <svg width="50" height={totalHeight} className="overflow-visible flex-shrink-0">
      <defs>
        <linearGradient id={"conn-" + connId} x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="var(--accent)" stopOpacity={isActive ? 0.8 : 0.3} />
          <stop offset="100%" stopColor="var(--magenta)" stopOpacity={isActive ? 0.8 : 0.3} />
        </linearGradient>
      </defs>
      {Array.from({ length: matchCount }, (_, i) => {
        const blockHeight = 2 * (cardHeight + gap)
        const y1Top = i * blockHeight + halfCard
        const y1Bot = i * blockHeight + cardHeight + gap + halfCard
        const yMid = i * blockHeight + cardHeight + gap / 2
        return (
          <g key={i}>
            <path
              d={"M 0 " + y1Top + " H 25 V " + yMid + " H 50"}
              fill="none"
              stroke={"url(#conn-" + connId + ")"}
              strokeWidth={isActive ? 2 : 1.5}
              opacity={isActive ? 0.9 : 0.4}
              className={isActive ? "animate-pulse" : ""}
            />
            <path
              d={"M 0 " + y1Bot + " H 25 V " + yMid + " H 50"}
              fill="none"
              stroke={"url(#conn-" + connId + ")"}
              strokeWidth={isActive ? 2 : 1.5}
              opacity={isActive ? 0.9 : 0.4}
              className={isActive ? "animate-pulse" : ""}
            />
          </g>
        )
      })}
    </svg>
  )
}

// ── Desktop Bracket (horizontal scroll) ──────────────────────────────────────

function DesktopBracket({ data, onMatchClick }: { data: BracketTree; onMatchClick: (matchId: number) => void }) {
  const { t } = useTranslation()

  const mainRounds = data.rounds.filter((r) => r.round !== "3rd" && r.round !== "F")
  const finalRound = data.rounds.find((r) => r.round === "F")
  const thirdPlaceRound = data.rounds.find((r) => r.round === "3rd")
  const sfRound = data.rounds.find((r) => r.round === "SF")
  const hasLive = data.rounds.some((r) => r.matches.some((m) => m.status === "live"))

  return (
    <div className="overflow-x-auto scrollbar-hide h-full">
      <div className="flex items-center min-w-max px-4 h-full">
        {mainRounds.map((round, idx) => {
          const nextRound = mainRounds[idx + 1]
          const isRoundActive = round.matches.some((m) => m.status === "live")
          const colors = ROUND_COLORS[round.round]
          return (
            <div key={round.round} className="flex items-center">
              <div className="flex flex-col items-center">
                <div className={cn("text-[10px] font-bold tracking-wider mb-3", colors.text)}>
                  {getRoundLabel(round.round, t)}
                </div>
                <div className="flex flex-col gap-3">
                  {round.matches.map((match) => (
                    <BracketCard key={match.id} match={match} onClick={() => onMatchClick(parseInt(match.id, 10))} />
                  ))}
                </div>
              </div>
              {nextRound && (
                <RoundConnector
                  matchCount={nextRound.matches.length}
                  isActive={isRoundActive || hasLive}
                  connId={round.round}
                />
              )}
            </div>
          )
        })}

        {/* SF -> Final connector + Final */}
        {finalRound && sfRound && (
          <div className="flex items-center">
            <RoundConnector
              matchCount={1}
              isActive={sfRound.matches.some((m) => m.status !== "upcoming")}
              connId="sf-to-f"
            />
            <div className="flex flex-col items-center">
              <div className="text-[10px] font-bold tracking-wider mb-3 text-gold">
                {getRoundLabel("F", t)}
              </div>
              <div className="relative">
                <div className="absolute -top-7 left-1/2 -translate-x-1/2">
                  <div className="relative">
                    <Trophy className="h-7 w-7 text-gold" />
                    <div className="absolute inset-0 blur-xl bg-gold/30" />
                  </div>
                </div>
                {finalRound.matches.map((match) => (
                  <BracketCard key={match.id} match={match} onClick={() => onMatchClick(parseInt(match.id, 10))} />
                ))}
              </div>
            </div>
          </div>
        )}

        {/* 3rd Place branch */}
        {thirdPlaceRound && (
          <div className="flex items-center ml-6">
            <RoundConnector
              matchCount={1}
              isActive={sfRound ? sfRound.matches.some((m) => m.status === "completed") : false}
              connId="sf-to-3rd"
            />
            <div className="flex flex-col items-center">
              <div className="text-[10px] font-bold tracking-wider mb-3 text-muted-foreground">
                {getRoundLabel("3rd", t)}
              </div>
              {thirdPlaceRound.matches.map((match) => (
                <BracketCard key={match.id} match={match} onClick={() => onMatchClick(parseInt(match.id, 10))} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Mobile Bracket (vertical stack) ──────────────────────────────────────────

function MobileBracket({ data, onMatchClick }: { data: BracketTree; onMatchClick: (matchId: number) => void }) {
  const { t } = useTranslation()

  return (
    <div className="flex flex-col gap-6 px-4">
      {data.rounds.map((round) => {
        const colors = ROUND_COLORS[round.round]
        return (
          <div key={round.round} className="flex flex-col items-center">
            <div className={cn("text-[10px] font-bold tracking-wider mb-3", colors.text)}>
              {getRoundLabel(round.round, t)}
            </div>
            <div className="flex flex-wrap justify-center gap-3">
              {round.matches.map((match) => (
                <BracketCard key={match.id} match={match} onClick={() => onMatchClick(parseInt(match.id, 10))} />
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ── Main exported component ──────────────────────────────────────────────────

export function TournamentBracket() {
  const { t } = useTranslation()
  const [data, setData] = useState<BracketTree | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [detailMatchId, setDetailMatchId] = useState<number | null>(null)
  const [detailOpen, setDetailOpen] = useState(false)

  const handleAnalyzeMatch = useCallback(
    (matchData: MatchDetailData, skillId: string) => {
      dispatchMatchAnalysis(matchData, skillId, () => setDetailOpen(false))
    },
    [],
  )

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const bracketTree = await getBracket()
      setData(bracketTree)
    } catch {
      setError(t("bracket.errorLoading"))
    } finally {
      setLoading(false)
    }
  }, [t])

  useEffect(() => {
    void fetchData()
  }, [fetchData])

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 text-accent animate-spin" />
          <span className="text-sm text-muted-foreground">{t("common.loading")}</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="flex flex-col items-center gap-4 text-center">
          <AlertCircle className="h-8 w-8 text-destructive" />
          <p className="text-sm text-muted-foreground">{error}</p>
          <button
            onClick={() => { setError(null); void fetchData() }}
            className="px-4 py-2 rounded-lg bg-accent/20 text-accent text-sm font-medium hover:bg-accent/30 transition-colors"
          >
            {t("common.retry")}
          </button>
        </div>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="text-center py-6 px-4 flex-shrink-0">
        <h2 className="text-xl font-bold text-foreground flex items-center justify-center gap-2">
          <Trophy className="h-5 w-5 text-gold" />
          <span className="bg-gradient-to-r from-primary via-accent to-magenta bg-clip-text text-transparent">
            {t("bracket.knockoutStage")}
          </span>
          <Trophy className="h-5 w-5 text-gold" />
        </h2>
        <p className="text-xs text-muted-foreground mt-1">{t("bracket.roadToGlory")}</p>
      </div>

      {/* Desktop bracket */}
      <div className="flex-1 overflow-hidden hidden md:block">
        <DesktopBracket data={data} onMatchClick={(id) => { setDetailMatchId(id); setDetailOpen(true) }} />
      </div>

      {/* Mobile bracket */}
      <div className="flex-1 overflow-y-auto md:hidden">
        <MobileBracket data={data} onMatchClick={(id) => { setDetailMatchId(id); setDetailOpen(true) }} />
      </div>

      {/* Legend */}
      <div className="flex-shrink-0 py-4 px-6 flex justify-center gap-4 text-[10px] text-muted-foreground border-t border-glass-border">
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded bg-accent/30 border border-accent" />
          <span>{t("bracket.liveMatch")}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded bg-primary/30 border border-primary" />
          <span>{t("bracket.winnerAdvances")}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-0.5 bg-gradient-to-r from-accent to-magenta" />
          <span>{t("bracket.advancementPath")}</span>
        </div>
      </div>

      <MatchDetailDialog
        matchId={detailMatchId}
        open={detailOpen}
        onOpenChange={setDetailOpen}
        onAnalyzeMatch={handleAnalyzeMatch}
      />
    </div>
  )
}
