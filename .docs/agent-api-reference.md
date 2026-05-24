# Agent API Reference

> Backend API contracts. Full spec is in `football-web/REQUIREMENTS.md` section VII.

## Status: NOT YET IMPLEMENTED

The `football-server/` directory is empty. All frontend data is hardcoded.

## Planned API Structure

```
/api
├── /matches
│   ├── GET /                    # Match list (filter: date, stage, group, team, status)
│   ├── GET /:id                 # Single match detail
│   └── GET /live                # Current live matches
├── /bracket
│   ├── GET /                    # Full knockout bracket tree
│   └── GET /predictions         # AI bracket predictions
├── /teams
│   ├── GET /                    # All teams
│   ├── GET /:code               # Team detail
│   └── GET /:code/stats         # Team statistics
├── /groups
│   ├── GET /                    # All group standings
│   └── GET /:group              # Single group (standings + matches)
├── /venues
│   └── GET /                    # Venue list (with timezone info)
├── /cheers
│   ├── GET /:matchId            # Fan vote data for a match
│   └── POST /:matchId           # Submit fan vote
├── /ai
│   └── POST /chat               # AI chat (SSE streaming)
└── /ws
    └── /live                    # WebSocket real-time events
```

## Key Data Models (from REQUIREMENTS.md)

See `football-web/REQUIREMENTS.md` for full request/response examples and field definitions.

### Match Response Shape
```typescript
interface MatchResponse {
  date: string
  matches: Array<{
    id: number
    stage: string
    round: number
    status: "upcoming" | "live" | "finished"
    isBigMatch: boolean
    activityLevel: number
    team1: { name: string; code: string; flag: string; fifaRanking: number }
    team2: { name: string; code: string; flag: string; fifaRanking: number }
    score: { team1: number; team2: number } | null
    localTime: string
    hostTime: string
    venue: string
    hostCity: string
    hostCityTimezone: string
  }>
}
```

### Bracket Response Shape
```typescript
interface BracketResponse {
  rounds: Array<{
    name: string
    shortName: "R32" | "R16" | "QF" | "SF" | "3rd" | "F"
    matches: Array<{
      id: string
      position: number
      status: "upcoming" | "live" | "completed"
      team1: BracketTeam
      team2: BracketTeam
      nextMatchId: string
      venue: string
      matchTime: string
    }>
  }>
}
```

### AI Chat (SSE Stream)
```
POST /api/ai/chat
Body: { messages: Array<{role, content}>, context: {currentView, selectedDate, timezone} }
Response: SSE stream
  data: {"type": "text", "content": "..."}
  data: {"type": "analysis", "data": {TeamAnalysis}}
  data: {"type": "done"}
```

### WebSocket Events
| Event | Data |
|-------|------|
| `score_update` | `{matchId, team, score, event}` |
| `match_start` | `{matchId, status}` |
| `match_end` | `{matchId, status, score}` |
| `activity_update` | `{matchId, activityLevel}` |
| `bracket_update` | `{matchId, winner, nextMatchId}` |
