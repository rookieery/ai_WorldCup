/**
 * Stats API — getScorers.
 *
 * All functions delegate to the core `apiRequest` wrapper which handles
 * base URL, language header, and error unwrapping.
 */

import { apiRequest, buildQueryString, getApiClientLanguage } from "@/lib/api-client"

// ── Types matching the backend ScorerItem VO ────────────────────────────────

export interface ScorerItem {
  rank: number
  player_name: string
  team_code: string
  team_name: string
  team_name_zh: string
  team_flag: string
  goals: number
  assists: number
}

// ── API functions ────────────────────────────────────────────────────────────

interface GetScorersParams {
  limit?: number
}

/**
 * Fetch the scorer leaderboard.
 */
export async function getScorers(
  params: GetScorersParams = {},
): Promise<ScorerItem[]> {
  const lang = getApiClientLanguage()

  const query = buildQueryString({
    lang,
    limit: params.limit,
  })

  return apiRequest<ScorerItem[]>(`/api/stats/scorers${query}`)
}
