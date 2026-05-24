/**
 * Shared Team type definitions.
 *
 * `Team` represents the minimal team shape used in match cards and throughout the UI.
 * `TeamDetail` extends it with additional data available from the teams API.
 */

export interface Team {
  name: string
  code: string
  flag: string
  fifaRanking?: number
}

export interface TeamDetail extends Team {
  nameZh: string
  confederation: string
  group: string
}

export interface TeamStanding {
  teamCode: string
  teamName: string
  flag: string
  played: number
  won: number
  drawn: number
  lost: number
  goalsFor: number
  goalsAgainst: number
  goalDifference: number
  points: number
}
