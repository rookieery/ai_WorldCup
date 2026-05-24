/**
 * Matches API — getMatchDates, getMatches, getMatchById, getLiveMatches.
 *
 * All functions delegate to the core `apiRequest` wrapper which handles
 * base URL, language header, and error unwrapping.
 */

import { apiRequest, buildQueryString, getApiClientLanguage } from "@/lib/api-client"
import type { Match, MatchQueryParams, MatchDateInfo } from "@/lib/types"

// ── Types matching the backend MatchResponse VO ──────────────────────────────

interface MatchListResponse {
  items: MatchApiItem[]
  total: number
  page: number
  page_size: number
}

/** Raw match item shape returned by the backend API. */
export interface MatchApiItem {
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
 * Fetch all match dates with their primary stage label.
 * Returns a sorted list of { date, stage } objects.
 */
export async function getMatchDates(): Promise<MatchDateInfo[]> {
  return apiRequest<MatchDateInfo[]>("/api/matches/dates")
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
}): Promise<MatchApiItem[]> {
  const lang = getApiClientLanguage()

  const query = buildQueryString({
    timezone: options?.timezone,
    lang: lang === "zh-CN" ? "zh" : "en",
  })

  return apiRequest<MatchApiItem[]>(`/api/matches/live${query}`)
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/** City-icon mapping based on venue city name (heuristic). */
function inferCityIcon(city: string): "palm" | "skyscraper" | "landmark" | "cactus" {
  const lower = city.toLowerCase()
  if (lower.includes("angeles") || lower.includes("miami") || lower.includes("houston")) return "palm"
  if (lower.includes("new york") || lower.includes("chicago") || lower.includes("toronto")) return "skyscraper"
  if (lower.includes("mexico") || lower.includes("guadalajara") || lower.includes("monterrey")) return "landmark"
  return "cactus"
}

/**
 * Convert a raw API match item to the frontend `Match` shape.
 * This bridges the gap between the backend VO and the UI component props.
 */
export function apiMatchToUi(m: MatchApiItem): import("@/lib/types").Match {
  return {
    id: m.id,
    team1: {
      name: m.home_team.name,
      code: m.home_team.code,
      flag: m.home_team.flag,
    },
    team2: {
      name: m.away_team.name,
      code: m.away_team.code,
      flag: m.away_team.flag,
    },
    localTime: m.local_time ?? "",
    hostTime: m.host_time ?? "",
    venue: m.venue.name,
    hostCity: m.venue.city,
    cityIcon: inferCityIcon(m.venue.city),
    stage: m.stage === "group" && m.group_label ? `Group ${m.group_label}` : m.stage,
    status: m.status as import("@/lib/types").MatchStatus,
    score1: m.home_score ?? undefined,
    score2: m.away_score ?? undefined,
    cheerTeam1: 50,
    cheerTeam2: 50,
    isBigMatch: m.is_big_match,
    activityLevel: m.activity_level,
  }
}