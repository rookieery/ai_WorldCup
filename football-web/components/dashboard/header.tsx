"use client"

import { Globe, LayoutGrid, GitBranch, Trophy } from "lucide-react"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"

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
            World Cup 2026
          </h1>
          <p className="text-[10px] text-muted-foreground tracking-[0.2em] uppercase">
            Next-Gen Dashboard
          </p>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-6">
        {/* Timezone Toggle */}
        <div className="flex items-center gap-3 glass-card rounded-xl px-4 py-2.5">
          <Globe className="h-4 w-4 text-[#00F0FF]" />
          <Label
            htmlFor="timezone-toggle"
            className={`text-sm transition-colors cursor-pointer ${
              timezone === "local" ? "text-foreground font-medium" : "text-muted-foreground"
            }`}
          >
            Local
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
            Host City
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
            Timeline
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
            Bracket
          </Label>
        </div>
      </div>
    </header>
  )
}
