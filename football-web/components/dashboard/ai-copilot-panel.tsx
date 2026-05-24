"use client"

import { useState, useEffect } from "react"
import { Send, Sparkles, Bot, User, Zap, Hexagon, TrendingUp, Shield, Target, Footprints, Activity } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import type { Message, TeamAnalysis, TeamStats } from "@/lib/types"

const quickPrompts = [
  { label: "Who plays tomorrow?", icon: "📅" },
  { label: "Mexico win probability?", icon: "🇲🇽" },
  { label: "Top scorers so far", icon: "⚽" },
  { label: "Bracket predictions", icon: "🏆" },
]

const brazilFranceAnalysis: TeamAnalysis = {
  team1: {
    name: "Brazil",
    flag: "🇧🇷",
    stats: { attack: 92, defense: 78, possession: 68, setpieces: 75, form: 88 },
    winProbability: 42,
  },
  team2: {
    name: "France",
    flag: "🇫🇷",
    stats: { attack: 89, defense: 85, possession: 62, setpieces: 82, form: 85 },
    winProbability: 35,
  },
  drawProbability: 23,
  keyInsights: [
    "Brazil has 15% higher attack rating in open play",
    "France leads in set-piece conversion (82% vs 75%)",
    "Historical H2H: Brazil 5W, France 4W, 3D",
    "Mbappé vs Vinícius Jr - key matchup to watch",
  ],
}

const initialMessages: Message[] = [
  {
    id: 1,
    role: "assistant",
    content:
      "Welcome to World Cup 2026! I'm your AI Copilot, powered by advanced match analytics. Ask me about live scores, predictions, player stats, or tournament insights.",
    type: "text",
  },
  {
    id: 2,
    role: "user",
    content: "Analyze the Brazil vs France matchup",
    type: "text",
  },
  {
    id: 3,
    role: "assistant",
    content: "Here's my comprehensive analysis of the Brazil vs France semi-final:",
    type: "analysis",
    analysisData: brazilFranceAnalysis,
  },
]

