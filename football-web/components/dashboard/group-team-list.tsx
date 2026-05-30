"use client"

import { useState, useEffect, useCallback } from "react"
import { Users, ChevronRight, ChevronLeft } from "lucide-react"
import { cn } from "@/lib/utils"
import { useTranslation } from "@/lib/i18n"
import { getGroups } from "@/lib/api/groups"
import { TeamFlag } from "@/lib/flags"

// ── Types ──────────────────────────────────────────────────────────────────────

interface GroupTeam {
  id: number
  name: string
  name_zh: string
  code: string
  flag: string
  group_label: string
}

interface GroupOverview {
  group_label: string
  standings: {
    id: number
    team: GroupTeam
    group_label: string
    position: number
  }[]
}

// ── Group color mapping (same as group-standings) ─────────────────────────────

const GROUP_COLORS: Record<string, string> = {
  A: "#CCFF00", B: "#00F0FF", C: "#FF00E5", D: "#FFD700",
  E: "#CCFF00", F: "#00F0FF", G: "#FF00E5", H: "#FFD700",
  I: "#CCFF00", J: "#00F0FF", K: "#FF00E5", L: "#FFD700",
}

// ── Loading Skeleton ───────────────────────────────────────────────────────────

function GroupSkeleton() {
  return (
    <div className="grid grid-cols-2 gap-2">
      {Array.from({ length: 12 }).map((_, i) => (
        <div key={i} className="glass-card rounded-lg overflow-hidden border border-glass-border animate-pulse">
          <div className="px-2 py-1.5 flex items-center justify-center bg-secondary/10">
            <div className="h-3 w-3 rounded bg-secondary/30" />
          </div>
          <div className="py-1 space-y-1.5 px-2">
            {Array.from({ length: 4 }).map((_, j) => (
              <div key={j} className="flex items-center gap-1.5">
                <div className="w-3.5 h-3.5 rounded-sm bg-secondary/20" />
                <div className="h-2.5 w-12 rounded bg-secondary/20" />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

// ── Single Group Mini Card ─────────────────────────────────────────────────────

function GroupMiniCard({ group, locale }: { group: GroupOverview; locale: string }) {
  const color = GROUP_COLORS[group.group_label] ?? "#CCFF00"
  const teamName = (team: GroupTeam) =>
    locale === "zh-CN" ? team.name_zh : team.name

  return (
    <div className="glass-card rounded-lg overflow-hidden border border-glass-border">
      {/* Group header */}
      <div
        className="px-2 py-1.5 flex items-center justify-center"
        style={{
          background: `linear-gradient(135deg, ${color}15 0%, transparent 100%)`,
          borderBottom: `1px solid ${color}20`,
        }}
      >
        <span
          className="text-xs font-black tracking-wider"
          style={{ color }}
        >
          {group.group_label}
        </span>
      </div>

      {/* Team list */}
      <div className="py-1">
        {group.standings.map((row) => (
          <div
            key={row.id}
            className="flex items-center gap-1.5 px-2 py-1 hover:bg-primary/5 transition-colors"
          >
            <TeamFlag code={row.team.code} size={14} className="rounded-sm flex-shrink-0" />
            <span className="text-[11px] text-foreground truncate leading-tight">
              {teamName(row.team)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Main Exported Component ────────────────────────────────────────────────────

export function GroupTeamList() {
  const { t, locale } = useTranslation()
  const [groups, setGroups] = useState<GroupOverview[]>([])
  const [loading, setLoading] = useState(true)
  const [collapsed, setCollapsed] = useState(false)

  const fetchGroups = useCallback(async () => {
    try {
      setLoading(true)
      const data = await getGroups()
      setGroups(data)
    } catch {
      setGroups([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchGroups()
  }, [fetchGroups])

  const hasContent = groups.length > 0 || loading

  if (!hasContent) return null

  return (
    <div
      className={cn(
        "flex-shrink-0 border-l border-glass-border glass-card transition-all duration-300 flex flex-col",
        collapsed ? "w-10" : "w-[220px]"
      )}
    >
      {/* Toggle button */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-center py-2 border-b border-glass-border hover:bg-primary/5 transition-colors flex-shrink-0"
        aria-label={collapsed ? t("bracket.expandGroups") : t("bracket.collapseGroups")}
      >
        {collapsed ? (
          <ChevronLeft className="h-4 w-4 text-muted-foreground" />
        ) : (
          <div className="flex items-center gap-1.5 w-full px-3">
            <Users className="h-3.5 w-3.5 text-accent flex-shrink-0" />
            <span className="text-xs font-bold text-foreground flex-1 text-left">
              {t("bracket.groupTeams")}
            </span>
            <ChevronRight className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
          </div>
        )}
      </button>

      {/* Group grid */}
      {!collapsed && (
        <div className="flex-1 overflow-y-auto scrollbar-hide p-2">
          {loading ? (
            <GroupSkeleton />
          ) : (
            <div className="grid grid-cols-2 gap-2">
              {groups.map((group) => (
                <GroupMiniCard key={group.group_label} group={group} locale={locale} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
