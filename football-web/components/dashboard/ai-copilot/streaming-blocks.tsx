"use client"

import { Zap, Hexagon, ChevronDown, ChevronUp } from "lucide-react"
import { MarkdownRenderer } from "@/components/ui/markdown-renderer"

// ── Thinking Indicator ─────────────────────────────────────────────────────────

export function ThinkingIndicator({ message }: { message: string }) {
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
export function TypewriterText({ text, streaming }: { text: string; streaming: boolean }) {
  return (
    <span>
      <MarkdownRenderer content={text} />
      {streaming && (
        <span className="inline-block w-[2px] h-[1em] bg-[#00F0FF] ml-[1px] animate-pulse align-text-bottom" />
      )}
    </span>
  )
}

// ── Thinking Block (collapsible) ───────────────────────────────────────────────

export function ThinkingBlock({
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
        <div className="text-[11px] text-muted-foreground/60 bg-secondary/20 border border-glass-border rounded-lg p-3 leading-relaxed">
          <MarkdownRenderer content={content} />
        </div>
      )}
    </div>
  )
}
