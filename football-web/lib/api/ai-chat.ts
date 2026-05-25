/**
 * AI Chat SSE Consumer — streams AI responses from the backend chat endpoint.
 *
 * Uses `fetch()` + `ReadableStream` to consume server-sent events via POST.
 * Manual `data:` line parsing distinguishes thinking/answer/analysis/done/error
 * events and drives callbacks that push data into the Zustand ai-chat store.
 */

import { getApiClientLanguage } from "@/lib/api-client"
import type { SSEEvent, TeamAnalysis } from "@/lib/types"
import type { Language } from "@/lib/store"

// ── Types ──────────────────────────────────────────────────────────────────────

/** A single chat message sent to the backend. */
export interface ChatMessageItem {
  role: "user" | "assistant"
  content: string
}

/** Client-side context that accompanies a chat request. */
export interface ChatContext {
  currentView?: string
  selectedDate?: string
  timezone?: string
}

/** Callbacks invoked as SSE events arrive. */
export interface StreamCallbacks {
  onThinking: (delta: string) => void
  onAnswer: (delta: string) => void
  onAnalysis: (data: TeamAnalysis) => void
  onDone: () => void
  onError: (message: string) => void
}

// ── Configuration ──────────────────────────────────────────────────────────────

const BASE_URL: string =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

const CHAT_ENDPOINT = `${BASE_URL}/api/ai/chat`

// ── SSE Parser ─────────────────────────────────────────────────────────────────

/**
 * Parse raw SSE text chunks into individual `data:` lines.
 * Handles partial chunks and multi-line payloads.
 */
function parseSSELines(
  buffer: string,
  chunk: string,
): { remaining: string; lines: string[] } {
  const combined = buffer + chunk
  const parts = combined.split("\n\n")
  const lines: string[] = []

  for (let i = 0; i < parts.length - 1; i++) {
    const block = parts[i].trim()
    for (const line of block.split("\n")) {
      const trimmed = line.trim()
      if (trimmed.startsWith("data: ")) {
        lines.push(trimmed.slice(6))
      }
    }
  }

  return { remaining: parts[parts.length - 1], lines }
}

/**
 * Parse a single `data:` payload string into an `SSEEvent` or `null`.
 * Recognises the `[DONE]` sentinel and malformed payloads.
 */
function parseSSEPayload(raw: string): SSEEvent | "done" | null {
  if (raw === "[DONE]") return "done"

  try {
    const parsed = JSON.parse(raw) as SSEEvent
    if (
      typeof parsed === "object" &&
      parsed !== null &&
      "type" in parsed
    ) {
      return parsed
    }
    return null
  } catch {
    return null
  }
}

// ── streamChat ─────────────────────────────────────────────────────────────────

/**
 * Start an SSE streaming chat session.
 *
 * Sends a POST request with the message history and optional context,
 * then consumes the response body as a ReadableStream of SSE events.
 * Each event is dispatched to the appropriate callback.
 *
 * @param messages  The conversation history (last item = current user question).
 * @param context   Optional UI context for personalised responses.
 * @param lang      Language preference ("zh-CN" | "en-US").
 * @param callbacks Callback functions for each SSE event type.
 * @param signal    Optional AbortController signal to cancel the stream.
 */
export async function streamChat(
  messages: ChatMessageItem[],
  context: ChatContext | undefined,
  lang: Language,
  callbacks: StreamCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  const body = {
    messages,
    context: context ?? null,
    lang,
  }

  let response: Response

  try {
    response = await fetch(CHAT_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "Accept-Language": getApiClientLanguage(),
      },
      body: JSON.stringify(body),
      signal,
    })
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === "AbortError") {
      return
    }
    callbacks.onError("connection")
    return
  }

  if (!response.ok) {
    callbacks.onError("stream")
    return
  }

  const reader = response.body?.getReader()
  if (!reader) {
    callbacks.onError("stream")
    return
  }

  const decoder = new TextDecoder()
  let buffer = ""

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      const { remaining, lines } = parseSSELines(buffer, chunk)
      buffer = remaining

      for (const line of lines) {
        const event = parseSSEPayload(line)

        if (event === "done") {
          callbacks.onDone()
          return
        }

        if (event === null) continue

        switch (event.type) {
          case "thinking":
            if (event.content) callbacks.onThinking(event.content)
            break
          case "answer":
            if (event.content) callbacks.onAnswer(event.content)
            break
          case "analysis":
            if (event.data) callbacks.onAnalysis(event.data as TeamAnalysis)
            break
          case "error":
            callbacks.onError(event.content ?? "stream")
            break
          case "done":
            callbacks.onDone()
            return
        }
      }
    }

    // Stream ended without [DONE] sentinel — still finalise
    callbacks.onDone()
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === "AbortError") {
      return
    }
    callbacks.onError("stream")
  }
}
