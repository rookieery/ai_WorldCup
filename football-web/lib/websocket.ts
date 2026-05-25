/**
 * WebSocket client — auto-connecting, reconnecting real-time event consumer.
 *
 * Connects to the backend WebSocket endpoint (`/ws/live`) and dispatches
 * incoming events into the Zustand `useLiveStore`. Provides a singleton
 * `wsClient` that can be started/stopped from any component lifecycle.
 *
 * Features:
 * - Auto-connect with exponential back-off reconnection
 * - Event dispatch to Zustand live store
 * - Ping/pong keep-alive handled by browser
 * - Clean disconnect on page unload
 * - Subscribe/unsubscribe to specific match channels
 */

import { useLiveStore } from "@/lib/store"
import type { WSConnectionStatus } from "@/lib/store"

// ── Configuration ────────────────────────────────────────────────────────────

const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL ??
  (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
    .replace(/^http/, "ws")

const WS_PATH = "/ws/live"

const RECONNECT_BASE_MS = 1_000
const RECONNECT_MAX_MS = 30_000
const RECONNECT_MAX_ATTEMPTS = 20

// ── WS Event types matching backend WSEventType enum ─────────────────────────

type WSEventName =
  | "connected"
  | "score_update"
  | "match_start"
  | "match_end"
  | "activity_update"
  | "cheer_update"
  | "bracket_update"
  | "ping"

interface WSMessage {
  event: WSEventName
  payload: Record<string, unknown>
}

// ── Client class ─────────────────────────────────────────────────────────────

class WSClient {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private disposed = false

  /** Start the WebSocket connection. Idempotent — safe to call multiple times. */
  start(): void {
    if (this.ws?.readyState === WebSocket.OPEN || this.ws?.readyState === WebSocket.CONNECTING) {
      return
    }
    this.disposed = false
    this.connect()
  }

  /** Gracefully close the connection and stop reconnecting. */
  stop(): void {
    this.disposed = true
    this.clearReconnectTimer()
    if (this.ws) {
      this.ws.close(1000, "client disconnect")
      this.ws = null
    }
    useLiveStore.getState().setWSStatus("disconnected")
  }

  /** Subscribe the current connection to updates for a specific match. */
  subscribeToMatch(matchId: number): void {
    this.send({ action: "subscribe", matchId })
  }

  /** Unsubscribe the current connection from updates for a specific match. */
  unsubscribeFromMatch(matchId: number): void {
    this.send({ action: "unsubscribe", matchId })
  }

  // ── Private helpers ────────────────────────────────────────────────────

  private connect(): void {
    if (this.disposed) return

    const url = `${WS_BASE_URL}${WS_PATH}`
    this.setStatus("connecting")

    const ws = new WebSocket(url)
    this.ws = ws

    ws.onopen = () => {
      this.reconnectAttempts = 0
      this.setStatus("connected")
    }

    ws.onmessage = (ev: MessageEvent<string>) => {
      this.handleMessage(ev.data)
    }

    ws.onclose = (ev) => {
      if (ev.code === 1000) {
        // Clean close — do not reconnect
        this.setStatus("disconnected")
        return
      }
      this.scheduleReconnect()
    }

    ws.onerror = () => {
      // onclose will fire after onerror, which handles reconnect
      this.setStatus("error")
    }
  }

  private handleMessage(raw: string): void {
    let msg: WSMessage
    try {
      msg = JSON.parse(raw) as WSMessage
    } catch {
      return
    }

    const { event, payload } = msg

    switch (event) {
      case "score_update":
        useLiveStore.getState().applyScoreUpdate({
          matchId: payload.match_id as number,
          score1: payload.home_score as number,
          score2: payload.away_score as number,
          status: (payload.status as string) ?? "live",
          activityLevel: (payload.activity_level as number) ?? 0,
        })
        break

      case "match_start":
        useLiveStore.getState().applyScoreUpdate({
          matchId: payload.match_id as number,
          score1: 0,
          score2: 0,
          status: "live",
          activityLevel: 0,
        })
        break

      case "match_end":
        useLiveStore.getState().applyScoreUpdate({
          matchId: payload.match_id as number,
          score1: payload.home_score as number,
          score2: payload.away_score as number,
          status: "finished",
          activityLevel: 0,
        })
        break

      case "activity_update": {
        // Preserve existing score data, only update activity level
        const existing = useLiveStore.getState().scoreUpdates[payload.match_id as number]
        useLiveStore.getState().applyScoreUpdate({
          matchId: payload.match_id as number,
          score1: existing?.score1 ?? 0,
          score2: existing?.score2 ?? 0,
          status: existing?.status ?? "live",
          activityLevel: payload.activity_level as number,
        })
        break
      }

      case "cheer_update":
        useLiveStore.getState().applyCheerUpdate({
          matchId: payload.match_id as number,
          home: payload.home as number,
          away: payload.away as number,
        })
        break

      case "connected": {
        // Initial payload with live matches — apply each one as a score patch
        const liveMatches = payload.live_matches as Array<Record<string, unknown>> | undefined
        if (liveMatches && Array.isArray(liveMatches)) {
          const store = useLiveStore.getState()
          for (const m of liveMatches) {
            store.applyScoreUpdate({
              matchId: m.match_id as number,
              score1: (m.home_score as number) ?? 0,
              score2: (m.away_score as number) ?? 0,
              status: (m.status as string) ?? "live",
              activityLevel: (m.activity as number) ?? 0,
            })
          }
        }
        break
      }

      case "ping":
        // Server keep-alive; browser auto-responds with pong
        break

      default:
        // bracket_update and future events — no live-store action needed
        break
    }
  }

  private scheduleReconnect(): void {
    if (this.disposed) return
    if (this.reconnectAttempts >= RECONNECT_MAX_ATTEMPTS) {
      this.setStatus("error")
      return
    }

    this.setStatus("disconnected")

    const delay = Math.min(
      RECONNECT_BASE_MS * Math.pow(2, this.reconnectAttempts),
      RECONNECT_MAX_MS,
    )
    this.reconnectAttempts++

    this.reconnectTimer = setTimeout(() => {
      this.connect()
    }, delay)
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }

  private setStatus(status: WSConnectionStatus): void {
    useLiveStore.getState().setWSStatus(status)
  }

  private send(data: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }
}

// ── Singleton instance ───────────────────────────────────────────────────────

export const wsClient = new WSClient()
