/**
 * Groups API — getGroups, getGroupDetail.
 */

import { apiRequest, buildQueryString, getApiClientLanguage } from "@/lib/api-client"

// ── Types matching the backend GroupStandingResponse / GroupDetailResponse VO ─

interface GroupStanding {
  id: number
  team: {
    id: number
    name: string
    name_zh: string
    code: string
    flag: string
    group_label: string
  }
  group_label: string
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

interface GroupOverview {
  group_label: string
  standings: GroupStanding[]
}

interface GroupDetail {
  group_label: string
  standings: GroupStanding[]
  matches: Array<{
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
  }>
}

// ── API functions ─────────────────────────────────────────────────────────────

/**
 * Fetch all 12 groups with their standings.
 */
export async function getGroups(): Promise<GroupOverview[]> {
  const lang = getApiClientLanguage()

  const query = buildQueryString({
    lang: lang === "zh-CN" ? "zh" : "en",
  })

  return apiRequest<GroupOverview[]>(`/api/groups${query}`)
}

/**
 * Fetch a single group's detail (standings + matches).
 */
export async function getGroupDetail(
  group: string,
  options?: { timezone?: string },
): Promise<GroupDetail> {
  const lang = getApiClientLanguage()

  const query = buildQueryString({
    timezone: options?.timezone,
    lang: lang === "zh-CN" ? "zh" : "en",
  })

  return apiRequest<GroupDetail>(`/api/groups/${group}${query}`)
}