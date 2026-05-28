"use client"

import Link from "next/link"
import { ArrowLeft } from "lucide-react"
import { I18nProvider, useTranslation } from "@/lib/i18n"
import { Header } from "@/components/dashboard/header"
import { GroupStandings } from "@/components/dashboard/group-standings"
import { useState } from "react"

function BackToTimelineLink() {
  const { t } = useTranslation()
  return (
    <div className="px-6 pt-4">
      <Link
        href="/"
        className="inline-flex items-center gap-2 px-4 py-2 rounded-xl glass-card border border-glass-border hover:border-primary/30 transition-all text-sm font-medium text-foreground hover:text-primary group/back"
      >
        <ArrowLeft className="h-4 w-4 text-primary transition-transform group-hover/back:-translate-x-1" />
        <span>{t("groups.backToTimeline")}</span>
      </Link>
    </div>
  )
}

type TimezoneOption = "local" | "host"
type ViewMode = "timeline" | "bracket"

export default function GroupsPage() {
  const [timezone, setTimezone] = useState<TimezoneOption>("local")
  const [viewMode, setViewMode] = useState<ViewMode>("timeline")

  return (
    <I18nProvider>
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

        <main className="flex-1 flex flex-col min-w-0">
          <BackToTimelineLink />
          <GroupStandings />
        </main>

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
    </I18nProvider>
  )
}