# AGENTS.md — lib/store/

## Purpose
Zustand global state stores for the frontend application. Each store manages a distinct domain of state with clean action APIs.

## Import Pattern
```typescript
import { usePreferencesStore, useMatchesStore, useLiveStore, useAIChatStore } from "@/lib/store"
// Or import specific types:
import type { Language, WSConnectionStatus } from "@/lib/store"
```

## Architecture
- `preferences.ts` → User settings (language, timezone, viewMode, theme). Uses `zustand/persist` middleware for localStorage persistence (key: `worldcup-preferences`).
- `matches.ts` → Match data cache indexed by date + live matches list. Fetch actions delegate to `@/lib/api/matches`. 5-minute TTL per date entry.
- `live.ts` → Real-time WebSocket state: connection status, score patches, cheer updates. Driven by `@/lib/websocket.ts` WSClient which dispatches backend events into this store.
- `ai-chat.ts` → AI chat conversation history + streaming state. Manages content buffers and analysis payloads during SSE streaming (to be connected in P3-04).
- `index.ts` → Barrel re-exports for all stores and types.

## Rules
- No `any` types — all state shapes are fully typed
- Stores are standalone hooks; no React Context wrapping needed (Zustand handles subscriptions)
- API calls in stores use the existing `@/lib/api/*` modules
- Persistence only in `preferences.ts`; other stores are session-scoped
