# Agent Component Map

> React component registry for `football-web`.

## Page Component

### `app/page.tsx` — `WorldCupDashboard`
- **Type**: Client component (`"use client"`)
- **State**: `timezone`, `viewMode`, `selectedDate` (all `useState`)
- **Layout**: Header → Main (Timeline|Bracket) + AI Sidebar → Footer
- **Props flow**: State drilled directly to child components

## Dashboard Components (`components/dashboard/`)

### `header.tsx` — `Header`
- **Props**: `timezone`, `viewMode`, `onTimezoneChange`, `onViewModeChange`
- **i18n**: Uses `useTranslation()` hook for all text; imports `Locale` type for language switch
- **UI**: Trophy icon + title, language switch (Globe + Select dropdown: zh-CN/en-US), timezone toggle (Clock icon + Switch), view toggle (Timeline/Bracket)
- **Language Switch**: Reads `locale`/`setLocale` from i18n context, renders as glass-card + Globe icon + shadcn Select
- **Dependencies**: `Switch`, `Label`, `Select`/`SelectContent`/`SelectItem`/`SelectTrigger`/`SelectValue` (shadcn), `lucide-react` icons (Globe, Clock, LayoutGrid, GitBranch, Trophy)
- **Lines**: ~139

### `date-timeline.tsx` — `DateTimeline`
- **Props**: `selectedDate`, `onDateSelect`
- **Data**: Fetched from API via `getMatchDates()` — dynamic match dates with stage labels
- **Auto-select**: On mount, selects today or nearest future match date
- **Auto-scroll**: Scrolls selected date into view on first render
- **UI**: Horizontal scroll with arrow nav, stage-colored date pills
- **Stage colors**: Group=lime, R32/R16=cyan, QF/SF=magenta, 3rd/Final=gold
- **i18n**: Uses `useTranslation()` for month/weekday labels and loading text
- **Dependencies**: `Button` (shadcn), `cn` utility, `getMatchDates` from API
- **Lines**: ~210

### `match-cards-grid.tsx` — `MatchCardsGrid`
- **Props**: `selectedDate`, `timezone` ("local" | "host")
- **Data**: Fetched from API via `getMatches({ date, timezone })` — dynamic, date-driven
- **Sub-components**: `MatchCard`, `CityIconComponent`, `EmptyState`
- **Features**: Live score display, Big Match badge, activity bar, Fan Cheer Meter (hover expand), loading/error/empty states
- **API mapping**: `apiMatchToUi()` converts backend `MatchApiItem` → frontend `Match` type
- **i18n**: Uses `useTranslation()` for all visible text
- **Types imported**: `Match`, `CityIcon` from `@/lib/types`, `MatchApiItem` from API module
- **Dependencies**: `cn` utility, `lucide-react` icons, `getMatches` + `apiMatchToUi` from API
- **Lines**: ~430

### `tournament-bracket.tsx` — `TournamentBracket`
- **Data**: Hardcoded `BracketMatch[]` (QF×4 + SF×2 + Final×1)
- **Sub-components**: `BracketCard`, `TeamRow`, `ConnectorLine`
- **UI**: Three-column grid with SVG connector lines, gradient glow effects
- **Note**: Currently only QF→SF→F, needs expansion to R32→R16→QF→SF→3rd→F
- **Types imported**: `BracketMatch`, `BracketTeam`, `BracketRoundName` from `@/lib/types`
- **Dependencies**: `cn` utility, `Trophy`/`Zap` icons
- **Lines**: ~438

### `ai-copilot-panel.tsx` — `AICopilotPanel`
- **State**: `messages[]`, `input`, `isTyping`, `isFocused`
- **Sub-components**: `MiniRadarChart`, `AnalysisCard`, `ThinkingIndicator`
- **Data**: Hardcoded initial messages + `brazilFranceAnalysis`
- **AI Simulation**: 2s timeout returns fixed string (no real API call)
- **Features**: Quick prompts, chat messages, radar chart analysis, streaming indicator
- **Types imported**: `Message`, `TeamAnalysis`, `TeamStats` from `@/lib/types`
- **Dependencies**: `Input`, `Button` (shadcn), `cn`, `lucide-react`
- **Lines**: ~437

## Shared Components

### `components/theme-provider.tsx`
- `next-themes` wrapper (ThemeProvider). **Not currently used in layout.tsx.**

### `components/ui/` — shadcn/ui primitives
~60 components installed. Key ones used in dashboard:
- `button.tsx`, `input.tsx`, `switch.tsx`, `label.tsx`
- Many installed but unused (accordion, dialog, tabs, table, etc.)

## Type Definitions

Types are centralized in `lib/types/` and re-exported from `@/lib/types`. Import with `import type { ... } from "@/lib/types"`.

## i18n System (`lib/i18n/`)

### Architecture
- **Approach**: Lightweight React Context (no external i18n library)
- **Provider**: `I18nProvider` wraps app in `layout.tsx`
- **Hook**: `useTranslation()` → `{ t, locale, setLocale }`
- **Persistence**: `localStorage` key `worldcup-locale`
- **Auto-detection**: Reads `navigator.language` on first visit (zh* → zh-CN, else en-US)
- **Language mapping**: zh-CN → `document.documentElement.lang = "zh"`, en-US → `"en"`

