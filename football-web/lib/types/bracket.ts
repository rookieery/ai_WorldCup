/**
 * Shared Bracket (knockout stage) type definitions.
 *
 * `BracketTeam` extends the base Team with bracket-specific fields (score,
 * winner flag, advancement source group info).
 * `BracketMatch` represents a single knockout fixture.
 * `BracketRound` groups matches by round.
 * `BracketTree` is the top-level container for the full knockout bracket.
 */

import type { Team } from "./team"

export type BracketRoundName = "R32" | "R16" | "QF" | "SF" | "3rd" | "F"

export interface BracketTeam extends Team {
  score?: number
  isWinner?: boolean
  color?: string
  fromGroup?: string
}

export type BracketMatchStatus = "upcoming" | "live" | "completed"

export interface BracketMatch {
  id: string
  round: BracketRoundName
  team1: BracketTeam
  team2: BracketTeam
  status: BracketMatchStatus
  venue?: string
  time?: string
}

export interface BracketRound {
  round: BracketRoundName
  label: string
  matches: BracketMatch[]
}

export interface BracketTree {
  rounds: BracketRound[]
}
