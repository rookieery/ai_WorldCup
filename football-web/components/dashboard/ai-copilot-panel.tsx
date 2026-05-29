"use client"

import { useState, useRef, useCallback, useEffect } from "react"
import { Send, Sparkles, Bot, User, Zap } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import { useTranslation } from "@/lib/i18n"
import { useAIChatStore, usePreferencesStore } from "@/lib/store"
import { streamChat, type ChatMessageItem } from "@/lib/api/ai-chat"
import { MarkdownRenderer } from "@/components/ui/markdown-renderer"
import { AnalysisCard } from "@/components/dashboard/ai-copilot/analysis-card"
import { ThinkingIndicator, TypewriterText, ThinkingBlock } from "@/components/dashboard/ai-copilot/streaming-blocks"

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
  const [streamGlow, setStreamGlow] = useState(false)
  const abortRef = useRef<AbortController | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const prevStreamingRef = useRef(false)

  // Auto-scroll to bottom on new content
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, currentStreamContent, currentThinkingContent, isStreaming])

  // Brief glow when streaming starts to draw attention to the panel
  useEffect(() => {
    if (isStreaming && !prevStreamingRef.current) {
      setStreamGlow(true)
      const timer = setTimeout(() => setStreamGlow(false), 2000)
      return () => clearTimeout(timer)
    }
    prevStreamingRef.current = isStreaming
  }, [isStreaming])

  // Seed the initial welcome message; re-seed when language changes
  // and no real conversation has started yet.
  useEffect(() => {
    const store = useAIChatStore.getState()
    const hasConversation = store.messages.some((m) => m.role === "user")
    if (hasConversation) return

    const welcomeText = t("ai.welcomeMessage")
    if (store.messages.length === 0) {
      store.startStreaming()
      store.appendStreamContent(welcomeText)
      store.finishStreaming()
    } else if (
      store.messages.length === 1 &&
      store.messages[0].role === "assistant" &&
      store.messages[0].content !== welcomeText
    ) {
      useAIChatStore.setState((s) => ({
        messages: [{ ...s.messages[0], content: welcomeText }],
      }))
    }
  }, [language, t]) // eslint-disable-line react-hooks/exhaustive-deps

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
      <div
        className={cn(
          "absolute inset-2 glass-card rounded-2xl overflow-hidden flex flex-col transition-shadow duration-700",
          streamGlow && "shadow-[0_0_40px_rgba(0,240,255,0.3),0_0_80px_rgba(0,240,255,0.1)]",
        )}
      >
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
          {messages.map((message) => {
            const isAnalysisContext = message.type === "analysis-context"

            return (
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
                    isAnalysisContext
                      ? "bg-gradient-to-br from-[#00F0FF]/20 to-[#CCFF00]/20 border border-[#00F0FF]/30"
                      : message.role === "user"
                        ? "bg-[#CCFF00]/20 border border-[#CCFF00]/30"
                        : "bg-[#00F0FF]/20 border border-[#00F0FF]/30"
                  )}
                >
                  {isAnalysisContext ? (
                    <Sparkles className="h-4 w-4 text-[#00F0FF]" />
                  ) : message.role === "user" ? (
                    <User className="h-4 w-4 text-[#CCFF00]" />
                  ) : (
                    <Bot className="h-4 w-4 text-[#00F0FF]" />
                  )}
                </div>
                <div
                  className={cn(
                    "max-w-[90%] rounded-xl px-4 py-3 text-sm",
                    isAnalysisContext
                      ? "bg-gradient-to-br from-[#00F0FF]/10 to-[#CCFF00]/5 border border-[#00F0FF]/30 text-foreground"
                      : message.role === "user"
                        ? "bg-[#CCFF00]/10 border border-[#CCFF00]/20 text-foreground"
                        : "bg-secondary/30 border border-glass-border text-foreground backdrop-blur-sm"
                  )}
                >
                  {message.role === "assistant" ? (
                    <MarkdownRenderer content={message.content} />
                  ) : (
                    message.content
                  )}
                  {message.type === "analysis" && message.analysisData && (
                    <AnalysisCard data={message.analysisData} t={t} />
                  )}
                </div>
              </div>
            )
          })}

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
