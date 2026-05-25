# Agent Component Map

> React component registry for `football-web`.

## Page Component

### `app/page.tsx` — `WorldCupDashboard`
- **Type**: Client component (`"use client"`)
- **State**: `timezone`, `viewMode`, `selectedDate` (all `useState`)
- **Layout**: Header → Main (Timeline|Bracket) + AI Sidebar → Footer
- **Props flow**: State drilled directly to child components
- **Features**: Groups quick-entry link (Trophy icon → `/groups`) in Timeline view

### `app/bracket/page.tsx` — `BracketPage`
- **Type**: Client component (`"use client"`)
- **Layout**: Header → TournamentBracket → Footer (full-width, no sidebar)
- **Wrapper**: `I18nProvider` for standalone page i18n context
- **Features**: Full-screen bracket view accessible at `/bracket`
- **Type**: Client component (`"use client"`)
- **State**: `timezone`, `viewMode`, `selectedDate` (all `useState`)
- **Layout**: Header → Main (Timeline|Bracket) + AI Sidebar → Footer
- **Props flow**: State drilled directly to child components
- **Features**: Groups quick-entry link (Trophy icon → `/groups`) in Timeline view

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
- **Real-time**: Subscribes to `useLiveStore` for live score patches, cheer updates, and WS status; starts `wsClient` on mount
- **Cheer Voting**: `MatchCard.handleCheer()` calls `postCheer(matchId, side)` API with optimistic update + rollback on failure
- **Match Detail**: Card click opens `MatchDetailDialog` via `onMatchClick` callback (passes matchId)
- **Features**: Live score display with WS-patched data, Big Match badge, activity bar, Fan Cheer Meter (hover expand), WS connection indicator, loading/error/empty states
- **API mapping**: `apiMatchToUi()` converts backend `MatchApiItem` → frontend `Match` type
- **i18n**: Uses `useTranslation()` for all visible text
- **Types imported**: `Match`, `CityIcon` from `@/lib/types`, `LiveScorePatch`, `CheerUpdate` from `@/lib/store`
- **Dependencies**: `cn` utility, `lucide-react` icons (incl. Wifi, WifiOff), `getMatches` + `apiMatchToUi` from API, `postCheer` from cheers API, `useLiveStore`, `wsClient`, `MatchDetailDialog`
- **Lines**: ~525

### `group-standings.tsx` — `GroupStandings`
- **Data**: Fetched from API via `getGroups()` — all 12 groups (A-L) with standings
- **Sub-components**: `GroupCard` (per-group standings card)
- **Features**: 12-group grid (responsive: 1→4 cols), qualified zone highlight (top 2), group color coding (A-L cycle), link to group detail page
- **UI**: Glass-card with color-coded header, shadcn Table, qualified indicator bar
- **i18n**: Uses `useTranslation()` for all visible text; locale-aware team names (zh-CN → name_zh)
- **Dependencies**: `cn` utility, `lucide-react` icons, `getGroups` from API, `Table` components from shadcn
- **Lines**: ~307

### `tournament-bracket.tsx` — `TournamentBracket`
- **Data**: Fetched from API via `getBracket()` — full BracketTree (R32→R16→QF→SF→3rd→F)
- **Sub-components**: `BracketCard`, `TeamRow`, `RoundConnector`, `DesktopBracket`, `MobileBracket`
- **Match Detail**: BracketCard click opens `MatchDetailDialog` via `onMatchClick` callback (parseInt from string match.id)
- **UI**: 6-round horizontal scroll with SVG connectors (desktop), vertical stack (mobile)
- **Features**: API data fetch with loading/error/retry, TBD teams show fromGroup info, winner gold highlight, LIVE pulse, 3rd place as separate branch
- **Responsive**: `hidden md:block` for DesktopBracket, `md:hidden` for MobileBracket
- **All colors**: Semantic theme variables (text-gold, text-accent, bg-primary/20, etc.)
- **All text**: Internationalized via `t()`
- **Types imported**: `BracketMatch`, `BracketTeam`, `BracketRoundName`, `BracketTree` from `@/lib/types`
- **Dependencies**: `cn` utility, `lucide-react` icons (Trophy, Zap, Loader2, AlertCircle, Medal), `getBracket` from API, `useTranslation` from i18n, `MatchDetailDialog`
- **Lines**: ~430

### `match-detail-dialog.tsx` — `MatchDetailDialog`
- **Props**: `matchId` (number | null), `open`, `onOpenChange`
- **Data**: Fetched from API via `getMatchById(id)` + `getCheers(matchId)` on dialog open
- **Real-time**: Merges live score patches and cheer updates from `useLiveStore`
- **Sections**: Match header (teams + score + status), Live activity bar, Fan cheer meter, Match events timeline (1st/2nd half + extra time), Match statistics (goals/cards), Venue info
- **Cyberpunk Style**: glass-card, glow effects, gradient overlays, LED display for live scores
- **i18n**: Uses `useTranslation()` for all visible text (matchDetail namespace)
- **Types imported**: `LiveScorePatch`, `CheerUpdate` from `@/lib/store`, `MatchDetailData` from `match-detail-helpers`
- **Dependencies**: Dialog, ScrollArea, Separator (shadcn), `cn`, `lucide-react` icons, `getMatchById` from API, `getCheers` from cheers API, `useLiveStore`, helper components
- **Lines**: ~465

