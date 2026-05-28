"use client"

import { cn } from "@/lib/utils"
import {
  Circle,
  ArrowRightLeft,
  Monitor,
} from "lucide-react"
import { usePreferencesStore, useAIChatStore } from "@/lib/store"
import { streamMatchAnalysis } from "@/lib/api/match-analysis"
import type { MatchAnalysisRequestBody } from "@/lib/api/match-analysis"
import { openMobileCopilotSheet } from "@/components/dashboard/ai-copilot-mobile"

// ── Detail types ───────────────────────────────────────────────────────────────

interface MatchDetailTeam {
  id: number
  name: string
  name_zh: string
  code: string
  flag: string
  group_label: string
}

interface MatchDetailVenue {
  id: number
  name: string
  name_zh: string
  city: string
  city_zh: string
  country: string
  country_zh: string
  timezone: string
  utc_offset: string
  capacity: number
}

export interface MatchDetailEvent {
  id: number
  match_id: number
  event_type: string
  minute: number
  team_side: string
  player_name: string | null
}

export interface MatchDetailData {
  id: number
  external_id: string
  home_team: MatchDetailTeam
  away_team: MatchDetailTeam
  venue: MatchDetailVenue
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
  events: MatchDetailEvent[]
}

// ── Event icon helper ──────────────────────────────────────────────────────────

function EventIcon({ type }: { type: string }) {
  switch (type) {
    case "goal":
      return <Circle className="h-3.5 w-3.5 text-[#CCFF00] fill-[#CCFF00]" />
    case "yellow_card":
      return <div className="h-3.5 w-3 rounded-sm bg-[#FFD700]" />
    case "red_card":
      return <div className="h-3.5 w-3 rounded-sm bg-red-500" />
    case "substitution":
      return <ArrowRightLeft className="h-3.5 w-3.5 text-[#00F0FF]" />
    case "var":
      return <Monitor className="h-3.5 w-3.5 text-[#FF00E5]" />
    default:
      return <Circle className="h-3.5 w-3.5 text-muted-foreground" />
  }
}

function EventLabel({
  type,
  t,
}: {
  type: string
  t: (key: string) => string
}) {
  switch (type) {
    case "goal":
      return <span className="text-[#CCFF00] font-bold">{t("matchDetail.goal")}</span>
    case "yellow_card":
      return <span className="text-[#FFD700] font-medium">{t("matchDetail.yellowCard")}</span>
    case "red_card":
      return <span className="text-red-400 font-medium">{t("matchDetail.redCard")}</span>
    case "substitution":
      return <span className="text-[#00F0FF] font-medium">{t("matchDetail.substitution")}</span>
    case "var":
      return <span className="text-[#FF00E5] font-medium">{t("matchDetail.var")}</span>
    default:
      return <span className="text-muted-foreground">{type}</span>
  }
}

// ── Events section ─────────────────────────────────────────────────────────────

