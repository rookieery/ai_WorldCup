/**
 * Championship Analysis SSE Client — streams champion/runner-up prediction from the backend.
 *
 * Provides `streamChampionshipAnalysis()` for SSE streaming of Monte Carlo
 * simulation-based championship predictions. Reuses the SSE parsing helpers
 * and callback signature exported by `@/lib/api/ai-chat`.
 */

import { getApiClientLanguage } from "@/lib/api-client"
import type { TeamAnalysis } from "@/lib/types"
import type { Language } from "@/lib/store"
import {
  parseSSELines,
  parseSSEPayload,
} from "@/lib/api/ai-chat"
import type { StreamCallbacks } from "@/lib/api/ai-chat"

// ── Types ──────────────────────────────────────────────────────────────────────

/** Request body matching the backend `ChampionshipAnalysisRequest` schema. */
export interface ChampionshipAnalysisRequestBody {
  skill_id?: string
  lang: string
}

// ── Configuration ──────────────────────────────────────────────────────────────

const BASE_URL: string =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

const CHAMPIONSHIP_ENDPOINT = `${BASE_URL}/api/ai/championship-analysis`

// ── streamChampionshipAnalysis ─────────────────────────────────────────────────

/**
 * Start an SSE streaming championship prediction session.
 *
 * Sends a POST request with the championship analysis parameters,
 * then consumes the response body as a ReadableStream of SSE events.
 * Uses the same parsing logic and callback signature as `streamMatchAnalysis`.
 *
 * @param body      The championship analysis request payload.
 * @param callbacks Callback functions for each SSE event type.
 * @param signal    Optional AbortController signal to cancel the stream.
 */
export async function streamChampionshipAnalysis(
  body: ChampionshipAnalysisRequestBody,
  callbacks: StreamCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  let response: Response

  try {
    response = await fetch(CHAMPIONSHIP_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
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
