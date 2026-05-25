"use client"

import { useState, useRef, useCallback, useEffect } from "react"
import { Send, Sparkles, Bot, User, Zap, Hexagon, TrendingUp, Shield, Target, Footprints, Activity, ChevronDown, ChevronUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import { useTranslation } from "@/lib/i18n"
import { useAIChatStore, usePreferencesStore } from "@/lib/store"
import { streamChat, type ChatMessageItem } from "@/lib/api/ai-chat"
import type { TeamAnalysis, TeamStats } from "@/lib/types"

// ── Quick Prompts ──────────────────────────────────────────────────────────────

interface QuickPromptDef {
  i18nKey: string
  icon: string
}

const quickPromptDefs: QuickPromptDef[] = [
  { i18nKey: "ai.quickPrompt1", icon: "📅" },
  { i18nKey: "ai.quickPrompt2", icon: "🇲🇽" },
  { i18nKey: "ai.quickPrompt3", icon: "⚽" },
  { i18nKey: "ai.quickPrompt4", icon: "🏆" },
]

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

function AnalysisCard({ data, t }: { data: TeamAnalysis; t: (key: string) => string }) {
  return (
    <div className="space-y-4 mt-2">
      {/* Win Probability Bar */}
      <div className="space-y-2">
        <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">
          {t("ai.winProbability")}
        </p>
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
              <span className="text-[10px] font-medium text-muted-foreground">{t("ai.draw")}</span>
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
          {t("ai.keyInsights")}
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

// ── Thinking Indicator ─────────────────────────────────────────────────────────

function ThinkingIndicator({ message }: { message: string }) {
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
        <span className="text-sm text-muted-foreground">{message}</span>
      </div>
    </div>
  )
}

// ── Typewriter Text ────────────────────────────────────────────────────────────

/** Renders text with a cursor blink at the end while streaming. */
function TypewriterText({ text, streaming }: { text: string; streaming: boolean }) {
  return (
    <span>
      {text}
      {streaming && (
        <span className="inline-block w-[2px] h-[1em] bg-[#00F0FF] ml-[1px] animate-pulse align-text-bottom" />
      )}
    </span>
  )
}

// ── Thinking Block (collapsible) ───────────────────────────────────────────────

function ThinkingBlock({
  content,
  collapsed,
  onToggle,
  t,
}: {
  content: string
  collapsed: boolean
  onToggle: () => void
  t: (key: string) => string
}) {
  return (
    <div className="mb-2">
      <button
        onClick={onToggle}
        className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-muted-foreground/70 hover:text-muted-foreground transition-colors mb-1"
      >
        <Zap className="h-3 w-3 text-[#CCFF00]/60" />
        {t("ai.thinkingLabel")}
        {collapsed ? (
          <ChevronDown className="h-3 w-3" />
        ) : (
          <ChevronUp className="h-3 w-3" />
        )}
      </button>
      {!collapsed && (
        <div className="text-[11px] text-muted-foreground/60 bg-secondary/20 border border-glass-border rounded-lg p-3 leading-relaxed whitespace-pre-wrap">
          {content}
        </div>
      )}
    </div>
  )
}

// ── Main Panel ─────────────────────────────────────────────────────────────────

export function AICopilotPanel() {
  const { t } = useTranslation()
  const language = usePreferencesStore((s) => s.language)

  const {
    messages,
    isStreaming,
    currentStreamContent,
    currentThinkingContent,
    pendingAnalysis,
    addUserMessage,
    startStreaming,
    appendStreamContent,
    appendThinkingContent,
    setPendingAnalysis,
    finishStreaming,
  } = useAIChatStore()

  const [input, setInput] = useState("")
  const [isFocused, setIsFocused] = useState(false)
  const [thinkingCollapsed, setThinkingCollapsed] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [showDisclaimer, setShowDisclaimer] = useState(false)
  const abortRef = useRef<AbortController | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom on new content
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, currentStreamContent, currentThinkingContent, isStreaming])

  // Seed the initial welcome message on first mount
  const seededRef = useRef(false)
  useEffect(() => {
    if (!seededRef.current && messages.length === 0) {
      seededRef.current = true
      useAIChatStore.getState().startStreaming()
      useAIChatStore.getState().appendStreamContent(t("ai.welcomeMessage"))
      useAIChatStore.getState().finishStreaming()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const sendMessage = useCallback(
    (content: string) => {
      const trimmed = content.trim()
      if (!trimmed || isStreaming) return

      setErrorMessage(null)
      setShowDisclaimer(false)

      // Add user message to store
      addUserMessage(trimmed)
      setInput("")

      // Build message history for the backend
      const storeMessages = useAIChatStore.getState().messages
      const chatHistory: ChatMessageItem[] = storeMessages.map((m) => ({
        role: m.role,
        content: m.content,
      }))

      // Start streaming
      const controller = new AbortController()
      abortRef.current = controller
      startStreaming()
      setThinkingCollapsed(false)

      void streamChat(
        chatHistory,
        undefined,
        language,
        {
          onThinking: (delta) => {
            appendThinkingContent(delta)
          },
          onAnswer: (delta) => {
            appendStreamContent(delta)
          },
          onAnalysis: (data) => {
            setPendingAnalysis(data)
          },
          onDone: () => {
            finishStreaming()
            setShowDisclaimer(true)
            abortRef.current = null
          },
          onError: (type) => {
            finishStreaming()
            const msg =
              type === "connection"
                ? t("ai.connectionError")
                : t("ai.streamError")
            setErrorMessage(msg)
            abortRef.current = null
          },
        },
        controller.signal,
      )
    },
    [
      isStreaming,
      language,
      t,
      addUserMessage,
      startStreaming,
      appendStreamContent,
      appendThinkingContent,
      setPendingAnalysis,
      finishStreaming,
    ],
  )

  const handleSend = () => {
    sendMessage(input)
  }

  const handleQuickPrompt = (i18nKey: string) => {
    const promptText = t(i18nKey)
    sendMessage(promptText)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <aside className="w-full h-full flex flex-col relative">
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
                {t("ai.copilotTitle")}
                <Zap className="h-3.5 w-3.5 text-[#CCFF00]" />
              </h2>
              <p className="text-[11px] text-muted-foreground">
                {t("ai.analyticsEngine")}
              </p>
            </div>
          </div>
        </div>

        {/* Quick Prompts */}
        <div className="p-3 border-b border-glass-border bg-glass-highlight">
          <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-2 font-medium">
            {t("ai.quickPrompts")}
          </p>
          <div className="flex flex-wrap gap-2">
            {quickPromptDefs.map((def) => (
              <button
                key={def.i18nKey}
                onClick={() => handleQuickPrompt(def.i18nKey)}
                disabled={isStreaming}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-secondary/30 hover:bg-[#00F0FF]/10 border border-glass-border hover:border-[#00F0FF]/30 rounded-full transition-all duration-300 text-muted-foreground hover:text-[#00F0FF] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span>{def.icon}</span>
                <span>{t(def.i18nKey)}</span>
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
                  <AnalysisCard data={message.analysisData} t={t} />
                )}
              </div>
            </div>
          ))}

          {/* Live streaming response */}
          {isStreaming && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-lg bg-[#00F0FF]/20 border border-[#00F0FF]/30 flex items-center justify-center shrink-0">
                <Bot className="h-4 w-4 text-[#00F0FF]" />
              </div>
              <div className="max-w-[90%] rounded-xl px-4 py-3 text-sm bg-secondary/30 border border-glass-border text-foreground backdrop-blur-sm">
                {/* Thinking block */}
                {currentThinkingContent && (
                  <ThinkingBlock
                    content={currentThinkingContent}
                    collapsed={thinkingCollapsed}
                    onToggle={() => setThinkingCollapsed((v) => !v)}
                    t={t}
                  />
                )}
                {/* Answer text with typewriter */}
                {currentStreamContent ? (
                  <TypewriterText text={currentStreamContent} streaming={isStreaming} />
                ) : (
                  !currentThinkingContent && (
                    <ThinkingIndicator message={t("ai.thinking")} />
                  )
                )}
                {/* Pending analysis rendered during stream */}
                {pendingAnalysis && <AnalysisCard data={pendingAnalysis} t={t} />}
              </div>
            </div>
          )}

          {/* Error message */}
          {errorMessage && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-lg bg-destructive/20 border border-destructive/30 flex items-center justify-center shrink-0">
                <Bot className="h-4 w-4 text-destructive" />
              </div>
              <div className="max-w-[90%] rounded-xl px-4 py-3 text-sm bg-destructive/10 border border-destructive/20 text-destructive">
                {errorMessage}
              </div>
            </div>
          )}

          {/* Disclaimer after stream ends */}
          {showDisclaimer && !isStreaming && (
            <p className="text-[10px] text-muted-foreground/50 text-center">
              {t("ai.disclaimer")}
            </p>
          )}

          <div ref={messagesEndRef} />
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
              onKeyDown={handleKeyDown}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder={t("ai.placeholder")}
              disabled={isStreaming}
              className={cn(
                "pr-12 bg-secondary/30 border-glass-border focus:border-[#00F0FF]/50 placeholder:text-muted-foreground/50 rounded-xl transition-all duration-300",
                isFocused && "border-[#00F0FF] ring-1 ring-[#00F0FF]/30"
              )}
            />
            <Button
              size="icon"
              onClick={handleSend}
              disabled={!input.trim() || isStreaming}
              className={cn(
                "absolute right-1.5 top-1/2 -translate-y-1/2 h-8 w-8 rounded-lg transition-all duration-300",
                input.trim() && !isStreaming
                  ? "bg-[#CCFF00] text-[#020617] hover:bg-[#CCFF00]/90 shadow-[0_0_20px_rgba(204,255,0,0.4)]"
                  : "bg-secondary text-muted-foreground"
              )}
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </aside>
  )
}
