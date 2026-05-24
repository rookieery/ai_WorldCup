/**
 * Cheers API — getCheers, postCheer.
 *
 * Fan voting endpoints for match-level cheer counts.
 */

import { apiRequest } from "@/lib/api-client"

// ── Types matching the backend CheerResponse VO ──────────────────────────────

interface CheerData {
  match_id: number
  home: number
  away: number
}

// ── API functions ─────────────────────────────────────────────────────────────

/**
 * Fetch the current cheer counts for a match.
 */
export async function getCheers(matchId: number): Promise<CheerData> {
  return apiRequest<CheerData>(`/api/cheers/${matchId}`)
}

/**
 * Submit a cheer vote for a match.
 *
 * @param matchId - The match to vote on.
 * @param side    - Which side to vote for: "home" or "away".
 */
export async function postCheer(
  matchId: number,
  side: "home" | "away",
): Promise<CheerData> {
  return apiRequest<CheerData>(`/api/cheers/${matchId}`, {
    method: "POST",
    body: { side },
  })
}