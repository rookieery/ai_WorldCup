"use client"

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from "react"
import type { Locale, LocaleMessages } from "./types"
import zhCN from "./locales/zh-CN.json"
import enUS from "./locales/en-US.json"
import { setApiClientLanguage } from "@/lib/api-client"
import { useMatchesStore, usePreferencesStore } from "@/lib/store"

const localeMap: Record<Locale, LocaleMessages> = {
  "zh-CN": zhCN as LocaleMessages,
  "en-US": enUS as LocaleMessages,
}

interface I18nContextValue {
  locale: Locale
  messages: LocaleMessages
  setLocale: (locale: Locale) => void
  t: (key: string) => string
}

const I18nContext = createContext<I18nContextValue | null>(null)

function detectLocale(): Locale {
  if (typeof navigator === "undefined") return "en-US"
  const lang = navigator.language
  if (lang.startsWith("zh")) return "zh-CN"
  return "en-US"
}

function getNestedValue(obj: Record<string, unknown>, path: string): string {
  const keys = path.split(".")
  let current: unknown = obj
  for (const key of keys) {
    if (current === null || current === undefined || typeof current !== "object") {
      return path
    }
    current = (current as Record<string, unknown>)[key]
  }
  return typeof current === "string" ? current : path
}

const STORAGE_KEY = "worldcup-locale"

export function I18nProvider({ children }: { children: ReactNode }) {
  // Always initialize with "en-US" to ensure SSR and client hydration match.
  // The actual locale is detected/applied in the useEffect below.
  const [locale, setLocaleState] = useState<Locale>("en-US")

  const messages = localeMap[locale]

  // After hydration, detect the user's preferred locale from localStorage
  // or browser settings and update if different from the default.
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as Locale | null
    const detected = stored && stored in localeMap ? stored : detectLocale()
    if (detected !== locale) {
      setLocaleState(detected)
    }
    setApiClientLanguage(detected === "zh-CN" ? "zh" : "en")
    // Sync the preferences store so all consumers (AI chat, championship
    // prediction, match detail, etc.) read the correct language instead of
    // the hardcoded "en-US" default.
    usePreferencesStore.getState().setLanguage(detected)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const setLocale = useCallback((newLocale: Locale) => {
    setLocaleState(newLocale)
    localStorage.setItem(STORAGE_KEY, newLocale)
    document.documentElement.lang = newLocale === "zh-CN" ? "zh" : "en"
    setApiClientLanguage(newLocale === "zh-CN" ? "zh" : "en")
    // Keep preferences store in sync so every consumer reads the right lang.
    usePreferencesStore.getState().setLanguage(newLocale)
    useMatchesStore.getState().invalidateAll()
  }, [])

  useEffect(() => {
    document.documentElement.lang = locale === "zh-CN" ? "zh" : "en"
  }, [locale])

  const t = useCallback(
    (key: string): string => {
      return getNestedValue(
        messages as unknown as Record<string, unknown>,
        key,
      )
    },
    [messages],
  )

  return (
    <I18nContext.Provider value={{ locale, messages, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  )
}

export function useI18n(): I18nContextValue {
  const ctx = useContext(I18nContext)
  if (!ctx) {
    throw new Error("useI18n must be used within an I18nProvider")
  }
  return ctx
}
