/**
 * Teams API — getTeams, getTeamByCode, getTeamStats.
 */

import { apiRequest, buildQueryString, getApiClientLanguage } from "@/lib/api-client"
import type { TeamDetail } from "@/lib/types"

// ── Types matching the backend TeamResponse / TeamListResponse VO ─────────────

interface TeamListItem {
  id: number
  name: string
  name_zh: string
  code: string
  flag: string
  group_label: string
}

interface TeamsListResponse {
  items: TeamListItem[]
  total: number
  page: number
  page_size: number
}

interface TeamFullDetail extends TeamDetail {
  id: number
  fifa_ranking: number
  world_cup_appearances: number
}

// ── Types matching the backend TeamStatsResponse VO ───────────────────────────

export interface TeamMatchVO {
  id: number
  opponent: string
  opponent_code: string
  opponent_flag: string
  home_away: "home" | "away"
  score_for: number | null
  score_against: number | null
  kickoff_utc: string
  host_time: string | null
  venue_name: string
  venue_city: string
  status: string
  stage: string
  group_label: string | null
}

export interface TeamStandingVO {
  played: number
  won: number
  drawn: number
  lost: number
  goals_for: number
  goals_against: number
  goal_difference: number
  points: number
  position: number
}

export interface TeamStatsData {
  id: number
  name: string
  name_zh: string
  code: string
  flag: string
  fifa_ranking: number
  confederation: string
  group_label: string
  world_cup_appearances: number
  standing: TeamStandingVO | null
  finished_matches: TeamMatchVO[]
  upcoming_matches: TeamMatchVO[]
}

// ── API functions ─────────────────────────────────────────────────────────────

interface GetTeamsParams {
  page?: number
  pageSize?: number
  group?: string
}

/**
 * Fetch a paginated list of teams, optionally filtered by group.
 */
export async function getTeams(params: GetTeamsParams = {}): Promise<TeamsListResponse> {
  const lang = getApiClientLanguage()

  const query = buildQueryString({
    page: params.page,
    page_size: params.pageSize,
    group: params.group,
    lang,
  })

  return apiRequest<TeamsListResponse>(`/api/teams${query}`)
}

/**
 * Fetch detail for a single team by its 3-letter code.
 */
export async function getTeamByCode(code: string): Promise<TeamFullDetail> {
  const lang = getApiClientLanguage()

  const query = buildQueryString({
    lang,
  })

  return apiRequest<TeamFullDetail>(`/api/teams/${code}${query}`)
}

/**
 * Fetch comprehensive statistics for a team by its 3-letter code.
 */
export async function getTeamStats(code: string): Promise<TeamStatsData> {
  const lang = getApiClientLanguage()

  const query = buildQueryString({
    lang,
  })

  return apiRequest<TeamStatsData>(`/api/teams/${code}/stats${query}`)
}