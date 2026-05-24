/**
 * Shared Match type definitions.
 *
 * `Match` is the canonical match shape used by the match-cards-grid and the
 * matches API. `MatchQueryParams` describes the filter parameters accepted
 * by the matches listing endpoint.
 */

import type { Team } from "./team"

export type MatchStatus = "upcoming" | "live" | "finished"
export type CityIcon = "palm" | "skyscraper" | "landmark" | "cactus"

export interface Match {
  id: number
  team1: Team
  team2: Team
  localTime: string
  hostTime: string
  venue: string
  hostCity: string
  cityIcon: CityIcon
  stage: string
  status: MatchStatus
  score1?: number
  score2?: number
  cheerTeam1: number
  cheerTeam2: number
  isBigMatch: boolean
  activityLevel: number
}

export type MatchEventType = "goal" | "yellow_card" | "red_card" | "substitution" | "var"

export interface MatchEvent {
  minute: number
  type: MatchEventType
  team: string
  player: string
  detail?: string
}

export interface MatchQueryParams {
  date?: string
  stage?: string
  status?: MatchStatus
  teamCode?: string
  live?: boolean
}

/** A single match-date entry returned by GET /api/matches/dates. */
export interface MatchDateInfo {
  date: string   // ISO-8601 date string, e.g. "2026-06-11"
  stage: string  // Primary stage: "group", "R32", "R16", "QF", "SF", "3rd", "F"
}
