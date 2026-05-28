/**
 * AI Match Analysis SSE Client — streams skill-driven analysis from the backend.
 *
 * Provides `streamMatchAnalysis()` for SSE streaming and `getAvailableSkills()`
 * for fetching the static skill registry. Reuses the SSE parsing helpers and
 * callback signature exported by `@/lib/api/ai-chat`.
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

/** Brief team information for match analysis requests. */
export interface TeamBrief {
  name: string
  name_zh: string
  code: string
  flag: string
}

/** Brief match event for analysis context. */
export interface MatchEventBrief {
  event_type: string
  minute: number
  team_side: string
  player_name: string | null
}

/** Request body matching the backend `MatchAnalysisRequest` schema. */
export interface MatchAnalysisRequestBody {
  match_id: number
  stage: string
  skill_id?: string
  home_team: TeamBrief
  away_team: TeamBrief
  home_score: number | null
  away_score: number | null
  status: string
  group_label?: string
  round?: string
  match_day?: number
  events?: MatchEventBrief[]
  lang: string
}

/** Metadata for an AI analysis Skill. */
export interface SkillInfo {
  skill_id: string
  name: string
  name_zh: string
  description: string
  description_zh: string
  applicable_stages: string[]
}

// ── Configuration ──────────────────────────────────────────────────────────────

const BASE_URL: string =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

const ANALYSIS_ENDPOINT = `${BASE_URL}/api/ai/match-analysis`
const SKILLS_ENDPOINT = `${BASE_URL}/api/ai/skills`

// ── streamMatchAnalysis ────────────────────────────────────────────────────────

/**
 * Start an SSE streaming match analysis session.
 *
 * Sends a POST request with the match context, then consumes the response
 * body as a ReadableStream of SSE events. Uses the same parsing logic and
 * callback signature as `streamChat` from `ai-chat.ts`.
 *
 * @param body      The match analysis request payload.
 * @param callbacks Callback functions for each SSE event type.
 * @param signal    Optional AbortController signal to cancel the stream.
 */
export async function streamMatchAnalysis(
  body: MatchAnalysisRequestBody,
  callbacks: StreamCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  let response: Response

  try {
    response = await fetch(ANALYSIS_ENDPOINT, {
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

// ── getAvailableSkills ─────────────────────────────────────────────────────────

/**
 * Fetch the list of available AI analysis skills from the backend.
 *
 * @param lang Optional language preference; defaults to the current client language.
 * @returns Array of `SkillInfo` objects.
 */
export async function getAvailableSkills(
  lang?: Language,
): Promise<SkillInfo[]> {
  const params = new URLSearchParams()
  if (lang) {
    params.set("lang", lang)
  }

  const url = params.toString()
    ? `${SKILLS_ENDPOINT}?${params.toString()}`
    : SKILLS_ENDPOINT

  const response = await fetch(url, {
    method: "GET",
    headers: {
      Accept: "application/json",
      "Accept-Language": getApiClientLanguage(),
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch skills: ${response.status}`)
  }

  const payload = await response.json()
  // Backend wraps in ApiResponse: { code, data, message }
  return (payload.data ?? payload) as SkillInfo[]
}