### `match-detail-helpers.tsx` — Helper components + types for MatchDetailDialog
- **Exported Types**: `MatchDetailEvent`, `MatchDetailData`
- **Components**: `EventsSection` (half-grouped event list), `StatRow` (dual-bar stat), `VenueInfoItem` (label-value pair)
- **Internal**: `EventIcon` (event-type icon), `EventLabel` (event-type i18n label)
- **Lines**: ~215

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
| `locales/zh-CN.json` | 简体中文 | 125 keys, 8 namespaces |
| `locales/en-US.json` | English | 125 keys, 8 namespaces |

### Namespaces
| Namespace | Keys | Purpose |
|-----------|------|---------|
| `header` | 8 | Title, subtitle, timezone/view labels, language labels (langZh/langEn) |
| `timeline` | 8 | Stage labels (Group/R32/R16/QF/SF/3rd/Final/Rest) |
| `match` | 12 | Match card labels (Live/Big Match/FT/cheer etc.) |
| `matchDetail` | 18 | Match detail dialog labels (events, stats, venue, cheer) |
| `bracket` | 16 | Knockout bracket labels (6 rounds, fromGroup, tbd, states) |
| `ai` | 20 | AI copilot panel labels |
| `footer` | 4 | Footer status bar labels |
| `groups` | 18 | Group standings labels (title, table columns, navigation, states) |
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

## State Management (`lib/store/`) — Zustand

### Architecture
- **Approach**: Zustand stores (lightweight, no boilerplate)
- **Import**: `import { usePreferencesStore, useMatchesStore, useLiveStore, useAIChatStore } from "@/lib/store"`
- **Persistence**: `usePreferencesStore` uses `zustand/persist` middleware (localStorage key `worldcup-preferences`)

### Store Registry
| Store | File | Purpose |
|-------|------|---------|
| `usePreferencesStore` | `preferences.ts` | User settings: language, timezone, viewMode, theme (localStorage persisted) |
| `useMatchesStore` | `matches.ts` | Match data cache indexed by date + live matches, fetch actions with TTL |
| `useLiveStore` | `live.ts` | Real-time WebSocket state: connection status, score patches, cheer updates |
| `useAIChatStore` | `ai-chat.ts` | AI chat messages, streaming buffers, pending analysis payload |

### Usage Pattern
```typescript
import { usePreferencesStore } from "@/lib/store"

function MyComponent() {
  const { language, timezone, setLanguage } = usePreferencesStore()
  // language: "zh-CN" | "en-US"
  // timezone: "local" | "host"
  // setLanguage("zh-CN")
}
```

### Key Design Decisions
- **Preferences** persist to localStorage via `zustand/middleware/persist`
- **Matches** store has a 5-minute TTL cache per date, avoiding redundant API calls
- **Live** store mirrors WebSocket events and is the single source of truth for real-time data
- **AI Chat** store manages streaming buffers and finalizes messages on stream completion

## WebSocket Client (`lib/websocket.ts`)

### `wsClient` — Singleton WebSocket client
- **Exports**: `wsClient` (WSClient instance)
- **Config**: `NEXT_PUBLIC_WS_URL` env var (auto-derived from `NEXT_PUBLIC_API_URL` by replacing `http` → `ws`)
- **Endpoint**: `/ws/live`
- **Features**:
  - Auto-connect with exponential back-off reconnection (1s base, 30s max, 20 attempts)
  - Dispatches all backend events into Zustand `useLiveStore`
  - Subscribe/unsubscribe to specific match channels
  - Connection status tracked in `useLiveStore.wsStatus`

### Event Mapping (Backend → Zustand Live Store)
| Backend WSEventType | Frontend Action | Store Method |
|---------------------|-----------------|--------------|
| `score_update` | Apply score patch | `applyScoreUpdate({ matchId, score1, score2, status, activityLevel })` |
| `match_start` | Set status=live, scores=0 | `applyScoreUpdate(...)` |
| `match_end` | Set status=finished, final scores | `applyScoreUpdate(...)` |
| `activity_update` | Update activity level (preserves scores) | `applyScoreUpdate(...)` |
| `cheer_update` | Update cheer counts | `applyCheerUpdate({ matchId, home, away })` |
| `connected` | Apply initial live matches payload | Batch `applyScoreUpdate(...)` for each live match |
| `ping` | No-op (browser auto-responds) | — |
| `bracket_update` | No-op (reserved for future) | — |

### Usage Pattern
```typescript
import { wsClient } from "@/lib/websocket"
import { useLiveStore } from "@/lib/store"

// Start connection (typically in top-level component mount)
wsClient.start()

// Subscribe to specific match updates
wsClient.subscribeToMatch(42)

// Read real-time data in components
const scorePatch = useLiveStore((s) => s.scoreUpdates[matchId])
const cheerData = useLiveStore((s) => s.cheerUpdates[matchId])
const wsStatus = useLiveStore((s) => s.wsStatus)

// Stop connection (on page unload)
wsClient.stop()
```

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