// Mini Radar Chart Component
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
    getPoint(stats[cat.key as keyof typeof stats], cat.angle)
  )

  const pathD = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ") + " Z"

  return (
    <div className="relative">
      <svg width="120" height="120" viewBox="0 0 120 120">
        {/* Background circles */}
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

        {/* Axis lines */}
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

        {/* Data polygon */}
        <path
          d={pathD}
          fill={`${color}20`}
          stroke={color}
          strokeWidth="2"
          className="drop-shadow-[0_0_6px_rgba(0,240,255,0.5)]"
        />

        {/* Data points */}
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

// Analysis Card Component
function AnalysisCard({ data }: { data: TeamAnalysis }) {
  return (
    <div className="space-y-4 mt-2">
      {/* Win Probability Bar */}
      <div className="space-y-2">
        <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Win Probability</p>
        <div className="flex items-center gap-2">
          <span className="text-lg">{data.team1.flag}</span>
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
              <span className="text-[10px] font-medium text-muted-foreground">Draw</span>
            </div>
            <div
              className="bg-gradient-to-l from-[#00F0FF] to-[#00F0FF]/70 flex items-center justify-start pl-2 transition-all duration-500"
              style={{ width: `${data.team2.winProbability}%` }}
            >
              <span className="text-xs font-bold text-[#020617]">{data.team2.winProbability}%</span>
            </div>
          </div>
          <span className="text-lg">{data.team2.flag}</span>
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
          Key Insights
        </p>
        <ul className="space-y-1.5">
          {data.keyInsights.map((insight, i) => (
            <li key={i} className="flex items-start gap-2 text-xs text-foreground/80">
              <span className="text-[#00F0FF] mt-0.5">▸</span>
              {insight}
            </li>
          ))}
        </ul>
      </div>

      {/* Stats Legend */}
      <div className="flex flex-wrap gap-2 pt-2 border-t border-glass-border">
        {[
          { icon: Target, label: "ATK", color: "#FF00E5" },
          { icon: Shield, label: "DEF", color: "#00F0FF" },
          { icon: Footprints, label: "POSS", color: "#CCFF00" },
          { icon: TrendingUp, label: "FORM", color: "#FFD700" },
        ].map((stat) => (
          <div key={stat.label} className="flex items-center gap-1 text-[10px] text-muted-foreground">
            <stat.icon className="h-3 w-3" style={{ color: stat.color }} />
            <span>{stat.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// Thinking Indicator Component
function ThinkingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-lg bg-[#00F0FF]/20 border border-[#00F0FF]/30 flex items-center justify-center">
        <Hexagon className="h-4 w-4 text-[#00F0FF] spin-geometric" />
      </div>
      <div className="bg-secondary/30 border border-glass-border rounded-xl px-4 py-3 flex items-center gap-3">
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-[#00F0FF] animate-pulse" style={{ animationDelay: "0ms" }} />
          <div className="w-2 h-2 rounded-full bg-[#00F0FF] animate-pulse" style={{ animationDelay: "150ms" }} />
          <div className="w-2 h-2 rounded-full bg-[#00F0FF] animate-pulse" style={{ animationDelay: "300ms" }} />
        </div>
        <span className="text-sm text-muted-foreground">Processing query...</span>
      </div>
    </div>
  )
}

export function AICopilotPanel() {
  const [messages, setMessages] = useState<Message[]>(initialMessages)
  const [input, setInput] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const [isFocused, setIsFocused] = useState(false)

  const handleSend = () => {
    if (!input.trim()) return

    const userMessage: Message = {
      id: messages.length + 1,
      role: "user",
      content: input,
      type: "text",
    }
    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsTyping(true)

    setTimeout(() => {
      const aiMessage: Message = {
        id: messages.length + 2,
        role: "assistant",
        content:
          "Based on my analysis of recent match data, team form, and historical performance metrics, I can provide detailed insights. This is a demo response - the full AI integration will deliver real-time predictions and statistics.",
        type: "text",
      }
      setMessages((prev) => [...prev, aiMessage])
      setIsTyping(false)
    }, 2000)
  }

  const handleQuickPrompt = (prompt: string) => {
    setInput(prompt)
  }

  return (
    <aside className="w-full h-full flex flex-col relative">
      {/* Floating Glass Module Effect */}
      <div className="absolute inset-2 glass-card rounded-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-glass-border">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-[#00F0FF]/20 to-[#FF00E5]/20 border border-[#00F0FF]/30 flex items-center justify-center">
                <Sparkles className="h-5 w-5 text-[#00F0FF]" />
              </div>
              <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full bg-[#CCFF00] border-2 border-[#020617] animate-pulse" />
            </div>
            <div>
              <h2 className="font-bold text-foreground flex items-center gap-2">
                World Cup AI Copilot
                <Zap className="h-3.5 w-3.5 text-[#CCFF00]" />
              </h2>
              <p className="text-[11px] text-muted-foreground">
                Real-time analytics engine
              </p>
            </div>
          </div>
        </div>

        {/* Quick Prompts */}
        <div className="p-3 border-b border-glass-border bg-glass-highlight">
          <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-2 font-medium">
            Quick Prompts
          </p>
          <div className="flex flex-wrap gap-2">
            {quickPrompts.map((prompt) => (
              <button
                key={prompt.label}
                onClick={() => handleQuickPrompt(prompt.label)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-secondary/30 hover:bg-[#00F0FF]/10 border border-glass-border hover:border-[#00F0FF]/30 rounded-full transition-all duration-300 text-muted-foreground hover:text-[#00F0FF]"
              >
                <span>{prompt.icon}</span>
                <span>{prompt.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex gap-3",
                message.role === "user" ? "flex-row-reverse" : "flex-row"
              )}
            >
              <div
                className={cn(
                  "w-8 h-8 rounded-lg flex items-center justify-center shrink-0",
                  message.role === "user"
                    ? "bg-[#CCFF00]/20 border border-[#CCFF00]/30"
                    : "bg-[#00F0FF]/20 border border-[#00F0FF]/30"
                )}
              >
                {message.role === "user" ? (
                  <User className="h-4 w-4 text-[#CCFF00]" />
                ) : (
                  <Bot className="h-4 w-4 text-[#00F0FF]" />
                )}
              </div>
              <div
                className={cn(
                  "max-w-[90%] rounded-xl px-4 py-3 text-sm",
                  message.role === "user"
                    ? "bg-[#CCFF00]/10 border border-[#CCFF00]/20 text-foreground"
                    : "bg-secondary/30 border border-glass-border text-foreground backdrop-blur-sm"
                )}
              >
                {message.content}
                {message.type === "analysis" && message.analysisData && (
                  <AnalysisCard data={message.analysisData} />
                )}
              </div>
            </div>
          ))}

          {/* Thinking Animation */}
          {isTyping && <ThinkingIndicator />}
        </div>

        {/* Input with Focus Glow */}
        <div className="p-4 border-t border-glass-border">
          <div
            className={cn(
              "relative rounded-xl transition-all duration-300",
              isFocused && "shadow-[0_0_20px_rgba(0,240,255,0.3)]"
            )}
          >
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder="Ask about matches, predictions, stats..."
              className={cn(
                "pr-12 bg-secondary/30 border-glass-border focus:border-[#00F0FF]/50 placeholder:text-muted-foreground/50 rounded-xl transition-all duration-300",
                isFocused && "border-[#00F0FF] ring-1 ring-[#00F0FF]/30"
              )}
            />
            <Button
              size="icon"
              onClick={handleSend}
              disabled={!input.trim()}
              className={cn(
                "absolute right-1.5 top-1/2 -translate-y-1/2 h-8 w-8 rounded-lg transition-all duration-300",
                input.trim()
                  ? "bg-[#CCFF00] text-[#020617] hover:bg-[#CCFF00]/90 shadow-[0_0_20px_rgba(204,255,0,0.4)]"
                  : "bg-secondary text-muted-foreground"
              )}
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
          <p className="text-[10px] text-muted-foreground/50 mt-2 text-center">
            AI predictions are for entertainment purposes only
          </p>
        </div>
      </div>
    </aside>
  )
}
