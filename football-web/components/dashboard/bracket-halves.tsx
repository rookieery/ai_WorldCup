"use client"

import { cn } from "@/lib/utils"
import { useTranslation } from "@/lib/i18n"
import type { BracketMatch, BracketRoundName } from "@/lib/types"
import { Trophy, Medal } from "lucide-react"

// ── Half-ordering constants ─────────────────────────────────────────────────
//
// Derived from BRACKET_LINKS in generate_bracket.py.
// Matches within each half are ordered so that adjacent pairs
// feed into the next round's match (matches[0]+matches[1] → nextMatch[0], etc.)

const UPPER_HALF: Record<BracketRoundName, string[]> = {
  R32: ["R32_03", "R32_06", "R32_01", "R32_04", "R32_12", "R32_11", "R32_10", "R32_09"],
  R16: ["R16_01", "R16_02", "R16_05", "R16_06"],
  QF: ["QF_01", "QF_02"],
  SF: ["SF_01"],
  "3rd": [],
  F: [],
}

const LOWER_HALF: Record<BracketRoundName, string[]> = {
  R32: ["R32_02", "R32_05", "R32_07", "R32_08", "R32_15", "R32_14", "R32_13", "R32_16"],
  R16: ["R16_03", "R16_04", "R16_07", "R16_08"],
  QF: ["QF_03", "QF_04"],
  SF: ["SF_02"],
  "3rd": [],
  F: [],
}

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

// ── Helper: split a round's matches into upper/lower halves ─────────────────

export function splitByHalf(
  matches: BracketMatch[],
  round: BracketRoundName,
): { upper: BracketMatch[]; lower: BracketMatch[] } {
  const byExtId = new Map(matches.map((m) => [m.externalId, m]))

  const upper = UPPER_HALF[round]
    .map((extId) => byExtId.get(extId))
    .filter((m): m is BracketMatch => m !== undefined)

  const lower = LOWER_HALF[round]
    .map((extId) => byExtId.get(extId))
    .filter((m): m is BracketMatch => m !== undefined)

  return { upper, lower }
}

// ── HalfDivider ──────────────────────────────────────────────────────────────

export function HalfDivider() {
  const { t } = useTranslation()

  return (
    <div className="flex items-center gap-3 py-2">
      <div className="flex-1 h-px bg-gradient-to-r from-transparent via-muted-foreground/30 to-muted-foreground/15" />
      <span className="text-[10px] font-bold tracking-[0.2em] text-muted-foreground/60 uppercase select-none">
        {t("bracket.upperHalfShort")} / {t("bracket.lowerHalfShort")}
      </span>
      <div className="flex-1 h-px bg-gradient-to-l from-transparent via-muted-foreground/30 to-muted-foreground/15" />
    </div>
  )
}

// ── HalfBracket (one horizontal row: R32→R16→QF→SF) ─────────────────────────

interface HalfBracketProps {
  label: string
  halfRounds: { round: BracketRoundName; matches: BracketMatch[] }[]
  hasLive: boolean
  onMatchClick: (matchId: number) => void
}

