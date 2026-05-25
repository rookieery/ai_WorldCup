# Agent File Map

> Navigate the codebase by purpose.

## Root

```
ai_WorldCup/
├── CLAUDE.md                 # Engineering standards (highest priority)
├── prompt.md                 # Ralph agent loop instructions
├── prd.json                  # Story tracker (branch + stories with passes flag)
├── progress.txt              # Ralph execution progress log
├── archive.js                # Unknown utility (standalone script)
├── ralph.sh                  # Shell entry point for Ralph agent
├── .claudeignore             # Claude ignore rules
├── .docs/                    # This documentation directory
├── data/                     # Raw tournament data
├── skills/                   # AI prediction skill definitions
├── football-web/             # Next.js frontend (MAIN APP)
└── football-server/          # Backend (EMPTY — not yet started)
```

## football-web/ — Frontend (Next.js 16 + React 19)

```
football-web/
├── app/
│   ├── layout.tsx            # Root layout (dark theme, Geist fonts, Analytics)
│   ├── page.tsx              # Single-page dashboard (all state lives here, Groups quick-entry link)
│   ├── globals.css           # CSS variables, animations, glassmorphism utilities
│   └── groups/
│       ├── page.tsx          # Groups overview page (all 12 groups standings grid)
│       └── [group]/
│           └── page.tsx      # Single group detail page (standings + match list)
├── bracket/
│   └── page.tsx              # Standalone full-screen bracket page
├── stats/
│   └── page.tsx              # Stats center page (scorer leaderboard + match statistics)
├── teams/
│   └── [code]/
│       └── page.tsx          # Team detail page (team profile + group standing + finished/upcoming matches)
├── components/
│   ├── dashboard/
│   │   ├── header.tsx        # Top bar (language switch + timezone + view mode toggles, i18n-aware)
│   │   ├── date-timeline.tsx # Horizontal date picker (Jun 11–Jul 19)
│   │   ├── match-cards-grid.tsx  # Match card list + Fan Cheer Meter + real-time WS score/cheer integration + live connection indicator + MatchDetailDialog on click
│   │   ├── match-detail-dialog.tsx # Match detail dialog (teams+score, events timeline, stats, cheer, venue info) — cyberpunk glass-card style
│   │   ├── match-detail-helpers.tsx # Helper components + types for MatchDetailDialog (EventsSection, StatRow, VenueInfoItem, EventIcon/Label)
│   │   ├── group-standings.tsx   # Group standings grid (12 groups A-L, qualified highlight)
│   │   ├── tournament-bracket.tsx # Full 6-round knockout bracket (R32→R16→QF→SF→3rd→F, API-driven) + MatchDetailDialog on click
│   │   └── ai-copilot-panel.tsx   # AI chat sidebar (real SSE streaming, typewriter effect, thinking block, analysis card, Zustand store)
│   ├── stats/
│   │   ├── scorers-table.tsx    # Scorers leaderboard table (sortable by goals/assists, cyberpunk glass-card, top-3 highlight)
│   │   └── match-stats-card.tsx # Match statistics card (upcoming/live/finished counts with progress bars)
│   ├── theme-provider.tsx    # next-themes wrapper (unused in layout currently)
│   └── ui/                   # shadcn/ui primitives (~60 components)
├── hooks/
│   ├── use-mobile.ts         # Mobile breakpoint hook
│   └── use-toast.ts          # Toast hook
├── lib/
│   ├── utils.ts              # cn() utility (clsx + tailwind-merge)
│   ├── api-client.ts         # Core fetch wrapper: base URL, Accept-Language, ApiResponse<T> unwrapping, error handling, query-string builder
│   ├── websocket.ts          # WebSocket client singleton (auto-connect/reconnect, event dispatch to Zustand live store)
│   ├── i18n/                 # Internationalization infrastructure
│   │   ├── index.ts          # Barrel exports (I18nProvider, useI18n, useTranslation, types)
│   │   ├── context.tsx       # I18nProvider (React Context: locale state, t() function, localStorage persistence)
│   │   ├── use-translation.ts # useTranslation hook — thin wrapper exposing { t, locale, setLocale }
│   │   ├── types.ts          # Locale union type + LocaleMessages interface (mirrors JSON shape)
│   │   └── locales/
│   │       ├── zh-CN.json    # Chinese translations (125 keys across 8 namespaces)
│   │       └── en-US.json    # English translations (125 keys, full zh-CN parity)
│   ├── api/                  # API module functions (one file per backend resource)
│   │   ├── matches.ts        # getMatchDates(), getMatches(params), getMatchById(id), getLiveMatches(), apiMatchToUi()
│   │   ├── bracket.ts        # getBracket()
│   │   ├── teams.ts          # getTeams(params), getTeamByCode(code), getTeamStats(code) — team detail with standing + matches
│   │   ├── groups.ts         # getGroups(), getGroupDetail(group)
│   │   ├── venues.ts         # getVenues(params)
│   │   ├── cheers.ts         # getCheers(matchId), postCheer(matchId, side)
│   │   ├── stats.ts          # getScorers(params) — scorer leaderboard data
│   │   └── ai-chat.ts        # streamChat() SSE consumer (fetch+ReadableStream, POST /api/ai/chat)
│   ├── store/                # Zustand global state stores
│   │   ├── index.ts          # Barrel re-exports for all stores
│   │   ├── preferences.ts    # User preferences (language, timezone, viewMode, theme) — localStorage persisted
│   │   ├── matches.ts        # Match data cache (by date + live) with fetch actions + TTL
│   │   ├── live.ts           # Real-time WebSocket state (scores, cheer updates, WS connection status) — driven by websocket.ts events
│   │   └── ai-chat.ts        # AI chat messages + streaming state (content buffers, analysis payload)
│   └── types/                # Shared TypeScript type definitions
│       ├── index.ts          # Unified re-exports
│       ├── team.ts           # Team, TeamDetail, TeamStanding
│       ├── match.ts          # Match, MatchStatus, MatchEvent, MatchQueryParams, CityIcon, MatchDateInfo
│       ├── bracket.ts        # BracketTeam, BracketMatch, BracketRound, BracketTree, BracketRoundName
│       ├── ai.ts             # Message, TeamAnalysis, TeamStats, SSEEvent
│       └── api.ts            # ApiResponse<T>, PaginatedResponse<T>, ApiError
├── styles/
│   └── globals.css           # Duplicate/alternate globals (check relevance)
├── package.json              # Dependencies (next 16, recharts, date-fns, zod, etc.)
├── components.json           # shadcn/ui config (new-york style, RSC enabled)
├── tsconfig.json             # TypeScript config
├── next.config.mjs           # Next.js config
└── postcss.config.mjs        # PostCSS config
```

