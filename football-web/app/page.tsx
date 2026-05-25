"use client"

import { useState } from "react"
import Link from "next/link"
import { Trophy } from "lucide-react"
import { Header } from "@/components/dashboard/header"
import { DateTimeline } from "@/components/dashboard/date-timeline"
import { MatchCardsGrid } from "@/components/dashboard/match-cards-grid"
import { TournamentBracket } from "@/components/dashboard/tournament-bracket"
import { AICopilotPanel } from "@/components/dashboard/ai-copilot-panel"
import { AICopilotMobile } from "@/components/dashboard/ai-copilot-mobile"
import { useTranslation } from "@/lib/i18n"

type TimezoneOption = "local" | "host"
type ViewMode = "timeline" | "bracket"

export default function WorldCupDashboard() {
  const [timezone, setTimezone] = useState<TimezoneOption>("local")
  const [viewMode, setViewMode] = useState<ViewMode>("bracket")
  const [selectedDate, setSelectedDate] = useState("")
  const { t } = useTranslation()

  return (
    <div className="min-h-screen flex flex-col">
      {/* Background Effects - Mesh Gradients */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        {/* Large soft mesh gradients with animation */}
        <div
          className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full blur-[120px] mesh-gradient-1"
          style={{
            background: "radial-gradient(circle, rgba(0, 240, 255, 0.15) 0%, transparent 70%)",
          }}
        />
        <div
          className="absolute top-[30%] right-[-5%] w-[500px] h-[500px] rounded-full blur-[100px] mesh-gradient-2"
          style={{
            background: "radial-gradient(circle, rgba(255, 0, 229, 0.12) 0%, transparent 70%)",
          }}
        />
        <div
          className="absolute bottom-[-10%] left-[30%] w-[700px] h-[700px] rounded-full blur-[140px] mesh-gradient-1"
          style={{
            background: "radial-gradient(circle, rgba(204, 255, 0, 0.08) 0%, transparent 70%)",
            animationDelay: "-5s",
          }}
        />

        {/* Subtle grid overlay */}
        <div
          className="absolute inset-0 opacity-[0.015]"
          style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
            backgroundSize: "60px 60px",
          }}
        />

        {/* Subtle noise texture */}
        <div
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
          }}
        />
      </div>

      {/* Header */}
      <Header
        timezone={timezone}
        viewMode={viewMode}
        onTimezoneChange={setTimezone}
        onViewModeChange={setViewMode}
      />

      {/* Main Content */}
      <div className="flex-1 flex relative">
        {/* Left/Center - Main Content (70%) */}
        <main className="flex-1 flex flex-col min-w-0">
          {viewMode === "timeline" ? (
            <>
              {/* Date Timeline */}
              <div className="border-b border-glass-border glass-card">
                <DateTimeline
                  selectedDate={selectedDate}
                  onDateSelect={setSelectedDate}
                />
              </div>

              {/* Groups Quick Entry */}
              <div className="px-6 pt-4">
                <Link
                  href="/groups"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl glass-card border border-glass-border hover:border-primary/30 transition-all text-sm font-medium text-foreground hover:text-primary group/entry"
                >
                  <Trophy className="h-4 w-4 text-primary" />
                  <span>{t("groups.title")}</span>
                  <span className="text-[10px] text-muted-foreground group-hover/entry:text-primary/60 transition-colors">
                    A-L
                  </span>
                </Link>
              </div>

              {/* Match Cards */}
              <MatchCardsGrid selectedDate={selectedDate} timezone={timezone} />
            </>
          ) : (
            /* Tournament Bracket */
            <TournamentBracket />
          )}
        </main>

        {/* Right Sidebar - AI Copilot (30%) — desktop only */}
        <div className="w-[30%] min-w-[340px] max-w-[480px] hidden lg:block border-l border-glass-border">
          <AICopilotPanel />
        </div>
      </div>

      {/* Mobile AI Copilot — FAB + bottom-sheet drawer */}
      <AICopilotMobile />

      {/* Footer Status Bar */}
      <footer className="h-10 border-t border-glass-border glass-card px-6 flex items-center justify-between text-xs text-muted-foreground relative z-10">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <div className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#CCFF00] opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#CCFF00]" />
            </div>
            <span>{t("footer.liveUpdates")}</span>
          </div>
          <span className="text-border">|</span>
          <span>{t("footer.teamsCitiesMatches")}</span>
        </div>
        <div className="flex items-center gap-4">
          <span>{t("footer.dataRefreshed")}</span>
          <span className="text-border">|</span>
          <span className="text-[#CCFF00] font-bold tracking-wide">{t("footer.fifaBrand")}</span>
        </div>
      </footer>
    </div>
  )
}
