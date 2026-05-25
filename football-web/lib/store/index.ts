/**
 * Centralized re-exports for all Zustand stores.
 *
 * Import from `@/lib/store` to access any store hook.
 */

export { usePreferencesStore } from "./preferences"
export type { Language, TimezoneMode, ViewMode, Theme } from "./preferences"

export { useMatchesStore } from "./matches"

export { useLiveStore } from "./live"
export type { WSConnectionStatus, LiveScorePatch, CheerUpdate } from "./live"

export { useAIChatStore } from "./ai-chat"
