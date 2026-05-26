"use client"

import { useEffect, useRef, useCallback, useState, useMemo } from "react"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useTranslation } from "@/lib/i18n"
import { getMatchDates } from "@/lib/api/matches"
import type { MatchDateInfo } from "@/lib/types"

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
  return map[stage] ?? "timeline.stageRest"
}

interface DateTimelineProps {
  selectedDate: string
  onDateSelect: (date: string) => void
}

interface RawDateItem {
  isoDate: string
  stage: string
  isToday: boolean
}

interface DateItem {
  isoDate: string
  label: string
  dayOfWeek: string
  stage: string
  stageLabel: string
  isToday: boolean
}

const WEEKDAY_KEYS = [
  "common.weekdaySun",
  "common.weekdayMon",
  "common.weekdayTue",
  "common.weekdayWed",
  "common.weekdayThu",
  "common.weekdayFri",
  "common.weekdaySat",
]

const MONTH_KEYS = [
  "common.monthJan", "common.monthFeb", "common.monthMar", "common.monthApr",
  "common.monthMay", "common.monthJun", "common.monthJul", "common.monthAug",
  "common.monthSep", "common.monthOct", "common.monthNov", "common.monthDec",
]

function formatDateLabel(d: Date, t: (k: string) => string): string {
  const month = t(MONTH_KEYS[d.getMonth()])
  return `${month} ${d.getDate()}`
}

function formatDayOfWeek(d: Date, t: (k: string) => string): string {
  return t(WEEKDAY_KEYS[d.getDay()])
}

export function DateTimeline({ selectedDate, onDateSelect }: DateTimelineProps) {
  const { t, locale } = useTranslation()
  const scrollRef = useRef<HTMLDivElement>(null)
  const [rawDates, setRawDates] = useState<RawDateItem[]>([])
  const [loading, setLoading] = useState(true)

  const dates = useMemo<DateItem[]>(() =>
    rawDates.map((item) => {
      const d = new Date(item.isoDate + "T00:00:00")
      return {
        ...item,
        label: formatDateLabel(d, t),
        dayOfWeek: formatDayOfWeek(d, t),
        stageLabel: t(stageKey(item.stage)),
      }
    }),
    [rawDates, t],
  )

  // ── Fetch match dates from API ──────────────────────────────────────────
  useEffect(() => {
    let cancelled = false

    async function fetchDates() {
      setLoading(true)
      try {
        const raw: MatchDateInfo[] = await getMatchDates()
        if (cancelled) return

        const today = new Date()
        today.setHours(0, 0, 0, 0)

        const items: RawDateItem[] = raw.map((entry) => {
          const d = new Date(entry.date + "T00:00:00")
          return {
            isoDate: entry.date,
            stage: entry.stage,
            isToday: d.getTime() === today.getTime(),
          }
        })

        setRawDates(items)

        // Auto-select today, or the nearest future date with matches
        const todayItem = items.find((i) => i.isToday)
        if (todayItem) {
          onDateSelect(todayItem.isoDate)
        } else {
          const nearestFuture = items.find((i) => {
            const d = new Date(i.isoDate + "T00:00:00")
            return d.getTime() >= today.getTime()
          })
          if (nearestFuture) {
            onDateSelect(nearestFuture.isoDate)
          } else if (items.length > 0) {
            onDateSelect(items[items.length - 1].isoDate)
          }
        }
      } catch {
        // Silently fail — dates remain empty, grid shows empty state
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetchDates()
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locale])

  // ── Scroll to selected / today on first render ─────────────────────────
  useEffect(() => {
    if (dates.length === 0) return
    const idx = dates.findIndex((d) => d.isoDate === selectedDate)
    if (idx >= 0 && scrollRef.current) {
      const child = scrollRef.current.children[idx] as HTMLElement | undefined
      if (child) {
        child.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" })
      }
    }
  }, [dates, selectedDate])

  const scroll = useCallback((direction: "left" | "right") => {
    if (scrollRef.current) {
      const scrollAmount = direction === "left" ? -300 : 300
      scrollRef.current.scrollBy({ left: scrollAmount, behavior: "smooth" })
    }
  }, [])

  const getStageColor = useCallback((stage: string, isSelected: boolean) => {
    if (isSelected) return "bg-[#CCFF00]/20 text-[#CCFF00] border-[#CCFF00]/30"
    switch (stage) {
      case "group":
        return "bg-[#CCFF00]/10 text-[#CCFF00]/80"
      case "R32":
      case "R16":
        return "bg-[#00F0FF]/10 text-[#00F0FF]/80"
      case "QF":
      case "SF":
        return "bg-[#FF00E5]/10 text-[#FF00E5]/80"
      case "3rd":
      case "F":
        return "bg-[#FFD700]/10 text-[#FFD700]/80"
      default:
        return "bg-muted text-muted-foreground"
    }
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-6">
        <span className="text-sm text-muted-foreground animate-pulse">{t("common.loading")}</span>
      </div>
    )
  }

  return (
    <div className="relative">
      {/* Navigation Buttons */}
      <Button
        variant="ghost"
        size="icon"
        className="absolute left-2 top-1/2 -translate-y-1/2 z-10 h-9 w-9 glass-card hover:bg-[#00F0FF]/10 hover:border-[#00F0FF]/30 rounded-lg"
        onClick={() => scroll("left")}
      >
        <ChevronLeft className="h-4 w-4" />
      </Button>

      <Button
        variant="ghost"
        size="icon"
        className="absolute right-2 top-1/2 -translate-y-1/2 z-10 h-9 w-9 glass-card hover:bg-[#00F0FF]/10 hover:border-[#00F0FF]/30 rounded-lg"
        onClick={() => scroll("right")}
      >
        <ChevronRight className="h-4 w-4" />
      </Button>

      {/* Timeline */}
      <div
        ref={scrollRef}
        className="flex gap-2 overflow-x-auto scrollbar-hide px-14 py-3"
      >
        {dates.map((item) => {
          const isSelected = selectedDate === item.isoDate
          return (
            <button
              key={item.isoDate}
              onClick={() => onDateSelect(item.isoDate)}
              className={cn(
                "flex flex-col items-center gap-1.5 px-4 py-3 rounded-xl min-w-[85px] transition-all duration-300 border",
                isSelected
                  ? "bg-[#CCFF00]/10 border-[#CCFF00]/40 shadow-[0_0_20px_rgba(204,255,0,0.15)]"
                  : item.isToday
                    ? "bg-[#00F0FF]/10 border-[#00F0FF]/30"
                    : "bg-secondary/20 border-glass-border hover:bg-secondary/40 hover:border-glass-border"
              )}
            >
              <span
                className={cn(
                  "text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border",
                  getStageColor(item.stage, isSelected)
                )}
              >
                {item.stageLabel}
              </span>
              <span
                className={cn(
                  "text-sm font-bold font-mono tracking-wide",
                  isSelected
                    ? "text-[#CCFF00]"
                    : item.isToday
                      ? "text-[#00F0FF]"
                      : "text-foreground"
                )}
              >
                {item.label}
              </span>
              <span className="text-[10px] text-muted-foreground">{item.dayOfWeek}</span>
              {/* Match dot indicator — always shown since every date has matches */}
              <div
                className={cn(
                  "w-1.5 h-1.5 rounded-full mt-0.5",
                  isSelected
                    ? "bg-[#CCFF00]"
                    : item.isToday
                      ? "bg-[#00F0FF]"
                      : "bg-muted-foreground/40"
                )}
              />
            </button>
          )
        })}
      </div>
    </div>
  )
}
