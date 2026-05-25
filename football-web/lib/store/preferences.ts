/**
 * Preferences Store — user settings persisted to localStorage.
 *
 * Manages language, timezone display mode, view mode (timeline / bracket),
 * and theme preference. Synced with the i18n provider and theme provider.
 */

import { create } from "zustand"
import { persist } from "zustand/middleware"

// ── Types ──────────────────────────────────────────────────────────────────────

export type Language = "zh-CN" | "en-US"
export type TimezoneMode = "local" | "host"
export type ViewMode = "timeline" | "bracket"
export type Theme = "dark" | "light" | "system"

interface PreferencesState {
  /** Active locale for i18n. */
  language: Language
  /** Whether match times show the user's local timezone or the host city time. */
  timezone: TimezoneMode
  /** Which dashboard view is active: timeline cards or knockout bracket. */
  viewMode: ViewMode
  /** Theme preference. */
  theme: Theme

  // ── Actions ──────────────────────────────────────────────────────────────
  setLanguage: (language: Language) => void
  setTimezone: (timezone: TimezoneMode) => void
  setViewMode: (viewMode: ViewMode) => void
  setTheme: (theme: Theme) => void
}

// ── Store ───────────────────────────────────────────────────────────────────────

export const usePreferencesStore = create<PreferencesState>()(
  persist(
    (set) => ({
      language: "en-US",
      timezone: "local",
      viewMode: "bracket",
      theme: "dark",

      setLanguage: (language) => set({ language }),
      setTimezone: (timezone) => set({ timezone }),
      setViewMode: (viewMode) => set({ viewMode }),
      setTheme: (theme) => set({ theme }),
    }),
    {
      name: "worldcup-preferences",
    },
  ),
)
