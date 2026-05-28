/**
 * Live Store — real-time update state driven by WebSocket events.
 *
 * Tracks WebSocket connection status and serves as the single source of
 * truth for live score updates, activity levels, and cheer data received
 * via the WebSocket channel. Components subscribe to this store instead of
 * managing individual listeners.
 */

import { create } from "zustand"

// ── Types ──────────────────────────────────────────────────────────────────────

export type WSConnectionStatus = "connecting" | "connected" | "disconnected" | "error"

/** A live score patch pushed from the server. */
export interface LiveScorePatch {
  matchId: number
  score1: number
  score2: number
  status: string
  activityLevel: number
}

/** A cheer count update pushed from the server. */
export interface CheerUpdate {
  matchId: number
  home: number
  away: number
}

interface LiveState {
  /** Current WebSocket connection status. */
  wsStatus: WSConnectionStatus
  /** Latest score patches keyed by matchId. */
  scoreUpdates: Record<number, LiveScorePatch>
  /** Latest cheer data keyed by matchId. */
  cheerUpdates: Record<number, CheerUpdate>

  // ── Actions ──────────────────────────────────────────────────────────────
  setWSStatus: (status: WSConnectionStatus) => void
  applyScoreUpdate: (patch: LiveScorePatch) => void
  applyCheerUpdate: (update: CheerUpdate) => void
  /** Clear all live data (e.g. on disconnect). */
  reset: () => void
}

// ── Store ───────────────────────────────────────────────────────────────────────

const initialState = {
  wsStatus: "disconnected" as WSConnectionStatus,
  scoreUpdates: {} as Record<number, LiveScorePatch>,
  cheerUpdates: {} as Record<number, CheerUpdate>,
}

export const useLiveStore = create<LiveState>()((set) => ({
  ...initialState,

  setWSStatus: (status) => set({ wsStatus: status }),

  applyScoreUpdate: (patch) =>
    set((s) => ({
      scoreUpdates: { ...s.scoreUpdates, [patch.matchId]: patch },
    })),

  applyCheerUpdate: (update) =>
    set((s) => ({
      cheerUpdates: { ...s.cheerUpdates, [update.matchId]: update },
    })),

  reset: () => set(initialState),
}))
