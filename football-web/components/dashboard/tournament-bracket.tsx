"use client"

import { cn } from "@/lib/utils"
import { Trophy, Zap } from "lucide-react"
import type { BracketMatch, BracketTeam, BracketRoundName } from "@/lib/types"

const bracketData: BracketMatch[] = [
  // Quarter Finals
  {
    id: "qf1",
    round: "QF",
    team1: { name: "Brazil", code: "BRA", flag: "🇧🇷", score: 2, isWinner: true, color: "#CCFF00" },
    team2: { name: "Netherlands", code: "NED", flag: "🇳🇱", score: 1 },
    status: "completed",
    venue: "MetLife Stadium",
    time: "Jul 4, 18:00",
  },
  {
    id: "qf2",
    round: "QF",
    team1: { name: "France", code: "FRA", flag: "🇫🇷", score: 3, isWinner: true, color: "#00F0FF" },
    team2: { name: "England", code: "ENG", flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿", score: 2 },
    status: "completed",
    venue: "AT&T Stadium",
    time: "Jul 4, 21:00",
  },
  {
    id: "qf3",
    round: "QF",
    team1: { name: "Argentina", code: "ARG", flag: "🇦🇷", score: 2, isWinner: true, color: "#00F0FF" },
    team2: { name: "Portugal", code: "POR", flag: "🇵🇹", score: 1 },
    status: "completed",
    venue: "SoFi Stadium",
    time: "Jul 5, 18:00",
  },
  {
    id: "qf4",
    round: "QF",
    team1: { name: "Germany", code: "GER", flag: "🇩🇪", score: 1 },
    team2: { name: "Spain", code: "ESP", flag: "🇪🇸", score: 2, isWinner: true, color: "#FF00E5" },
    status: "completed",
    venue: "Rose Bowl",
    time: "Jul 5, 21:00",
  },
  // Semi Finals
  {
    id: "sf1",
    round: "SF",
    team1: { name: "Brazil", code: "BRA", flag: "🇧🇷", color: "#CCFF00" },
    team2: { name: "France", code: "FRA", flag: "🇫🇷", color: "#00F0FF" },
    status: "live",
    venue: "MetLife Stadium",
    time: "Jul 8, 20:00",
  },
  {
    id: "sf2",
    round: "SF",
    team1: { name: "Argentina", code: "ARG", flag: "🇦🇷", color: "#00F0FF" },
    team2: { name: "Spain", code: "ESP", flag: "🇪🇸", color: "#FF00E5" },
    status: "upcoming",
    venue: "AT&T Stadium",
    time: "Jul 9, 20:00",
  },
  // Final
  {
    id: "f1",
    round: "F",
    team1: { name: "TBD", code: "---", flag: "🏳️" },
    team2: { name: "TBD", code: "---", flag: "🏳️" },
    status: "upcoming",
    venue: "MetLife Stadium",
    time: "Jul 19, 20:00",
  },
]

function BracketCard({ match }: { match: BracketMatch }) {
  const isLive = match.status === "live"
  const isCompleted = match.status === "completed"
  const isFinal = match.round === "F"

  return (
    <div
      className={cn(
        "relative glass-card rounded-xl overflow-hidden transition-all duration-300",
        isFinal ? "min-w-[200px]" : "min-w-[180px]",
        isLive && "border-[#00F0FF] shadow-[0_0_20px_rgba(0,240,255,0.3)]",
        isFinal && "border-[#FFD700]/50 shadow-[0_0_30px_rgba(255,215,0,0.2)]"
      )}
    >
      {/* Live Badge */}
      {isLive && (
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-[#00F0FF] via-[#CCFF00] to-[#00F0FF] animate-pulse" />
      )}

      {/* Final Badge */}
      {isFinal && (
        <div className="absolute top-2 right-2">
          <Trophy className="h-4 w-4 text-[#FFD700]" />
        </div>
      )}

      <div className="p-3 space-y-2">
        {/* Round Badge */}
        <div className="flex items-center justify-between">
          <span
            className={cn(
              "text-[10px] font-bold tracking-wider px-2 py-0.5 rounded-full",
              match.round === "F"
                ? "bg-[#FFD700]/20 text-[#FFD700]"
                : match.round === "SF"
                ? "bg-[#FF00E5]/20 text-[#FF00E5]"
                : "bg-[#00F0FF]/20 text-[#00F0FF]"
            )}
          >
            {match.round === "QF" ? "QUARTER-FINAL" : match.round === "SF" ? "SEMI-FINAL" : "FINAL"}
          </span>
          {isLive && (
            <span className="flex items-center gap-1 text-[10px] text-[#00F0FF]">
              <Zap className="h-3 w-3" />
              LIVE
            </span>
          )}
        </div>

        {/* Team 1 */}
        <TeamRow team={match.team1} isCompleted={isCompleted} />

        {/* VS Divider */}
        <div className="flex items-center gap-2">
          <div className="flex-1 h-px bg-glass-border" />
          <span className="text-[10px] text-muted-foreground font-medium">VS</span>
          <div className="flex-1 h-px bg-glass-border" />
        </div>

        {/* Team 2 */}
        <TeamRow team={match.team2} isCompleted={isCompleted} />

        {/* Venue & Time */}
        {match.venue && (
          <div className="pt-2 border-t border-glass-border">
            <p className="text-[10px] text-muted-foreground truncate">{match.venue}</p>
            <p className="text-[10px] text-muted-foreground/70">{match.time}</p>
          </div>
        )}
      </div>
    </div>
  )
}

function TeamRow({ team, isCompleted }: { team: BracketTeam; isCompleted: boolean }) {
  return (
    <div
      className={cn(
        "flex items-center gap-2 py-1.5 px-2 rounded-lg transition-all",
        team.isWinner && isCompleted && "bg-[#CCFF00]/10"
      )}
    >
      <span className="text-lg">{team.flag}</span>
      <span
        className={cn(
          "flex-1 font-medium text-sm",
          team.isWinner && isCompleted ? "text-foreground" : "text-muted-foreground"
        )}
      >
        {team.code}
      </span>
      {team.score !== undefined && (
        <span
          className={cn(
            "font-score text-lg w-6 text-center",
            team.isWinner && isCompleted ? "text-[#CCFF00]" : "text-muted-foreground"
          )}
        >
          {team.score}
        </span>
      )}
    </div>
  )
}

function ConnectorLine({
  from,
  to,
  isWinnerPath,
  teamColor,
}: {
  from: "top" | "bottom"
  to: "left" | "right"
  isWinnerPath?: boolean
  teamColor?: string
}) {
  return (
    <svg
      className="absolute pointer-events-none"
      style={{
        width: "60px",
        height: "100%",
        left: to === "right" ? "100%" : "auto",
        right: to === "left" ? "100%" : "auto",
        top: 0,
      }}
    >
      <defs>
        <linearGradient id={`line-gradient-${from}-${to}`} x1="0%" y1="0%" x2="100%" y2="0%">
          <stop
            offset="0%"
            stopColor={isWinnerPath ? (teamColor || "#00F0FF") : "rgba(255,255,255,0.1)"}
          />
          <stop
            offset="100%"
            stopColor={isWinnerPath ? (teamColor || "#00F0FF") : "rgba(255,255,255,0.05)"}
          />
        </linearGradient>
        {isWinnerPath && (
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        )}
      </defs>
      <path
        d={
          to === "right"
            ? `M 0 50% Q 30 50%, 30 ${from === "top" ? "20%" : "80%"} L 60 ${from === "top" ? "20%" : "80%"}`
            : `M 60 50% Q 30 50%, 30 ${from === "top" ? "20%" : "80%"} L 0 ${from === "top" ? "20%" : "80%"}`
        }
        fill="none"
        stroke={`url(#line-gradient-${from}-${to})`}
        strokeWidth={isWinnerPath ? 3 : 2}
        filter={isWinnerPath ? "url(#glow)" : undefined}
        className={isWinnerPath ? "animate-pulse" : ""}
      />
    </svg>
  )
}

export function TournamentBracket() {
  const quarterFinals = bracketData.filter((m) => m.round === "QF")
  const semiFinals = bracketData.filter((m) => m.round === "SF")
  const finalMatch = bracketData.find((m) => m.round === "F")!

  return (
    <div className="flex-1 overflow-x-auto overflow-y-auto p-6">
      {/* Bracket Title */}
      <div className="mb-8 text-center">
        <h2 className="text-2xl font-bold text-foreground flex items-center justify-center gap-3">
          <Trophy className="h-6 w-6 text-[#FFD700]" />
          <span className="bg-gradient-to-r from-[#CCFF00] via-[#00F0FF] to-[#FF00E5] bg-clip-text text-transparent">
            Knockout Stage
          </span>
          <Trophy className="h-6 w-6 text-[#FFD700]" />
        </h2>
        <p className="text-sm text-muted-foreground mt-1">Road to Glory - FIFA World Cup 2026</p>
      </div>

      {/* Bracket Grid */}
      <div className="flex items-center justify-center gap-8 min-w-max">
        {/* Quarter Finals Column */}
        <div className="flex flex-col gap-6">
          <div className="text-center mb-2">
            <span className="text-xs font-bold text-[#00F0FF] tracking-wider">QUARTER-FINALS</span>
          </div>
          <div className="space-y-4">
            {quarterFinals.slice(0, 2).map((match) => (
              <BracketCard key={match.id} match={match} />
            ))}
          </div>
          <div className="h-16" />
          <div className="space-y-4">
            {quarterFinals.slice(2, 4).map((match) => (
              <BracketCard key={match.id} match={match} />
            ))}
          </div>
        </div>

        {/* Connector Lines QF -> SF */}
        <div className="flex flex-col justify-between h-full py-20">
          <svg width="80" height="200" className="overflow-visible">
            <defs>
              <linearGradient id="sf1-line" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#CCFF00" stopOpacity="0.8" />
                <stop offset="100%" stopColor="#00F0FF" stopOpacity="0.8" />
              </linearGradient>
              <filter id="glow-sf1">
                <feGaussianBlur stdDeviation="4" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>
            {/* Top bracket lines */}
            <path
              d="M 0 40 H 30 V 100 H 80"
              fill="none"
              stroke="url(#sf1-line)"
              strokeWidth="3"
              filter="url(#glow-sf1)"
              className="animate-pulse"
            />
            <path
              d="M 0 160 H 30 V 100 H 80"
              fill="none"
              stroke="url(#sf1-line)"
              strokeWidth="3"
              filter="url(#glow-sf1)"
              className="animate-pulse"
            />
          </svg>
          <div className="h-20" />
          <svg width="80" height="200" className="overflow-visible">
            <defs>
              <linearGradient id="sf2-line" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#00F0FF" stopOpacity="0.6" />
                <stop offset="100%" stopColor="#FF00E5" stopOpacity="0.6" />
              </linearGradient>
            </defs>
            {/* Bottom bracket lines */}
            <path
              d="M 0 40 H 30 V 100 H 80"
              fill="none"
              stroke="url(#sf2-line)"
              strokeWidth="2"
              opacity="0.7"
            />
            <path
              d="M 0 160 H 30 V 100 H 80"
              fill="none"
              stroke="url(#sf2-line)"
              strokeWidth="2"
              opacity="0.7"
            />
          </svg>
        </div>

        {/* Semi Finals Column */}
        <div className="flex flex-col justify-center gap-48">
          <div className="text-center mb-2">
            <span className="text-xs font-bold text-[#FF00E5] tracking-wider">SEMI-FINALS</span>
          </div>
          {semiFinals.map((match) => (
            <BracketCard key={match.id} match={match} />
          ))}
        </div>

        {/* Connector Lines SF -> Final */}
        <div className="flex items-center">
          <svg width="80" height="300" className="overflow-visible">
            <defs>
              <linearGradient id="final-line" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#FFD700" stopOpacity="0.4" />
                <stop offset="100%" stopColor="#FFD700" stopOpacity="0.8" />
              </linearGradient>
            </defs>
            {/* Final bracket lines */}
            <path
              d="M 0 60 H 30 V 150 H 80"
              fill="none"
              stroke="url(#final-line)"
              strokeWidth="2"
              strokeDasharray="6 4"
              opacity="0.5"
            />
            <path
              d="M 0 240 H 30 V 150 H 80"
              fill="none"
              stroke="url(#final-line)"
              strokeWidth="2"
              strokeDasharray="6 4"
              opacity="0.5"
            />
          </svg>
        </div>

        {/* Final Column */}
        <div className="flex flex-col items-center justify-center">
          <div className="text-center mb-4">
            <span className="text-xs font-bold text-[#FFD700] tracking-wider">FINAL</span>
          </div>
          <div className="relative">
            {/* Trophy Glow */}
            <div className="absolute -top-8 left-1/2 -translate-x-1/2">
              <div className="relative">
                <Trophy className="h-8 w-8 text-[#FFD700]" />
                <div className="absolute inset-0 blur-xl bg-[#FFD700]/30" />
              </div>
            </div>
            <BracketCard match={finalMatch} />
            {/* Stadium Info */}
            <div className="mt-4 text-center">
              <p className="text-xs text-[#FFD700] font-medium">MetLife Stadium</p>
              <p className="text-[10px] text-muted-foreground">New Jersey, USA</p>
              <p className="text-[10px] text-muted-foreground">July 19, 2026 • 20:00 ET</p>
            </div>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-10 flex justify-center gap-6 text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-[#00F0FF]/30 border border-[#00F0FF]" />
          <span>Live Match</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-[#CCFF00]/30 border border-[#CCFF00]" />
          <span>Winner Advances</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-1 bg-gradient-to-r from-[#00F0FF] to-[#FF00E5]" />
          <span>Advancement Path</span>
        </div>
      </div>
    </div>
  )
}
