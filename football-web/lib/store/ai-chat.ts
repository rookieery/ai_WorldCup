/**
 * AI Chat Store — conversation state for the AI Copilot panel.
 *
 * Manages the message history, streaming state, and the current stream
 * content buffer. Designed to be driven by the SSE consumer
 * (`@/lib/api/ai-chat.ts`) which pushes events into this store.
 */

import { create } from "zustand"
import type { Message, TeamAnalysis } from "@/lib/types"

// ── Types ──────────────────────────────────────────────────────────────────────

interface AIChatState {
  /** Ordered list of chat messages. */
  messages: Message[]
  /** Whether an SSE stream is currently in progress. */
  isStreaming: boolean
  /** Buffered content for the current assistant response being streamed. */
  currentStreamContent: string
  /** Buffered thinking content for the current response. */
  currentThinkingContent: string
  /** Analysis payload received during streaming (if any). */
  pendingAnalysis: TeamAnalysis | null

  // ── Actions ──────────────────────────────────────────────────────────────
  /** Append a user message and begin streaming. */
  addUserMessage: (content: string) => void
  /** Begin a new assistant streaming response. */
  startStreaming: () => void
  /** Append answer content to the current stream buffer. */
  appendStreamContent: (delta: string) => void
  /** Append thinking content to the current thinking buffer. */
  appendThinkingContent: (delta: string) => void
  /** Store an analysis payload received during streaming. */
  setPendingAnalysis: (analysis: TeamAnalysis) => void
  /** Finalise the current stream into a message and stop streaming. */
  finishStreaming: () => void
  /** Abort the current stream (e.g. on error) and clean up. */
  abortStreaming: () => void
  /** Clear all messages. */
  clearMessages: () => void
}

// ── Helpers ─────────────────────────────────────────────────────────────────────

let nextId = 1
function nextMessageId(): number {
  return nextId++
}

// ── Store ───────────────────────────────────────────────────────────────────────

export const useAIChatStore = create<AIChatState>()((set, get) => ({
  messages: [],
  isStreaming: false,
  currentStreamContent: "",
  currentThinkingContent: "",
  pendingAnalysis: null,

  addUserMessage: (content) => {
    const msg: Message = {
      id: nextMessageId(),
      role: "user",
      content,
      type: "text",
    }
    set((s) => ({ messages: [...s.messages, msg] }))
  },

  startStreaming: () => {
    set({
      isStreaming: true,
      currentStreamContent: "",
      currentThinkingContent: "",
      pendingAnalysis: null,
    })
  },

  appendStreamContent: (delta) => {
    set((s) => ({
      currentStreamContent: s.currentStreamContent + delta,
    }))
  },

  appendThinkingContent: (delta) => {
    set((s) => ({
      currentThinkingContent: s.currentThinkingContent + delta,
    }))
  },

  setPendingAnalysis: (analysis) => {
    set({ pendingAnalysis: analysis })
  },

  finishStreaming: () => {
    const { currentStreamContent, pendingAnalysis, messages } = get()
    const trimmed = currentStreamContent.trim()

    if (trimmed || pendingAnalysis) {
      const assistantMsg: Message = {
        id: nextMessageId(),
        role: "assistant",
        content: trimmed,
        type: pendingAnalysis ? "analysis" : "text",
        analysisData: pendingAnalysis ?? undefined,
      }
      set({
        messages: [...messages, assistantMsg],
        isStreaming: false,
        currentStreamContent: "",
        currentThinkingContent: "",
        pendingAnalysis: null,
      })
    } else {
      set({
        isStreaming: false,
        currentStreamContent: "",
        currentThinkingContent: "",
        pendingAnalysis: null,
      })
    }
  },

  abortStreaming: () => {
    const { currentStreamContent, messages } = get()
    const trimmed = currentStreamContent.trim()

    if (trimmed) {
      const partialMsg: Message = {
        id: nextMessageId(),
        role: "assistant",
        content: trimmed + " (interrupted)",
        type: "text",
      }
      set({
        messages: [...messages, partialMsg],
        isStreaming: false,
        currentStreamContent: "",
        currentThinkingContent: "",
        pendingAnalysis: null,
      })
    } else {
      set({
        isStreaming: false,
        currentStreamContent: "",
        currentThinkingContent: "",
        pendingAnalysis: null,
      })
    }
  },

  clearMessages: () => {
    set({
      messages: [],
      isStreaming: false,
      currentStreamContent: "",
      currentThinkingContent: "",
      pendingAnalysis: null,
    })
  },
}))
