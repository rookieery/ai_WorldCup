"use client"

import { Globe, LayoutGrid, GitBranch, Trophy, Clock } from "lucide-react"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useTranslation } from "@/lib/i18n"
import type { Locale } from "@/lib/i18n"

interface HeaderProps {
  timezone: "local" | "host"
  viewMode: "timeline" | "bracket"
  onTimezoneChange: (value: "local" | "host") => void
  onViewModeChange: (value: "timeline" | "bracket") => void
}

export function Header({
  timezone,
  viewMode,
  onTimezoneChange,
  onViewModeChange,
}: HeaderProps) {
  const { t, locale, setLocale } = useTranslation()

  return (
    <header className="h-16 border-b border-glass-border glass-card px-6 flex items-center justify-between sticky top-0 z-50">
      {/* Logo & Title */}
      <div className="flex items-center gap-4">
        <div className="relative">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#CCFF00]/20 to-[#FFD700]/20 border border-[#CCFF00]/30 flex items-center justify-center">
            <Trophy className="h-5 w-5 text-[#CCFF00]" />
          </div>
          <div className="absolute inset-0 blur-xl bg-[#CCFF00]/20 -z-10" />
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-tight text-foreground">
            {t("header.title")}
          </h1>
          <p className="text-[10px] text-muted-foreground tracking-[0.2em] uppercase">
            {t("header.subtitle")}
          </p>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-6">
        {/* Language Switch */}
        <div className="flex items-center gap-2 glass-card rounded-xl px-3 py-2">
          <Globe className="h-4 w-4 text-[#CCFF00]" />
          <Select
            value={locale}
            onValueChange={(value) => setLocale(value as Locale)}
          >
            <SelectTrigger
              size="sm"
              className="border-0 bg-transparent shadow-none h-7 text-sm gap-1 px-1 focus-visible:ring-0 focus-visible:ring-offset-0"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="zh-CN">{t("header.langZh")}</SelectItem>
              <SelectItem value="en-US">{t("header.langEn")}</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Timezone Toggle */}
        <div className="flex items-center gap-3 glass-card rounded-xl px-4 py-2.5">
          <Clock className="h-4 w-4 text-[#00F0FF]" />
          <Label
            htmlFor="timezone-toggle"
            className={`text-sm transition-colors cursor-pointer ${
              timezone === "local" ? "text-foreground font-medium" : "text-muted-foreground"
            }`}
          >
            {t("header.local")}
          </Label>
          <Switch
            id="timezone-toggle"
            checked={timezone === "host"}
            onCheckedChange={(checked) =>
              onTimezoneChange(checked ? "host" : "local")
            }
            className="data-[state=checked]:bg-[#00F0FF] data-[state=unchecked]:bg-secondary"
          />
          <Label
            htmlFor="timezone-toggle"
            className={`text-sm transition-colors cursor-pointer ${
              timezone === "host" ? "text-foreground font-medium" : "text-muted-foreground"
            }`}
          >
            {t("header.hostCity")}
          </Label>
        </div>

        {/* View Mode Toggle */}
        <div className="flex items-center gap-3 glass-card rounded-xl px-4 py-2.5">
          <LayoutGrid className="h-4 w-4 text-[#FF00E5]" />
          <Label
            htmlFor="view-toggle"
            className={`text-sm transition-colors cursor-pointer ${
              viewMode === "timeline"
                ? "text-foreground font-medium"
                : "text-muted-foreground"
            }`}
          >
            {t("header.timeline")}
          </Label>
          <Switch
            id="view-toggle"
            checked={viewMode === "bracket"}
            onCheckedChange={(checked) =>
              onViewModeChange(checked ? "bracket" : "timeline")
            }
            className="data-[state=checked]:bg-[#FF00E5] data-[state=unchecked]:bg-secondary"
          />
          <Label
            htmlFor="view-toggle"
            className={`text-sm transition-colors cursor-pointer flex items-center gap-1.5 ${
              viewMode === "bracket"
                ? "text-foreground font-medium"
                : "text-muted-foreground"
            }`}
          >
            <GitBranch className="h-3.5 w-3.5" />
            {t("header.bracket")}
          </Label>
        </div>
      </div>
    </header>
  )
}
