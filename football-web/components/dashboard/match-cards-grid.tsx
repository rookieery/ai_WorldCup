"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import {
  MapPin,
  Clock,
  Flame,
  Heart,
  Palmtree,
  Building2,
  Landmark,
  Sun,
  Activity,
  Inbox,
  RefreshCw,
  Wifi,
  WifiOff,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useTranslation } from "@/lib/i18n"
import { getMatches, apiMatchToUi } from "@/lib/api/matches"
import { postCheer } from "@/lib/api/cheers"
import { useLiveStore } from "@/lib/store"
import type { LiveScorePatch, CheerUpdate } from "@/lib/store"
import { wsClient } from "@/lib/websocket"
import type { Match, CityIcon } from "@/lib/types"

const CityIconComponent = ({ type }: { type: CityIcon }) => {
  switch (type) {
    case "palm":
      return <Palmtree className="h-3 w-3" />
    case "skyscraper":
      return <Building2 className="h-3 w-3" />
    case "landmark":
      return <Landmark className="h-3 w-3" />
    case "cactus":
      return <Sun className="h-3 w-3" />
    default:
      return <MapPin className="h-3 w-3" />
  }
}

interface MatchCardProps {
  match: Match
}

function MatchCard({ match }: MatchCardProps) {
  const [isHovered, setIsHovered] = useState(false)
  const [cheeringSide, setCheeringSide] = useState<"home" | "away" | null>(null)
  const { t } = useTranslation()

  // ── Real-time data from Zustand live store ────────────────────────────────
  const scorePatch = useLiveStore(
    (s) => s.scoreUpdates[match.id],
  ) as LiveScorePatch | undefined
  const cheerUpdate = useLiveStore(
    (s) => s.cheerUpdates[match.id],
  ) as CheerUpdate | undefined

  // Merge real-time data into local match props
  const liveScore1 = scorePatch?.score1 ?? match.score1
  const liveScore2 = scorePatch?.score2 ?? match.score2
  const liveStatus = scorePatch?.status ?? match.status
  const liveActivity = scorePatch?.activityLevel ?? match.activityLevel

  // Cheer data: prefer live store, fallback to base match data
  const cheerTotal = (cheerUpdate?.home ?? match.cheerTeam1) + (cheerUpdate?.away ?? match.cheerTeam2)
  const rawCheer1 = cheerUpdate?.home ?? match.cheerTeam1
  const rawCheer2 = cheerUpdate?.away ?? match.cheerTeam2
  const cheerPercent1 = cheerTotal > 0 ? Math.round((rawCheer1 / cheerTotal) * 100) : 50
  const cheerPercent2 = cheerTotal > 0 ? 100 - cheerPercent1 : 50

  const handleCheer = async (team: 1 | 2) => {
    if (cheeringSide) return
    const side = team === 1 ? "home" : "away"
    setCheeringSide(side)

    // Optimistic update — immediately update local store
    const store = useLiveStore.getState()
    const current = store.cheerUpdates[match.id] ?? {
      matchId: match.id,
      home: match.cheerTeam1,
      away: match.cheerTeam2,
    }

    if (side === "home") {
      store.applyCheerUpdate({
        matchId: match.id,
        home: current.home + 1,
        away: current.away,
      })
    } else {
      store.applyCheerUpdate({
        matchId: match.id,
        home: current.home,
        away: current.away + 1,
      })
    }

    try {
      const result = await postCheer(match.id, side)
      // Server response is authoritative — apply it
      store.applyCheerUpdate({
        matchId: result.match_id,
        home: result.home,
        away: result.away,
      })
    } catch {
      // Rollback on failure — revert to previous values
      store.applyCheerUpdate({
        matchId: match.id,
        home: current.home,
        away: current.away,
      })
    } finally {
      setCheeringSide(null)
    }
  }

  const isLive = liveStatus === "live"
  const isBigMatch = match.isBigMatch
  const isFinished = liveStatus === "finished"

  return (
    <div
      className={cn(
        "group relative glass-card rounded-2xl overflow-hidden transition-all duration-500",
        isLive && "border-2 border-pulse-cyan",
        isBigMatch && !isLive && "border-2 border-[#FFD700]/50 glow-pulse-gold",
        !isLive && !isBigMatch && "border border-glass-border hover:border-[#00F0FF]/30",
        isHovered && "card-3d"
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        perspective: "1000px",
      }}
    >
      {/* Big Match ambient wave background */}
      {isBigMatch && (
        <div
          className="absolute inset-0 opacity-20 ambient-wave pointer-events-none"
          style={{
            background:
              "linear-gradient(45deg, rgba(255, 215, 0, 0.1), rgba(255, 0, 229, 0.1), rgba(255, 215, 0, 0.1))",
          }}
        />
      )}

      {/* Live match glow overlay */}
      {isLive && (
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute inset-0 bg-gradient-to-br from-[#00F0FF]/5 via-transparent to-[#00F0FF]/5" />
        </div>
      )}

      <div className="relative p-5">
        {/* Header: Stage Badge & Status */}
        <div className="flex items-center justify-between mb-4">
          <span
            className={cn(
              "text-[10px] font-bold uppercase tracking-wider px-3 py-1.5 rounded-full",
              isBigMatch
                ? "bg-[#FFD700]/20 text-[#FFD700] border border-[#FFD700]/30"
                : isLive
                  ? "bg-[#00F0FF]/20 text-[#00F0FF] border border-[#00F0FF]/30"
                  : "bg-[#CCFF00]/10 text-[#CCFF00] border border-[#CCFF00]/20"
            )}
          >
            {match.stage}
          </span>

          {isLive && (
            <div className="flex items-center gap-2">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00F0FF] opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[#00F0FF]" />
              </span>
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#00F0FF]">
                {t("match.live")}
              </span>
            </div>
          )}

          {isBigMatch && !isLive && (
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#FFD700] flex items-center gap-1">
              <Flame className="h-3 w-3" />
              {t("match.bigMatch")}
            </span>
          )}

          {isFinished && (
            <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
              {t("match.ft")}
            </span>
          )}
        </div>

        {/* Teams & Score */}
        <div className="flex items-center justify-between gap-4 mb-4">
          {/* Team 1 */}
          <div className="flex items-center gap-3 flex-1">
            <div className="w-14 h-14 rounded-xl bg-secondary/50 border border-glass-border flex items-center justify-center text-2xl">
              {match.team1.flag}
            </div>
            <div>
              <p className="font-bold text-foreground text-lg">{match.team1.code}</p>
              <p className="text-xs text-muted-foreground">{match.team1.name}</p>
            </div>
          </div>

          {/* Score / VS */}
          <div className="flex flex-col items-center px-4">
            {(isLive || isFinished) && liveScore1 !== undefined ? (
              <div
                className={cn(
                  "flex items-center gap-3 font-score text-3xl",
                  isLive && "led-display text-[#00F0FF]",
                  isFinished && "text-foreground"
                )}
              >
                <span>{liveScore1}</span>
                <span className="text-muted-foreground text-lg">-</span>
                <span>{liveScore2}</span>
              </div>
            ) : (
              <span className="text-2xl font-bold text-muted-foreground/40">{t("match.vs")}</span>
            )}
          </div>

          {/* Team 2 */}
          <div className="flex items-center gap-3 flex-1 justify-end text-right">
            <div>
              <p className="font-bold text-foreground text-lg">{match.team2.code}</p>
              <p className="text-xs text-muted-foreground">{match.team2.name}</p>
            </div>
            <div className="w-14 h-14 rounded-xl bg-secondary/50 border border-glass-border flex items-center justify-center text-2xl">
              {match.team2.flag}
            </div>
          </div>
        </div>

        {/* Dynamic Timezone Display */}
        <div className="flex items-center justify-between gap-4 py-3 border-t border-glass-border">
          <div className="flex items-center gap-4">
            {/* Local Time */}
            <div className="flex items-center gap-2 text-sm">
              <Clock className="h-3.5 w-3.5 text-[#CCFF00]" />
              <span className="text-foreground font-medium">{match.localTime}</span>
              <span className="text-[10px] text-muted-foreground uppercase">{t("match.local")}</span>
            </div>

            <div className="h-4 w-px bg-border" />

            {/* Host City Time with Icon */}
            <div className="flex items-center gap-2 text-sm">
              <div className="text-[#00F0FF]">
                <CityIconComponent type={match.cityIcon} />
              </div>
              <span className="text-muted-foreground">{match.hostTime}</span>
              <span className="text-[10px] text-muted-foreground">{match.hostCity}</span>
            </div>
          </div>

          <div className="flex items-center gap-1.5 text-muted-foreground">
            <MapPin className="h-3 w-3 text-[#00F0FF]" />
            <span className="text-xs">{match.venue}</span>
          </div>
        </div>

        {/* Live Activity Bar */}
        {isLive && (
          <div className="mt-3 pt-3 border-t border-glass-border">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium flex items-center gap-1.5">
                <Activity className="h-3 w-3 text-[#00F0FF]" />
                {t("match.matchActivity")}
              </span>
              <span className="text-[10px] font-bold text-[#00F0FF]">{liveActivity}%</span>
            </div>
            <div className="h-1.5 bg-secondary/50 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-[#00F0FF] to-[#CCFF00] rounded-full activity-pulse"
                style={{ width: `${liveActivity}%` }}
              />
            </div>
          </div>
        )}

        {/* Fan Cheer Meter - Slides out on hover */}
        <div
          className={cn(
            "overflow-hidden transition-all duration-500 ease-out",
            isHovered ? "max-h-32 opacity-100 mt-4" : "max-h-0 opacity-0 mt-0"
          )}
        >
          <div className="pt-3 border-t border-glass-border">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">
                {t("match.fanSupport")}
              </span>
              <span className="text-[10px] text-[#FF00E5] font-medium">{t("match.castVote")}</span>
            </div>

            {/* Cheer Bar */}
            <div className="relative h-3 bg-secondary/30 rounded-full overflow-hidden mb-3">
              <div
                className="absolute left-0 top-0 h-full bg-gradient-to-r from-[#CCFF00] to-[#CCFF00]/70 transition-all duration-300"
                style={{ width: `${cheerPercent1}%` }}
              />
              <div
                className="absolute right-0 top-0 h-full bg-gradient-to-l from-[#00F0FF] to-[#00F0FF]/70 transition-all duration-300"
                style={{ width: `${cheerPercent2}%` }}
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-[9px] font-bold text-background drop-shadow-md">
                  {cheerPercent1}% - {cheerPercent2}%
                </span>
              </div>
            </div>

            {/* Cheer Buttons */}
            <div className="flex items-center justify-between">
              <button
                onClick={() => handleCheer(1)}
                disabled={cheeringSide !== null}
                className={cn(
                  "cheer-btn flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all",
                  cheeringSide === "home"
                    ? "bg-[#CCFF00]/30 border-[#CCFF00]/60 text-[#CCFF00]"
                    : "bg-[#CCFF00]/10 border-[#CCFF00]/30 hover:bg-[#CCFF00]/20 hover:border-[#CCFF00]/50 text-[#CCFF00]",
                  cheeringSide !== null && cheeringSide !== "home" && "opacity-50 cursor-not-allowed"
                )}
              >
                <Flame className="h-3.5 w-3.5" />
                <span className="text-xs font-medium">{t("match.cheer")} {match.team1.code}</span>
              </button>

              <button
                onClick={() => handleCheer(2)}
                disabled={cheeringSide !== null}
                className={cn(
                  "cheer-btn flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all",
                  cheeringSide === "away"
                    ? "bg-[#00F0FF]/30 border-[#00F0FF]/60 text-[#00F0FF]"
                    : "bg-[#00F0FF]/10 border-[#00F0FF]/30 hover:bg-[#00F0FF]/20 hover:border-[#00F0FF]/50 text-[#00F0FF]",
                  cheeringSide !== null && cheeringSide !== "away" && "opacity-50 cursor-not-allowed"
                )}
              >
                <Heart className="h-3.5 w-3.5" />
                <span className="text-xs font-medium">{t("match.cheer")} {match.team2.code}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Hover glow effect */}
      <div
        className={cn(
          "absolute inset-0 rounded-2xl pointer-events-none transition-opacity duration-500",
          isHovered ? "opacity-100" : "opacity-0"
        )}
        style={{
          boxShadow: isBigMatch
            ? "0 0 40px rgba(255, 215, 0, 0.2), inset 0 0 30px rgba(255, 215, 0, 0.05)"
            : isLive
              ? "0 0 40px rgba(0, 240, 255, 0.2), inset 0 0 30px rgba(0, 240, 255, 0.05)"
              : "0 0 30px rgba(204, 255, 0, 0.15), inset 0 0 20px rgba(204, 255, 0, 0.03)",
        }}
      />
    </div>
  )
}

