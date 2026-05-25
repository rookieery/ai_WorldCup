/**
 * Matches Store — match data cache with loading/error states.
 *
 * Stores matches indexed by date for efficient timeline lookups, plus a
 * separate live matches list. Provides fetch actions that delegate to the
 * existing API layer (`@/lib/api/matches`).
 */

import { create } from "zustand"
import { getMatches, getLiveMatches, apiMatchToUi } from "@/lib/api/matches"
import type { Match } from "@/lib/types"

// ── Types ──────────────────────────────────────────────────────────────────────

interface DateCache {
  matches: Match[]
  fetchedAt: number
}

interface MatchesState {
  /** Match lists keyed by ISO date string (e.g. "2026-06-11"). */
  byDate: Record<string, DateCache>
  /** Currently-live matches. */
  liveMatches: Match[]
  /** Loading flags per date + live. */
  loading: Record<string, boolean>
  /** Error flags per date + live. */
  error: Record<string, boolean>

  // ── Actions ──────────────────────────────────────────────────────────────
  fetchMatchesByDate: (date: string, timezone?: string) => Promise<void>
  fetchLiveMatches: (timezone?: string) => Promise<void>
  /** Upsert a single match (e.g. from a real-time update). */
  upsertMatch: (date: string, match: Match) => void
  /** Update a live match's score / status in-place. */
  updateLiveMatch: (matchId: number, patch: Partial<Match>) => void
}

// ── Cache TTL ───────────────────────────────────────────────────────────────────

const CACHE_TTL_MS = 5 * 60 * 1000 // 5 minutes

// ── Store ───────────────────────────────────────────────────────────────────────

export const useMatchesStore = create<MatchesState>()((set, get) => ({
  byDate: {},
  liveMatches: [],
  loading: {},
  error: {},

  fetchMatchesByDate: async (date, timezone) => {
    const state = get()
    const cached = state.byDate[date]

    // Return early if cache is still fresh
    if (cached && Date.now() - cached.fetchedAt < CACHE_TTL_MS) {
      return
    }

    set((s) => ({
      loading: { ...s.loading, [date]: true },
      error: { ...s.error, [date]: false },
    }))

    try {
      const tzName =
        timezone === "host"
          ? undefined
          : Intl.DateTimeFormat().resolvedOptions().timeZone

      const res = await getMatches({
        date,
        timezone: tzName,
        pageSize: 50,
      })

      const matches = res.items.map(apiMatchToUi)

      set((s) => ({
        byDate: {
          ...s.byDate,
          [date]: { matches, fetchedAt: Date.now() },
        },
        loading: { ...s.loading, [date]: false },
      }))
    } catch {
      set((s) => ({
        loading: { ...s.loading, [date]: false },
        error: { ...s.error, [date]: true },
      }))
    }
  },

  fetchLiveMatches: async (timezone) => {
    const key = "live"
    set((s) => ({
      loading: { ...s.loading, [key]: true },
      error: { ...s.error, [key]: false },
    }))

    try {
      const tzName =
        timezone === "host"
          ? undefined
          : Intl.DateTimeFormat().resolvedOptions().timeZone

      const raw = await getLiveMatches({ timezone: tzName })
      const matches = raw.map(apiMatchToUi)

      set((s) => ({
        liveMatches: matches,
        loading: { ...s.loading, [key]: false },
      }))
    } catch {
      set((s) => ({
        loading: { ...s.loading, [key]: false },
        error: { ...s.error, [key]: true },
      }))
    }
  },

  upsertMatch: (date, match) => {
    set((s) => {
      const dateCache = s.byDate[date] ?? { matches: [], fetchedAt: Date.now() }
      const idx = dateCache.matches.findIndex((m) => m.id === match.id)

      const updated =
        idx >= 0
          ? dateCache.matches.map((m, i) => (i === idx ? match : m))
          : [...dateCache.matches, match]

      return {
        byDate: {
          ...s.byDate,
          [date]: { matches: updated, fetchedAt: dateCache.fetchedAt },
        },
      }
    })
  },

  updateLiveMatch: (matchId, patch) => {
    set((s) => ({
      liveMatches: s.liveMatches.map((m) =>
        m.id === matchId ? { ...m, ...patch } : m,
      ),
    }))
  },
}))
