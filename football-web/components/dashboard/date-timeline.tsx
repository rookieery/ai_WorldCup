"use client"

import { useRef } from "react"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const dates = [
  { date: "Jun 11", day: "Wed", isToday: false, hasMatches: true, stage: "Group" },
  { date: "Jun 12", day: "Thu", isToday: false, hasMatches: true, stage: "Group" },
  { date: "Jun 13", day: "Fri", isToday: false, hasMatches: true, stage: "Group" },
  { date: "Jun 14", day: "Sat", isToday: true, hasMatches: true, stage: "Group" },
  { date: "Jun 15", day: "Sun", isToday: false, hasMatches: true, stage: "Group" },
  { date: "Jun 16", day: "Mon", isToday: false, hasMatches: true, stage: "Group" },
  { date: "Jun 17", day: "Tue", isToday: false, hasMatches: true, stage: "Group" },
  { date: "Jun 18", day: "Wed", isToday: false, hasMatches: true, stage: "Group" },
  { date: "Jun 19", day: "Thu", isToday: false, hasMatches: true, stage: "Group" },
  { date: "Jun 20", day: "Fri", isToday: false, hasMatches: true, stage: "Group" },
  { date: "Jun 21", day: "Sat", isToday: false, hasMatches: true, stage: "Group" },
  { date: "Jun 22", day: "Sun", isToday: false, hasMatches: true, stage: "Group" },
  { date: "Jun 23", day: "Mon", isToday: false, hasMatches: true, stage: "Group" },
  { date: "Jun 24", day: "Tue", isToday: false, hasMatches: true, stage: "Group" },
  { date: "Jun 25", day: "Wed", isToday: false, hasMatches: true, stage: "Group" },
  { date: "Jun 26", day: "Thu", isToday: false, hasMatches: true, stage: "Group" },
  { date: "Jun 27", day: "Fri", isToday: false, hasMatches: false, stage: "Rest" },
  { date: "Jun 28", day: "Sat", isToday: false, hasMatches: true, stage: "R32" },
  { date: "Jun 29", day: "Sun", isToday: false, hasMatches: true, stage: "R32" },
  { date: "Jun 30", day: "Mon", isToday: false, hasMatches: true, stage: "R32" },
  { date: "Jul 01", day: "Tue", isToday: false, hasMatches: true, stage: "R32" },
  { date: "Jul 02", day: "Wed", isToday: false, hasMatches: true, stage: "R16" },
  { date: "Jul 03", day: "Thu", isToday: false, hasMatches: true, stage: "R16" },
  { date: "Jul 04", day: "Fri", isToday: false, hasMatches: true, stage: "R16" },
  { date: "Jul 05", day: "Sat", isToday: false, hasMatches: true, stage: "R16" },
  { date: "Jul 06", day: "Sun", isToday: false, hasMatches: false, stage: "Rest" },
  { date: "Jul 07", day: "Mon", isToday: false, hasMatches: true, stage: "QF" },
  { date: "Jul 08", day: "Tue", isToday: false, hasMatches: true, stage: "QF" },
  { date: "Jul 09", day: "Wed", isToday: false, hasMatches: false, stage: "Rest" },
  { date: "Jul 10", day: "Thu", isToday: false, hasMatches: true, stage: "SF" },
  { date: "Jul 11", day: "Fri", isToday: false, hasMatches: true, stage: "SF" },
  { date: "Jul 12", day: "Sat", isToday: false, hasMatches: false, stage: "Rest" },
  { date: "Jul 13", day: "Sun", isToday: false, hasMatches: true, stage: "3rd" },
  { date: "Jul 14", day: "Mon", isToday: false, hasMatches: false, stage: "Rest" },
  { date: "Jul 15", day: "Tue", isToday: false, hasMatches: false, stage: "Rest" },
  { date: "Jul 16", day: "Wed", isToday: false, hasMatches: false, stage: "Rest" },
  { date: "Jul 17", day: "Thu", isToday: false, hasMatches: false, stage: "Rest" },
  { date: "Jul 18", day: "Fri", isToday: false, hasMatches: false, stage: "Rest" },
  { date: "Jul 19", day: "Sat", isToday: false, hasMatches: true, stage: "Final" },
]

interface DateTimelineProps {
  selectedDate: string
  onDateSelect: (date: string) => void
}

export function DateTimeline({ selectedDate, onDateSelect }: DateTimelineProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  const scroll = (direction: "left" | "right") => {
    if (scrollRef.current) {
      const scrollAmount = direction === "left" ? -300 : 300
      scrollRef.current.scrollBy({ left: scrollAmount, behavior: "smooth" })
    }
  }

  const getStageColor = (stage: string, isSelected: boolean, isToday: boolean) => {
    if (isSelected) {
      return "bg-[#CCFF00]/20 text-[#CCFF00] border-[#CCFF00]/30"
    }
    switch (stage) {
      case "Group":
        return "bg-[#CCFF00]/10 text-[#CCFF00]/80"
      case "R32":
      case "R16":
        return "bg-[#00F0FF]/10 text-[#00F0FF]/80"
      case "QF":
      case "SF":
        return "bg-[#FF00E5]/10 text-[#FF00E5]/80"
      case "3rd":
      case "Final":
        return "bg-[#FFD700]/10 text-[#FFD700]/80"
      default:
        return "bg-muted text-muted-foreground"
    }
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
          const isSelected = selectedDate === item.date
          return (
            <button
              key={item.date}
              onClick={() => onDateSelect(item.date)}
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
                  getStageColor(item.stage, isSelected, item.isToday)
                )}
              >
                {item.stage}
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
                {item.date}
              </span>
              <span className="text-[10px] text-muted-foreground">{item.day}</span>
              {item.hasMatches && (
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
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}
