/**
 * Bracket API — getBracket.
 *
 * Returns the full knockout bracket tree (R32 → R16 → QF → SF → 3rd → F).
 */

import { apiRequest, buildQueryString, getApiClientLanguage } from "@/lib/api-client"
import type { BracketTree } from "@/lib/types"

// ── API functions ─────────────────────────────────────────────────────────────

/**
 * Fetch the complete knockout bracket tree.
 */
export async function getBracket(options?: {
  timezone?: string
}): Promise<BracketTree> {
  const lang = getApiClientLanguage()

  const query = buildQueryString({
    timezone: options?.timezone,
    lang: lang === "zh-CN" ? "zh" : "en",
  })

  return apiRequest<BracketTree>(`/api/bracket${query}`)
}