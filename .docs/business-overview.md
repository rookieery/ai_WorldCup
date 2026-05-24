# Business Overview — World Cup 2026 Dashboard

## Product Summary

Real-time FIFA World Cup 2026 dashboard for global football fans. Features match schedules, live scores, knockout bracket visualization, and AI-powered match analysis chatbot.

**Visual Style**: Cyberpunk dark glassmorphism (Midnight Navy + Electric Lime/Cyan/Magenta accents).

## Current State

| Aspect | Status |
|--------|--------|
| Frontend UI | Complete visual shell (all components built) |
| Data Source | 100% hardcoded in components |
| Backend API | Not started (football-server/ is empty) |
| State Management | Local `useState` only, no global store |
| Routing | Single `/` route, no navigation |
| AI Service | Simulated (2s timeout, fixed response) |
| Real-time Updates | None (WebSocket not implemented) |

## Core Business Entities

### Match
- Identified by `id` (number)
- Has two `Team` objects, stage, status, scores, times, venue
- Status flow: `upcoming` → `live` → `finished`
- Special flags: `isBigMatch`, `activityLevel` (0–100)

### Team
- Identified by 3-letter code (`BRA`, `FRA`, etc.)
- Properties: name, code, flag (emoji), FIFA ranking

### Bracket Match
- Identified by string `id` (`"qf1"`, `"sf1"`, `"f1"`)
- Round types: `QF`, `SF`, `F` (needs expansion: `R32`, `R16`, `3rd`)
- Links to next match via `nextMatchId` (defined in REQUIREMENTS but not yet in code)

### Team Analysis (AI)
- 5-dimension radar: attack, defense, possession, setpieces, form (0–100 each)
- Win/draw probabilities, key insights list

## Data Flow (Current)

```
page.tsx (state owner)
├── timezone ──────→ Header (toggle display)
├── viewMode ──────→ Header (toggle) → switches Timeline/Bracket
├── selectedDate ──→ DateTimeline (highlight) → MatchCardsGrid (passed but unused)
│
├── [Timeline Mode]
│   ├── DateTimeline ──── hardcoded 40-day array
│   └── MatchCardsGrid ── hardcoded 4-match array
│
├── [Bracket Mode]
│   └── TournamentBracket ── hardcoded 7-match array (QF+SF+F)
│
└── AICopilotPanel ──── hardcoded messages + 2s fake response
```

## Data Flow (Target — from REQUIREMENTS.md)

```
page.tsx (state owner)
├── [State Store: Zustand]
│   ├── user preferences (timezone, view mode, theme)
│   ├── match data cache (from API)
│   ├── live updates (from WebSocket)
│   └── AI chat history
│
├── [API Layer]
│   ├── GET /api/matches?date=... → match list
│   ├── GET /api/bracket → full knockout tree
│   ├── GET /api/groups/:group → standings
│   ├── POST /api/ai/chat → streaming AI response
│   ├── GET /api/cheers/:matchId → fan vote data
│   └── WS /api/ws/live → real-time score updates
│
└── [Routes]
    ├── / → Dashboard (Timeline/Bracket)
    ├── /groups → Group standings
    ├── /groups/:group → Single group detail
    ├── /matches/:id → Match detail
    ├── /teams/:code → Team detail
    ├── /bracket → Full bracket (standalone)
    └── /stats → Statistics center
```

## Tournament Structure (2026 World Cup)

| Phase | Details |
|-------|---------|
| Groups | 12 groups (A–L), 4 teams each |
| Group Stage | 72 matches (6 per group) |
| Qualification | Top 2 per group + 8 best 3rd-place = 32 teams |
| Knockout R32 | 16 matches |
| Knockout R16 | 8 matches |
| Quarter-Finals | 4 matches |
| Semi-Finals | 2 matches |
| 3rd Place | 1 match |
| Final | 1 match |
| **Total** | **104 matches** |

## Key Implementation Gaps

1. **No API integration** — all data hardcoded
2. **No global state** — Zustand recommended
3. **No routing** — single page only
4. **Bracket incomplete** — only QF→SF→F, needs R32→R16→QF→SF→3rd→F
5. **Types not shared** — duplicated across components
6. **Date filtering missing** — `selectedDate` passed but not used
7. **Group standings missing** — entire UI section not built
8. **Match detail missing** — no click-to-view match info
9. **AI is fake** — simulated responses, no backend
10. **No real-time updates** — no WebSocket/SSE

## AI Prediction Skills

Two skill files define the reasoning framework for match predictions:

- `skills/group_stage_predict.md` — 6-step reasoning (form, H2H, tactics, key players, home advantage, intangibles)
- `skills/knockout_stage_predict.md` — 5-step reasoning (form, H2H, knockout psychology, tactical matchup, X-factors)

These should power the backend AI service (`POST /api/ai/chat`).
