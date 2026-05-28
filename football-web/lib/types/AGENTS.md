# AGENTS.md — lib/types/

## Purpose
Centralized TypeScript type definitions shared across the frontend. All components should import from `@/lib/types` rather than defining inline interfaces.

## Import Pattern
```typescript
import type { Match, Team, BracketMatch, Message, ApiResponse } from "@/lib/types"
```

## Architecture
- `team.ts` → base `Team` (name/code/flag), extended by `BracketTeam` in bracket.ts
- `match.ts` → `Match` uses `Team` from team.ts; `MatchQueryParams` for API filtering; `MatchDateInfo` for date-stage pairs from `GET /api/matches/dates`
- `bracket.ts` → `BracketTeam extends Team` with score/winner/fromGroup fields; `BracketTree` is the top-level bracket container
- `ai.ts` → `Message` for chat; `TeamAnalysis` for analysis payload; `SSEEvent` for streaming
- `api.ts` → `ApiResponse<T>` standard envelope matching backend `app/schemas/common.py`
- `index.ts` → re-exports all types via `export type { ... }` (type-only exports)

## Rules
- No `any` types allowed
- All exports are `export type` (type-only) in index.ts
- Cross-module references use `import type` (e.g., bracket.ts imports from team.ts)
