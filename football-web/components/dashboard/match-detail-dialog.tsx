"use client"

import { useState, useEffect, useCallback } from "react"
import {
  Dialog,
  DialogContent,
} from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"
import { useTranslation } from "@/lib/i18n"
import { getMatchById } from "@/lib/api/matches"
import { getCheers } from "@/lib/api/cheers"
import { useLiveStore } from "@/lib/store"
import type { LiveScorePatch, CheerUpdate } from "@/lib/store"
import {
  MapPin,
  Clock,
  Activity,
  Flame,
  Heart,
  AlertTriangle,
  Loader2,
  Zap,
  XIcon,
  Trophy,
  Users,
  Target,
  Swords,
  Sparkles,
} from "lucide-react"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { getAvailableSkills } from "@/lib/api/match-analysis"
import type { SkillInfo } from "@/lib/api/match-analysis"
import { useAIChatStore, recommendedSkillId } from "@/lib/store/ai-chat"
import { usePreferencesStore } from "@/lib/store/preferences"
import {
  EventsSection,
  StatRow,
  VenueInfoItem,
} from "@/components/dashboard/match-detail-helpers"
import type { MatchDetailData } from "@/components/dashboard/match-detail-helpers"
import { TeamFlag } from "@/lib/flags"

// ── Match Detail Dialog ────────────────────────────────────────────────────────

/** Map a backend stage value to its i18n key. */
function stageKey(stage: string): string {
  const map: Record<string, string> = {
    group: "timeline.stageGroup",
    R32: "timeline.stageR32",
    R16: "timeline.stageR16",
    QF: "timeline.stageQF",
    SF: "timeline.stageSF",
    "3rd": "timeline.stage3rd",
    F: "timeline.stageFinal",
  }
  return map[stage] ?? stage
}

interface MatchDetailDialogProps {
  matchId: number | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onAnalyzeMatch?: (matchData: MatchDetailData, skillId: string) => void
}

