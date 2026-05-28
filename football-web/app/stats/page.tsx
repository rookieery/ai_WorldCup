"use client"

import { BarChart3 } from "lucide-react"
import { Header } from "@/components/dashboard/header"
import { ScorersTable } from "@/components/stats/scorers-table"
import { MatchStatsCard } from "@/components/stats/match-stats-card"
import { useTranslation } from "@/lib/i18n"
import { useState } from "react"

type TimezoneOption = "local" | "host"
type ViewMode = "timeline" | "bracket"

export default function StatsPage() {
  const [timezone, setTimezone] = useState<TimezoneOption>("local")
  const [viewMode, setViewMode] = useState<ViewMode>("bracket")
  const { t } = useTranslation()

  return (
    <div className="min-h-screen flex flex-col">
      {/* Background Effects */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div
          className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full blur-[120px]"
          style={{
            background: "radial-gradient(circle, rgba(0, 240, 255, 0.15) 0%, transparent 70%)",
          }}
        />
        <div
          className="absolute top-[30%] right-[-5%] w-[500px] h-[500px] rounded-full blur-[100px]"
          style={{
            background: "radial-gradient(circle, rgba(255, 0, 229, 0.12) 0%, transparent 70%)",
          }}
        />
        <div
          className="absolute bottom-[-10%] left-[30%] w-[700px] h-[700px] rounded-full blur-[140px]"
          style={{
            background: "radial-gradient(circle, rgba(204, 255, 0, 0.08) 0%, transparent 70%)",
          }}
        />
      </div>

      <Header
        timezone={timezone}
        viewMode={viewMode}
        onTimezoneChange={setTimezone}
        onViewModeChange={setViewMode}
      />

      <main className="flex-1 flex flex-col min-w-0 p-6">
        {/* Page Title */}
        <div className="flex items-center gap-4 mb-6">
          <div className="relative">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#00F0FF]/20 to-[#FF00E5]/20 border border-[#00F0FF]/30 flex items-center justify-center">
              <BarChart3 className="h-6 w-6 text-[#00F0FF]" />
            </div>
            <div className="absolute inset-0 blur-xl bg-[#00F0FF]/20 -z-10" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground">{t("stats.title")}</h1>
            <p className="text-sm text-muted-foreground">{t("stats.subtitle")}</p>
          </div>
        </div>

        {/* Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Scorers Table (takes 2 cols) */}
          <div className="lg:col-span-2">
            <ScorersTable />
          </div>

          {/* Right: Match Stats Card */}
          <div className="lg:col-span-1">
            <MatchStatsCard />
          </div>
        </div>
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
        <span className="text-primary font-bold tracking-wide">FIFA World Cup 2026</span>
      </footer>
    </div>
  )
}
