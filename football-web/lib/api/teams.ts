/**
 * Teams API — getTeams, getTeamByCode.
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
    lang: lang === "zh-CN" ? "zh" : "en",
  })

  return apiRequest<TeamsListResponse>(`/api/teams${query}`)
}

/**
 * Fetch detail for a single team by its 3-letter code.
 */
export async function getTeamByCode(code: string): Promise<TeamFullDetail> {
  const lang = getApiClientLanguage()

  const query = buildQueryString({
    lang: lang === "zh-CN" ? "zh" : "en",
  })

  return apiRequest<TeamFullDetail>(`/api/teams/${code}${query}`)
}