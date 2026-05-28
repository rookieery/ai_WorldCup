/**
 * Bracket API — getBracket.
 *
 * Returns the full knockout bracket tree (R32 → R16 → QF → SF → 3rd → F).
 * Includes a mapping layer to adapt backend field names to frontend types.
 */

import { apiRequest, buildQueryString, getApiClientLanguage } from "@/lib/api-client"
import type { BracketTree, BracketRound, BracketMatch, BracketTeam, BracketRoundName } from "@/lib/types"

// ── Backend response shape (raw from API) ──────────────────────────────────────

interface BackendBracketTeam {
  id?: number | null
  name?: string | null
  name_zh?: string | null
  code?: string | null
  flag?: string | null
  score?: number | null
  from_group?: string | null
  from_position?: number | null
}

interface BackendBracketMatch {
  id: number
  external_id: string
  stage: string
  home_team: BackendBracketTeam
  away_team: BackendBracketTeam
  status: string
  kickoff_utc?: string | null
  position?: number | null
}

interface BackendBracketRound {
  round_name: string
  display_name: string
  matches: BackendBracketMatch[]
}

interface BackendBracketTree {
  rounds: BackendBracketRound[]
}

// ── Mapping helpers ────────────────────────────────────────────────────────────

function mapTeam(raw: BackendBracketTeam): BracketTeam {
  const code = raw.code ?? "---"
  const isTbd = code === "---" || code === "TBD" || code === "tbd"
  let fromGroup: string | undefined

  if (isTbd && raw.from_group && raw.from_position) {
    const posLabel =
      raw.from_position === 1 ? "1st" :
      raw.from_position === 2 ? "2nd" :
      raw.from_position === 3 ? "3rd" : "4th"
    fromGroup = `${posLabel}${raw.from_group}`
  }

  return {
    name: raw.name ?? code,
    code,
    flag: raw.flag ?? "🏳️",
    score: raw.score ?? undefined,
    isWinner: undefined,
    fromGroup,
  }
}

function mapMatch(raw: BackendBracketMatch): BracketMatch {
  return {
    id: String(raw.id),
    round: raw.stage as BracketRoundName,
    team1: mapTeam(raw.home_team),
    team2: mapTeam(raw.away_team),
    status: raw.status as BracketMatch["status"],
    time: raw.kickoff_utc ?? undefined,
  }
}

function mapBracketTree(raw: BackendBracketTree): BracketTree {
  return {
    rounds: raw.rounds.map((r): BracketRound => ({
      round: r.round_name as BracketRoundName,
      label: r.display_name,
      matches: r.matches.map(mapMatch),
    })),
  }
}

// ── API functions ──────────────────────────────────────────────────────────────

/**
 * Fetch the complete knockout bracket tree.
 */
export async function getBracket(options?: {
  timezone?: string
}): Promise<BracketTree> {
  const lang = getApiClientLanguage()

  const query = buildQueryString({
    timezone: options?.timezone,
    lang,
  })

  const raw = await apiRequest<BackendBracketTree>(`/api/bracket${query}`)
  return mapBracketTree(raw)
}
