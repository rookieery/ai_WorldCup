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
- **UI**: Trophy icon + title, timezone toggle (Local/Host), view toggle (Timeline/Bracket)
- **Dependencies**: `Switch`, `Label` (shadcn), `lucide-react` icons
- **Lines**: ~107

### `date-timeline.tsx` — `DateTimeline`
- **Props**: `selectedDate`, `onDateSelect`
- **Data**: Hardcoded 40-day array (Jun 11–Jul 19) with stage labels
- **UI**: Horizontal scroll with arrow nav, stage-colored date pills
- **Stage colors**: Group=lime, R32/R16=cyan, QF/SF=magenta, 3rd/Final=gold
- **Dependencies**: `Button` (shadcn), `cn` utility
- **Lines**: ~167

### `match-cards-grid.tsx` — `MatchCardsGrid`
- **Props**: `selectedDate` (not yet used for filtering)
- **Data**: Hardcoded `Match[]` array (4 sample matches)
- **Sub-components**: `MatchCard`, `CityIconComponent`
- **Features**: Live score display, Big Match badge, activity bar, Fan Cheer Meter (hover expand)
- **Types imported**: `Match`, `CityIcon` from `@/lib/types`
- **Dependencies**: `cn` utility, `lucide-react` icons
- **Lines**: ~432

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