export function HalfBracket({
  label,
  halfRounds,
  hasLive,
  onMatchClick,
}: HalfBracketProps) {
  const { t } = useTranslation()

  return (
    <div className="flex items-center min-w-max">
      {/* Vertical half label */}
      <div className="flex-shrink-0 w-8 flex items-center justify-center">
        <span
          className={cn(
            "text-[9px] font-bold tracking-wider select-none",
            "text-muted-foreground/50",
            "[writing-mode:vertical-lr] [text-orientation:mixed] rotate-180",
          )}
        >
          {label}
        </span>
      </div>

      {halfRounds.map((round, idx) => {
        const nextRound = halfRounds[idx + 1]
        const isRoundActive = round.matches.some((m) => m.status === "live")
        const colors = ROUND_COLORS[round.round]

        return (
          <div key={`${round.round}-${label}`} className="flex items-center">
            <div className="flex flex-col items-center">
              <div className={cn("text-[10px] font-bold tracking-wider mb-3", colors.text)}>
                {getRoundLabel(round.round, t)}
              </div>
              <div className="flex flex-col gap-3">
                {round.matches.map((match) => (
                  <BracketCardWrapper
                    key={match.id}
                    match={match}
                    onClick={() => onMatchClick(parseInt(match.id, 10))}
                  />
                ))}
              </div>
            </div>
            {nextRound && nextRound.matches.length > 0 && (
              <RoundConnector
                matchCount={nextRound.matches.length}
                isActive={isRoundActive || hasLive}
                connId={`${round.round}-${label}`}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}

// ── BracketCard wrapper (re-exports from parent module) ──────────────────────
// We accept a `match` + `onClick` and render the card inline to avoid
// circular imports.  The card rendering is identical to tournament-bracket.tsx.

import { TeamFlag } from "@/lib/flags"
import { Zap } from "lucide-react"

function BracketCardWrapper({
  match,
  onClick,
}: {
  match: BracketMatch
  onClick: () => void
}) {
  const { t } = useTranslation()
  const isLive = match.status === "live"
  const isCompleted = match.status === "completed"
  const colors = ROUND_COLORS[match.round]

  return (
    <div
      className={cn(
        "relative glass-card rounded-xl overflow-hidden transition-all duration-300 w-[170px] cursor-pointer hover:border-primary/30",
        isLive && "border-accent glow-pulse-cyan",
      )}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") onClick()
      }}
    >
      {isLive && (
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-accent via-primary to-accent animate-pulse" />
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

function TeamRow({ team, isCompleted }: { team: BracketMatch["team1"]; isCompleted: boolean }) {
  const { t } = useTranslation()
  const isTbd = team.code === "---" || team.code === "TBD"
  const displayName = isTbd ? team.fromGroup ?? t("bracket.tbd") : team.code

  return (
    <div
      className={cn(
        "flex items-center gap-2 py-1.5 px-2 rounded-lg transition-all",
        team.isWinner && isCompleted && "bg-primary/10",
      )}
    >
      <TeamFlag code={team.code} size={18} className="rounded-sm" />
      <span
        className={cn(
          "flex-1 font-medium text-xs truncate",
          team.isWinner && isCompleted ? "text-foreground" : "text-muted-foreground",
        )}
      >
        {displayName}
      </span>
      {team.score !== undefined && (
        <span
          className={cn(
            "font-score text-base w-6 text-center",
            team.isWinner && isCompleted ? "text-gold" : "text-muted-foreground",
          )}
        >
          {team.score}
        </span>
      )}
    </div>
  )
}

// ── SVG Connector between rounds ────────────────────────────────────────────

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
        <linearGradient id={`conn-${connId}`} x1="0%" y1="0%" x2="100%" y2="0%">
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
              d={`M 0 ${y1Top} H 25 V ${yMid} H 50`}
              fill="none"
              stroke={`url(#conn-${connId})`}
              strokeWidth={isActive ? 2 : 1.5}
              opacity={isActive ? 0.9 : 0.4}
              className={isActive ? "animate-pulse" : ""}
            />
            <path
              d={`M 0 ${y1Bot} H 25 V ${yMid} H 50`}
              fill="none"
              stroke={`url(#conn-${connId})`}
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

// ── SfToFinalConnector: SVG bridging both SF rows to Final ──────────────────

export function SfToFinalConnector({ isActive }: { isActive: boolean }) {
  return (
    <div className="flex flex-col items-center justify-center w-[50px] mx-1 self-stretch">
      <svg
        width="50"
        height="100%"
        viewBox="0 0 50 100"
        className="overflow-visible"
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id="conn-sf-final" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity={isActive ? 0.8 : 0.3} />
            <stop offset="100%" stopColor="var(--gold)" stopOpacity={isActive ? 0.8 : 0.3} />
          </linearGradient>
        </defs>
        {/* Upper SF → midpoint */}
        <path
          d="M 0 0 H 15 V 50 H 50"
          fill="none"
          stroke="url(#conn-sf-final)"
          strokeWidth={isActive ? 2 : 1.5}
          opacity={isActive ? 0.9 : 0.4}
          className={isActive ? "animate-pulse" : ""}
        />
        {/* Lower SF → midpoint */}
        <path
          d="M 0 100 H 15 V 50 H 50"
          fill="none"
          stroke="url(#conn-sf-final)"
          strokeWidth={isActive ? 2 : 1.5}
          opacity={isActive ? 0.9 : 0.4}
          className={isActive ? "animate-pulse" : ""}
        />
      </svg>
    </div>
  )
}

// ── FinalSection: Final + 3rd place rendered at convergence point ───────────

interface FinalSectionProps {
  finalRound?: { round: BracketRoundName; matches: BracketMatch[] }
  thirdPlaceRound?: { round: BracketRoundName; matches: BracketMatch[] }
  sfActive: boolean
  onMatchClick: (matchId: number) => void
}

export function FinalSection({
  finalRound,
  thirdPlaceRound,
  sfActive,
  onMatchClick,
}: FinalSectionProps) {
  const { t } = useTranslation()

  if (!finalRound) return null

  return (
    <div className="flex items-center self-center">
      {/* Final match */}
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
            <FinalCard key={match.id} match={match} onClick={() => onMatchClick(parseInt(match.id, 10))} />
          ))}
        </div>
      </div>

      {/* 3rd Place branch */}
      {thirdPlaceRound && (
        <div className="flex items-center ml-2">
          <RoundConnector
            matchCount={1}
            isActive={sfActive}
            connId="sf-to-3rd"
          />
          <div className="flex flex-col items-center">
            <div className="text-[10px] font-bold tracking-wider mb-3 text-muted-foreground">
              {getRoundLabel("3rd", t)}
            </div>
            {thirdPlaceRound.matches.map((match) => (
              <ThirdPlaceCard
                key={match.id}
                match={match}
                onClick={() => onMatchClick(parseInt(match.id, 10))}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function FinalCard({ match, onClick }: { match: BracketMatch; onClick: () => void }) {
  const { t } = useTranslation()
  const isLive = match.status === "live"
  const isCompleted = match.status === "completed"
  const colors = ROUND_COLORS[match.round]

  return (
    <div
      className="relative glass-card rounded-xl overflow-hidden transition-all duration-300 w-[170px] cursor-pointer hover:border-primary/30 border-gold/50 glow-pulse-gold"
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") onClick()
      }}
    >
      <div className="absolute top-2 right-2">
        <Trophy className="h-4 w-4 text-gold" />
      </div>
      {isLive && (
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-accent via-primary to-accent animate-pulse" />
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
      </div>
    </div>
  )
}

function ThirdPlaceCard({ match, onClick }: { match: BracketMatch; onClick: () => void }) {
  const { t } = useTranslation()
  const isCompleted = match.status === "completed"

  return (
    <div
      className="relative glass-card rounded-xl overflow-hidden transition-all duration-300 w-[170px] cursor-pointer hover:border-primary/30 border-border"
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") onClick()
      }}
    >
      <div className="absolute top-2 right-2">
        <Medal className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="p-2.5 space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="text-[9px] font-bold tracking-wider px-1.5 py-0.5 rounded-full bg-muted text-muted-foreground">
            {getRoundLabel("3rd", t)}
          </span>
        </div>
        <TeamRow team={match.team1} isCompleted={isCompleted} />
        <div className="flex items-center gap-1.5">
          <div className="flex-1 h-px bg-glass-border" />
          <span className="text-[9px] text-muted-foreground font-medium">{t("bracket.vs")}</span>
          <div className="flex-1 h-px bg-glass-border" />
        </div>
        <TeamRow team={match.team2} isCompleted={isCompleted} />
      </div>
    </div>
  )
}
