/**
 * Matches API — getMatches, getMatchById, getLiveMatches.
 *
 * All functions delegate to the core `apiRequest` wrapper which handles
 * base URL, language header, and error unwrapping.
 */

import { apiRequest, buildQueryString, getApiClientLanguage } from "@/lib/api-client"
import type { Match, MatchQueryParams } from "@/lib/types"

// ── Types matching the backend MatchResponse VO ──────────────────────────────

interface MatchListResponse {
  items: Match[]
  total: number
  page: number
  page_size: number
}

interface MatchDetail {
  id: number
  external_id: string
  home_team: {
    id: number
    name: string
    name_zh: string
    code: string
    flag: string
    group_label: string
  }
  away_team: {
    id: number
    name: string
    name_zh: string
    code: string
    flag: string
    group_label: string
  }
  venue: {
    id: number
    name: string
    city: string
    country: string
    timezone: string
    utc_offset: string
    capacity: number
  }
  stage: string
  group_label: string | null
  round: string
  match_day: number | null
  kickoff_utc: string
  local_time: string | null
  host_time: string | null
  status: string
  home_score: number | null
  away_score: number | null
  is_big_match: boolean
  activity_level: number
  events: Array<{
    id: number
    match_id: number
    event_type: string
    minute: number
    team_side: string
    player_name: string | null
  }>
}

// ── API functions ─────────────────────────────────────────────────────────────

interface GetMatchesParams extends MatchQueryParams {
  page?: number
  pageSize?: number
  timezone?: string
}

/**
 * Fetch a paginated list of matches with optional filters.
 */
export async function getMatches(params: GetMatchesParams = {}): Promise<MatchListResponse> {
  const lang = getApiClientLanguage()

  const query = buildQueryString({
    date: params.date,
    stage: params.stage,
    status: params.status,
    team: params.teamCode,
    timezone: params.timezone,
    lang: lang === "zh-CN" ? "zh" : "en",
    page: params.page,
    page_size: params.pageSize,
  })

  return apiRequest<MatchListResponse>(`/api/matches${query}`)
}

/**
 * Fetch detail for a single match by its ID (includes events).
 */
export async function getMatchById(
  id: number,
  options?: { timezone?: string },
): Promise<MatchDetail> {
  const lang = getApiClientLanguage()

  const query = buildQueryString({
    timezone: options?.timezone,
    lang: lang === "zh-CN" ? "zh" : "en",
  })

  return apiRequest<MatchDetail>(`/api/matches/${id}${query}`)
}

/**
 * Fetch all currently live matches.
 */
export async function getLiveMatches(options?: {
  timezone?: string
}): Promise<Match[]> {
  const lang = getApiClientLanguage()

  const query = buildQueryString({
    timezone: options?.timezone,
    lang: lang === "zh-CN" ? "zh" : "en",
  })

  return apiRequest<Match[]>(`/api/matches/live${query}`)
}