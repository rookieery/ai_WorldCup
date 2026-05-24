# i18n Module — Agent Notes

## Architecture
- Lightweight React Context approach (no next-intl or other external deps)
- `I18nProvider` wraps all children in `layout.tsx`
- `useTranslation()` hook exposes `{ t, locale, setLocale }`

## Key Files
- `context.tsx` — Provider + `useI18n` hook, locale detection, localStorage persistence
- `use-translation.ts` — Public-facing `useTranslation` hook (thin wrapper)
- `types.ts` — `Locale` union type + `LocaleMessages` interface
- `locales/zh-CN.json` — Chinese translations
- `locales/en-US.json` — English translations

## Patterns
- Access translations via dot-notation keys: `t("header.title")`
- The `t()` function returns the key itself as fallback if not found
- Locale is persisted in `localStorage` under key `worldcup-locale`
- Language detection: `navigator.language.startsWith("zh")` → zh-CN, else en-US
- `document.documentElement.lang` is synced: zh-CN → "zh", en-US → "en"

## Adding New Keys
1. Add the key to BOTH `zh-CN.json` AND `en-US.json` (must have parity)
2. Add the corresponding field to the `LocaleMessages` interface in `types.ts`
3. Use in components: `t("namespace.keyName")`

## Namespace Convention
- `header.*` — Header component texts
- `timeline.*` — Date timeline stage labels
- `match.*` — Match card labels and statuses
- `bracket.*` — Tournament bracket labels
- `ai.*` — AI copilot panel texts
- `footer.*` — Footer status bar
- `common.*` — Shared: weekdays, months, generic messages
