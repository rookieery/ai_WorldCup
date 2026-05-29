"use client"

import { Zap, Shield, Target, Footprints, TrendingUp, Activity } from "lucide-react"
import { TeamFlag } from "@/lib/flags"
import type { TeamAnalysis, TeamStats } from "@/lib/types"

// ── Mini Radar Chart ───────────────────────────────────────────────────────────

function MiniRadarChart({ stats, color, label }: { stats: TeamStats; color: string; label: string }) {
  const centerX = 60
  const centerY = 60
  const radius = 45
  const categories = [
    { key: "attack", angle: -90 },
    { key: "defense", angle: -18 },
    { key: "form", angle: 54 },
    { key: "possession", angle: 126 },
    { key: "setpieces", angle: 198 },
  ]

  const getPoint = (value: number, angleDeg: number) => {
    const angleRad = (angleDeg * Math.PI) / 180
    const r = (value / 100) * radius
    return {
      x: centerX + r * Math.cos(angleRad),
      y: centerY + r * Math.sin(angleRad),
    }
  }

  const points = categories.map((cat) =>
    getPoint(stats[cat.key as keyof TeamStats], cat.angle)
  )

  const pathD = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ") + " Z"

  return (
    <div className="relative">
      <svg width="120" height="120" viewBox="0 0 120 120">
        {[0.25, 0.5, 0.75, 1].map((scale) => (
          <polygon
            key={scale}
            points={categories
              .map((cat) => {
                const p = getPoint(100 * scale, cat.angle)
                return `${p.x},${p.y}`
              })
              .join(" ")}
            fill="none"
            stroke="rgba(255,255,255,0.1)"
            strokeWidth="1"
          />
        ))}

        {categories.map((cat) => {
          const p = getPoint(100, cat.angle)
          return (
            <line
              key={cat.key}
              x1={centerX}
              y1={centerY}
              x2={p.x}
              y2={p.y}
              stroke="rgba(255,255,255,0.1)"
              strokeWidth="1"
            />
          )
        })}

        <path
          d={pathD}
          fill={`${color}20`}
          stroke={color}
          strokeWidth="2"
          className="drop-shadow-[0_0_6px_rgba(0,240,255,0.5)]"
        />

        {points.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r="3"
            fill={color}
            className="drop-shadow-[0_0_4px_rgba(0,240,255,0.8)]"
          />
        ))}
      </svg>
      <p className="text-[10px] text-center text-muted-foreground mt-1">{label}</p>
    </div>
  )
}

// ── Analysis Card ──────────────────────────────────────────────────────────────

export function AnalysisCard({ data, t }: { data: TeamAnalysis; t: (key: string) => string }) {
  return (
    <div className="space-y-4 mt-2">
      {/* Win Probability Bar */}
      <div className="space-y-2">
        <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">
          {t("ai.winProbability")}
        </p>
        <div className="flex items-center gap-2">
          <TeamFlag code={data.team1.code ?? data.team1.name} size={20} className="rounded-sm" />
          <div className="flex-1 h-8 rounded-lg overflow-hidden flex relative">
            <div
              className="bg-gradient-to-r from-[#CCFF00] to-[#CCFF00]/70 flex items-center justify-end pr-2 transition-all duration-500"
              style={{ width: `${data.team1.winProbability}%` }}
            >
              <span className="text-xs font-bold text-[#020617]">{data.team1.winProbability}%</span>
            </div>
            <div
              className="bg-secondary/50 flex items-center justify-center transition-all duration-500"
              style={{ width: `${data.drawProbability}%` }}
            >
              <span className="text-[10px] font-medium text-muted-foreground">{t("ai.draw")}</span>
            </div>
            <div
              className="bg-gradient-to-l from-[#00F0FF] to-[#00F0FF]/70 flex items-center justify-start pl-2 transition-all duration-500"
              style={{ width: `${data.team2.winProbability}%` }}
            >
              <span className="text-xs font-bold text-[#020617]">{data.team2.winProbability}%</span>
            </div>
          </div>
          <TeamFlag code={data.team2.code ?? data.team2.name} size={20} className="rounded-sm" />
        </div>
      </div>

      {/* Radar Charts */}
      <div className="flex justify-between items-center">
        <MiniRadarChart stats={data.team1.stats} color="#CCFF00" label={data.team1.name} />
        <div className="text-center">
          <p className="text-lg font-bold text-muted-foreground">VS</p>
          <Activity className="h-5 w-5 text-[#FF00E5] mx-auto mt-1" />
        </div>
        <MiniRadarChart stats={data.team2.stats} color="#00F0FF" label={data.team2.name} />
      </div>

      {/* Key Insights */}
      <div className="space-y-2">
        <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium flex items-center gap-1.5">
          <Zap className="h-3 w-3 text-[#CCFF00]" />
          {t("ai.keyInsights")}
        </p>
        <ul className="space-y-1.5">
          {data.keyInsights.map((insight, i) => (
            <li key={i} className="flex items-start gap-2 text-xs text-foreground/80">
              <span className="text-[#00F0FF] mt-0.5">&#9656;</span>
              {insight}
            </li>
          ))}
        </ul>
      </div>

      {/* Stats Legend */}
      <div className="flex flex-wrap gap-2 pt-2 border-t border-glass-border">
        {[
          { icon: Target, labelKey: "ai.statATK", color: "#FF00E5" },
          { icon: Shield, labelKey: "ai.statDEF", color: "#00F0FF" },
          { icon: Footprints, labelKey: "ai.statPOSS", color: "#CCFF00" },
          { icon: TrendingUp, labelKey: "ai.statFORM", color: "#FFD700" },
        ].map((stat) => (
          <div key={stat.labelKey} className="flex items-center gap-1 text-[10px] text-muted-foreground">
            <stat.icon className="h-3 w-3" style={{ color: stat.color }} />
            <span>{t(stat.labelKey)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