export function EventsSection({
  title,
  events,
  homeCode,
  awayCode,
  t,
}: {
  title: string
  events: MatchDetailEvent[]
  homeCode: string
  awayCode: string
  t: (key: string) => string
}) {
  return (
    <div className="space-y-2">
      <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
        {title}
      </p>
      <div className="space-y-1.5">
        {events.map((event) => {
          const isHome = event.team_side === "home"
          return (
            <div
              key={event.id}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg transition-colors",
                "bg-secondary/20 hover:bg-secondary/30"
              )}
            >
              <span className="text-[10px] font-bold text-[#00F0FF] w-8 text-right tabular-nums">
                {event.minute}&apos;
              </span>
              <EventIcon type={event.event_type} />
              <EventLabel type={event.event_type} t={t} />
              {event.player_name && (
                <span className="text-xs text-muted-foreground flex-1 truncate">
                  {event.player_name}
                </span>
              )}
              <span
                className={cn(
                  "text-[10px] font-bold px-2 py-0.5 rounded-full",
                  isHome
                    ? "bg-[#CCFF00]/10 text-[#CCFF00] border border-[#CCFF00]/20"
                    : "bg-[#00F0FF]/10 text-[#00F0FF] border border-[#00F0FF]/20"
                )}
              >
                {isHome ? homeCode : awayCode}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Stat row ───────────────────────────────────────────────────────────────────

export function StatRow({
  label,
  homeValue,
  awayValue,
  colorClass,
  barColor,
}: {
  label: string
  homeValue: number
  awayValue: number
  colorClass: string
  barColor: string
}) {
  const total = homeValue + awayValue
  const homeWidth = total > 0 ? (homeValue / total) * 100 : 50
  const awayWidth = total > 0 ? (awayValue / total) * 100 : 50

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className={cn("text-sm font-score", colorClass)}>{homeValue}</span>
        <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-medium">{label}</span>
        <span className={cn("text-sm font-score", colorClass)}>{awayValue}</span>
      </div>
      <div className="flex gap-1 h-1">
        <div className="flex-1 bg-secondary/30 rounded-full overflow-hidden flex justify-end">
          <div
            className={cn("h-full bg-gradient-to-l rounded-full transition-all duration-500", barColor)}
            style={{ width: `${homeWidth}%` }}
          />
        </div>
        <div className="flex-1 bg-secondary/30 rounded-full overflow-hidden">
          <div
            className={cn("h-full bg-gradient-to-r rounded-full transition-all duration-500", barColor)}
            style={{ width: `${awayWidth}%` }}
          />
        </div>
      </div>
    </div>
  )
}

// ── Venue info item ────────────────────────────────────────────────────────────

export function VenueInfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="space-y-0.5">
      <p className="text-[10px] text-muted-foreground uppercase tracking-wider">{label}</p>
      <p className="text-xs text-foreground font-medium truncate">{value}</p>
    </div>
  )
}

// ── Analysis Dispatch Helper ───────────────────────────────────────────────────

/**
 * Kick off a match analysis SSE stream and wire it into the AI chat store.
 *
 * Shared by `match-cards-grid.tsx` and `tournament-bracket.tsx` so that both
 * views can trigger AI analysis from their `MatchDetailDialog` instances
 * without duplicating ~60 lines of wiring code.
 *
 * @param matchData  The match detail data from the dialog.
 * @param skillId    The resolved skill ID (e.g. `"group_stage_predict"`).
 * @param closeDialog  Callback to close the parent dialog.
 */
export function dispatchMatchAnalysis(
  matchData: MatchDetailData,
  skillId: string,
  closeDialog: () => void,
): void {
  const lang = usePreferencesStore.getState().language

  const body: MatchAnalysisRequestBody = {
    match_id: matchData.id,
    stage: matchData.stage,
    skill_id: skillId,
    home_team: {
      name: matchData.home_team.name,
      name_zh: matchData.home_team.name_zh,
      code: matchData.home_team.code,
      flag: matchData.home_team.flag,
    },
    away_team: {
      name: matchData.away_team.name,
      name_zh: matchData.away_team.name_zh,
      code: matchData.away_team.code,
      flag: matchData.away_team.flag,
    },
    home_score: matchData.home_score,
    away_score: matchData.away_score,
    status: matchData.status,
    group_label: matchData.group_label ?? undefined,
    round: matchData.round || undefined,
    match_day: matchData.match_day ?? undefined,
    events: matchData.events.map((e) => ({
      event_type: e.event_type,
      minute: e.minute,
      team_side: e.team_side,
      player_name: e.player_name,
    })),
    lang,
  }

  const homeName = lang === "zh-CN" ? matchData.home_team.name_zh : matchData.home_team.name
  const awayName = lang === "zh-CN" ? matchData.away_team.name_zh : matchData.away_team.name
  const summary = `${homeName} vs ${awayName}`

  const store = useAIChatStore.getState()
  store.addAnalysisContextMessage(summary)
  store.startStreaming()

  closeDialog()
  openMobileCopilotSheet()

  const controller = new AbortController()
  void streamMatchAnalysis(body, {
    onThinking: (delta) => useAIChatStore.getState().appendThinkingContent(delta),
    onAnswer: (delta) => useAIChatStore.getState().appendStreamContent(delta),
    onAnalysis: (data) => useAIChatStore.getState().setPendingAnalysis(data),
    onDone: () => useAIChatStore.getState().finishStreaming(),
    onError: () => useAIChatStore.getState().finishStreaming(),
  }, controller.signal)
}