### Locale Files
| File | Language | Keys |
|------|----------|------|
| `locales/zh-CN.json` | 简体中文 | 83 keys, 6 namespaces |
| `locales/en-US.json` | English | 83 keys, 6 namespaces |

### Namespaces
| Namespace | Keys | Purpose |
|-----------|------|---------|
| `header` | 8 | Title, subtitle, timezone/view labels, language labels (langZh/langEn) |
| `timeline` | 8 | Stage labels (Group/R32/R16/QF/SF/3rd/Final/Rest) |
| `match` | 12 | Match card labels (Live/Big Match/FT/cheer etc.) |
| `bracket` | 9 | Knockout bracket labels |
| `ai` | 20 | AI copilot panel labels |
| `footer` | 4 | Footer status bar labels |
| `common` | 22 | Weekdays, months, generic messages |

### Usage Pattern
```typescript
import { useTranslation } from "@/lib/i18n"

function MyComponent() {
  const { t, locale, setLocale } = useTranslation()
  return <h1>{t("header.title")}</h1>  // "World Cup 2026" or "世界杯 2026"
}
```

## API Client Layer (`lib/api-client.ts` + `lib/api/`)

### `lib/api-client.ts` — Core fetch wrapper
- **Exports**: `apiRequest<T>(path, options)`, `buildQueryString(params)`, `setApiClientLanguage(lang)`, `getApiClientLanguage()`, `ApiClientError`
- **Config**: `NEXT_PUBLIC_API_URL` env var (default: `http://localhost:8000`)
- **Features**: 
  - Auto-prepends base URL
  - Attaches `Accept-Language` header from i18n state (module-level `currentLang`, updated via `setApiClientLanguage`)
  - Timeout support (default 15s, AbortController)
  - Unwraps `ApiResponse<T>` envelope (returns `data` field directly)
  - Unified error handling: network errors, HTTP status codes (401/403/404/422/429/500/502-504) → `ApiClientError`
  - `buildQueryString()` skips undefined/null values

### API Modules (`lib/api/`)
| Module | Functions | Backend Endpoints |
|--------|-----------|-------------------|
| `matches.ts` | `getMatchDates()`, `getMatches(params)`, `getMatchById(id, opts)`, `getLiveMatches(opts)`, `apiMatchToUi(item)` | `GET /api/matches/dates`, `GET /api/matches`, `GET /api/matches/:id`, `GET /api/matches/live` |
| `bracket.ts` | `getBracket(opts)` | `GET /api/bracket` |
| `teams.ts` | `getTeams(params)`, `getTeamByCode(code)` | `GET /api/teams`, `GET /api/teams/:code` |
| `groups.ts` | `getGroups()`, `getGroupDetail(group, opts)` | `GET /api/groups`, `GET /api/groups/:group` |
| `venues.ts` | `getVenues(params)` | `GET /api/venues` |
| `cheers.ts` | `getCheers(matchId)`, `postCheer(matchId, side)` | `GET /api/cheers/:matchId`, `POST /api/cheers/:matchId` |

**Usage pattern**:
```typescript
import { getMatches } from "@/lib/api/matches"
import { setApiClientLanguage } from "@/lib/api-client"

// Set language from i18n provider
setApiClientLanguage("zh-CN")

// Fetch data — ApiResponse envelope is auto-unwrapped
const result = await getMatches({ date: "2026-06-14", page: 1, pageSize: 20 })
// result = { items: Match[], total, page, page_size }
```

| Module | Types | Purpose |
|--------|-------|---------|
| `lib/types/team.ts` | `Team`, `TeamDetail`, `TeamStanding` | Team base shape, API detail, group standings row |
| `lib/types/match.ts` | `Match`, `MatchStatus`, `CityIcon`, `MatchEvent`, `MatchEventType`, `MatchQueryParams` | Match card data, event timeline, API query filters |
| `lib/types/bracket.ts` | `BracketTeam`, `BracketMatch`, `BracketRound`, `BracketTree`, `BracketRoundName`, `BracketMatchStatus` | Knockout bracket tree (R32→F) |
| `lib/types/ai.ts` | `Message`, `MessageRole`, `MessageType`, `TeamAnalysis`, `TeamAnalysisSide`, `TeamStats`, `SSEEvent`, `SSEEventType` | AI chat messages, analysis payload, SSE streaming |
| `lib/types/api.ts` | `ApiResponse<T>`, `PaginatedResponse<T>`, `ApiError` | Standard API envelope types |

## CSS Architecture (`app/globals.css`)

| Concept | CSS Variable / Class | Usage |
|---------|---------------------|-------|
| Primary | `--primary` (`#CCFF00`) | Electric Lime, buttons, highlights |
| Accent | `--accent` (`#00F0FF`) | Cyber Cyan, live indicators |
| Magenta | `--magenta` (`#FF00E5`) | Bracket SF stage, accents |
| Gold | `--gold` (`#FFD700`) | Big Match, Final, premium |
| Glass card | `.glass-card` | `backdrop-filter: blur(20px)` |
| Glass border | `--glass-border` | `rgba(255,255,255,0.08)` |
| Score font | `.font-score` | Geist Mono, tabular-nums |
| LED display | `.led-display` | Text-shadow glow for live scores |
| Scrollbar hide | `.scrollbar-hide` | Cross-browser scrollbar hidden |