## data/ — Tournament Data

```
data/
├── 2026_FIFA_World_Cup_Group_Stage.md  # 12 groups × 6 matches (72 total), results TBD
└── 2022_FIFA_World_Cup_Results.md      # Qatar 2022 results (64 matches, Chinese)
```

## skills/ — AI Prediction Prompts

```
skills/
├── README.md                     # Skills overview
├── group_stage_predict.md        # 6-step reasoning for group match prediction
└── knockout_stage_predict.md     # 5-step reasoning for knockout match prediction
```

## football-server/ — Backend (FastAPI + SQLite + Redis)

```
football-server/
├── pyproject.toml               # Project metadata + all core dependencies
├── alembic.ini                  # Alembic config (DB URL from app.config, logging)
├── .env.example                 # Environment variable templates
├── .gitignore                   # Python/venv/db ignore rules
├── run.py                       # Uvicorn entry point (python run.py or python run.py --prod)
├── alembic/
│   ├── env.py                   # Async migration runner (reads settings.DATABASE_URL)
│   ├── script.py.mako           # Migration script template
│   └── versions/
│       └── 001_initial_schema.py  # Initial migration: 5 tables + FK relationships
├── app/
│   ├── __init__.py              # Package init (empty)
│   ├── config.py                # Pydantic Settings: all env vars with defaults (incl. REDIS_URL, REDIS_ENABLED, SCRAPER_*, scraper intervals)
│   ├── main.py                  # FastAPI app factory (lifespan: DB + Redis init/close, ScraperScheduler start/stop, middleware, routers, /docs)
│   ├── dependencies.py          # DI providers: get_db, get_*_service, get_ai_service, get_language; Redis DI via app.redis.get_redis
│   ├── exceptions/
│   │   ├── __init__.py          # Re-exports all exception classes
│   │   └── exceptions.py        # AppException hierarchy (NotFound, Validation, Business, ExternalService)
│   ├── middleware/
│   │   ├── __init__.py          # Re-exports all middleware classes
│   │   ├── error_handler.py     # Global exception → ApiResponse {code, data, message} middleware
│   │   ├── cors.py              # CORS middleware (origins from config)
│   │   └── logging.py           # Request logging middleware (method/path/status/duration)
│   ├── models/
│   │   ├── __init__.py          # Re-exports all model classes + Base
│   │   ├── base.py              # DeclarativeBase + TimestampMixin (created_at, updated_at)
│   │   ├── team.py              # Team model (48 teams, code/name UNIQUE)
│   │   ├── venue.py             # Venue model (16 stadiums with timezone info)
│   │   ├── match.py             # Match model (104 fixtures, FK→Team/Venue/self)
│   │   ├── group_standing.py    # GroupStanding model (48 rows, FK→Team UNIQUE)
│   │   └── match_event.py       # MatchEvent model (goals/cards/subs, FK→Match)
│   ├── repositories/
│   │   ├── __init__.py          # Re-exports all repository classes
│   │   ├── base.py              # BaseRepository[T] generic CRUD (get_by_id, get_all, create, update, delete)
│   │   ├── team_repo.py         # TeamRepository: get_by_code, get_by_group
│   │   ├── match_repo.py        # MatchRepository: get_by_date, get_by_stage, get_by_status, get_live_matches, get_bracket_matches, get_by_group_label, get_by_team_code, get_match_dates
│   │   ├── venue_repo.py        # VenueRepository: inherits base CRUD only
│   │   ├── group_repo.py        # GroupRepository: get_by_group_label (sorted by points), get_group_matches
│   │   └── match_event_repo.py  # MatchEventRepository: get_by_match (ordered by minute)
│   ├── services/
│   │   ├── __init__.py          # Re-exports AIService, TeamService, VenueService, MatchService, GroupService, BracketService, StatsService, LiveService, ConnectionManager, PromptBuilder, get_manager
│   │   ├── ai_service.py        # AIService: Deepseek API client (stream_chat AsyncGenerator → SSEEvent objects: thinking/answer/analysis/done/error, 30s timeout, graceful error handling)
│   │   ├── prompt_builder.py    # PromptBuilder: build_system_prompt, build_match_analysis_prompt, build_knockout_prompt, build_chat_context (bilingual zh-CN/en-US, reads skills/ markdowns)
│   │   ├── team_service.py      # TeamService: get_all_teams, get_team_by_code, get_teams_by_group, get_team_stats (lang + timezone aware)
│   │   ├── venue_service.py     # VenueService: get_all_venues (paginated)
│   │   ├── match_service.py     # MatchService: get_match_dates, get_matches (multi-filter + Redis live merge), get_match_by_id (with events + Redis live), get_live_matches (Redis live merge); uses shared app.utils.timezone
│   │   ├── group_service.py     # GroupService: get_all_groups (12 groups standings), get_group_detail (standings + matches); lang + timezone aware (shared utils)
│   │   ├── bracket_service.py   # BracketService: get_full_bracket (R32→F tree), get_bracket_by_round, get_predictions (TBD placeholder); uses shared app.utils.timezone
│   │   ├── cheer_service.py     # CheerService: get_cheers, vote_cheer (Redis HASH + in-memory fallback, IP rate limiting)
│   │   ├── stats_service.py     # StatsService: get_scorers (aggregated goal leaderboard from MatchEventRepository)
│   │   ├── live_service.py      # LiveService: update_match_status, update_score, update_activity, get_live_matches, get_match_live_data, apply_sync_data (Redis HASH + in-memory fallback, cache invalidation, WebSocket broadcast on state changes)
│   │   └── websocket_manager.py # ConnectionManager: connect/disconnect, subscribe/unsubscribe, broadcast/broadcast_to_match, get_manager singleton
│   ├── controllers/
│   │   ├── __init__.py          # Re-exports team_router, venue_router, match_router, group_router, bracket_router, cheer_router, ws_router, ai_router, stats_router
│   │   ├── ai_controller.py    # POST /api/ai/chat (SSE streaming: PromptBuilder + AIService.stream_chat → StreamingResponse text/event-stream)
│   │   ├── team_controller.py   # GET /api/teams, GET /api/teams/:code/stats, GET /api/teams/:code (uses get_team_service DI)
│   │   ├── venue_controller.py  # GET /api/venues (uses get_venue_service DI)
│   │   ├── match_controller.py  # GET /api/matches, /dates, /live, /:id (uses get_match_service DI)
│   │   ├── group_controller.py  # GET /api/groups, /:group (uses get_group_service DI)
│   │   ├── bracket_controller.py # GET /api/bracket, /predictions (uses get_bracket_service DI)
│   │   ├── cheer_controller.py  # GET /api/cheers/:matchId, POST /api/cheers/:matchId (IP rate-limited voting)
│   │   ├── stats_controller.py  # GET /api/stats/scorers (scorer leaderboard, uses StatsService DI)
│   │   └── ws_controller.py     # WS /ws/live (WebSocket endpoint: initial payload, subscribe/unsubscribe, ping/pong keep-alive)
│   ├── redis/
│   │   ├── __init__.py          # Re-exports RedisKeys, get_redis, init_redis_pool, close_redis_pool, is_redis_available
│   │   ├── client.py            # Redis connection pool (init_redis_pool, close_redis_pool, get_redis DI, is_redis_available)
│   │   └── keys.py              # RedisKeys namespace class (LIVE_MATCH, CHEERS_MATCH, WS_CONNECTIONS, CACHE_GROUPS, CACHE_BRACKET, SCRAPER_LOCK)
│   ├── utils/
│   │   ├── __init__.py          # Re-exports MarkdownParser, utc_to_local, get_host_city_time
│   │   ├── markdown_parser.py   # MarkdownParser: parses data/*.md → list[ParsedMatch] (72 group-stage fixtures)
│   │   └── timezone.py          # utc_to_local, get_host_city_time, convert_datetime (zoneinfo-based)
│   └── schemas/
│       ├── __init__.py          # Re-exports all schema classes
│       ├── common.py            # ApiResponse[T] + PaginatedResponse[T] generic envelopes
│       ├── team_schema.py       # TeamCreate/TeamUpdate DTOs + TeamResponse/TeamListResponse/TeamStatsResponse VOs (standing + match VOs)
│       ├── match_schema.py      # MatchQueryParams DTO + MatchResponse/MatchDetailResponse/MatchEventResponse VOs
│       ├── venue_schema.py      # VenueResponse VO
│       ├── group_schema.py      # GroupStandingResponse + GroupDetailResponse VOs
│       ├── bracket_schema.py    # BracketTeam/Match/Round/TreeResponse VOs (TBD support)
│       ├── cheer_schema.py      # CheerVoteRequest DTO + CheerResponse VO
│       ├── stats_schema.py      # ScorerItem VO (rank, player_name, team info, goals, assists)
│       ├── ai_schema.py         # ChatRequest DTO + SSEEvent + TeamAnalysisResponse VOs
│       ├── ws_schema.py         # WSEventType enum + WSMessage VO
│       └── scraper_schema.py   # ScrapedMatch/Schedule/LiveScore/LiveScoreBatch/Event/LiveEvent/MatchResult VOs for scraper data validation
├── scraping/                    # Web scraping infrastructure
│   ├── __init__.py              # Re-exports BaseScraper, FIFAScraper, LiveScoreScraper, DataSyncService, ScraperScheduler
│   ├── base_scraper.py          # BaseScraper: rate limiting (asyncio.Semaphore), retry with exponential backoff (max 3), structured logging, error hierarchy (ScraperError/Timeout/HTTP/Parse)
│   ├── fifa_scraper.py          # FIFAScraper(BaseScraper): scrape_match_schedule(), scrape_match_result(match_id); __NEXT_DATA__ JSON extraction from FIFA.com pages
│   ├── live_score_scraper.py    # LiveScoreScraper(BaseScraper): scrape_live_scores() -> ScrapedLiveScoreBatch; activity level estimation heuristic
│   ├── data_sync.py             # DataSyncService: sync_live_scores, sync_match_result, sync_group_standings; Redis distributed lock (scraper:lock)
│   └── scheduler.py             # ScraperScheduler: periodic task orchestrator (live 30s, finished 5min, group 1h); started in main.py lifespan when SCRAPER_ENABLED=true
├── scripts/                     # Database seeding scripts
│   ├── __init__.py              # Package init
│   ├── seed_data.py             # One-click init orchestrator (seed_venues→teams→matches→bracket→standings)
│   ├── generate_bracket.py      # Bracket tree verification + R32 group qualification mapping
│   ├── seed_teams.py            # Seed 48 teams (idempotent upsert by code)
│   ├── team_data.py             # 48-team roster data (bilingual, FIFA rankings, confederations)
│   ├── seed_venues.py           # Seed 16 venues (idempotent upsert by name)
│   ├── venue_data.py            # 16-venue roster data (city, country, IANA timezone, capacity)
│   └── seed_matches.py          # Seed 104 matches (72 group + 32 knockout, bracket linkage, TBD placeholder team)
└── scalable-beaming-riddle.md   # Backend architecture plan
```