/** Empty state shown when no matches exist for a given date. */
function EmptyState() {
  const { t } = useTranslation()
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="w-16 h-16 rounded-2xl bg-secondary/30 border border-glass-border flex items-center justify-center mb-4">
        <Inbox className="h-8 w-8 text-muted-foreground/40" />
      </div>
      <p className="text-muted-foreground text-sm">{t("match.noMatches")}</p>
    </div>
  )
}

interface MatchCardsGridProps {
  selectedDate: string
  timezone: "local" | "host"
}

export function MatchCardsGrid({ selectedDate, timezone }: MatchCardsGridProps) {
  const { t } = useTranslation()
  const [matches, setMatches] = useState<Match[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)
  const wsStatus = useLiveStore((s) => s.wsStatus)
  const wsStarted = useRef(false)

  // Start WebSocket connection on mount (once)
  useEffect(() => {
    if (!wsStarted.current) {
      wsStarted.current = true
      wsClient.start()
    }
    return () => {
      // Do NOT stop on unmount — keep WS alive across date changes
    }
  }, [])

  const fetchMatches = useCallback(async () => {
    if (!selectedDate) return
    setLoading(true)
    setError(false)
    try {
      const tzName = timezone === "host" ? undefined : Intl.DateTimeFormat().resolvedOptions().timeZone
      const res = await getMatches({ date: selectedDate, timezone: tzName, pageSize: 50 })
      setMatches(res.items.map(apiMatchToUi))
    } catch {
      setError(true)
      setMatches([])
    } finally {
      setLoading(false)
    }
  }, [selectedDate, timezone])

  useEffect(() => {
    fetchMatches()
  }, [fetchMatches])

  return (
    <div className="flex-1 p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-foreground">{t("match.title")}</h2>
          <p className="text-sm text-muted-foreground">{selectedDate}</p>
        </div>
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          {/* WebSocket connection indicator */}
          <div className="flex items-center gap-1.5">
            {wsStatus === "connected" ? (
              <>
                <Wifi className="h-3 w-3 text-[#00F0FF]" />
                <span className="text-[#00F0FF]">{t("match.liveUpdates")}</span>
              </>
            ) : wsStatus === "connecting" ? (
              <>
                <div className="w-2 h-2 rounded-full bg-[#FFD700] animate-pulse" />
                <span>{t("common.loading")}</span>
              </>
            ) : (
              <>
                <WifiOff className="h-3 w-3 text-muted-foreground/50" />
                <span className="text-muted-foreground/50">{t("match.disconnected")}</span>
              </>
            )}
          </div>
          <div className="h-4 w-px bg-border" />
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-[#00F0FF] animate-pulse" />
            <span>{t("match.live")}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-[#FFD700]" />
            <span>{t("match.bigMatch")}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-[#CCFF00]" />
            <span>{t("match.upcoming")}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-muted-foreground/50" />
            <span>{t("match.finished")}</span>
          </div>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-20">
          <span className="text-sm text-muted-foreground animate-pulse">{t("common.loading")}</span>
        </div>
      )}

      {error && !loading && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-16 h-16 rounded-2xl bg-secondary/30 border border-glass-border flex items-center justify-center mb-4">
            <RefreshCw className="h-8 w-8 text-muted-foreground/40" />
          </div>
          <p className="text-muted-foreground text-sm mb-3">{t("match.errorLoading")}</p>
          <button
            onClick={fetchMatches}
            className="text-xs text-[#00F0FF] hover:underline"
          >
            {t("common.retry")}
          </button>
        </div>
      )}

      {!loading && !error && matches.length === 0 && <EmptyState />}

      {!loading && !error && matches.length > 0 && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
          {matches.map((match) => (
            <MatchCard key={match.id} match={match} />
          ))}
        </div>
      )}
    </div>
  )
}