export function MatchDetailDialog({
  matchId,
  open,
  onOpenChange,
  onAnalyzeMatch,
}: MatchDetailDialogProps) {
  const { t } = useTranslation()
  const [data, setData] = useState<MatchDetailData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)
  const [cheerHome, setCheerHome] = useState(0)
  const [cheerAway, setCheerAway] = useState(0)
  const [selectedSkillId, setSelectedSkillId] = useState<string | null>(null)
  const [availableSkills, setAvailableSkills] = useState<SkillInfo[]>([])
  const isStreaming = useAIChatStore((s) => s.isStreaming)
  const lang = usePreferencesStore((s) => s.language)

  // Real-time score patch from live store
  const scorePatch = useLiveStore(
    (s) => (matchId ? s.scoreUpdates[matchId] : undefined) as LiveScorePatch | undefined,
  )
  const cheerUpdate = useLiveStore(
    (s) => (matchId ? s.cheerUpdates[matchId] : undefined) as CheerUpdate | undefined,
  )

  const fetchDetail = useCallback(async () => {
    if (!matchId) return
    setLoading(true)
    setError(false)
    try {
      const detail = await getMatchById(matchId)
      setData(detail)
      // Fetch cheer data in parallel (fire-and-forget, non-blocking)
      try {
        const cheers = await getCheers(matchId)
        setCheerHome(cheers.home)
        setCheerAway(cheers.away)
      } catch {
        // Cheer data is optional — keep defaults
        setCheerHome(0)
        setCheerAway(0)
      }
    } catch {
      setError(true)
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [matchId])

  useEffect(() => {
    if (open && matchId) {
      void fetchDetail()
    }
    if (!open) {
      setData(null)
      setError(false)
    }
  }, [open, matchId, fetchDetail])

  // Fetch available skills once on mount
  useEffect(() => {
    let cancelled = false
    void (async () => {
      try {
        const skills = await getAvailableSkills(lang)
        if (!cancelled) setAvailableSkills(skills)
      } catch {
        // Skills are optional — keep empty list
      }
    })()
    return () => { cancelled = true }
  }, [lang])

  // Compute live-merged values
  const homeScore = data
    ? (scorePatch?.score1 ?? data.home_score ?? 0)
    : 0
  const awayScore = data
    ? (scorePatch?.score2 ?? data.away_score ?? 0)
    : 0
  const matchStatus = data
    ? (scorePatch?.status ?? data.status)
    : "upcoming"
  const activityLevel = data
    ? (scorePatch?.activityLevel ?? data.activity_level)
    : 0

  const isLive = matchStatus === "live"
  const isFinished = matchStatus === "finished"
  const isBigMatch = data?.is_big_match ?? false

  // Cheer data — prefer live store, then API fetch
  const liveCheerHome = cheerUpdate?.home ?? cheerHome
  const liveCheerAway = cheerUpdate?.away ?? cheerAway
  const cheerTotal = liveCheerHome + liveCheerAway
  const cheerPercentHome = cheerTotal > 0 ? Math.round((liveCheerHome / cheerTotal) * 100) : 50
  const cheerPercentAway = cheerTotal > 0 ? 100 - cheerPercentHome : 50

  // Group events by half
  const firstHalfEvents = data?.events.filter((e) => e.minute <= 45) ?? []
  const secondHalfEvents = data?.events.filter((e) => e.minute > 45 && e.minute <= 90) ?? []
  const extraTimeEvents = data?.events.filter((e) => e.minute > 90) ?? []
  const hasEvents = (data?.events.length ?? 0) > 0

  // Compute stats from events
  const homeGoals = data?.events.filter((e) => e.event_type === "goal" && e.team_side === "home").length ?? 0
  const awayGoals = data?.events.filter((e) => e.event_type === "goal" && e.team_side === "away").length ?? 0
  const homeYellowCards = data?.events.filter((e) => e.event_type === "yellow_card" && e.team_side === "home").length ?? 0
  const awayYellowCards = data?.events.filter((e) => e.event_type === "yellow_card" && e.team_side === "away").length ?? 0
  const homeRedCards = data?.events.filter((e) => e.event_type === "red_card" && e.team_side === "home").length ?? 0
  const awayRedCards = data?.events.filter((e) => e.event_type === "red_card" && e.team_side === "away").length ?? 0

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="glass-card-opaque border-glass-border max-w-2xl p-0 gap-0 overflow-hidden"
        showCloseButton={false}
      >
        {/* Close button overlay */}
        <button
          onClick={() => onOpenChange(false)}
          className="absolute top-3 right-3 z-10 rounded-full p-1.5 bg-secondary/50 border border-glass-border hover:bg-secondary/80 transition-colors"
        >
          <XIcon className="h-4 w-4 text-muted-foreground" />
        </button>

        <ScrollArea className="max-h-[85vh]">
          <div className="p-6">
            {/* Loading State */}
            {loading && (
              <div className="flex flex-col items-center justify-center py-16 gap-3">
                <Loader2 className="h-8 w-8 text-[#00F0FF] animate-spin" />
                <span className="text-sm text-muted-foreground">{t("common.loading")}</span>
              </div>
            )}

            {/* Error State */}
            {error && !loading && (
              <div className="flex flex-col items-center justify-center py-16 gap-3">
                <AlertTriangle className="h-8 w-8 text-destructive" />
                <p className="text-sm text-muted-foreground">{t("matchDetail.loadError")}</p>
                <button
                  onClick={() => void fetchDetail()}
                  className="text-xs text-[#00F0FF] hover:underline"
                >
                  {t("common.retry")}
                </button>
              </div>
            )}

            {/* Match Content */}
            {data && !loading && !error && (
              <div className="space-y-5">
                {/* ── Header: Teams + Score ──────────────────────────────── */}
                <div className="relative">
                  {/* Live glow overlay */}
                  {isLive && (
                    <div className="absolute -inset-4 rounded-xl bg-gradient-to-br from-[#00F0FF]/5 via-transparent to-[#00F0FF]/5 pointer-events-none" />
                  )}
                  {/* Big Match ambient */}
                  {isBigMatch && !isLive && (
                    <div className="absolute -inset-4 rounded-xl pointer-events-none"
                      style={{
                        background: "linear-gradient(45deg, rgba(255, 215, 0, 0.05), rgba(255, 0, 229, 0.05), rgba(255, 215, 0, 0.05))",
                      }}
                    />
                  )}

                  <div className="relative">
                    {/* Stage + Status badges */}
                    <div className="flex items-center justify-between mb-4">
                      <span className={cn(
                        "text-[10px] font-bold uppercase tracking-wider px-3 py-1 rounded-full",
                        isBigMatch
                          ? "bg-[#FFD700]/20 text-[#FFD700] border border-[#FFD700]/30"
                          : isLive
                            ? "bg-[#00F0FF]/20 text-[#00F0FF] border border-[#00F0FF]/30"
                            : "bg-[#CCFF00]/10 text-[#CCFF00] border border-[#CCFF00]/20"
                      )}>
                        {data.stage === "group" && data.group_label
                          ? `${t("matchDetail.groupStage")} ${data.group_label}`
                          : t(stageKey(data.stage))}
                      </span>

                      <div className="flex items-center gap-2">
                        {isLive && (
                          <span className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-[#00F0FF]">
                            <span className="relative flex h-2 w-2">
                              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00F0FF] opacity-75" />
                              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#00F0FF]" />
                            </span>
                            {t("match.live")}
                          </span>
                        )}
                        {isFinished && (
                          <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                            {t("match.ft")}
                          </span>
                        )}
                        {isBigMatch && (
                          <span className="flex items-center gap-1 text-[10px] font-bold text-[#FFD700]">
                            <Trophy className="h-3 w-3" />
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Teams + Score */}
                    <div className="flex items-center justify-between gap-6">
                      {/* Home Team */}
                      <div className="flex flex-col items-center gap-2 flex-1">
                        <div className="w-16 h-16 rounded-2xl bg-secondary/50 border border-glass-border flex items-center justify-center overflow-hidden">
                          <TeamFlag code={data.home_team.code} size={48} />
                        </div>
                        <p className="font-bold text-foreground text-lg truncate max-w-[140px]">{data.home_team.name}</p>
                      </div>

                      {/* Score */}
                      <div className="flex flex-col items-center px-4">
                        {(isLive || isFinished) ? (
                          <div className={cn(
                            "flex items-center gap-3 font-score text-4xl",
                            isLive && "led-display text-[#00F0FF]",
                            isFinished && "text-foreground"
                          )}>
                            <span>{homeScore}</span>
                            <span className="text-muted-foreground text-lg">-</span>
                            <span>{awayScore}</span>
                          </div>
                        ) : (
                          <span className="text-2xl font-bold text-muted-foreground/40">{t("match.vs")}</span>
                        )}
                      </div>

                      {/* Away Team */}
                      <div className="flex flex-col items-center gap-2 flex-1">
                        <div className="w-16 h-16 rounded-2xl bg-secondary/50 border border-glass-border flex items-center justify-center overflow-hidden">
                          <TeamFlag code={data.away_team.code} size={48} />
                        </div>
                        <p className="font-bold text-foreground text-lg truncate max-w-[140px]">{data.away_team.name}</p>
                      </div>
                    </div>

                    {/* Match Info Row */}
                    <div className="flex items-center justify-center gap-4 mt-4 text-xs text-muted-foreground">
                      <div className="flex items-center gap-1.5">
                        <Clock className="h-3 w-3 text-[#CCFF00]" />
                        <span>{data.local_time ?? "--:--"}</span>
                      </div>
                      <div className="h-3 w-px bg-border" />
                      <div className="flex items-center gap-1.5">
                        <MapPin className="h-3 w-3 text-[#00F0FF]" />
                        <span>{data.venue.name}</span>
                      </div>
                      <div className="h-3 w-px bg-border" />
                      <div className="flex items-center gap-1.5">
                        <Users className="h-3 w-3 text-[#FF00E5]" />
                        <span>{data.venue.city}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* ── Live Activity Bar ──────────────────────────────────── */}
                {isLive && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium flex items-center gap-1.5">
                        <Activity className="h-3 w-3 text-[#00F0FF]" />
                        {t("match.matchActivity")}
                      </span>
                      <span className="text-[10px] font-bold text-[#00F0FF]">{activityLevel}%</span>
                    </div>
                    <div className="h-1.5 bg-secondary/50 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-[#00F0FF] to-[#CCFF00] rounded-full activity-pulse"
                        style={{ width: `${activityLevel}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* ── Fan Cheer Section ──────────────────────────────────── */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium flex items-center gap-1.5">
                      <Flame className="h-3 w-3 text-[#CCFF00]" />
                      {t("matchDetail.fanCheer")}
                    </span>
                    <span className="text-[10px] text-[#FF00E5]">
                      {cheerTotal} {t("matchDetail.votes")}
                    </span>
                  </div>
                  <div className="relative h-4 bg-secondary/30 rounded-full overflow-hidden">
                    <div
                      className="absolute left-0 top-0 h-full bg-gradient-to-r from-[#CCFF00] to-[#CCFF00]/70 transition-all duration-500"
                      style={{ width: `${cheerPercentHome}%` }}
                    />
                    <div
                      className="absolute right-0 top-0 h-full bg-gradient-to-l from-[#00F0FF] to-[#00F0FF]/70 transition-all duration-500"
                      style={{ width: `${cheerPercentAway}%` }}
                    />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-[9px] font-bold text-foreground drop-shadow-md">
                        {cheerPercentHome}% - {cheerPercentAway}%
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Flame className="h-3 w-3 text-[#CCFF00]" />
                      {data.home_team.code}
                    </span>
                    <span className="flex items-center gap-1">
                      {data.away_team.code}
                      <Heart className="h-3 w-3 text-[#00F0FF]" />
                    </span>
                  </div>
                </div>

                <Separator className="bg-glass-border" />

                {/* ── Match Events Timeline ──────────────────────────────── */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-[#00F0FF]" />
                    <h3 className="text-sm font-bold text-foreground">{t("matchDetail.matchEvents")}</h3>
                  </div>

                  {!hasEvents && (
                    <div className="flex flex-col items-center justify-center py-8 text-center">
                      <Swords className="h-6 w-6 text-muted-foreground/30 mb-2" />
                      <p className="text-xs text-muted-foreground/60">{t("matchDetail.noEvents")}</p>
                    </div>
                  )}

                  {hasEvents && (
                    <div className="space-y-4">
                      {/* First Half */}
                      {firstHalfEvents.length > 0 && (
                        <EventsSection
                          title={t("matchDetail.firstHalf")}
                          events={firstHalfEvents}
                          homeCode={data.home_team.code}
                          awayCode={data.away_team.code}
                          t={t}
                        />
                      )}
                      {/* Second Half */}
                      {secondHalfEvents.length > 0 && (
                        <EventsSection
                          title={t("matchDetail.secondHalf")}
                          events={secondHalfEvents}
                          homeCode={data.home_team.code}
                          awayCode={data.away_team.code}
                          t={t}
                        />
                      )}
                      {/* Extra Time */}
                      {extraTimeEvents.length > 0 && (
                        <EventsSection
                          title={t("matchDetail.extraTime")}
                          events={extraTimeEvents}
                          homeCode={data.home_team.code}
                          awayCode={data.away_team.code}
                          t={t}
                        />
                      )}
                    </div>
                  )}
                </div>

                {/* ── Match Statistics ───────────────────────────────────── */}
                {(homeGoals > 0 || awayGoals > 0 || homeYellowCards > 0 || awayYellowCards > 0 || homeRedCards > 0 || awayRedCards > 0) && (
                  <>
                    <Separator className="bg-glass-border" />
                    <div className="space-y-4">
                      <div className="flex items-center gap-2">
                        <Target className="h-4 w-4 text-[#CCFF00]" />
                        <h3 className="text-sm font-bold text-foreground">{t("matchDetail.matchStats")}</h3>
                      </div>

                      <div className="space-y-3">
                        {/* Goals */}
                        <StatRow
                          label={t("matchDetail.goals")}
                          homeValue={homeGoals}
                          awayValue={awayGoals}
                          colorClass="text-[#CCFF00]"
                          barColor="from-[#CCFF00] to-[#CCFF00]/50"
                        />
                        {/* Yellow Cards */}
                        <StatRow
                          label={t("matchDetail.yellowCards")}
                          homeValue={homeYellowCards}
                          awayValue={awayYellowCards}
                          colorClass="text-[#FFD700]"
                          barColor="from-[#FFD700] to-[#FFD700]/50"
                        />
                        {/* Red Cards */}
                        <StatRow
                          label={t("matchDetail.redCards")}
                          homeValue={homeRedCards}
                          awayValue={awayRedCards}
                          colorClass="text-red-400"
                          barColor="from-red-400 to-red-400/50"
                        />
                      </div>
                    </div>
                  </>
                )}

                {/* ── Venue Info ─────────────────────────────────────────── */}
                <Separator className="bg-glass-border" />
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-[#00F0FF]" />
                    <h3 className="text-sm font-bold text-foreground">{t("matchDetail.venueInfo")}</h3>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <VenueInfoItem label={t("matchDetail.venue")} value={data.venue.name} />
                    <VenueInfoItem label={t("matchDetail.city")} value={`${data.venue.city}, ${data.venue.country}`} />
                    <VenueInfoItem label={t("matchDetail.kickoff")} value={data.host_time ?? "--:--"} />
                    <VenueInfoItem label={t("matchDetail.capacity")} value={data.venue.capacity.toLocaleString()} />
                  </div>
                </div>

                {/* ── AI Analysis Section ───────────────────────────────── */}
                <Separator className="bg-glass-border" />
                <div className="space-y-3 rounded-xl bg-secondary/20 border border-glass-border p-4">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-[#00F0FF]" />
                    <h3 className="text-sm font-bold text-foreground">{t("matchDetail.aiAnalysis")}</h3>
                  </div>
                  <div className="flex items-center gap-3">
                    <Select value={selectedSkillId ?? "__auto__"} onValueChange={(v) => setSelectedSkillId(v === "__auto__" ? null : v)}>
                      <SelectTrigger className="flex-1 bg-secondary/30 border-glass-border text-xs h-8">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__auto__">{t("matchDetail.autoDetect")}</SelectItem>
                        {availableSkills.map((skill) => (
                          <SelectItem key={skill.skill_id} value={skill.skill_id}>
                            {lang === "zh-CN" ? skill.name_zh : skill.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <button
                      disabled={isStreaming}
                      onClick={() => {
                        if (!onAnalyzeMatch || !data) return
                        const resolved = selectedSkillId ?? recommendedSkillId(data.stage)
                        onAnalyzeMatch(data, resolved)
                      }}
                      className={cn(
                        "flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold",
                        "bg-gradient-to-r from-[#00F0FF] to-[#CCFF00] text-background",
                        "hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed",
                      )}
                    >
                      {isStreaming
                        ? <><Loader2 className="h-3.5 w-3.5 animate-spin" />{t("matchDetail.analyzingMatch")}</>
                        : <><Sparkles className="h-3.5 w-3.5" />{t("matchDetail.analysisButton")}</>
                      }
                    </button>
                  </div>
                  <p className="text-[10px] text-muted-foreground">{t("matchDetail.analysisDesc")}</p>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Glow border effect at bottom */}
        {isLive && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-[#00F0FF] via-[#CCFF00] to-[#00F0FF] animate-pulse" />
        )}
      </DialogContent>
    </Dialog>
  )
}